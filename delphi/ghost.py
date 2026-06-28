"""Ghost Delphi — Delphi's paper-only learning shadow.

Delphi is a sector-rotation + pure-momentum strategy: it rotates into strong
sectors and picks names within them by 63-day momentum. Ghost Delphi opens a
paper position for EVERY screened candidate — not just the few the sleeve
holds — grades the forward return over a momentum holding window, and reports
whether the signals actually predict returns:

  - per-SECTOR return (did the rotation pick the right sectors?)
  - momentum terciles (does higher momentum -> higher forward return?)
  - per-REGIME return (did risk-off actually avoid losses?)

Engine is `shared.ghost`; this is Delphi's candidate adapter + signal report.
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, grade_entries, graded_only,
    group_stats, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)

DEFAULT_DELPHI_HORIZON_DAYS = 90  # ~one momentum holding window (63 trading days)


def candidates_to_ghost(
    candidates: Iterable[dict], price_lookup: PriceLookup, *,
    horizon_days: int = DEFAULT_DELPHI_HORIZON_DAYS,
    regime: Optional[str] = None,
    chosen_sectors: Optional[list[str]] = None,
) -> list[dict]:
    """Turn Delphi screener candidates into priced ghost candidates.

    Skips blocked names (untradeable). Features: sector (categorical), momentum
    (numeric), regime (categorical — stamped from the current rotation plan),
    chosen (boolean — was this candidate's sector picked by the rotator?).
    """
    chosen_set = set(chosen_sectors or [])
    out: list[dict] = []
    for c in candidates:
        sym = (c.get("symbol") or "").upper()
        if not sym or c.get("blocked"):
            continue
        px = price_lookup(sym)
        if px is None or px <= 0:
            continue
        sector = c.get("sector")
        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": horizon_days,
            "source": "sector",
            "features": {
                "sector": sector,
                "momentum": c.get("momentum"),
                "score": c.get("score"),
                "regime": regime,
                "chosen": sector in chosen_set if (sector and chosen_set) else None,
            },
        })
    return out


def signal_report(entries: Iterable[GhostEntry]) -> dict:
    """Overall stats + per-sector + momentum terciles + regime analysis.

    Key questions answered:
      - momentum_terciles: does higher momentum predict higher forward return?
      - sector_return: which sectors are generating alpha?
      - regime_return: did risk-off/cautious regimes avoid drawdowns?
      - rotation_lift: do chosen-sector names outperform unchosen?
    """
    graded = graded_only(entries)
    if not graded:
        return {"n": 0, "mean_return": None, "hit_rate": None,
                "sector_return": {}, "momentum_terciles": {},
                "regime_return": {}, "rotation_lift": {}}
    from shared.ghost import boolean_lift
    return {
        **overall_stats(graded),
        "sector_return": group_stats(graded, "sector"),
        "momentum_terciles": numeric_tercile_stats(graded, "momentum"),
        "regime_return": group_stats(graded, "regime"),
        "rotation_lift": boolean_lift(graded),
    }
