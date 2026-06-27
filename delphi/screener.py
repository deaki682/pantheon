"""Screener for individual stocks inside chosen sectors.

Combines momentum (price-based) and quality (fundamentals-based). The
fundamentals quality scorer is shared with Oracle to keep one source of truth.
"""
from __future__ import annotations

from shared.fundamentals import FundamentalSnapshot
from shared.quality import (
    dilution_score, fcf_margin_score, mean_of_present,
    operating_margin_score, revenue_growth_score,
)

from .signals import momentum
from .sleeve import is_blocked


def quality_for_delphi(snap: FundamentalSnapshot) -> float:
    """Quality from fundamentals, weighted toward profitability + cash flow.

    Same component scorers as Oracle (shared.quality), but omits gross margin.
    """
    return mean_of_present([
        operating_margin_score(snap),
        fcf_margin_score(snap),
        revenue_growth_score(snap),
        dilution_score(snap),
    ])


def build_candidate(
    symbol: str,
    *,
    sector: str,
    prices: list[float],
    snap: FundamentalSnapshot | None,
) -> dict:
    if is_blocked(symbol):
        return {"symbol": symbol, "sector": sector, "score": 0.0, "blocked": True}
    m = momentum(prices, 63)
    q = quality_for_delphi(snap) if snap is not None else 0.0
    return {
        "symbol": symbol,
        "sector": sector,
        "momentum": m,
        "quality": q,
        "score": 0.6 * m + 0.4 * q,
    }


def screen_universe(
    by_sector: dict[str, list[tuple[str, list[float], FundamentalSnapshot | None]]],
) -> dict[str, list[dict]]:
    """For each sector -> list of (symbol, prices, snap) -> candidate list."""
    out: dict[str, list[dict]] = {}
    for sec, rows in by_sector.items():
        out[sec] = [build_candidate(sym, sector=sec, prices=prices, snap=snap) for sym, prices, snap in rows]
    return out
