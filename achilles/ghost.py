"""Ghost Achilles — Achilles's paper-only PEAD event-study shadow.

The engine (open/grade/mark/persist/analysis) lives in `shared.ghost`; this
module is Achilles's adapter (event briefs → candidates) and its report
composition.

Report covers:
  - class_drift: empirical mean drift per event class (earnings_reaction,
    ma_target, guidance_revision, bankruptcy, delisting). This replaces the
    literature-seeded playbook priors with measured numbers.
  - lens_lift: boolean signal lift — disqualified, insider_preactivity,
    concurrent_guidance
  - neglect_terciles: core PEAD thesis test (high-neglect → higher drift?)
  - surprise_terciles: is the piecewise surprise-strength curve correct?
  - conviction_terciles: does higher conviction → higher returns?
  - score_terciles: is the multiplicative score monotonic in forward return?
  - liquidity_terciles: does the market-cap edge curve correctly weight?
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, group_stats, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger, tier_stats,
)

HORIZON_DAYS = 10  # Achilles holds 5 trading days ~ 7-10 calendar days


def briefs_to_candidates(
    briefs: Iterable[dict],
    price_lookup: PriceLookup,
) -> list[dict]:
    """Convert classified event briefs into ghost candidate dicts.

    Includes ALL events — disqualified ones too — so the report can test
    whether disqualifiers actually filter losers vs kill winners.

    Each brief must have at minimum: symbol, event_class. Optional enrichment
    keys: price (falls back to price_lookup), market_cap, surprise_pct,
    neglect, liquidity, conviction, score, insider_preactivity,
    concurrent_guidance, disqualified, revenue_beat, guidance_raised,
    short_float_pct.
    """
    out: list[dict] = []
    for b in briefs:
        sym = (b.get("symbol") or "").upper()
        if not sym:
            continue

        px = b.get("price")
        if px is None or float(px) <= 0:
            px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue
        px = float(px)

        event_class = b.get("event_class") or "unknown"
        features: dict = {
            "event_class": event_class,
            "score": b.get("score"),
            "disqualified": bool(b.get("disqualified", False)),
            "neglect": b.get("neglect"),
            "surprise_pct": b.get("surprise_pct"),
            "insider_preactivity": bool(b.get("insider_preactivity", False)),
            "concurrent_guidance": b.get("concurrent_guidance"),
            "conviction": b.get("conviction"),
            "liquidity": b.get("liquidity"),
            "revenue_beat": bool(b.get("revenue_beat", False)),
            "guidance_raised": bool(b.get("guidance_raised", False)),
        }
        if b.get("short_float_pct") is not None:
            features["short_float_pct"] = float(b["short_float_pct"])

        out.append({
            "symbol": sym,
            "price": px,
            "horizon_days": int(b.get("horizon_days") or HORIZON_DAYS),
            "source": "event",
            "features": features,
        })
    return out


def drift_report(entries: Iterable[GhostEntry]) -> dict:
    """Full PEAD signal-validation report from graded entries.

    Returns empty/null sections when n < 3 (not enough data yet). The
    class_drift section is the gating signal for enabling disabled playbooks:
    keep playbook priors Bayesian-shrunk toward the literature until n is large.
    """
    graded = graded_only(entries)
    if not graded:
        return {
            "n": 0, "mean_return": None, "hit_rate": None,
            "class_drift": {},
            "lens_lift": {},
            "neglect_terciles": {},
            "surprise_terciles": {},
            "conviction_terciles": {},
            "score_terciles": {},
            "liquidity_terciles": {},
        }

    return {
        **overall_stats(graded),
        "class_drift": group_stats(graded, "event_class"),
        "lens_lift": boolean_lift(graded),
        "neglect_terciles": numeric_tercile_stats(graded, "neglect"),
        "surprise_terciles": numeric_tercile_stats(graded, "surprise_pct"),
        "conviction_terciles": numeric_tercile_stats(graded, "conviction"),
        "score_terciles": numeric_tercile_stats(graded, "score"),
        "liquidity_terciles": numeric_tercile_stats(graded, "liquidity"),
    }
