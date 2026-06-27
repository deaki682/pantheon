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


def gross_margin_score(snap: FundamentalSnapshot) -> Optional[float]:
    if snap.gross_margin_ttm is None:
        return None
    return _clamp01(snap.gross_margin_ttm / 0.5)


def operating_margin_score(snap: FundamentalSnapshot) -> Optional[float]:
    if snap.operating_margin_ttm is None:
        return None
    return _clamp01((snap.operating_margin_ttm + 0.1) / 0.3)


def fcf_margin_score(snap: FundamentalSnapshot) -> Optional[float]:
    # Falsy revenue (0 or None) -> undefined margin, skip.
    if snap.free_cash_flow_ttm is None or not snap.revenue_ttm:
        return None
    return _clamp01((snap.free_cash_flow_ttm / snap.revenue_ttm) / 0.2)


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


def mean_of_present(values: Iterable[Optional[float]]) -> float:
    """Average the non-None component scores; 0.0 when none are present."""
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else 0.0
