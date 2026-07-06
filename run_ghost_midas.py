#!/usr/bin/env python3
"""Ghost Midas — paper-only signal-convergence learning shadow.

Shadows Midas's weekend convergence scan (`/midas-scan`) but places NO orders
and touches NO real sleeve (Midas himself is fully live-retired 2026-07-04;
this ghost outlives him and keeps running the live-vs-legacy A/B race). Opens
a paper position for EVERY stage-2 finalist it can price — including names
the LLM would disqualify (the control group for the disqualification-gate
test) — marks the book to market, grades matured (5-day horizon) positions,
and emits a convergence report. Each finalist carries both `score` (live,
flattened max-of-timely formula) and `score_legacy` (old convergence-
multiplier formula); `signal_lift` grades `live_pick` vs `legacy_pick` head
to head — the 2026-07-04 A/B.

State namespace: cache/ghost_midas_*
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ghost_midas")

TODAY = date.today().isoformat()

GHOST_LEDGER_PATH  = "cache/ghost_midas_ledger.json"
GHOST_CURVE_PATH   = "cache/ghost_midas_curve.json"
GHOST_REPORT_PATH  = "cache/ghost_midas_report.json"
GHOST_CADENCE_PATH = "cache/ghost_midas_cadence.json"

SCAN_PATH = "cache/midas_scan.json"

# Quotes are staged via MCP get_equity_quotes *before* this script runs (this
# script is invoked mid-session, after the caller already fetched quotes for
# every symbol it needs) and dropped here so hydrate() (which restores cache/
# from git) never clobbers them.
QUOTES_PREFETCH_PATH = "cache_prefetch/ghost_midas_quotes.json"

SPY_SYMBOL = "SPY"

DEATH_CLOCK_GRADED_WEEKS = 20


def _load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _save_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, path)


def _read(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return "{}"


def _graded_week_pairs(entries) -> int:
    """Count weeks where BOTH live_pick and legacy_pick are graded (head-to-head)."""
    by_week: dict[str, dict[str, bool]] = {}
    for e in entries:
        if not e.graded:
            continue
        wk = e.entry_date
        slot = by_week.setdefault(wk, {"live": False, "legacy": False})
        if e.features.get("live_pick") is True:
            slot["live"] = True
        if e.features.get("legacy_pick") is True:
            slot["legacy"] = True
    return sum(1 for v in by_week.values() if v["live"] and v["legacy"])


def main() -> None:
    log.info("=== GHOST MIDAS  %s ===", TODAY)
    log.info("Step 0: Hydrating from claude/live...")
    import pantheon
    hydrated = pantheon.hydrate()
    log.info("Hydrate: %s", "OK — cache restored" if hydrated else "no live branch yet — starting fresh")

    from midas.ghost import (
        finalists_to_candidates, convergence_report,
        load_ledger, save_ledger, open_entries,
        mark_to_market, grade_entries, append_equity_point,
        HORIZON_DAYS,
    )
    from oracle import calendar as oracle_calendar

    # ── Step 1: Restore ghost ledger ──────────────────────────────────────
    log.info("Step 1: Restoring ghost ledger from %s...", GHOST_LEDGER_PATH)
    existing_entries = load_ledger(GHOST_LEDGER_PATH)
    n_graded_start = sum(1 for e in existing_entries if e.graded)
    log.info("Ghost ledger: %d total  %d graded  %d open",
             len(existing_entries), n_graded_start,
             len(existing_entries) - n_graded_start)

    # ── Step 2: Load finalists + quotes ────────────────────────────────────
    scan = _load_json(SCAN_PATH, {})
    finalists = scan.get("finalists") or []
    log.info("Step 2: %d finalists from %s (scanned_at=%s)",
              len(finalists), SCAN_PATH, scan.get("scanned_at"))

    quotes = _load_json(QUOTES_PREFETCH_PATH, {})
    log.info("Prefetched quotes: %d symbols", len(quotes))

    def price_lookup(sym: str) -> Optional[float]:
        px = quotes.get(sym.upper())
        return float(px) if px else None

    # ── Step 2b: Open paper positions for ALL finalists (incl. disqualified) ──
    candidates = finalists_to_candidates(finalists, price_lookup)
    log.info("Priced candidates: %d / %d finalists", len(candidates), len(finalists))

    new_entries = open_entries(candidates, existing_entries, today=TODAY, skip_open=True)
    log.info("New paper entries opened: %d", len(new_entries))
    all_entries = existing_entries + new_entries

    # ── Step 3: Mark to market ────────────────────────────────────────────
    log.info("Step 3: Marking ghost book to market...")
    snapshot = mark_to_market(all_entries, price_lookup)
    log.info("Ghost book: n=%d  open=%d  closed=%d  equity=$%.2f  return=%.2f%%",
             snapshot["n"], snapshot["n_open"], snapshot["n_closed"],
             snapshot["equity"], snapshot["total_return"] * 100)

    ghost_curve = _load_json(GHOST_CURVE_PATH, [])
    if not isinstance(ghost_curve, list):
        ghost_curve = []

    spy_px = price_lookup(SPY_SYMBOL)
    spy_return = 0.0
    if ghost_curve and spy_px:
        first_spy = next((p.get("benchmark", {}).get("SPY_price") for p in ghost_curve
                          if p.get("benchmark", {}).get("SPY_price")), None)
        if first_spy and float(first_spy) > 0:
            spy_return = spy_px / float(first_spy) - 1.0

    bench = {"SPY": round(spy_return, 6), "SPY_price": spy_px or 0.0}
    ghost_curve = append_equity_point(ghost_curve, TODAY, snapshot, benchmark=bench)

    # ── Step 4: Grade matured positions ───────────────────────────────────
    log.info("Step 4: Grading matured positions (%d-day horizon)...", HORIZON_DAYS)
    n_newly_graded = grade_entries(all_entries, price_lookup, today=TODAY)
    total_graded = sum(1 for e in all_entries if e.graded)
    log.info("Graded: %d new  %d total", n_newly_graded, total_graded)

    # ── Step 5: Convergence report ─────────────────────────────────────────
    log.info("Step 5: Computing convergence report...")
    report = convergence_report(all_entries)

    log.info("=== GHOST MIDAS CONVERGENCE REPORT ===")
    n_rep = report.get("n", 0)
    mr    = report.get("mean_return")
    hr    = report.get("hit_rate")
    log.info("Graded: %d  mean_return: %s  hit_rate: %s",
             n_rep,
             f"{mr*100:.1f}%" if mr is not None else "N/A",
             f"{hr*100:.0f}%" if hr is not None else "N/A")

    conv = report.get("convergence_terciles", {})
    if conv:
        log.info("Convergence terciles: n=%d monotonic=%s", conv.get("n", 0), conv.get("monotonic"))

    lift = report.get("signal_lift", {})
    for flag in ("live_pick", "legacy_pick", "disqualified"):
        row = lift.get(flag, {})
        if row:
            mo, mf = row.get("mean_on"), row.get("mean_off")
            log.info("  %-12s n_on=%-3d mean_on=%s  n_off=%-3d mean_off=%s  lift=%s",
                      flag, row.get("n_on", 0),
                      f"{mo*100:+.1f}%" if mo is not None else "N/A",
                      row.get("n_off", 0),
                      f"{mf*100:+.1f}%" if mf is not None else "N/A",
                      f"{row.get('lift')*100:+.1f}%" if row.get("lift") is not None else "N/A")

    graded_week_pairs = _graded_week_pairs(all_entries)
    log.info("Graded weekly live_pick-vs-legacy_pick head-to-heads: %d / %d death-clock target",
              graded_week_pairs, DEATH_CLOCK_GRADED_WEEKS)
    if graded_week_pairs >= DEATH_CLOCK_GRADED_WEEKS:
        log.warning("DEATH CLOCK REACHED (%d >= %d) — final comparison due, NOT run automatically here.",
                    graded_week_pairs, DEATH_CLOCK_GRADED_WEEKS)

    # ── Step 6: Persist ───────────────────────────────────────────────────
    log.info("Step 6: Saving and persisting...")
    os.makedirs("cache", exist_ok=True)

    save_ledger(GHOST_LEDGER_PATH, all_entries)
    _save_json(GHOST_CURVE_PATH, ghost_curve)
    _save_json(GHOST_REPORT_PATH, report)
    oracle_calendar.mark_run(GHOST_CADENCE_PATH, "session")

    persist_files = {
        GHOST_LEDGER_PATH:  _read(GHOST_LEDGER_PATH),
        GHOST_CURVE_PATH:   _read(GHOST_CURVE_PATH),
        GHOST_REPORT_PATH:  _read(GHOST_REPORT_PATH),
        GHOST_CADENCE_PATH: _read(GHOST_CADENCE_PATH),
    }

    try:
        sha = pantheon.persist(
            "ghost_midas",
            persist_files,
            branch="claude/live",
            message=(
                f"ghost_midas: {TODAY}  "
                f"n={snapshot['n']}  new={len(new_entries)}  graded+={n_newly_graded}  "
                f"total_graded={total_graded}  weekly_pairs={graded_week_pairs}"
            ),
        )
        log.info("Persisted: %s", sha)
    except Exception as exc:
        log.error("Persist FAILED: %s", exc)
        raise

    log.info("=== DONE ===")


if __name__ == "__main__":
    main()
