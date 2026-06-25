"""Apollo.io connector (stubbed call surface).

Fill in the real REST calls against https://api.apollo.io/v1/mixed_people/search .
"""
from __future__ import annotations

from ..models import ICPQuery, SearchPage, PersonProfile


class ApolloSource:
    name = "apollo"

    def __init__(self, api_key: str | None):
        if not api_key:
            raise ValueError("APOLLO_API_KEY is required for PEOPLE_SOURCE=apollo")
        self.api_key = api_key

    def _build_params(self, query: ICPQuery, page: int) -> dict:
        return {
            "person_titles": query.titles,
            "person_locations": query.locations,
            "q_keywords": " ".join(query.keywords),
            "page": page,
            "per_page": 25,
        }

    def search(self, query: ICPQuery, cursor: str | None = None) -> SearchPage:
        # TODO: POST self._build_params(...) to Apollo with api_key in the body,
        # paginate via `page`, map `people[]` -> PersonProfile.
        raise NotImplementedError(
            "Wire up the Apollo /mixed_people/search REST call here."
        )

    def enrich(self, person: PersonProfile) -> PersonProfile:
        return person
