"""PEAD-focused scoring for Achilles.

score = surprise_strength x confirming_boost x neglect x liquidity

The base signal is always the earnings beat. Confirming signals (revenue
beat, guidance raise, short squeeze, insider pre-buy) boost the base
score but are never independent entry signals.

Preserved exports: surprise_strength, liquidity_score (used by Midas).
"""
from __future__ import annotations

import math
from typing import Optional


# --- Surprise-strength curve (shared with Midas) ---

SURPRISE_ANCHORS = (
    (0.0, 0.0),
    (3.0, 0.3),
    (5.0, 0.7),
    (10.0, 0.95),
    (20.0, 1.0),
    (50.0, 1.0),
    (100.0, 0.95),
    (200.0, 0.85),
    (500.0, 0.7),
)


def surprise_strength(surprise_pct: Optional[float]) -> float:
    if surprise_pct is None:
        return 1.0
    mag = abs(float(surprise_pct))
    if mag <= SURPRISE_ANCHORS[0][0]:
        return SURPRISE_ANCHORS[0][1]
    if mag >= SURPRISE_ANCHORS[-1][0]:
        return SURPRISE_ANCHORS[-1][1]
    for i in range(len(SURPRISE_ANCHORS) - 1):
        lo_s, lo_v = SURPRISE_ANCHORS[i]
        hi_s, hi_v = SURPRISE_ANCHORS[i + 1]
        if lo_s <= mag < hi_s:
            t = (mag - lo_s) / (hi_s - lo_s)
            return lo_v + t * (hi_v - lo_v)
    return SURPRISE_ANCHORS[-1][1]


# --- Liquidity curve (shared with Midas) ---

LIQ_ANCHORS = (
    (50_000_000, 0.3),
    (300_000_000, 0.6),
    (1_000_000_000, 0.8),
    (10_000_000_000, 1.0),
)

MEGACAP_DECAY_START = 50_000_000_000
MEGACAP_DECAY_END = 200_000_000_000
MEGACAP_FLOOR = 0.2


def liquidity_score(market_cap: Optional[float]) -> float:
    if not market_cap or market_cap <= 0:
        return 0.0
    cap = float(market_cap)
    if cap < LIQ_ANCHORS[0][0]:
        return 0.1
    if cap < LIQ_ANCHORS[-1][0]:
        for i in range(len(LIQ_ANCHORS) - 1):
            lo_cap, lo_s = LIQ_ANCHORS[i]
            hi_cap, hi_s = LIQ_ANCHORS[i + 1]
            if lo_cap <= cap < hi_cap:
                t = (math.log(cap) - math.log(lo_cap)) / (
                    math.log(hi_cap) - math.log(lo_cap)
                )
                return lo_s + t * (hi_s - lo_s)
    if cap <= MEGACAP_DECAY_START:
        return 1.0
    if cap >= MEGACAP_DECAY_END:
        return MEGACAP_FLOOR
    t = (math.log(cap) - math.log(MEGACAP_DECAY_START)) / (
        math.log(MEGACAP_DECAY_END) - math.log(MEGACAP_DECAY_START)
    )
    return 1.0 - t * (1.0 - MEGACAP_FLOOR)


# --- PEAD neglect curve (Achilles-specific) ---

NEGLECT_ANCHORS = (
    (50_000_000, 1.0),
    (200_000_000, 0.90),
    (500_000_000, 0.80),
    (2_000_000_000, 0.60),
    (10_000_000_000, 0.40),
    (50_000_000_000, 0.25),
)

MIN_MARKET_CAP = 50_000_000
MAX_MARKET_CAP = 50_000_000_000


def pead_neglect(market_cap: Optional[float]) -> float:
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


def market_cap_ok(market_cap: Optional[float]) -> bool:
    if not market_cap or market_cap <= 0:
        return False
    return MIN_MARKET_CAP <= market_cap <= MAX_MARKET_CAP


# --- Confirming signal boosts ---

REVENUE_BEAT_BOOST = 0.15
GUIDANCE_RAISED_BOOST = 0.25
SHORT_SQUEEZE_MAX_BOOST = 0.30
INSIDER_PREBUY_BOOST = 0.15


def confirming_boost(
    *,
    revenue_beat: bool = False,
    guidance_raised: bool = False,
    short_float_pct: Optional[float] = None,
    insider_prebuy: bool = False,
) -> float:
    boost = 1.0
    if revenue_beat:
        boost += REVENUE_BEAT_BOOST
    if guidance_raised:
        boost += GUIDANCE_RAISED_BOOST
    if short_float_pct and short_float_pct > 20.0:
        boost += min(SHORT_SQUEEZE_MAX_BOOST, short_float_pct / 100.0)
    if insider_prebuy:
        boost += INSIDER_PREBUY_BOOST
    return boost


def score_beat(
    *,
    surprise_pct: float,
    market_cap: Optional[float] = None,
    revenue_beat: bool = False,
    guidance_raised: bool = False,
    short_float_pct: Optional[float] = None,
    insider_prebuy: bool = False,
) -> dict:
    if not market_cap_ok(market_cap):
        return {"score": 0.0, "reason": "market_cap_filter"}

    base = surprise_strength(surprise_pct)
    if base <= 0:
        return {"score": 0.0, "reason": "no_surprise"}

    boost = confirming_boost(
        revenue_beat=revenue_beat,
        guidance_raised=guidance_raised,
        short_float_pct=short_float_pct,
        insider_prebuy=insider_prebuy,
    )
    neglect = pead_neglect(market_cap)
    liq = liquidity_score(market_cap)

    raw = base * boost * neglect * liq

    confirming = {}
    if revenue_beat:
        confirming["revenue_beat"] = True
    if guidance_raised:
        confirming["guidance_raised"] = True
    if short_float_pct and short_float_pct > 20.0:
        confirming["short_squeeze"] = short_float_pct
    if insider_prebuy:
        confirming["insider_prebuy"] = True

    return {
        "score": raw,
        "confirming_count": len(confirming),
        "confirming_signals": confirming,
        "components": {
            "surprise_strength": base,
            "confirming_boost": boost,
            "neglect": neglect,
            "liquidity": liq,
        },
    }
