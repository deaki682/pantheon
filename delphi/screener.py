"""Screener for individual stocks inside chosen sectors.

Scores by momentum only. Quality (fundamentals) was tested in the backtest
and showed no predictive value for within-sector stock selection — removing
it also eliminates the look-ahead bias from using today's XBRL data to
score past decisions. The quality scorer is kept available for the ghost
shadow's signal validation.
"""
from __future__ import annotations

from shared.fundamentals import FundamentalSnapshot
from shared.quality import (
    MIN_QUALITY_COMPONENTS, dilution_score, fcf_margin_score, mean_of_present,
    operating_margin_score, revenue_growth_score,
)

from .signals import momentum
from .sleeve import is_blocked


def quality_for_delphi(snap: FundamentalSnapshot) -> float:
    """Quality from fundamentals. Retained for the ghost shadow's tercile
    validation — not used in production scoring."""
    return mean_of_present([
        operating_margin_score(snap),
        fcf_margin_score(snap),
        revenue_growth_score(snap),
        dilution_score(snap),
    ], min_count=MIN_QUALITY_COMPONENTS)


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
        "score": m,
    }


def screen_universe(
    by_sector: dict[str, list[tuple[str, list[float], FundamentalSnapshot | None]]],
) -> dict[str, list[dict]]:
    """For each sector -> list of (symbol, prices, snap) -> candidate list."""
    out: dict[str, list[dict]] = {}
    for sec, rows in by_sector.items():
        out[sec] = [build_candidate(sym, sector=sec, prices=prices, snap=snap) for sym, prices, snap in rows]
    return out
