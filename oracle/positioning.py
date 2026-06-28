"""Position sizing math.

Derived dossier values:
  - expected_price  = sum(p_i * target_i)
  - expected_return = expected_price / current - 1
  - expected_cagr   = (1 + expected_return)^(1/horizon_years) - 1
  - asymmetry       = (upside * P_up) / (downside * P_down)
  - quality_mult    = 0.5 + avg(ratings)       in [0.5, 1.5]
  - asymmetry_mult  = min(sqrt(asymmetry), 2)  in [0, 2]
  - potential_score = expected_cagr * quality_mult * asymmetry_mult

Conviction is a monotone transform of potential_score onto [0, 1].
Weight = conviction^1.5; normalized so weights sum to (1 - cash_floor).
"""
from __future__ import annotations

import math
from typing import Iterable

from .sleeve import CASH_FLOOR, MAX_MCAP, MAX_POSITIONS, PER_NAME_CAP, PER_SECTOR_CAP, MIN_TICKET


def compute_derived(dossier: dict, *, current_price: float, horizon_years: float = 2.0) -> dict:
    """Return a dict of derived metrics for a dossier."""
    scenarios = dossier["scenarios"]
    expected_price = sum(s["probability"] * s["target"] for s in scenarios.values())
    if current_price <= 0:
        return {
            "expected_price": expected_price, "expected_return": 0.0,
            "expected_cagr": 0.0, "asymmetry": 0.0,
            "quality_mult": 0.5, "asymmetry_mult": 0.0, "potential_score": 0.0,
        }
    expected_return = expected_price / current_price - 1.0
    if horizon_years <= 0:
        expected_cagr = expected_return
    else:
        base = 1.0 + expected_return
        expected_cagr = (math.copysign(abs(base) ** (1.0 / horizon_years), base) - 1.0) if base != 0 else -1.0

    bull = scenarios["bull"]
    bear = scenarios["bear"]
    upside = max(0.0, bull["target"] - current_price)
    downside = max(0.0, current_price - bear["target"])
    p_up = bull["probability"]
    p_down = bear["probability"]
    if downside * p_down <= 1e-9:
        asymmetry = 10.0 if upside > 0 else 0.0
    else:
        asymmetry = (upside * p_up) / (downside * p_down)

    ratings = dossier["ratings"]
    avg_rating = sum(ratings[k] for k in ("moat", "runway", "quality", "management")) / 4.0
    quality_mult = 0.5 + avg_rating
    asymmetry_mult = min(math.sqrt(max(0.0, asymmetry)), 2.0)
    potential_score = expected_cagr * quality_mult * asymmetry_mult

    return {
        "expected_price": expected_price,
        "expected_return": expected_return,
        "expected_cagr": expected_cagr,
        "asymmetry": asymmetry,
        "quality_mult": quality_mult,
        "asymmetry_mult": asymmetry_mult,
        "potential_score": potential_score,
    }


def potential_to_conviction(score: float) -> float:
    """Map a potential score to [0, 1] via a tanh-ish squash.

    score ~ 0 -> ~0; score ~ 0.5 -> ~0.5; score >= 1.5 -> ~1.0.
    """
    if score <= 0:
        return 0.0
    return 1.0 - math.exp(-score / 0.7)


def size_book(
    scored: list[dict],
    equity: float,
    *,
    sector_caps: dict[str, float] | None = None,
    per_name_cap: float = PER_NAME_CAP,
    per_sector_cap: float = PER_SECTOR_CAP,
    cash_floor: float = CASH_FLOOR,
    max_positions: int = MAX_POSITIONS,
    min_ticket: float = MIN_TICKET,
    max_mcap: float = MAX_MCAP,
    weighting: str = "equal",
) -> dict[str, float]:
    """Allocate dollar targets across candidates.

    `scored` is a list of {symbol, conviction, sector, market_cap?}.
    Returns symbol -> $ target.
    Constraints: per-name cap, per-sector cap, 10% cash floor, market-cap ceiling.

    Construction is rank-to-select, then size:
      - FILTER: drop names above `max_mcap` — insider signals lose edge at mega-cap.
      - SELECT: rank by conviction, keep the best K — capped at `max_positions`
        AND at however many can clear `min_ticket` with the investable cash.
      - SIZE: `weighting="equal"` (default) gives each held name an equal slice;
        `weighting="conviction"` weights by conviction**1.5. Equal is the default
        because conviction here is self-assigned (dossier scenarios) and unproven
        — only graduate to conviction-weighting once the calibration loop shows
        high-conviction calls actually outperform.
    """
    if equity <= 0 or not scored:
        return {}
    invest_share = max(0.0, 1.0 - cash_floor)
    items = [s for s in scored if s.get("conviction", 0) > 0]
    if max_mcap > 0:
        items = [s for s in items if (s.get("market_cap") or 0) <= max_mcap or not s.get("market_cap")]
    if not items:
        return {}
    # SELECT: rank by conviction, keep the best K we can fund above min_ticket.
    deployable = max(1, int((equity * invest_share) // min_ticket)) if min_ticket > 0 else len(items)
    keep = min(max_positions, deployable, len(items))
    items = sorted(items, key=lambda s: s.get("conviction", 0.0), reverse=True)[:keep]
    # SIZE: equal slices by default; conviction-weighted only when earned.
    if weighting == "conviction":
        weights = {s["symbol"]: s["conviction"] ** 1.5 for s in items}
    else:
        weights = {s["symbol"]: 1.0 for s in items}
    sectors = {s["symbol"]: s.get("sector", "") for s in items}
    # Initial normalization
    targets = _normalize(weights, equity, invest_share, per_name_cap)
    # Sector cap enforcement (one pass — clip exceeders, redistribute residue).
    cap_dollars = per_sector_cap * equity
    sector_totals: dict[str, float] = {}
    for sym, dollars in targets.items():
        sec = sectors[sym]
        sector_totals[sec] = sector_totals.get(sec, 0.0) + dollars
    residue = 0.0
    for sec, total in sector_totals.items():
        if total > cap_dollars + 1e-9:
            scale = cap_dollars / total
            for sym in [s for s, v in sectors.items() if v == sec]:
                if sym in targets:
                    new = targets[sym] * scale
                    residue += targets[sym] - new
                    targets[sym] = new
    # Drop sub-min-ticket positions
    targets = {k: v for k, v in targets.items() if v >= min_ticket}
    return targets


def _normalize(
    weights: dict[str, float], equity: float, invest_share: float, per_name_cap: float,
) -> dict[str, float]:
    if not weights:
        return {}
    invest_dollars = equity * invest_share
    cap_dollars = equity * per_name_cap
    # Iterate: cap any over-the-cap names, redistribute the residue across uncapped.
    remaining = dict(weights)
    fixed: dict[str, float] = {}
    while True:
        total_w = sum(remaining.values())
        if total_w <= 0:
            break
        budget_left = invest_dollars - sum(fixed.values())
        if budget_left <= 0:
            break
        any_capped = False
        for sym, w in list(remaining.items()):
            share = w / total_w * budget_left
            if share > cap_dollars + 1e-9:
                fixed[sym] = cap_dollars
                del remaining[sym]
                any_capped = True
        if not any_capped:
            for sym, w in remaining.items():
                fixed[sym] = w / total_w * budget_left
            break
    return fixed


def rotation_decision(
    incumbent_score: float, challenger_score: float, *, margin: float = 0.25
) -> bool:
    """True iff challenger's score exceeds incumbent's by `margin` (25% default)."""
    if incumbent_score <= 0:
        return challenger_score > 0
    return challenger_score >= incumbent_score * (1.0 + margin)
