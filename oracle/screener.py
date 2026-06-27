"""Heavy quarterly screen.

Scores each candidate across multi-lens dimensions:
  - insider clusters
  - smart-money 13F holdings
  - 13D activist filings
  - broad quality screen
  - sector breadth

This module is a pure scorer — fetching is the caller's job. We accept
pre-computed signal dicts and emit a ranked survivor list.
"""
from __future__ import annotations

from typing import Iterable

from shared.fundamentals import FundamentalSnapshot


def quality_score(snap: FundamentalSnapshot) -> float:
    """Score 0..1 from fundamentals. Higher = better quality."""
    score = 0.0
    n = 0
    if snap.gross_margin_ttm is not None:
        score += min(1.0, max(0.0, snap.gross_margin_ttm / 0.5))
        n += 1
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
        # Less dilution = better. Clamp to [0,1] like every other component —
        # buybacks (negative dilution_yoy) would otherwise make this term
        # unbounded above (e.g. a noisy -5.0 → 51), letting one component
        # dominate the average and swamp the lens signals downstream.
        score += min(1.0, max(0.0, 1.0 - snap.dilution_yoy * 10))
        n += 1
    return score / n if n else 0.0


def multi_lens_score(
    symbol: str,
    *,
    insider_cluster: bool = False,
    smart_money: bool = False,
    activist_13d: bool = False,
    quality: float = 0.0,
    sector_breadth: float = 0.0,
) -> dict:
    """Combine the 5 lenses into a composite score 0..1."""
    score = (
        (0.25 if insider_cluster else 0.0)
        + (0.20 if smart_money else 0.0)
        + (0.20 if activist_13d else 0.0)
        + 0.25 * quality
        + 0.10 * sector_breadth
    )
    return {
        "symbol": symbol,
        "score": score,
        "lenses": {
            "insider_cluster": insider_cluster,
            "smart_money": smart_money,
            "activist_13d": activist_13d,
            "quality": quality,
            "sector_breadth": sector_breadth,
        },
    }


def rank_survivors(rows: Iterable[dict], *, top_n: int = 100) -> list[dict]:
    """Sort by score descending and return the top N."""
    sorted_rows = sorted(rows, key=lambda r: r.get("score", 0.0), reverse=True)
    return sorted_rows[:top_n]
