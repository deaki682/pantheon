"""Ghost Midas — paper-only signal-convergence shadow.

The engine (open/grade/mark/persist/analysis) lives in `shared.ghost`; this
module is Midas's adapter (scan finalists → candidates) and its report
composition.

Report covers:
  - convergence_terciles: core thesis test — do multi-signal names outperform
    single-signal names?
  - score_terciles: is the timing-weighted convergence score monotonic in
    forward return?
  - signal_lift: per-channel boolean lift — which signals predict 5-day pops?
  - timing_weighted_terciles: do timing-weighted strengths predict better than
    raw signal count?
  - disqualified lift: do LLM disqualifications filter losers or kill winners?
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)

HORIZON_DAYS = 5


def finalists_to_candidates(
    finalists: Iterable[dict],
    price_lookup: PriceLookup,
) -> list[dict]:
    """Convert stage-2 ranked finalists into ghost candidate dicts.

    Opens ALL finalists (including those the LLM would disqualify) so the
    report can test whether disqualification actually filters losers.

    Each finalist should have: symbol, score, convergence_count, active_signals,
    timing_adjusted. Dossier fields (disqualified, disqualify_reason) are
    optional — present only for names that went through stage 3.
    """
    out: list[dict] = []
    for f in finalists:
        sym = (f.get("symbol") or "").upper()
        if not sym:
            continue

        px = f.get("current_price")
        if px is None or float(px) <= 0:
            px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue
        px = float(px)

        active_signals = f.get("active_signals", {})
        features: dict = {
            "score": f.get("score", 0),
            "convergence_count": f.get("convergence_count", 0),
            "disqualified": bool(f.get("disqualified", False)),
        }

        for channel in ("insider_cluster", "earnings_beat", "smart_money",
                        "activist_13d", "guidance_raised", "volume_anomaly",
                        "short_squeeze"):
            features[channel] = channel in active_signals

        timing_adjusted = f.get("timing_adjusted", {})
        if timing_adjusted:
            features["mean_timing_weighted"] = (
                sum(timing_adjusted.values()) / len(timing_adjusted)
            )

        out.append({
            "symbol": sym,
            "price": px,
            "horizon_days": HORIZON_DAYS,
            "source": "convergence",
            "features": features,
        })
    return out


def convergence_report(entries: Iterable[GhostEntry]) -> dict:
    """Full signal-convergence validation report from graded entries.

    The convergence_terciles section is the single most important output —
    if multi-signal names don't outperform single-signal names, the core
    thesis is wrong.
    """
    graded = graded_only(entries)
    if not graded:
        return {
            "n": 0, "mean_return": None, "hit_rate": None,
            "convergence_terciles": {},
            "score_terciles": {},
            "timing_weighted_terciles": {},
            "signal_lift": {},
        }

    return {
        **overall_stats(graded),
        "convergence_terciles": numeric_tercile_stats(graded, "convergence_count"),
        "score_terciles": numeric_tercile_stats(graded, "score"),
        "timing_weighted_terciles": numeric_tercile_stats(graded, "mean_timing_weighted"),
        "signal_lift": boolean_lift(graded),
    }
