"""Screener for individual stocks inside chosen sectors.

Combines momentum (price-based) and quality (fundamentals-based). The
fundamentals quality scorer is shared with Oracle to keep one source of truth.
"""
from __future__ import annotations

from shared.fundamentals import FundamentalSnapshot

from .signals import momentum
from .sleeve import is_blocked


def quality_for_delphi(snap: FundamentalSnapshot) -> float:
    """Quality from fundamentals, weighted toward profitability + cash flow."""
    score = 0.0
    n = 0
    if snap.operating_margin_ttm is not None:
        score += min(1.0, max(0.0, (snap.operating_margin_ttm + 0.1) / 0.3))
        n += 1
    if snap.free_cash_flow_ttm is not None and snap.revenue_ttm:
        fcf_margin = snap.free_cash_flow_ttm / snap.revenue_ttm
        score += min(1.0, max(0.0, fcf_margin / 0.2))
        n += 1
    if snap.revenue_yoy is not None:
        score += min(1.0, max(0.0, (snap.revenue_yoy + 0.05) / 0.3))
        n += 1
    if snap.dilution_yoy is not None:
        # Clamp to [0,1] like the other terms — buybacks (negative dilution_yoy)
        # would otherwise make this unbounded above and dominate the average.
        score += min(1.0, max(0.0, 1.0 - snap.dilution_yoy * 10))
        n += 1
    return score / n if n else 0.0


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
