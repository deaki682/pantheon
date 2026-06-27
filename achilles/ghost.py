"""Ghost Achilles — Achilles's paper-only event-study shadow.

Achilles trades 6 event classes on per-class drift estimates "seeded from
literature" (playbooks.py). Those priors are guesses until measured. Ghost
Achilles opens a paper position on EVERY classified event — not just the few the
$1k sleeve can afford — grades the short-horizon drift, and reports the MEASURED
drift per event class, so the literature priors can be replaced with data. Short
horizons mean statistically useful answers in weeks, not years.

The engine (open/grade/mark/persist/analysis) is `shared.ghost`; this module is
just Achilles's event adapter and its per-class drift report.

Note: the shared ledger de-dupes by (symbol, source, day), so two distinct events
on the same symbol the same day collapse to one. Rare in practice; revisit with
an event_id-aware key if it matters.
"""
from __future__ import annotations

from typing import Iterable

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, group_stats, load_ledger, mark_to_market, open_entries,
    overall_stats, save_ledger,
)

DEFAULT_EVENT_HORIZON_DAYS = 10  # post-event drift is a short-horizon phenomenon


def _attr(obj, name, default=None):
    """Read a field from a Brief dataclass or a plain dict."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def briefs_to_candidates(
    briefs: Iterable, price_lookup: PriceLookup, *,
    default_horizon_days: int = DEFAULT_EVENT_HORIZON_DAYS,
) -> list[dict]:
    """Turn Achilles briefs (dataclass or dict) into priced ghost candidates.

    Opens EVERY classified event that has a symbol — including disqualified ones,
    so the report can later test whether disqualifiers actually filter losers.
    Features: event_class (categorical -> per-class drift), score, disqualified.
    """
    out: list[dict] = []
    for b in briefs:
        sym = (_attr(b, "symbol") or "").upper()
        ec = _attr(b, "event_class")
        if not sym or not ec:
            continue
        px = price_lookup(sym)
        if px is None or px <= 0:
            continue
        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": int(_attr(b, "horizon_days") or default_horizon_days),
            "source": "event",
            "features": {
                "event_class": ec,
                "score": _attr(b, "score"),
                "disqualified": bool(_attr(b, "disqualifiers")),
            },
        })
    return out


def drift_report(entries: Iterable[GhostEntry]) -> dict:
    """Overall stats + MEASURED per-event-class drift + disqualifier lift.

    `class_drift[event_class]` is the empirical mean forward return for that class
    — the number Achilles's playbooks currently guess from literature.
    `lens_lift["disqualified"]` shows whether disqualified events actually
    underperformed (i.e. whether the filter earns its keep).
    """
    graded = graded_only(entries)
    if not graded:
        return {"n": 0, "mean_return": None, "hit_rate": None,
                "class_drift": {}, "lens_lift": {}}
    return {
        **overall_stats(graded),
        "class_drift": group_stats(graded, "event_class"),
        "lens_lift": boolean_lift(graded),
    }
