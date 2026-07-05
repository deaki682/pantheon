"""Plutus deluxe overlay — the LLM quality read + conviction/cap-weight tilt.

The deluxe live pipeline is:  composite two-factor basket (strategy.py)
  → LLM quality read (prune junk buybacks, score conviction)   [this module]
  → conviction / cap-weight tilted weights                     [this module]

NONE of this is forward-validated (the LLM overlay has zero graded rounds;
the tilt is a measured regime bet). It runs on real money by a conscious
operator override — "the deluxe package, even if risky" (2026-07-04). The
pure mechanical spec stays tracked in parallel so we can grade whether any of
this bought excess. See docs/plutus_launch_override.md (deluxe amendment).

The LLM read itself is a session judgment (the /plutus session does it live,
per the runbook). This module only (a) types that read so it can be journaled
and replayed, and (b) turns keeps + convictions into bounded target weights —
pure arithmetic, unit-tested without any network or model call.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

# Conviction is a bounded tilt multiplier, same spirit as Delphi's 0.5x–2.0x
# sizing tilts: extreme tilts defeat the diversification a thin factor needs.
CONVICTION_MIN = 0.5
CONVICTION_MAX = 2.0
PER_NAME_CAP = 0.06     # no single name above 6% of the book
CASH_FLOOR = 0.02       # keep 2% cash
CAP_BLEND_DEFAULT = 0.5  # 0 = pure conviction/equal, 1 = full cap-weight lean


@dataclass
class QualityRead:
    """The LLM's per-name buyback-quality verdict for one quarter. `keep`
    prunes the basket; `conviction` (only meaningful when kept) drives the
    tilt; `rationale` is the one-line reason, journaled for grading."""
    symbol: str
    keep: bool
    conviction: float = 1.0   # clamped to [CONVICTION_MIN, CONVICTION_MAX]
    rationale: str = ""

    def clamped(self) -> float:
        return max(CONVICTION_MIN, min(CONVICTION_MAX, float(self.conviction)))

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize(raw: dict, target: float) -> dict:
    tot = sum(raw.values())
    if tot <= 0:
        return {k: 0.0 for k in raw}
    return {k: v / tot * target for k, v in raw.items()}


def _apply_cap(weights: dict, cap: float, invest: float) -> dict:
    """Iteratively clip any weight above `cap`, redistributing the excess
    proportionally among the uncapped names until stable. If everything hits
    the cap, the leftover simply stays in cash (safe for a small book)."""
    w = dict(weights)
    for _ in range(200):
        over = [k for k, v in w.items() if v > cap + 1e-12]
        if not over:
            break
        for k in over:
            w[k] = cap
        remaining = invest - cap * len(over)
        under = {k: w[k] for k in w if k not in over}
        under_sum = sum(under.values())
        if under_sum <= 1e-12 or remaining <= 0:
            break
        scale = remaining / under_sum
        for k in under:
            w[k] = w[k] * scale
    return w


def conviction_weights(
    names: list,
    convictions: dict,
    marketcaps: Optional[dict] = None,
    *,
    cap_blend: float = 0.0,
    per_name_cap: float = PER_NAME_CAP,
    cash_floor: float = CASH_FLOOR,
) -> dict:
    """Target portfolio weights (fractions of the whole book) for `names`.

    base raw weight per name = conviction × marketcap**cap_blend
      - cap_blend = 0  → pure conviction tilt on an equal base
      - cap_blend = 1  → full cap-weight lean (chases SPY, which is cap-weighted)
      - 0 < cap_blend < 1 → a moderate cap lean (the deluxe default is 0.5)
    Then normalized to (1 - cash_floor) and capped at per_name_cap with
    redistribution. Returns {symbol: weight}; the residual up to 1.0 is cash.
    """
    names = [n for n in names if convictions.get(n, 0) > 0 or n in convictions]
    if not names:
        return {}
    invest = max(0.0, 1.0 - cash_floor)
    raw = {}
    for s in names:
        w = max(1e-9, float(convictions.get(s, 1.0)))
        if marketcaps and cap_blend > 0:
            cap = max(1.0, float(marketcaps.get(s, 0.0)))
            w *= cap ** cap_blend
        raw[s] = w
    weights = _normalize(raw, invest)
    # Effective cap = the concentration ceiling OR ~2x equal weight, whichever
    # is larger. This keeps the book fully invested for small baskets (a hard
    # 6% cap would strand cash below ~16 names) and lets a max-conviction name
    # (2.0x) actually express, while still clamping runaway concentration in
    # the large baskets where per_name_cap binds.
    effective_cap = max(per_name_cap, 2.0 * invest / len(names))
    weights = _apply_cap(weights, effective_cap, invest)
    return weights


def apply_overlay(
    candidates: list,
    reads: dict,
    marketcaps: Optional[dict] = None,
    *,
    cap_blend: float = CAP_BLEND_DEFAULT,
    per_name_cap: float = PER_NAME_CAP,
    cash_floor: float = CASH_FLOOR,
) -> dict:
    """Full deluxe weighting: prune `candidates` to the LLM's keeps, then
    conviction/cap-weight-tilt the survivors.

    `reads`: {symbol: QualityRead}. Candidates with no read, or read.keep
    False, are dropped. Returns {symbol: target_weight}. Empty if the LLM
    kept nothing (a legitimate "sit in more cash this quarter" outcome).
    """
    kept = [c for c in candidates if c in reads and reads[c].keep]
    if not kept:
        return {}
    convictions = {c: reads[c].clamped() for c in kept}
    return conviction_weights(
        kept, convictions, marketcaps,
        cap_blend=cap_blend, per_name_cap=per_name_cap, cash_floor=cash_floor,
    )
