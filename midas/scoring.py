"""Signal scoring for Midas.

LIVE formula (operator directive 2026-07-04):

    score = max(strength × timing_weight) × neglect × liquidity × quality

The original thesis — signal convergence multiplying pop probability
non-linearly — was REFUTED at the 5-day horizon under two independent
countings (docs/midas_convergence_results_2026-07.md + correction
addendum): multi-signal names did not beat quiet single-signal names.
The convergence multiplier is therefore flattened out of the live
ranking; the strongest single timely signal carries the pick.

LEGACY formula (ghost leg only, graded weekly via /midas-ghost so the
convergence thesis can earn its way back with live evidence):

    score_legacy = convergence_multiplier × mean(strength × timing_weight) × neglect × liquidity × quality

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

# Convergence is supposed to mean independent informed-money sources agreeing
# — not one press release counted three times. An earnings report routinely
# trips earnings_beat (the EPS surprise), guidance_raised (often disclosed in
# the SAME 8-K), and volume_anomaly (the reaction bar TO that report) — three
# channel names, one underlying event. Added 2026-07-04 (LLM integration
# audit, finding: "convergence count treats correlated signals from a single
# event as independent"). insider_cluster/smart_money/activist_13d/
# short_squeeze are genuinely distinct filers/data sources and stay singleton
# clusters.
SIGNAL_EVENT_CLUSTERS = (
    frozenset({"earnings_beat", "guidance_raised", "volume_anomaly"}),
    frozenset({"insider_cluster"}),
    frozenset({"smart_money"}),
    frozenset({"activist_13d"}),
    frozenset({"short_squeeze"}),
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
CONVERGENCE_TIMING_FLOOR = 0.4

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

    if not active:
        return {"score": 0.0, "reason": "no_signals"}

    # Apply timing weights: strength × timing_weight per signal.
    weighted = {k: v * TIMING_WEIGHTS.get(k, 0.5) for k, v in active.items()}
    mean_strength = sum(weighted.values()) / len(weighted)

    # Signals below the timing floor still contribute to mean_strength
    # but don't elevate the convergence multiplier tier. Count DISTINCT
    # EVENT CLUSTERS with an active, above-floor member — not distinct
    # channel names — so a single earnings report can't earn a 2x or 3x
    # convergence bonus against itself (fixed 2026-07-04; see
    # SIGNAL_EVENT_CLUSTERS above).
    above_floor = {k for k in active if TIMING_WEIGHTS.get(k, 0.5) >= CONVERGENCE_TIMING_FLOOR}
    n_convergence = sum(1 for cluster in SIGNAL_EVENT_CLUSTERS if cluster & above_floor)
    conv = convergence_multiplier(n_convergence)
    neglect = neglect_score(market_cap)
    liq = _achilles_liquidity(market_cap)

    qv_factor = max(quality_value, QUALITY_VALUE_FLOOR) if quality_value > 0 else QUALITY_VALUE_FLOOR

    # LIVE score (operator directive 2026-07-04): the convergence
    # multiplier is FLATTENED out of the ranking. The pre-registered
    # convergence test refuted the multiplier under two independent
    # countings (docs/midas_convergence_results_2026-07.md and the
    # correction addendum) — multi-signal names did NOT beat quiet ones
    # at the 5-day horizon. The live pick is now "strongest single
    # TIMELY signal in a neglected, liquid name": MAX of the
    # timing-weighted strengths among above-floor signals, so an extra
    # weaker signal never raises OR lowers a name's rank, and slow
    # signals (13F/13D) still cannot carry a name on their own — the
    # timing-floor gate the multiplier used to enforce is preserved
    # explicitly. The old formula is kept below as score_legacy and
    # ghost-traded weekly so the convergence thesis can earn its way
    # back with live grades (see /midas-ghost).
    best_strength = max((weighted[k] for k in above_floor), default=0.0)
    raw = best_strength * neglect * liq * qv_factor

    # LEGACY score — the exact pre-2026-07-04 formula (convergence
    # multiplier x mean strength). Ghost leg only; never ranks live money.
    raw_legacy = conv * mean_strength * neglect * liq * qv_factor

    return {
        "score": raw,
        "score_legacy": raw_legacy,
        "convergence_count": n_convergence,
        "convergence_multiplier": conv,
        "active_signals": active,
        "timing_adjusted": weighted,
        "components": {
            "best_strength": best_strength,
            "convergence_legacy": conv,
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
