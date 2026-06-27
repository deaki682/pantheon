"""Ghost Oracle — Oracle's paper-only learning shadow.

The engine (open/grade/mark/persist/analysis) lives in `shared.ghost`; this
module is just Oracle's adapters (screen rows + dossiers -> candidates) and its
report composition (lens lift + conviction-tier calibration). See `shared.ghost`
for the why.
"""
from __future__ import annotations

from typing import Iterable, Optional

# Re-export the shared engine so existing `from oracle.ghost import …` keeps working.
from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, group_stats, load_ledger, mark_to_market, open_entries,
    overall_stats, save_ledger, tier_stats,
)


def calibration_report(entries: Iterable[GhostEntry]) -> dict:
    """Overall stats + per-lens lift + conviction-tier calibration."""
    graded = graded_only(entries)
    if not graded:
        return {"n": 0, "mean_return": None, "hit_rate": None,
                "lens_lift": {}, "conviction_tiers": {}, "conviction_monotonic": False}
    from .learning import conviction_tier
    tiers = tier_stats(graded, "conviction", conviction_tier, ("high", "mid", "low"))
    return {
        **overall_stats(graded),
        "lens_lift": boolean_lift(graded),
        "conviction_tiers": tiers["tiers"],
        "conviction_monotonic": tiers["monotonic"],
    }


# ------- Adapters: screen rows / dossiers -> candidates -------

def screen_rows_to_candidates(
    rows: Iterable[dict], price_lookup: PriceLookup, *, horizon_days: int = 365,
) -> list[dict]:
    """Turn `oracle_screen.json` `top` rows into priced candidates.

    Features = the row's lens flags (so lens lift is measurable). Names that
    can't be priced are dropped at open time (they never enter the ledger).
    """
    out: list[dict] = []
    for r in rows:
        sym = (r.get("symbol") or "").upper()
        if not sym:
            continue
        px = price_lookup(sym)
        if px is None or px <= 0:
            continue
        feats = dict(r.get("lenses") or {})
        feats["score"] = r.get("score")
        out.append({"symbol": sym, "price": float(px), "horizon_days": horizon_days,
                    "source": "screen", "features": feats})
    return out


def dossiers_to_candidates(
    dossiers: Iterable[dict], price_lookup: Optional[PriceLookup] = None,
    *, default_horizon_days: int = 365,
) -> list[dict]:
    """Turn dossiers into priced candidates carrying their conviction as a feature."""
    out: list[dict] = []
    for d in dossiers:
        sym = (d.get("symbol") or "").upper()
        if not sym:
            continue
        px = d.get("current_price")
        if (px is None or float(px) <= 0) and price_lookup:
            px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue
        hd = int(round(float(d.get("horizon_years", 1.0)) * 365)) or default_horizon_days
        out.append({"symbol": sym, "price": float(px), "horizon_days": hd,
                    "source": "dossier", "features": {"conviction": d.get("conviction")}})
    return out
