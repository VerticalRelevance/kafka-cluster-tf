#!/usr/bin/env python3
"""Run the full pipeline locally with stub data. No AWS, no API keys required.

  python run_local.py

Set ANTHROPIC_API_KEY for real Claude-drafted notes; PDL_API_KEY/APOLLO_API_KEY
plus PEOPLE_SOURCE=pdl|apollo for a real provider.
"""
from __future__ import annotations

import datetime

from linkedin_finder.config import load_config
from linkedin_finder.pipeline import run
from sample_preferences import sample_preferences


def main() -> None:
    cfg = load_config()
    prefs = sample_preferences()
    date = datetime.date.today().isoformat()
    batch = run(prefs, date, cfg)

    print(f"\n=== Daily batch {batch['date']} ({batch['source']}) ===")
    print(f"considered={batch['considered']} after_filter={batch['after_filter']} "
          f"selected={batch['selected']}\n")
    for i, row in enumerate(batch["people"][:10], 1):
        p, msg = row["person"], row["message"]
        print(f"{i:>2}. {p['name']} — {p['title']} @ {p['company']}  (score {row['score']})")
        print(f"    note: {msg['note']}")
    if batch["selected"] > 10:
        print(f"\n... and {batch['selected'] - 10} more. Full batch saved under "
              f"{cfg.local_dir}/batch-{batch['date']}.json")


if __name__ == "__main__":
    main()
