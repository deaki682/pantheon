"""Earnings surprise detection and qualification.

The PEAD edge lives in three things:
  1. Direction — beat vs miss (only go long on beats)
  2. Surprise magnitude — 10-20% surprise is the sweet spot
  3. Speed — detect before the market fully reprices

This module fetches earnings results (actual vs estimate EPS) from the
broker and computes the surprise signal that drives event strength.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from shared import broker

log = logging.getLogger("achilles.earnings")


@dataclass
class EarningsSurprise:
    symbol: str
    actual_eps: float
    estimate_eps: float
    surprise_pct: float      # (actual - estimate) / |estimate| * 100
    is_beat: bool             # positive surprise
    report_date: str = ""     # YYYY-MM-DD from the earnings data
    quarter: str = ""         # e.g. "Q3 2025"


def compute_surprise(actual: float, estimate: float) -> tuple[float, bool]:
    """Compute surprise % and direction.

    Returns (surprise_pct, is_beat). Uses absolute estimate as denominator
    to handle negative EPS correctly. When estimate is near-zero, uses
    the absolute difference as the signal.
    """
    if abs(estimate) < 0.005:
        # Near-zero estimate: use raw difference
        # A penny of surprise on a zero estimate is meaningful
        diff = actual - estimate
        return (diff * 100.0, diff > 0)
    surprise_pct = (actual - estimate) / abs(estimate) * 100.0
    return (surprise_pct, actual > estimate)


def fetch_earnings_surprise(symbol: str) -> Optional[EarningsSurprise]:
    """Fetch the most recent earnings result and compute surprise.

    Returns None if earnings data unavailable or if no estimate exists
    (can't compute surprise without a consensus estimate).
    """
    results = broker.get_earnings(symbol)
    if not results:
        return None

    # Find the most recent report with both actual and estimate
    for r in results:
        actual = r.get("actual_eps")
        estimate = r.get("estimate_eps")
        if actual is None or estimate is None:
            continue
        try:
            actual_f = float(actual)
            estimate_f = float(estimate)
        except (TypeError, ValueError):
            continue

        surprise_pct, is_beat = compute_surprise(actual_f, estimate_f)

        return EarningsSurprise(
            symbol=symbol.upper(),
            actual_eps=actual_f,
            estimate_eps=estimate_f,
            surprise_pct=surprise_pct,
            is_beat=is_beat,
            report_date=r.get("report_date", r.get("report", {}).get("date", "")),
            quarter=r.get("quarter", ""),
        )
    return None


def fetch_earnings_calendar(symbols: list[str]) -> dict[str, dict]:
    """Fetch upcoming earnings dates for a list of symbols.

    Returns {SYMBOL: {report_date, is_before_market}} for symbols
    with earnings in the next 14 days.
    """
    return broker.get_earnings_calendar(symbols)


# ── qualification ─────────────────────────────────────────────────────

SURPRISE_MIN_PCT = 3.0      # Below this, likely noise
SURPRISE_MAX_PCT = 100.0    # Above this, negative expectancy (reversals)


def is_actionable_beat(surprise: EarningsSurprise) -> bool:
    """Check if a beat is in the actionable sweet spot."""
    if not surprise.is_beat:
        return False
    return SURPRISE_MIN_PCT <= surprise.surprise_pct <= SURPRISE_MAX_PCT


def surprise_to_strength(surprise: EarningsSurprise) -> float:
    """Convert a surprise into event strength using the scoring curve.

    This wraps the existing surprise_strength() function from scoring.py
    but adds direction: misses get 0.0, beats get the curve value.
    """
    if not surprise.is_beat:
        return 0.0
    from .scoring import surprise_strength
    return surprise_strength(surprise.surprise_pct)
