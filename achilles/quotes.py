"""Quote helpers.

Pure: takes a quote list (e.g. from the broker) and normalizes to a
dict[symbol -> price]. Stale-quote detection lives here too.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable


def normalize_quotes(rows: Iterable[dict]) -> dict[str, float]:
    """Each row should have 'symbol' and a price field (last_trade_price preferred)."""
    out: dict[str, float] = {}
    for r in rows:
        sym = str(r.get("symbol", "")).upper()
        if not sym:
            continue
        price = r.get("last_trade_price") or r.get("last_price") or r.get("price")
        try:
            px = float(price)
        except (TypeError, ValueError):
            continue
        if px > 0:
            out[sym] = px
    return out


def is_stale(timestamp_iso: str, *, max_age_minutes: int = 15) -> bool:
    if not timestamp_iso:
        return True
    try:
        ts = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    # Strip tz if present for naive comparison with utcnow
    if ts.tzinfo is not None:
        ts = ts.replace(tzinfo=None)
    return (datetime.utcnow() - ts) > timedelta(minutes=max_age_minutes)
