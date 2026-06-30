"""Ghost Delphi — momentum compounder learning shadow.

Opens a paper position for every candidate in the momentum ranking, grades
forward returns, and reports whether momentum actually predicts returns.

Engine is `shared.ghost`; this is Delphi's candidate adapter + signal report.
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, group_stats, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)

DEFAULT_DELPHI_HORIZON_DAYS = 90


def candidates_to_ghost(
    candidates: Iterable[dict], price_lookup: PriceLookup, *,
    horizon_days: int = DEFAULT_DELPHI_HORIZON_DAYS,
) -> list[dict]:
    """Turn momentum-ranked candidates into priced ghost candidates."""
    out: list[dict] = []
    for c in candidates:
        sym = (c.get("symbol") or "").upper()
        if not sym:
            continue
        px = price_lookup(sym)
        if px is None or px <= 0:
            continue
        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": horizon_days,
            "source": "momentum",
            "features": {
                "momentum": c.get("momentum"),
                "above_ma": c.get("ma") is not None and c.get("price", 0) >= c.get("ma", 0),
            },
        })
    return out


def signal_report(entries: Iterable[GhostEntry]) -> dict:
    """Overall stats + momentum terciles."""
    graded = graded_only(entries)
    if not graded:
        return {"n": 0, "mean_return": None, "hit_rate": None,
                "momentum_terciles": {}}
    return {
        **overall_stats(graded),
        "momentum_terciles": numeric_tercile_stats(graded, "momentum"),
    }
