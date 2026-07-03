"""Ghost Nemesis — paper-only validation of the spinoff reader.

The engine (open/grade/mark/persist/analysis) lives in `shared.ghost`; this is
Nemesis v2's adapter. It paper-buys EVERY priceable spinco at its window
trigger — the names the LLM read AND the names it never got to — because the
untagged buy-all book is the baseline: academic spinoff outperformance needs
no reader at all. On top of that baseline the report measures THE question
this god exists to answer: does LLM document judgment add alpha over buying
every spinoff?

  - llm_selected lift: do the LLM's picks beat the reviewed names it passed
    over? This is the whole ballgame — positive lift means reading Form 10s
    pays; flat means buy-all is the strategy and the reading is theater.
  - verdict_groups: forward returns by "own" / "watch" / "avoid". If "avoid"
    names re-rate just as hard, the garbage-barge detector detects nothing.
  - conviction_terciles / incentive_terciles: do higher conviction and
    stronger management incentive-alignment scores predict bigger re-ratings?
    These are the two numbers the dossier forces the LLM to commit to.
  - window_groups: "in_window" vs "late" entries — is the post-dump window
    real, or does entry timing wash out over a 5-month hold?

Fair comparison is enforced structurally, not by discipline: judgment
features exist ONLY on symbols the LLM actually reviewed, so every lift
compares picks against reviewed-but-passed-over names — never against names
nobody read. An unread spinoff is not a rejected one.

Entries are tagged source="spinoff". Ledger files may still carry entries
from the retired v1 crash-fade ghost (source="nemesis"); the report filters
those out so a dead strategy's shadow can't pollute the living one's verdict.
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, group_stats, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)

SOURCE = "spinoff"
HORIZON_DAYS = 150   # ~5 months — the re-rating window after the forced-seller dump


def spins_to_ghost(
    spins: Iterable,
    price_lookup: PriceLookup,
    *,
    reviewed: Optional[Iterable[str]] = None,
    selected: Optional[Iterable[str]] = None,
) -> list[dict]:
    """Convert distributed spinoffs into ghost candidate dicts.

    Opens EVERY priceable spinco — the buy-all control leg. `spins` may be
    plain dicts or objects with the same attribute names (symbol,
    entry_window, and optionally market_cap / verdict / conviction /
    incentive_alignment); the pipeline hands over dicts, dossier-bearing
    code hands over objects. Names with no symbol or no positive price from
    `price_lookup` are skipped — an unpriceable ghost position could never
    be graded, so opening it would just be a hole in the ledger.

    reviewed: symbols whose Form 10 the LLM actually read this cycle.
    selected: the subset of those the LLM chose to (paper-)own.

    FAIR-COMPARISON RULE: llm_selected / verdict / conviction /
    incentive_alignment are attached ONLY to reviewed symbols, with
    llm_selected = sym in selected. An unreviewed name carries no judgment
    features at all — ABSENT, not False — so boolean_lift's picks-vs-passed
    comparison can never be polluted by names the LLM never saw. Judgment
    values riding on an unreviewed spin (say, a stale dossier from a prior
    cycle) are deliberately dropped for the same reason.
    """
    rev = {s.upper() for s in (reviewed or [])}
    sel = {s.upper() for s in (selected or [])}

    out: list[dict] = []
    for spin in spins:
        get = spin.get if isinstance(spin, dict) else (
            lambda k, d=None: getattr(spin, k, d)
        )
        sym = (get("symbol") or "").upper()
        if not sym:
            continue
        px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue

        features: dict = {"entry_window": get("entry_window")}
        if get("market_cap") is not None:
            features["market_cap"] = float(get("market_cap"))

        # Judgment features gated on the reviewed set — see the docstring.
        if sym in rev:
            features["llm_selected"] = sym in sel
            if get("verdict") is not None:
                features["verdict"] = str(get("verdict"))
            if get("conviction") is not None:
                features["conviction"] = float(get("conviction"))
            if get("incentive_alignment") is not None:
                features["incentive_alignment"] = float(get("incentive_alignment"))
            if get("garbage_barge_risk") is not None:
                features["garbage_barge_risk"] = float(get("garbage_barge_risk"))

        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": HORIZON_DAYS,
            "source": SOURCE,
            "features": features,
        })
    return out


def spinoff_report(entries: Iterable[GhostEntry]) -> dict:
    """Judgment-vs-buy-all verdict from graded entries (source='spinoff' only).

    The llm_selected row of signal_lift is the single number the whole god
    hangs on. Foreign-source entries (the retired v1 crash-fade ghost, any
    other god sharing a ledger) are filtered out before anything is averaged.
    """
    graded = [e for e in graded_only(entries) if e.source == SOURCE]
    if not graded:
        return {
            "n": 0, "mean_return": None, "hit_rate": None,
            "signal_lift": {},
            "conviction_terciles": {},
            "incentive_terciles": {},
            "verdict_groups": {},
            "window_groups": {},
            "veto_filtered": {},
            "condemned": {},
        }
    kept = [e for e in graded if not _condemned(e)]
    tossed = [e for e in graded if _condemned(e)]
    return {
        **overall_stats(graded),
        "signal_lift": boolean_lift(graded),
        "conviction_terciles": numeric_tercile_stats(graded, "conviction"),
        "incentive_terciles": numeric_tercile_stats(graded, "incentive_alignment"),
        "verdict_groups": group_stats(graded, "verdict"),
        "window_groups": group_stats(graded, "entry_window"),
        # The THIRD contender — the "bouncer" strategy: buy every trigger
        # EXCEPT names the reading condemned. Unreviewed names ride along
        # (you cannot veto a document you never read; live reality is the
        # same). At the promotion checkpoint this leg competes head-to-head
        # with buy-all (overall stats above) and own-selected (signal_lift).
        "veto_filtered": overall_stats(kept) if kept else {},
        "condemned": overall_stats(tossed) if tossed else {},
    }


def _condemned(e: GhostEntry) -> bool:
    """A reviewed name the reading threw out: verdict 'avoid', or a
    garbage_barge_risk past the own-gate's 0.6 line. Absence of judgment
    tags (unreviewed) is never condemnation."""
    f = e.features or {}
    if str(f.get("verdict", "")).lower() == "avoid":
        return True
    g = f.get("garbage_barge_risk")
    try:
        return g is not None and float(g) > 0.6
    except (TypeError, ValueError):
        return False
