"""Ghost Achilles — paper-only shadow of the PEAD basket strategy.

The engine (open/grade/mark/persist/analysis) lives in `shared.ghost`; this
module is Achilles's adapter and report composition, aligned to the CURRENT
strategy: a diversified basket of small/mid-cap earnings beats gated on the
post-report *reaction* (only rewarded beats are bought; sold beats are never
bought). The ghost shadows EVERYTHING — rewarded, sold, and unconfirmed beats
alike — because the unbought names are the control groups that prove (or
refute) each gate:

  - rewarded lift: do market-rewarded beats beat sold beats? This is THE core
    test of the reaction-direction gate — if sold beats drift up just as well,
    the gate is costing money; if they drift down, it's saving it.
  - basket_selected lift: did rank_beats' final selection beat the rewarded
    names it passed over? (tests scoring + confirming-signal boosts end-to-end)
  - reaction_terciles: does a BIGGER positive reaction predict MORE drift?
    (drift-follows-reaction, the directional thesis itself)
  - surprise_terciles: does surprise magnitude predict drift?
  - signal_lift: revenue_beat / guidance_raised / short-squeeze confirmations.
  - cap_terciles: market-cap terciles — PEAD says NEGLECT wins, so the healthy
    reading is low-cap ABOVE high-cap (inverse monotonicity).

Entries are tagged source="pead". Ledger files may still carry entries from the
retired event-study ghost (source="event"); the report filters those out so the
old strategy's shadow can't pollute the new strategy's verdict.
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)

# Achilles holds 5 trading days ≈ 7 calendar days.
HORIZON_DAYS = 7
SOURCE = "pead"


def beats_to_candidates(
    beats: Iterable,
    price_lookup: PriceLookup,
    *,
    basket_selected: Optional[Iterable[str]] = None,
) -> list[dict]:
    """Convert BeatCandidate objects (or equivalent dicts) into ghost candidates.

    Opens ALL actionable beats — rewarded, sold, and unconfirmed-reaction — so
    the reaction gate has its control groups. Sold beats are opened LONG on
    purpose: if the gate is right, their forward returns should be visibly
    worse, and that shows up as `rewarded` lift.

    basket_selected: symbols the live strategy actually put in the basket
    (rank_beats output). Flagged only on rewarded names, so the lift compares
    picks vs rewarded-but-passed-over — not vs names the ranker never ranked.
    """
    sel = {s.upper() for s in (basket_selected or [])}
    flag_selection = basket_selected is not None

    out: list[dict] = []
    for b in beats:
        get = b.get if isinstance(b, dict) else lambda k, d=None: getattr(b, k, d)
        sym = (get("symbol") or "").upper()
        if not sym:
            continue

        px = get("current_price")
        if px is None or float(px) <= 0:
            px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue

        reaction = get("reaction_pct")
        features: dict = {
            "surprise_pct": get("surprise_pct"),
            "score": get("score", 0.0),
            "reaction_confirmed": reaction is not None,
            "rewarded": bool(reaction is not None and reaction > 0),
            "revenue_beat": bool(get("revenue_beat", False)),
            "guidance_raised": bool(get("guidance_raised", False)),
        }
        if reaction is not None:
            features["reaction_pct"] = float(reaction)
        if get("short_float_pct") is not None:
            features["short_float_pct"] = float(get("short_float_pct"))
            features["short_squeeze"] = float(get("short_float_pct")) > 20.0
        if get("market_cap") is not None:
            features["market_cap"] = float(get("market_cap"))
        if flag_selection and features["rewarded"]:
            features["basket_selected"] = sym in sel

        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": HORIZON_DAYS,
            "source": SOURCE,
            "features": features,
        })
    return out


def pead_report(entries: Iterable[GhostEntry]) -> dict:
    """PEAD-basket validation report from graded entries (source='pead' only).

    The `rewarded` row of signal_lift is the single most important number: it
    is the measured value of the reaction-direction gate. cap_terciles should
    read INVERSE (low above high) if the neglect thesis holds.
    """
    graded = [e for e in graded_only(entries) if e.source == SOURCE]
    if not graded:
        return {
            "n": 0, "mean_return": None, "hit_rate": None,
            "signal_lift": {},
            "reaction_terciles": {},
            "surprise_terciles": {},
            "score_terciles": {},
            "cap_terciles": {},
        }
    return {
        **overall_stats(graded),
        "signal_lift": boolean_lift(graded),
        "reaction_terciles": numeric_tercile_stats(graded, "reaction_pct"),
        "surprise_terciles": numeric_tercile_stats(graded, "surprise_pct"),
        "score_terciles": numeric_tercile_stats(graded, "score"),
        "cap_terciles": numeric_tercile_stats(graded, "market_cap"),
    }
