"""Heavy quarterly screen — insider-first.

Discovery axis: insider buying conviction (clusters, officer buys, activist 13D).
Conviction boosters: valuation cheapness, business quality, sector breadth.

The screen requires at least one insider signal (cluster, smart-money, activist)
to enter the candidate pool — valuation or quality alone don't qualify. The
insider signal is the edge; valuation and quality rank within that universe.

Weights (insider-first — the insider signal IS the edge, not a booster):
  insider    20%   — cluster buying is the primary discovery signal
  smart_money 19%  — officer/director buys > passive 10%% holders
  valuation  25%   — cheapness ranks within the insider universe
  quality    15%   — business quality (margins, growth, dilution)
  activist   12%   — 13D pressure
  sector      9%   — breadth confirmation

This module is a pure scorer — fetching is the caller's job.
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional

from shared.fundamentals import FundamentalSnapshot
from shared.quality import (
    MIN_QUALITY_COMPONENTS, dilution_score, fcf_margin_score, gross_margin_score,
    mean_of_present, operating_margin_score, revenue_growth_score,
    valuation_score,
)

log = logging.getLogger(__name__)

MAX_SCREEN_MCAP = 20_000_000_000  # $20B — filter mega/large-caps from screen


def quality_score(snap: FundamentalSnapshot) -> float:
    """Score 0..1 from fundamentals. Higher = better quality.

    Components live in shared.quality so Oracle and Delphi can't diverge.
    Oracle uses the full set including gross margin.
    """
    return mean_of_present([
        gross_margin_score(snap),
        operating_margin_score(snap),
        fcf_margin_score(snap),
        revenue_growth_score(snap),
        dilution_score(snap),
    ], min_count=MIN_QUALITY_COMPONENTS)


def multi_lens_score(
    symbol: str,
    *,
    insider_cluster: bool = False,
    smart_money: bool = False,
    activist_13d: bool = False,
    quality: float = 0.0,
    valuation: float = 0.0,
    sector_breadth: float = 0.0,
) -> dict:
    """Insider-first composite score 0..1."""
    score = (
        (0.20 if insider_cluster else 0.0)
        + (0.19 if smart_money else 0.0)
        + 0.25 * valuation
        + 0.15 * quality
        + (0.12 if activist_13d else 0.0)
        + 0.09 * sector_breadth
    )
    return {
        "symbol": symbol,
        "score": score,
        "lenses": {
            "insider_cluster": insider_cluster,
            "smart_money": smart_money,
            "activist_13d": activist_13d,
            "quality": quality,
            "valuation": valuation,
            "sector_breadth": sector_breadth,
        },
    }


def rank_survivors(
    rows: Iterable[dict],
    *,
    top_n: int = 100,
    market_caps: Optional[dict[str, float]] = None,
    max_mcap: Optional[float] = None,
) -> list[dict]:
    """Sort by score descending and return the top N.

    If *market_caps* and *max_mcap* are provided, symbols whose market cap
    exceeds the ceiling are dropped before ranking.
    """
    out = list(rows)
    if market_caps and max_mcap is not None:
        before = len(out)
        out = [
            r for r in out
            if market_caps.get(r.get("symbol", ""), 0) <= max_mcap
            or market_caps.get(r.get("symbol", ""), 0) == 0  # keep unknowns
        ]
        dropped = before - len(out)
        if dropped:
            log.info("market-cap filter (>$%.0fB): dropped %d names", max_mcap / 1e9, dropped)
    sorted_rows = sorted(out, key=lambda r: r.get("score", 0.0), reverse=True)
    return sorted_rows[:top_n]
