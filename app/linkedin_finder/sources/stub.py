"""Deterministic fake source so the whole pipeline runs with zero API keys."""
from __future__ import annotations

from ..models import ICPQuery, SearchPage, PersonProfile, Signal

_COMPANIES = ["Northwind", "Acme Data", "Globex", "Initech", "Umbra Labs",
              "Stark Cloud", "Wayne Analytics", "Hooli", "Pied Piper", "Vandelay"]
_SIGNALS = [
    ("job_change", "Recently joined as {title}", 9),
    ("funding", "Company raised a Series B last month", 21),
    ("post", "Posted about real-time data platforms", 3),
    ("event", "Speaking at a Kafka Summit track", 14),
]


class StubSource:
    name = "stub"

    def search(self, query: ICPQuery, cursor: str | None = None) -> SearchPage:
        start = int(cursor) if cursor else 0
        page_size = 25
        people: list[PersonProfile] = []
        title = (query.titles or ["Head of Data"])[0]
        for i in range(start, start + page_size):
            company = _COMPANIES[i % len(_COMPANIES)]
            stype, sdetail, days = _SIGNALS[i % len(_SIGNALS)]
            people.append(PersonProfile(
                person_id=f"{query.label}-{i}",
                name=f"Pat Candidate {i}",
                title=title,
                company=company,
                location=(query.locations or ["Remote"])[0],
                summary=f"{title} at {company}. Works on {' '.join(query.keywords) or 'data systems'}.",
                source=self.name,
                public_url=f"https://example.com/in/pat-{i}",
                segment=query.label,
                signals=[Signal(stype, sdetail.format(title=title), days)],
            ))
        next_cursor = str(start + page_size) if start + page_size < 200 else None
        return SearchPage(people=people, next_cursor=next_cursor)

    def enrich(self, person: PersonProfile) -> PersonProfile:
        return person
