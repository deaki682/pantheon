"""Cadence helpers.

Oracle runs research every few days, with a heavy quarterly screening pass.
This module tracks last-run timestamps and reports whether it's time.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone


RESEARCH_INTERVAL_DAYS = 3
SCREEN_INTERVAL_DAYS = 90


# NYSE full-closure holidays (observed dates). Extend annually; a date
# past the table's horizon fails loudly in is_trading_day rather than
# silently treating a holiday as open.
US_MARKET_HOLIDAYS: frozenset[str] = frozenset({
    # 2026
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
    "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
    "2026-11-26", "2026-12-25",
    # 2027
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
    "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06",
    "2027-11-25", "2027-12-24",
})

_HOLIDAY_TABLE_YEARS = frozenset({2026, 2027})


def is_trading_day(iso_date: str) -> bool:
    """True if the US equity market is open on iso_date (YYYY-MM-DD).

    Weekends and NYSE holidays are closed. Raises ValueError for years
    outside the holiday table — extend US_MARKET_HOLIDAYS rather than
    guessing.
    """
    d = datetime.fromisoformat(iso_date[:10])
    if d.year not in _HOLIDAY_TABLE_YEARS:
        raise ValueError(
            f"{iso_date}: year {d.year} not in US_MARKET_HOLIDAYS table; extend it"
        )
    if d.weekday() >= 5:
        return False
    return iso_date[:10] not in US_MARKET_HOLIDAYS


def ran_today(path: str, key: str, *, today: str | None = None) -> bool:
    """True if mark_run(path, key) was already called on today's UTC date.

    Unlike should_run's rolling 24h window, this compares calendar dates,
    so a run at 15:00 doesn't push the next day's eligible run past 15:00.
    """
    today = (today or datetime.utcnow().date().isoformat())[:10]
    raw = _read(path).get(key, "")
    return isinstance(raw, str) and raw[:10] == today


def _read(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def _aware_utc(ts: datetime) -> datetime:
    """Normalize any datetime to timezone-aware UTC. Cadence files in the wild
    hold a MIX of naive ('2026-07-05T12:00:00'), offset-aware ('...+00:00'), and
    Z-suffixed timestamps; comparing naive to aware raises TypeError, which
    killed Zeus's whole gate block (audit 2026-07-10). Naive is assumed UTC —
    every writer in the house stamps UTC."""
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def mark_run(path: str, key: str, *, now: datetime | None = None) -> None:
    now = _aware_utc(now or datetime.now(timezone.utc))
    d = _read(path)
    d[key] = now.isoformat()
    _write(path, d)


def days_since(path: str, key: str, *, now: datetime | None = None) -> float | None:
    now = _aware_utc(now or datetime.now(timezone.utc))
    d = _read(path)
    raw = d.get(key)
    if not raw:
        return None
    try:
        ts = _aware_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
    except (ValueError, TypeError, AttributeError):
        return None
    return (now - ts).total_seconds() / 86_400.0


def should_run(
    path: str, key: str, interval_days: float, *, now: datetime | None = None
) -> bool:
    elapsed = days_since(path, key, now=now)
    if elapsed is None:
        return True
    return elapsed >= interval_days
