"""Heavy quarterly screen — valuation-first.

Discovery axis: statistical cheapness (FCF yield, earnings yield, P/B, ROE).
Conviction boosters: insider clusters, smart-money 13F, 13D activist, quality.

The old screen discovered via lenses, then checked quality. This one discovers
via valuation, then asks "who else is buying the dip?" The lenses are worth
10× more when they confirm a valuation thesis than when they *are* the thesis.

Weights:
  valuation  40%   — primary discovery axis
  quality    20%   — business quality (margins, growth, dilution)
  insider    15%   — cluster buying confirms dip
  smart_money 10%  — 13F conviction
  activist   10%  — 13D pressure
  sector      5%  — breadth confirmation

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
    """Valuation-first composite score 0..1."""
    score = (
        0.40 * valuation
        + 0.20 * quality
        + (0.15 if insider_cluster else 0.0)
        + (0.10 if smart_money else 0.0)
        + (0.10 if activist_13d else 0.0)
        + 0.05 * sector_breadth
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
