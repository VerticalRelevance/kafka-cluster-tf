"""Environment-driven configuration for the connection finder."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    # Discovery
    people_source: str = field(default_factory=lambda: os.getenv("PEOPLE_SOURCE", "stub"))
    daily_target: int = field(default_factory=lambda: int(os.getenv("DAILY_TARGET", "50")))
    candidate_pool: int = field(default_factory=lambda: int(os.getenv("CANDIDATE_POOL", "500")))

    # Scoring weights (tunable; learned from feedback over time)
    w_fit: float = field(default_factory=lambda: float(os.getenv("W_FIT", "0.35")))
    w_work: float = field(default_factory=lambda: float(os.getenv("W_WORK", "0.30")))
    w_timeliness: float = field(default_factory=lambda: float(os.getenv("W_TIMELINESS", "0.15")))
    w_path: float = field(default_factory=lambda: float(os.getenv("W_PATH", "0.12")))
    w_reach: float = field(default_factory=lambda: float(os.getenv("W_REACH", "0.08")))

    # Diversification caps for the final 50
    max_per_company: int = field(default_factory=lambda: int(os.getenv("MAX_PER_COMPANY", "3")))

    # Messaging
    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8"))
    note_char_limit: int = 300  # LinkedIn connection-note hard limit

    # Persistence
    store_backend: str = field(default_factory=lambda: os.getenv("STORE_BACKEND", "local"))
    dynamo_table: str = field(default_factory=lambda: os.getenv("DYNAMO_TABLE", "linkedin-finder"))
    local_dir: str = field(default_factory=lambda: os.getenv("LOCAL_DIR", "./.data"))

    # Provider keys
    pdl_api_key: str | None = field(default_factory=lambda: os.getenv("PDL_API_KEY"))
    apollo_api_key: str | None = field(default_factory=lambda: os.getenv("APOLLO_API_KEY"))


def load_config() -> Config:
    return Config()
