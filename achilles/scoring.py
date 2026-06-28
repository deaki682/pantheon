"""Multiplicative event scoring.

score = base_rate × event_strength × company_quality × liquidity × time_decay

Multiplicative is intentional: any weak factor hurts the whole score. You
can't compensate for terrible liquidity with great event strength.

Disqualifiers (universal OR per-class) zero the score entirely.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Iterable, Optional

from .playbooks import CLASS_DISQUALIFIERS, Playbook, UNIVERSAL_DISQUALIFIERS


# Time decay constants
TIME_HALFLIFE_HOURS = 48.0

# Surprise-strength curve for earnings_reaction
# Backtest (214 trades, Q4 2025): sweet spot is 5-30% surprise.
#   3-10%  → 73.6% WR, Sharpe 1.52
#   10-20% → 67.6% WR, Sharpe 2.70
#   >100%  → 41.7% WR, negative expectancy
SURPRISE_ANCHORS = (
    (0.0, 0.0),     # inline with estimate — no signal
    (3.0, 0.3),     # too small, likely noise
    (5.0, 0.7),     # borderline actionable
    (10.0, 0.95),   # strong sweet spot
    (20.0, 1.0),    # peak — best risk-adjusted return
    (30.0, 0.8),    # still good but gap-chase risk rising
    (50.0, 0.4),    # extreme — edge fading
    (100.0, 0.15),  # negative expectancy territory
    (200.0, 0.05),  # near-zero — these reverse
)

# Liquidity log-scale anchors (market cap -> score)
LIQ_ANCHORS = (
    (50_000_000, 0.3),
    (300_000_000, 0.6),
    (1_000_000_000, 0.8),
    (10_000_000_000, 1.0),
)

MEGACAP_DECAY_START = 50_000_000_000   # $50B — edge starts fading
MEGACAP_DECAY_END = 200_000_000_000    # $200B — minimal edge left
MEGACAP_FLOOR = 0.2                    # score floor for mega-caps


def surprise_strength(surprise_pct: Optional[float]) -> float:
    """Map EPS surprise % to event strength (0–1).

    Uses absolute value — both beats and misses get the same curve; the
    caller decides directionality (Achilles goes long on beats only).
    """
    if surprise_pct is None:
        return 1.0  # no data → neutral, don't penalise
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


def liquidity_score(market_cap: Optional[float]) -> float:
    """Log-scaled liquidity score from market cap.

    Peaks at 1.0 around $10B, then decays above $50B — event-driven edge
    fades as coverage density increases and market reaction speed rises.
    """
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
                t = (math.log(cap) - math.log(lo_cap)) / (math.log(hi_cap) - math.log(lo_cap))
                return lo_s + t * (hi_s - lo_s)
    if cap <= MEGACAP_DECAY_START:
        return 1.0
    if cap >= MEGACAP_DECAY_END:
        return MEGACAP_FLOOR
    t = (math.log(cap) - math.log(MEGACAP_DECAY_START)) / (math.log(MEGACAP_DECAY_END) - math.log(MEGACAP_DECAY_START))
    return 1.0 - t * (1.0 - MEGACAP_FLOOR)


def time_decay(first_seen_iso: str, now: Optional[datetime] = None) -> float:
    """48-hour half-life decay, anchored to when Achilles first saw the event."""
    if not first_seen_iso:
        return 1.0
    try:
        seen = datetime.fromisoformat(first_seen_iso)
    except ValueError:
        return 1.0
    now = now or datetime.utcnow()
    hours = (now - seen).total_seconds() / 3600.0
    if hours <= 0:
        return 1.0
    return 0.5 ** (hours / TIME_HALFLIFE_HOURS)


def has_disqualifier(flags: Iterable[str], event_class: str) -> bool:
    flag_set = set(flags or ())
    if any(d in flag_set for d in UNIVERSAL_DISQUALIFIERS):
        return True
    if any(d in flag_set for d in CLASS_DISQUALIFIERS.get(event_class, ())):
        return True
    return False


def score_event(
    *,
    playbook: Playbook,
    event_strength: float,
    company_quality: float,
    market_cap: Optional[float],
    first_seen_iso: str,
    disqualifier_flags: Iterable[str] = (),
    now: Optional[datetime] = None,
) -> dict:
    """Compute the multiplicative score. Disqualifiers zero it out."""
    if playbook.disabled:
        return {"score": 0.0, "reason": "playbook_disabled"}
    if has_disqualifier(disqualifier_flags, playbook.event_class):
        return {"score": 0.0, "reason": "disqualified"}

    liq = liquidity_score(market_cap)
    td = time_decay(first_seen_iso, now=now)
    raw = (
        max(0.0, playbook.base_rate)
        * max(0.0, event_strength)
        * max(0.0, company_quality)
        * max(0.0, liq)
        * max(0.0, td)
    )
    return {
        "score": raw,
        "components": {
            "base_rate": playbook.base_rate,
            "event_strength": event_strength,
            "company_quality": company_quality,
            "liquidity": liq,
            "time_decay": td,
        },
    }
