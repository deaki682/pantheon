"""Ghost Nemesis — the head-to-head test of fade-the-crash vs chase-the-flow.

The engine lives in `shared.ghost`; this adapter opens BOTH legs plus the
control group every trigger week, tagged so the report can answer, from graded
outcomes, the question the strategy was born from:

  - leg_returns (fade vs destination): which half of "target who's losing and
    where the money's going" actually pays?
  - signal_lift.news_driven: the conditioning check. News-driven crashes are
    opened ON PURPOSE and should FAIL to bounce (drift, not revert) — a
    negative lift here VALIDATES the no-news filter; a flat one kills it.
  - signal_lift.sector_cascade: do flow-cascade crashes revert harder than
    idiosyncratic ones?
  - zscore_terciles: does a more violent crash mean a bigger bounce?

Entries are tagged source="nemesis". No sleeve, no orders — Nemesis earns a
capital conversation only if a leg survives grading in the current regime.
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, group_stats, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)

HORIZON_DAYS = 7   # 5 trading days ≈ the reversal window the matrix measures
SOURCE = "nemesis"


def crashes_to_ghost(crashes: Iterable, price_lookup: PriceLookup) -> list[dict]:
    """FADE leg + control: every crashed name, news-driven ones included.

    news_driven=None (unchecked) is kept but tagged unconfirmed rather than
    silently treated as clean — the report needs the distinction.
    """
    out: list[dict] = []
    for c in crashes:
        get = c.get if isinstance(c, dict) else lambda k, d=None: getattr(c, k, d)
        sym = (get("symbol") or "").upper()
        if not sym:
            continue
        px = get("price")
        if px is None or float(px) <= 0:
            px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue
        news = get("news_driven")
        features: dict = {
            "leg": "fade",
            "crash_zscore": get("zscore"),
            "crash_day_return": get("day_return"),
            "sector_cascade": bool(get("sector_cascade", False)),
            "news_checked": news is not None,
        }
        if news is not None:
            features["news_driven"] = bool(news)
        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": HORIZON_DAYS,
            "source": SOURCE,
            "features": features,
        })
    return out


def destinations_to_ghost(
    destinations: Iterable[dict],
    price_lookup: PriceLookup,
) -> list[dict]:
    """DESTINATION leg: the predicted receiver ETFs from the rotation matrix.

    Each destination dict comes from nemesis.rotation.predicted_destinations
    ({symbol, excess, hit_rate, ...}); the matrix numbers ride along so the
    report can later test whether higher predicted excess meant higher
    realized return.
    """
    out: list[dict] = []
    for d in destinations:
        sym = (d.get("symbol") or "").upper()
        if not sym:
            continue
        px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue
        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": HORIZON_DAYS,
            "source": SOURCE,
            "features": {
                "leg": "destination",
                "predicted_excess": d.get("excess"),
                "predicted_hit_rate": d.get("hit_rate"),
            },
        })
    return out


def nemesis_report(entries: Iterable[GhostEntry]) -> dict:
    """Head-to-head verdict from graded entries (source='nemesis' only)."""
    graded = [e for e in graded_only(entries) if e.source == SOURCE]
    if not graded:
        return {
            "n": 0, "mean_return": None, "hit_rate": None,
            "leg_returns": {},
            "signal_lift": {},
            "zscore_terciles": {},
            "predicted_excess_terciles": {},
        }
    return {
        **overall_stats(graded),
        "leg_returns": group_stats(graded, "leg"),
        "signal_lift": boolean_lift(graded),
        "zscore_terciles": numeric_tercile_stats(graded, "crash_zscore"),
        "predicted_excess_terciles": numeric_tercile_stats(graded, "predicted_excess"),
    }
