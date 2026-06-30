"""Convergence-weighted scoring for Midas.

The edge is signal convergence: when multiple independent informed-money
signals fire on the same name simultaneously, the probability of a
short-term pop increases non-linearly.

score = convergence_multiplier × mean(strength × timing_weight) × neglect × liquidity

Each signal's raw strength is multiplied by a timing weight that reflects
how well the signal's resolution timescale matches Midas's 5-day hold.
Squeezes and earnings beats (days) get 1.0; activist 13D (months) gets 0.2.

Signals (7 channels + quality floor):
  1. insider_cluster   — 2+ insiders buying $10k+ in tight window
  2. earnings_beat     — EPS surprise via surprise_strength curve
  3. smart_money       — Berkshire/Baupost/Pershing etc. accumulated
  4. activist_13d      — fresh Schedule 13D filing
  5. guidance_raised   — forward guidance raised in 8-K
  6. volume_anomaly    — unusual recent volume vs 30-day average (timely)
  7. short_squeeze     — high short float (>20%), squeeze setup with other signals
  8. quality_value     — fundamental quality × valuation (floor, not signal)
"""
from __future__ import annotations

import math
from typing import Optional

from achilles.scoring import liquidity_score as _achilles_liquidity


CONVERGENCE_MULTIPLIERS = {
    0: 0.0,
    1: 1.0,
    2: 2.5,
    3: 5.0,
}
CONVERGENCE_MAX = 8.0

SIGNAL_CHANNELS = (
    "insider_cluster",
    "earnings_beat",
    "smart_money",
    "activist_13d",
    "guidance_raised",
    "volume_anomaly",
    "short_squeeze",
)

# How well each signal's resolution timescale fits a 5-day hold.
# Signals that can pay off within a week get 1.0; multi-month signals
# get discounted so they don't dominate the convergence ranking.
TIMING_WEIGHTS = {
    "short_squeeze": 1.0,       # days–weeks
    "earnings_beat": 1.0,       # 1–5 days (PEAD)
    "volume_anomaly": 0.9,      # days
    "guidance_raised": 0.8,     # days–weeks
    "insider_cluster": 0.5,     # weeks–months
    "smart_money": 0.3,         # months (13F is 45-day delayed)
    "activist_13d": 0.2,        # 3–12 months
}

QUALITY_VALUE_FLOOR = 0.3

MIN_MARKET_CAP = 50_000_000
MAX_MARKET_CAP = 20_000_000_000
MIN_LISTING_DAYS = 90
STALENESS_PCT = 0.15

NEGLECT_ANCHORS = (
    (50_000_000, 1.0),
    (500_000_000, 0.85),
    (2_000_000_000, 0.65),
    (10_000_000_000, 0.45),
    (20_000_000_000, 0.3),
)


def convergence_multiplier(n_signals: int) -> float:
    if n_signals <= 0:
        return 0.0
    if n_signals in CONVERGENCE_MULTIPLIERS:
        return CONVERGENCE_MULTIPLIERS[n_signals]
    return CONVERGENCE_MAX


def neglect_score(market_cap: Optional[float]) -> float:
    """Under-followed names score HIGHER — PEAD drift is strongest where
    coverage is thin. Inverse of Achilles's liquidity_score."""
    if not market_cap or market_cap <= 0:
        return 0.0
    cap = float(market_cap)
    if cap < NEGLECT_ANCHORS[0][0]:
        return 0.5
    if cap >= NEGLECT_ANCHORS[-1][0]:
        return NEGLECT_ANCHORS[-1][1]
    for i in range(len(NEGLECT_ANCHORS) - 1):
        lo_cap, lo_s = NEGLECT_ANCHORS[i]
        hi_cap, hi_s = NEGLECT_ANCHORS[i + 1]
        if lo_cap <= cap < hi_cap:
            t = (math.log(cap) - math.log(lo_cap)) / (
                math.log(hi_cap) - math.log(lo_cap)
            )
            return lo_s + t * (hi_s - lo_s)
    return NEGLECT_ANCHORS[-1][1]


def liquidity_ok(market_cap: Optional[float]) -> bool:
    if not market_cap or market_cap <= 0:
        return False
    return MIN_MARKET_CAP <= market_cap <= MAX_MARKET_CAP


def score_candidate(
    *,
    signals: dict[str, float],
    quality_value: float = 0.0,
    market_cap: Optional[float] = None,
) -> dict:
    """Score a candidate by signal convergence.

    signals: maps signal channel name -> strength (0..1). 0 = not firing.
    quality_value: combined quality × valuation score (0..1).
    market_cap: for neglect and liquidity checks.

    Returns dict with score, convergence_count, active_signals, components.
    """
    if not liquidity_ok(market_cap):
        return {"score": 0.0, "reason": "liquidity_filter"}

    active = {k: v for k, v in signals.items() if k in SIGNAL_CHANNELS and v > 0}
    n_active = len(active)

    if n_active == 0:
        return {"score": 0.0, "reason": "no_signals"}

    # Apply timing weights: strength × timing_weight per signal.
    # This discounts slow-resolving signals (activist, 13F) so they
    # don't dominate the ranking for a 5-day hold window.
    weighted = {k: v * TIMING_WEIGHTS.get(k, 0.5) for k, v in active.items()}
    mean_strength = sum(weighted.values()) / len(weighted)

    conv = convergence_multiplier(n_active)
    neglect = neglect_score(market_cap)
    liq = _achilles_liquidity(market_cap)

    qv_factor = max(quality_value, QUALITY_VALUE_FLOOR) if quality_value > 0 else QUALITY_VALUE_FLOOR

    raw = conv * mean_strength * neglect * liq * qv_factor

    return {
        "score": raw,
        "convergence_count": n_active,
        "convergence_multiplier": conv,
        "active_signals": active,
        "timing_adjusted": weighted,
        "components": {
            "convergence": conv,
            "mean_strength": mean_strength,
            "neglect": neglect,
            "liquidity": liq,
            "quality_value": qv_factor,
        },
    }


def rank_candidates(candidates: list[dict], *, top_n: int = 10) -> list[dict]:
    """Sort candidates by score descending, return top N."""
    scored = [c for c in candidates if c.get("score", 0) > 0]
    scored.sort(key=lambda c: c["score"], reverse=True)
    return scored[:top_n]
