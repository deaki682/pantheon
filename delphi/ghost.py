"""Ghost Delphi — Delphi's paper-only learning shadow.

Delphi is a sector-rotation + momentum/quality strategy: it rotates into strong
sectors and picks momentum+quality names within them (`score = 0.6*momentum +
0.4*quality`). Ghost Delphi opens a paper position for EVERY screened candidate —
not just the few the sleeve holds — grades the forward return over a momentum
holding window, and reports whether the signals actually predict returns:

  - per-SECTOR forward return (did the rotation pick the right sectors?)
  - momentum terciles (does higher momentum -> higher forward return?)
  - score terciles (is the composite score monotonic in forward return?)

Engine is `shared.ghost`; this is Delphi's candidate adapter + signal report.
"""
from __future__ import annotations

from typing import Iterable

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, grade_entries, graded_only,
    group_stats, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)

DEFAULT_DELPHI_HORIZON_DAYS = 90  # ~one momentum holding window (63 trading days)


def candidates_to_ghost(
    candidates: Iterable[dict], price_lookup: PriceLookup, *,
    horizon_days: int = DEFAULT_DELPHI_HORIZON_DAYS,
) -> list[dict]:
    """Turn Delphi screener candidates into priced ghost candidates.

    Skips blocked names (untradeable). Features: sector (categorical), momentum,
    quality, score (numeric). A candidate is {symbol, sector, momentum, quality,
    score, blocked?}.
    """
    out: list[dict] = []
    for c in candidates:
        sym = (c.get("symbol") or "").upper()
        if not sym or c.get("blocked"):
            continue
        px = price_lookup(sym)
        if px is None or px <= 0:
            continue
        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": horizon_days,
            "source": "sector",
            "features": {
                "sector": c.get("sector"),
                "momentum": c.get("momentum"),
                "quality": c.get("quality"),
                "score": c.get("score"),
            },
        })
    return out


def signal_report(entries: Iterable[GhostEntry]) -> dict:
    """Overall stats + per-sector return + momentum/score tercile predictiveness."""
    graded = graded_only(entries)
    if not graded:
        return {"n": 0, "mean_return": None, "hit_rate": None,
                "sector_return": {}, "momentum_terciles": {}, "score_terciles": {}}
    return {
        **overall_stats(graded),
        "sector_return": group_stats(graded, "sector"),
        "momentum_terciles": numeric_tercile_stats(graded, "momentum"),
        "score_terciles": numeric_tercile_stats(graded, "score"),
    }
