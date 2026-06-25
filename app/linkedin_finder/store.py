"""Persistence: local JSON for dev, DynamoDB for serverless.

Tracks `seen` people (so they never resurface) and saves each `DailyBatch`.
"""
from __future__ import annotations

import json
import os
from typing import Any

from .config import Config


class LocalStore:
    def __init__(self, cfg: Config):
        self.dir = cfg.local_dir
        os.makedirs(self.dir, exist_ok=True)
        self._seen_path = os.path.join(self.dir, "seen.json")

    def seen_keys(self) -> set[str]:
        if not os.path.exists(self._seen_path):
            return set()
        with open(self._seen_path) as f:
            return set(json.load(f))

    def mark_seen(self, keys: list[str]) -> None:
        keys_set = self.seen_keys() | set(keys)
        with open(self._seen_path, "w") as f:
            json.dump(sorted(keys_set), f, indent=2)

    def save_batch(self, date: str, batch: dict[str, Any]) -> str:
        path = os.path.join(self.dir, f"batch-{date}.json")
        with open(path, "w") as f:
            json.dump(batch, f, indent=2)
        return path


class DynamoStore:
    """DynamoDB-backed store. Single table, keyed by (pk, sk).

    pk='seen'              sk=<dedupe_key>     -> seen marker
    pk='batch#<date>'      sk='meta'           -> the day's 50 + drafts
    """
    def __init__(self, cfg: Config):
        import boto3  # imported lazily so local dev needs no boto3
        self.table = boto3.resource("dynamodb").Table(cfg.dynamo_table)

    def seen_keys(self) -> set[str]:
        resp = self.table.query(
            KeyConditionExpression="pk = :p",
            ExpressionAttributeValues={":p": "seen"},
        )
        return {item["sk"] for item in resp.get("Items", [])}

    def mark_seen(self, keys: list[str]) -> None:
        with self.table.batch_writer() as bw:
            for k in keys:
                bw.put_item(Item={"pk": "seen", "sk": k})

    def save_batch(self, date: str, batch: dict[str, Any]) -> str:
        self.table.put_item(Item={"pk": f"batch#{date}", "sk": "meta", "data": json.dumps(batch)})
        return f"batch#{date}"


def get_store(cfg: Config):
    return DynamoStore(cfg) if cfg.store_backend == "dynamo" else LocalStore(cfg)
