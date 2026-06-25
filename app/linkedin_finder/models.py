"""Core data models for the connection finder."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ICPQuery:
    """An ideal-customer-profile / target segment query for a data provider."""
    label: str                       # e.g. "data-platform-leaders"
    titles: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    seniority: list[str] = field(default_factory=list)
    quota: int = 10                  # reserved slots for this segment in the final 50


@dataclass
class Preferences:
    """The user's preference profile + what they're currently working on."""
    me: str                          # how to describe yourself in outreach
    current_work: str                # live description of active projects
    connection_rationale: str        # why you generally want to connect
    tone: str = "warm, concise, not salesy"
    segments: list[ICPQuery] = field(default_factory=list)
    exclude_companies: list[str] = field(default_factory=list)


@dataclass
class Signal:
    """A timely reason to reach out now."""
    type: str                        # job_change | funding | post | event | mutual
    detail: str
    recency_days: int = 999


@dataclass
class PersonProfile:
    person_id: str
    name: str
    title: str
    company: str
    location: str = ""
    summary: str = ""
    source: str = "stub"
    public_url: str = ""
    signals: list[Signal] = field(default_factory=list)
    segment: str = ""                # which ICPQuery surfaced them

    def dedupe_key(self) -> str:
        return f"{self.name.lower().strip()}|{self.company.lower().strip()}"


@dataclass
class ScoredPerson:
    person: PersonProfile
    score: float
    breakdown: dict[str, float] = field(default_factory=dict)


@dataclass
class DraftedMessage:
    person_id: str
    note: str                        # <=300 char connection note
    followup: str                    # post-accept DM
    rationale: str                   # why this person, for your review


@dataclass
class SearchPage:
    people: list[PersonProfile]
    next_cursor: str | None = None


def to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses to plain dicts for storage/serialization."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj
