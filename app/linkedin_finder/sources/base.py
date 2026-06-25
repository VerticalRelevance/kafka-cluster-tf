"""The connector contract every licensed data provider must satisfy."""
from __future__ import annotations

from typing import Protocol

from ..models import ICPQuery, SearchPage, PersonProfile


class PeopleSource(Protocol):
    """Compliant, licensed people-data provider.

    Implementations call a vendor REST API (People Data Labs, Apollo, Proxycurl,
    etc.) under that vendor's ToS. They must NEVER scrape LinkedIn directly.
    """

    name: str

    def search(self, query: ICPQuery, cursor: str | None = None) -> SearchPage:
        """Return one page of candidates matching the ICP query."""
        ...

    def enrich(self, person: PersonProfile) -> PersonProfile:
        """Optionally hydrate a person with extra fields/signals."""
        ...
