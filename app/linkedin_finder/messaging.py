"""Draft a personalized connection note + follow-up per person, via Claude.

Facts-only prompting: the model may only reference details we pass in (the
matched signal), never invented shared history. Falls back to a deterministic
template in dry-run (no ANTHROPIC_API_KEY) so the pipeline always completes.
"""
from __future__ import annotations

import json

from .config import Config
from .models import Preferences, ScoredPerson, DraftedMessage

_SYSTEM = (
    "You draft LinkedIn connection notes. Rules: reference ONLY the facts provided "
    "(never invent shared history or mutual connections); give one honest reason to "
    "connect tied to the sender's current work; one low-pressure ask; warm, not salesy. "
    "The note MUST be <= {limit} characters. Return STRICT JSON: "
    '{{"note": "...", "followup": "...", "rationale": "..."}}'
)


def _template(sp: ScoredPerson, prefs: Preferences, limit: int) -> DraftedMessage:
    p = sp.person
    signal = p.signals[0].detail if p.signals else f"your work at {p.company}"
    note = f"Hi {p.name.split()[0]} — noticed {signal.lower()}. I'm {prefs.me}; would love to connect."
    return DraftedMessage(
        person_id=p.person_id,
        note=note[:limit],
        followup=(f"Thanks for connecting! {prefs.connection_rationale} "
                  f"Given your work at {p.company}, I'd value comparing notes sometime."),
        rationale=f"score={sp.score} signals={[s.type for s in p.signals]}",
    )


def draft_message(sp: ScoredPerson, prefs: Preferences, cfg: Config) -> DraftedMessage:
    if not cfg.anthropic_api_key:
        return _template(sp, prefs, cfg.note_char_limit)

    try:
        import anthropic
    except ImportError:
        return _template(sp, prefs, cfg.note_char_limit)

    p = sp.person
    facts = {
        "their_name": p.name,
        "their_title": p.title,
        "their_company": p.company,
        "trigger_signal": p.signals[0].detail if p.signals else "",
        "their_summary": p.summary,
        "me": prefs.me,
        "current_work": prefs.current_work,
        "connection_rationale": prefs.connection_rationale,
        "tone": prefs.tone,
    }
    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    resp = client.messages.create(
        model=cfg.model,
        max_tokens=400,
        system=_SYSTEM.format(limit=cfg.note_char_limit),
        messages=[{"role": "user", "content": json.dumps(facts)}],
    )
    text = resp.content[0].text.strip()
    try:
        data = json.loads(text)
        msg = DraftedMessage(
            person_id=p.person_id,
            note=data["note"][: cfg.note_char_limit],
            followup=data.get("followup", ""),
            rationale=data.get("rationale", ""),
        )
    except (json.JSONDecodeError, KeyError):
        return _template(sp, prefs, cfg.note_char_limit)

    return _quality_gate(msg, cfg) or _template(sp, prefs, cfg.note_char_limit)


def _quality_gate(msg: DraftedMessage, cfg: Config) -> DraftedMessage | None:
    """Reject drafts that violate hard constraints; returns None on failure."""
    if not msg.note or len(msg.note) > cfg.note_char_limit:
        return None
    banned = ("synergy", "circle back", "pick your brain", "dear sir")
    if any(b in msg.note.lower() for b in banned):
        return None
    return msg
