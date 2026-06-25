"""Orchestrates one daily run: discover -> filter -> score -> pick 50 -> draft -> save."""
from __future__ import annotations

from .config import Config, load_config
from .models import Preferences, PersonProfile, to_jsonable
from .sources import get_source
from .scoring import filter_candidates, score_person, select_daily
from .messaging import draft_message
from .store import get_store


def discover(cfg: Config, prefs: Preferences) -> list[PersonProfile]:
    source = get_source(cfg)
    pool: list[PersonProfile] = []
    for seg in prefs.segments:
        cursor = None
        pulled = 0
        while pulled < cfg.candidate_pool // max(1, len(prefs.segments)):
            page = source.search(seg, cursor)
            pool.extend(page.people)
            pulled += len(page.people)
            cursor = page.next_cursor
            if not cursor:
                break
    return pool


def run(prefs: Preferences, date: str, cfg: Config | None = None) -> dict:
    cfg = cfg or load_config()
    store = get_store(cfg)

    raw = discover(cfg, prefs)
    candidates = filter_candidates(raw, prefs, store.seen_keys())
    scored = [score_person(p, prefs, cfg) for p in candidates]
    chosen = select_daily(scored, cfg)
    drafts = [draft_message(sp, prefs, cfg) for sp in chosen]

    batch = {
        "date": date,
        "source": cfg.people_source,
        "considered": len(raw),
        "after_filter": len(candidates),
        "selected": len(chosen),
        "people": [
            {
                "person": to_jsonable(sp.person),
                "score": sp.score,
                "breakdown": sp.breakdown,
                "message": to_jsonable(msg),
            }
            for sp, msg in zip(chosen, drafts)
        ],
    }

    store.save_batch(date, batch)
    store.mark_seen([sp.person.dedupe_key() for sp in chosen])
    return batch
