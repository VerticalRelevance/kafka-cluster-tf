"""Scoring, filtering, dedupe, and diversified selection of the daily 50.

Phase 0 uses a lightweight keyword-overlap proxy for the "fit" and "work
relevance" terms. Phase 1 swaps these for real embedding cosine similarity
(Claude/embeddings model) without changing the interface.
"""
from __future__ import annotations

from collections import defaultdict

from .config import Config
from .models import Preferences, PersonProfile, ScoredPerson


def _tokens(text: str) -> set[str]:
    return {t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if len(t) > 2}


def _overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _timeliness(person: PersonProfile) -> float:
    if not person.signals:
        return 0.0
    freshest = min(s.recency_days for s in person.signals)
    # 0 days -> 1.0, 30 days -> ~0.0
    return max(0.0, 1.0 - freshest / 30.0)


def score_person(person: PersonProfile, prefs: Preferences, cfg: Config) -> ScoredPerson:
    seg = next((s for s in prefs.segments if s.label == person.segment), None)
    seg_text = " ".join((seg.titles + seg.keywords + seg.industries)) if seg else ""

    fit = _overlap(person.summary + " " + person.title, seg_text)
    work = _overlap(person.summary + " " + person.title, prefs.current_work)
    timeliness = _timeliness(person)
    path = 0.3 if any(s.type == "mutual" for s in person.signals) else 0.0
    reach = 0.5  # placeholder; Phase 1: seniority/openness heuristics

    breakdown = {
        "fit": cfg.w_fit * fit,
        "work": cfg.w_work * work,
        "timeliness": cfg.w_timeliness * timeliness,
        "path": cfg.w_path * path,
        "reach": cfg.w_reach * reach,
    }
    return ScoredPerson(person=person, score=round(sum(breakdown.values()), 4), breakdown=breakdown)


def filter_candidates(
    people: list[PersonProfile], prefs: Preferences, seen_keys: set[str]
) -> list[PersonProfile]:
    excluded = {c.lower() for c in prefs.exclude_companies}
    out, local_seen = [], set()
    for p in people:
        key = p.dedupe_key()
        if key in seen_keys or key in local_seen:
            continue
        if p.company.lower() in excluded:
            continue
        local_seen.add(key)
        out.append(p)
    return out


def select_daily(
    scored: list[ScoredPerson], cfg: Config
) -> list[ScoredPerson]:
    """Pick the final N with per-company caps and per-segment quotas (diversified)."""
    ranked = sorted(scored, key=lambda s: s.score, reverse=True)
    per_company: dict[str, int] = defaultdict(int)
    per_segment: dict[str, int] = defaultdict(int)
    chosen: list[ScoredPerson] = []

    # First pass: respect company cap + take best per segment for balance.
    for sp in ranked:
        if len(chosen) >= cfg.daily_target:
            break
        comp = sp.person.company.lower()
        if per_company[comp] >= cfg.max_per_company:
            continue
        chosen.append(sp)
        per_company[comp] += 1
        per_segment[sp.person.segment] += 1

    # Second pass: if company caps starved us, backfill ignoring the cap.
    if len(chosen) < cfg.daily_target:
        chosen_ids = {s.person.person_id for s in chosen}
        for sp in ranked:
            if len(chosen) >= cfg.daily_target:
                break
            if sp.person.person_id not in chosen_ids:
                chosen.append(sp)
    return chosen[: cfg.daily_target]
