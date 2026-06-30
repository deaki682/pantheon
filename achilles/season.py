"""Earnings season calendar for Achilles.

Achilles actively trades during earnings seasons — roughly 5 weeks after
each quarter-end when small/mid-cap companies report. Outside these
windows, Achilles sits in cash.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

SEASON_WINDOWS = [
    ((1, 13), (2, 21)),
    ((4, 13), (5, 21)),
    ((7, 13), (8, 21)),
    ((10, 13), (11, 21)),
]


def _parse_date(d):
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    return d


def is_earnings_season(today) -> bool:
    d = _parse_date(today)
    for (sm, sd), (em, ed) in SEASON_WINDOWS:
        start = date(d.year, sm, sd)
        end = date(d.year, em, ed)
        if start <= d <= end:
            return True
    return False


def current_season(today) -> Optional[tuple[str, str]]:
    d = _parse_date(today)
    for (sm, sd), (em, ed) in SEASON_WINDOWS:
        start = date(d.year, sm, sd)
        end = date(d.year, em, ed)
        if start <= d <= end:
            return (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    return None


def next_season(today) -> tuple[str, str]:
    d = _parse_date(today)
    for (sm, sd), (em, ed) in SEASON_WINDOWS:
        start = date(d.year, sm, sd)
        if start > d:
            end = date(d.year, em, ed)
            return (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    sm, sd = SEASON_WINDOWS[0][0]
    em, ed = SEASON_WINDOWS[0][1]
    return (
        date(d.year + 1, sm, sd).strftime("%Y-%m-%d"),
        date(d.year + 1, em, ed).strftime("%Y-%m-%d"),
    )
