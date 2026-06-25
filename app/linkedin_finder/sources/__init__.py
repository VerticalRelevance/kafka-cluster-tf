"""Swappable people-data sources. Add a provider by implementing PeopleSource."""
from __future__ import annotations

from ..config import Config
from .base import PeopleSource
from .stub import StubSource
from .pdl import PDLSource
from .apollo import ApolloSource


def get_source(cfg: Config) -> PeopleSource:
    name = cfg.people_source.lower()
    if name == "stub":
        return StubSource()
    if name == "pdl":
        return PDLSource(cfg.pdl_api_key)
    if name == "apollo":
        return ApolloSource(cfg.apollo_api_key)
    raise ValueError(f"Unknown PEOPLE_SOURCE={name!r} (expected stub|pdl|apollo)")
