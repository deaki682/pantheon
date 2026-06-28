"""Shared fundamental-quality component scorers.

Oracle and Delphi both score quality from the same fundamentals, with the same
per-component formulas — they only differ in which components they include
(Delphi omits gross margin). They used to keep separate copies of the math,
which is how the unbounded-dilution bug ended up in both. Keep one source of
truth here: each component returns a value in [0,1] or None when the input is
absent, and `mean_of_present` averages the components a given god opts into.
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.fundamentals import FundamentalSnapshot


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


# A margin can't exceed 100% of revenue — gross/operating income are bounded by
# revenue by definition. A value above 1.0 means revenue is mis-tagged
# (understated / wrong XBRL concept), which inflates every ratio; distrust it.
def _impossible_margin(m: float) -> bool:
    return m > 1.0


def gross_margin_score(snap: FundamentalSnapshot) -> Optional[float]:
    if snap.gross_margin_ttm is None or _impossible_margin(snap.gross_margin_ttm):
        return None
    return _clamp01(snap.gross_margin_ttm / 0.5)


def operating_margin_score(snap: FundamentalSnapshot) -> Optional[float]:
    if snap.operating_margin_ttm is None or _impossible_margin(snap.operating_margin_ttm):
        return None
    return _clamp01((snap.operating_margin_ttm + 0.1) / 0.3)


def fcf_margin_score(snap: FundamentalSnapshot) -> Optional[float]:
    # Falsy revenue (0 or None) -> undefined margin, skip.
    if snap.free_cash_flow_ttm is None or not snap.revenue_ttm:
        return None
    margin = snap.free_cash_flow_ttm / snap.revenue_ttm
    # FCF above 100% of revenue is implausible — same mis-tagged-revenue signature.
    if _impossible_margin(margin):
        return None
    return _clamp01(margin / 0.2)


def revenue_growth_score(snap: FundamentalSnapshot) -> Optional[float]:
    if snap.revenue_yoy is None:
        return None
    return _clamp01((snap.revenue_yoy + 0.05) / 0.3)


def dilution_score(snap: FundamentalSnapshot) -> Optional[float]:
    # Less dilution = better. Clamp to [0,1]: buybacks (negative dilution_yoy),
    # including noisy share-count artifacts, would otherwise run unbounded above
    # and dominate the average.
    if snap.dilution_yoy is None:
        return None
    return _clamp01(1.0 - snap.dilution_yoy * 10)


# A quality score is only trustworthy with enough underlying components. Below
# this, divide by the floor instead of the (small) present count, so a single
# component that happens to clamp to 1.0 can't read as "perfect quality".
MIN_QUALITY_COMPONENTS = 3


def mean_of_present(values: Iterable[Optional[float]], *, min_count: int = 1) -> float:
    """Average the non-None component scores; 0.0 when none are present.

    With `min_count > 1`, sparse coverage is penalized: the sum is divided by
    `max(n_present, min_count)`, so thin data can't produce a confident score.
    """
    present = [v for v in values if v is not None]
    if not present:
        return 0.0
    return sum(present) / max(len(present), min_count)


# ---- Valuation component scores ----

def fcf_yield_score(snap: FundamentalSnapshot, market_cap: float) -> Optional[float]:
    """FCF yield mapped to [0, 1]. Higher yield = cheaper = better score.

    Anchors: 0% → 0, 5% → 0.5, 10%+ → 1.0.  Negative FCF → 0.
    """
    if snap.free_cash_flow_ttm is None or market_cap <= 0:
        return None
    fcf_yield = snap.free_cash_flow_ttm / market_cap
    if fcf_yield <= 0:
        return 0.0
    return _clamp01(fcf_yield / 0.10)


def earnings_yield_score(snap: FundamentalSnapshot, market_cap: float) -> Optional[float]:
    """Earnings yield (inverse P/E) mapped to [0, 1].

    Anchors: 0% → 0, 5% → 0.5, 10%+ → 1.0.  Negative earnings → 0.
    """
    if snap.net_income_ttm is None or market_cap <= 0:
        return None
    ey = snap.net_income_ttm / market_cap
    if ey <= 0:
        return 0.0
    return _clamp01(ey / 0.10)


def pb_score(snap: FundamentalSnapshot, market_cap: float) -> Optional[float]:
    """Price-to-book mapped to [0, 1]. Lower P/B = cheaper = better score.

    Anchors: P/B ≤ 1 → 1.0, P/B = 3 → 0.5, P/B ≥ 5 → 0.
    Negative equity → None (meaningless ratio).
    """
    if snap.equity is None or snap.equity <= 0 or market_cap <= 0:
        return None
    pb = market_cap / snap.equity
    return _clamp01((5.0 - pb) / 4.0)


def roe_score(snap: FundamentalSnapshot) -> Optional[float]:
    """Return on equity mapped to [0, 1].

    Anchors: 0% → 0, 15% → 0.75, 20%+ → 1.0.
    Guards against negative equity or earnings (both → 0).
    """
    if snap.net_income_ttm is None or snap.equity is None or snap.equity <= 0:
        return None
    roe = snap.net_income_ttm / snap.equity
    if roe <= 0:
        return 0.0
    return _clamp01(roe / 0.20)


MIN_VALUATION_COMPONENTS = 2


def valuation_score(
    snap: FundamentalSnapshot, market_cap: float
) -> float:
    """Composite valuation score 0–1. Higher = cheaper + better quality."""
    return mean_of_present([
        fcf_yield_score(snap, market_cap),
        earnings_yield_score(snap, market_cap),
        pb_score(snap, market_cap),
        roe_score(snap),
    ], min_count=MIN_VALUATION_COMPONENTS)
