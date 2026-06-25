"""People Data Labs connector (stubbed call surface).

Fill in the real REST calls against https://api.peopledatalabs.com/v5/person/search .
Kept import-light so the pipeline runs without the dependency installed.
"""
from __future__ import annotations

from ..models import ICPQuery, SearchPage, PersonProfile, Signal


class PDLSource:
    name = "pdl"

    def __init__(self, api_key: str | None):
        if not api_key:
            raise ValueError("PDL_API_KEY is required for PEOPLE_SOURCE=pdl")
        self.api_key = api_key

    def _build_query(self, query: ICPQuery) -> dict:
        """Translate an ICPQuery into a PDL Elasticsearch-style query."""
        must = []
        if query.titles:
            must.append({"terms": {"job_title": [t.lower() for t in query.titles]}})
        if query.industries:
            must.append({"terms": {"industry": [i.lower() for i in query.industries]}})
        if query.locations:
            must.append({"terms": {"location_country": [l.lower() for l in query.locations]}})
        return {"query": {"bool": {"must": must}}, "size": 25}

    def search(self, query: ICPQuery, cursor: str | None = None) -> SearchPage:
        # TODO: POST self._build_query(query) to PDL with header X-Api-Key,
        # paginate via the returned `scroll_token`, map records -> PersonProfile.
        raise NotImplementedError(
            "Wire up the PDL /person/search REST call here. "
            "Map each record to PersonProfile and signals from `job_last_changed`, etc."
        )

    def enrich(self, person: PersonProfile) -> PersonProfile:
        return person
