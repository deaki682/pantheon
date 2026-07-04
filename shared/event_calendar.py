"""Shared IPO / lockup / spinoff / event-date calendar.

Nemesis needs spinoff dates, Proteus needs IPO + lockup expiries, Midas
cares about index reconstitutions — and until 2026-07-04 each of them
hand-scraped and hand-classified the same public aggregators per
session. This module is the build-once version: a validated, deduped,
source-cited event store at `cache/shared_event_calendar.json`, owned
by the `shared` prefix so any god may read it and any session that does
the classification work may deposit it.

Rules the writer enforces (the Delphi lesson — no stub rows):
- every event needs symbol, a known type, an ISO date, and a SPECIFIC
  source (URL or filing accession; "some website" doesn't validate);
- (symbol, type, date) is the identity — re-adding updates note/source
  instead of duplicating.
"""
from __future__ import annotations

import json
import os
from datetime import date as _date, timedelta
from typing import Iterable, Optional

CALENDAR_PATH = "cache/shared_event_calendar.json"

EVENT_TYPES = (
    "ipo",
    "lockup_expiry",
    "spinoff",
    "merger_close",
    "spac_deadline",
    "index_reconstitution",
    "other",
)


def _valid_iso(d: str) -> bool:
    try:
        _date.fromisoformat(d)
        return True
    except (TypeError, ValueError):
        return False


def validate_event(ev: dict) -> dict:
    """Return a normalized copy or raise ValueError."""
    sym = str(ev.get("symbol", "")).strip().upper()
    if not sym:
        raise ValueError("event needs a symbol")
    etype = str(ev.get("type", "")).strip().lower()
    if etype not in EVENT_TYPES:
        raise ValueError(f"unknown event type {etype!r}; one of {EVENT_TYPES}")
    d = str(ev.get("date", ""))[:10]
    if not _valid_iso(d):
        raise ValueError(f"bad date {ev.get('date')!r} (need YYYY-MM-DD)")
    source = str(ev.get("source", "")).strip()
    if len(source) < 8:
        raise ValueError("source required and must be specific (URL / accession)")
    out = {
        "symbol": sym,
        "type": etype,
        "date": d,
        "source": source,
        "note": str(ev.get("note", "")).strip(),
    }
    if ev.get("added_on"):
        out["added_on"] = str(ev["added_on"])[:10]
    return out


def _key(ev: dict) -> tuple:
    return (ev["symbol"], ev["type"], ev["date"])


def load_calendar(path: str = CALENDAR_PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    return data.get("events", []) if isinstance(data, dict) else []


def save_calendar(events: list[dict], path: str = CALENDAR_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    ordered = sorted(events, key=lambda e: (e["date"], e["symbol"], e["type"]))
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"events": ordered}, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def add_events(
    new_events: Iterable[dict],
    *,
    path: str = CALENDAR_PATH,
    today: Optional[str] = None,
) -> dict:
    """Validate + merge events into the calendar file.

    Returns {"added": n, "updated": n, "total": n}. Any invalid event
    raises before anything is written — all-or-nothing per call.
    """
    validated = [validate_event(e) for e in new_events]
    if today:
        for v in validated:
            v.setdefault("added_on", str(today)[:10])
    existing = {_key(e): e for e in load_calendar(path)}
    added = updated = 0
    for v in validated:
        k = _key(v)
        if k in existing:
            prev = existing[k]
            merged = dict(prev)
            if v["note"]:
                merged["note"] = v["note"]
            if v["source"] != prev.get("source"):
                merged["source"] = v["source"]
            if merged != prev:
                updated += 1
            existing[k] = merged
        else:
            existing[k] = v
            added += 1
    save_calendar(list(existing.values()), path)
    return {"added": added, "updated": updated, "total": len(existing)}


def upcoming(
    events: list[dict],
    *,
    today: str,
    within_days: int = 45,
    types: Optional[Iterable[str]] = None,
) -> list[dict]:
    """Events dated today..today+within_days, soonest first."""
    t0 = _date.fromisoformat(str(today)[:10])
    t1 = t0 + timedelta(days=within_days)
    wanted = set(t.lower() for t in types) if types else None
    hits = [
        e for e in events
        if _valid_iso(e.get("date", ""))
        and t0 <= _date.fromisoformat(e["date"]) <= t1
        and (wanted is None or e.get("type") in wanted)
    ]
    return sorted(hits, key=lambda e: (e["date"], e["symbol"]))
