#!/usr/bin/env python3
"""Ghost Oracle — paper-only learning shadow.

Runs Oracle's full scoring brain against the screen + dossier pool but places
NO orders and touches NO real sleeve.  Opens an unconstrained paper position for
every priceable candidate, marks the book to market, grades matured positions,
and emits a calibration report (lens lift, conviction tiers, signal terciles).

State namespace: cache/ghost_oracle_*
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date, datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ghost_oracle")

TODAY = date.today().isoformat()

GHOST_LEDGER_PATH = "cache/ghost_oracle_ledger.json"
GHOST_CURVE_PATH  = "cache/ghost_oracle_curve.json"
GHOST_REPORT_PATH = "cache/ghost_oracle_report.json"

SCREEN_PATH   = "cache/oracle_screen.json"
DOSSIER_PATH  = "cache/oracle_dossiers.json"
QUOTES_PATH   = "cache/ghost_oracle_quotes.json"

SPY_SYMBOL = "SPY"


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


# ── Step 0: Hydrate ───────────────────────────────────────────────────
log.info("=== GHOST ORACLE  %s ===", TODAY)
log.info("Step 0: Hydrating from claude/live...")
import pantheon
hydrated = pantheon.hydrate()
log.info("Hydrate: %s", "OK — cache restored" if hydrated else "no live branch yet — starting fresh")

from oracle.ghost import (
    calibration_report,
    dossiers_to_candidates,
    screen_rows_to_candidates,
    load_ledger,
    save_ledger,
    open_entries,
    mark_to_market,
    grade_entries,
    append_equity_point,
)
from shared import broker

# ── Step 1: Restore ghost ledger ──────────────────────────────────────
log.info("Step 1: Restoring ghost ledger from %s...", GHOST_LEDGER_PATH)
existing_entries = load_ledger(GHOST_LEDGER_PATH)
n_graded_start = sum(1 for e in existing_entries if e.graded)
log.info("Ghost ledger: %d total  %d graded  %d open",
         len(existing_entries), n_graded_start,
         len(existing_entries) - n_graded_start)

# ── Step 2: Build candidates ──────────────────────────────────────────
log.info("Step 2: Building candidates from screen + dossiers...")

screen_data = _load_json(SCREEN_PATH, {})
if isinstance(screen_data, dict):
    screen_rows = screen_data.get("top") or screen_data.get("rows") or []
else:
    screen_rows = []
log.info("Screen rows: %d", len(screen_rows))

dossiers_data = _load_json(DOSSIER_PATH, [])
if isinstance(dossiers_data, dict):
    dossiers_list = dossiers_data.get("dossiers", list(dossiers_data.values()))
elif isinstance(dossiers_data, list):
    dossiers_list = dossiers_data
else:
    dossiers_list = []
log.info("Dossiers: %d", len(dossiers_list))

# Collect all symbols that need pricing
need_symbols: set[str] = set()
for r in screen_rows:
    sym = (r.get("symbol") or "").upper()
    if sym:
        need_symbols.add(sym)
for d in dossiers_list:
    sym = (d.get("symbol") or "").upper()
    if sym:
        need_symbols.add(sym)
for e in existing_entries:
    if not e.graded and e.symbol:
        need_symbols.add(e.symbol.upper())
need_symbols.add(SPY_SYMBOL)
need_symbols.discard("")

log.info("Need quotes for %d symbols", len(need_symbols))

# ── Fetch live quotes ─────────────────────────────────────────────────
# Load any pre-fetched quotes as a baseline (written by MCP or prior runs)
quotes: dict[str, float] = {}
try:
    with open(QUOTES_PATH) as _f:
        _raw = json.load(_f)
    quotes = {k.upper(): float(v) for k, v in _raw.items() if v}
    log.info("Pre-fetched quotes loaded: %d", len(quotes))
except (FileNotFoundError, ValueError):
    pass

broker_ok = broker.login()
log.info("Broker: %s", "connected" if broker_ok else "unavailable")

if broker_ok and need_symbols:
    sym_list = sorted(need_symbols)
    for i in range(0, len(sym_list), 100):
        chunk = sym_list[i:i + 100]
        chunk_quotes = broker.get_quotes(chunk)
        if chunk_quotes:
            quotes.update({k.upper(): float(v) for k, v in chunk_quotes.items() if v})
    log.info("Live quotes fetched: %d total", len(quotes))
elif not quotes:
    log.warning("No quotes available — open and mark will use entry prices")

def price_lookup(sym: str) -> Optional[float]:
    return quotes.get(sym.upper())

# ── Build candidates ──────────────────────────────────────────────────
screen_candidates = screen_rows_to_candidates(screen_rows, price_lookup)
log.info("Screen candidates (priced): %d / %d", len(screen_candidates), len(screen_rows))

dossier_candidates = dossiers_to_candidates(dossiers_list, price_lookup)
log.info("Dossier candidates (priced): %d / %d", len(dossier_candidates), len(dossiers_list))

all_candidates = screen_candidates + dossier_candidates

# ── Liquidity filter (skip sub-$2 stocks) ────────────────────────────
MIN_PRICE = 2.0
all_candidates = [c for c in all_candidates if c["price"] >= MIN_PRICE]
log.info("After liquidity filter (>=$%.0f): %d candidates", MIN_PRICE, len(all_candidates))

# ── Step 2b: Open new paper positions (skip_open=True for recurring) ──
new_entries = open_entries(all_candidates, existing_entries, today=TODAY, skip_open=True)
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

# Benchmark: SPY return vs first curve point
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
log.info("Step 4: Grading matured positions (1-year horizon)...")
n_newly_graded = grade_entries(all_entries, price_lookup, today=TODAY)
total_graded = sum(1 for e in all_entries if e.graded)
log.info("Graded: %d new  %d total", n_newly_graded, total_graded)

# ── Step 5: Calibration report ────────────────────────────────────────
log.info("Step 5: Computing calibration report...")
report = calibration_report(all_entries)

log.info("=== GHOST ORACLE CALIBRATION REPORT ===")
n_rep = report.get("n", 0)
mr    = report.get("mean_return")
hr    = report.get("hit_rate")
log.info("Graded: %d  mean_return: %s  hit_rate: %s",
         n_rep,
         f"{mr*100:.1f}%" if mr is not None else "N/A",
         f"{hr*100:.0f}%" if hr is not None else "N/A")

lens_lift = report.get("lens_lift", {})
if lens_lift:
    log.info("Lens lift:")
    for flag, stats in lens_lift.items():
        lift = stats.get("lift")
        log.info("  %-30s on=%+.1f%% (n=%d)  off=%+.1f%% (n=%d)  lift=%s",
                 flag,
                 (stats.get("mean_on") or 0) * 100, stats.get("n_on", 0),
                 (stats.get("mean_off") or 0) * 100, stats.get("n_off", 0),
                 f"{lift*100:+.1f}%" if lift is not None else "N/A")

for key, label in [
    ("conviction_tiers",    "Conviction tiers"),
    ("valuation_terciles",  "Valuation terciles"),
    ("quality_terciles",    "Quality terciles"),
    ("score_terciles",      "Score terciles"),
]:
    val = report.get(key, {})
    if isinstance(val, dict) and val.get("n", val.get("n_on", 1)):
        mono = val.get("monotonic")
        log.info("%s  monotonic=%s", label, mono)

sector_ret = report.get("sector_return", {})
if sector_ret:
    log.info("Sector returns (graded):")
    for sector, stats in sorted(sector_ret.items(),
                                 key=lambda x: -(x[1].get("mean") or 0)):
        log.info("  %-25s n=%-3d mean=%+.1f%%",
                 sector, stats["n"], (stats.get("mean") or 0) * 100)

# ── Step 6: Persist ───────────────────────────────────────────────────
log.info("Step 6: Saving and persisting...")
os.makedirs("cache", exist_ok=True)

save_ledger(GHOST_LEDGER_PATH, all_entries)
_save_json(GHOST_CURVE_PATH, ghost_curve)
_save_json(GHOST_REPORT_PATH, report)

def _read(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return "{}"

persist_files = {
    GHOST_LEDGER_PATH: _read(GHOST_LEDGER_PATH),
    GHOST_CURVE_PATH:  _read(GHOST_CURVE_PATH),
    GHOST_REPORT_PATH: _read(GHOST_REPORT_PATH),
    QUOTES_PATH:       _read(QUOTES_PATH),
}

try:
    sha = pantheon.persist(
        "ghost_oracle",
        persist_files,
        branch="claude/live",
        message=(
            f"ghost_oracle: {TODAY}  "
            f"entries={len(all_entries)}  graded={total_graded}  "
            f"new={len(new_entries)}"
        ),
    )
    log.info("Persisted to claude/live  sha=%s", sha[:12] if sha else "?")
except Exception as exc:
    log.error("Persist failed: %s", exc)

log.info("=== GHOST ORACLE COMPLETE ===")
log.info("Entries: %d total  %d open  %d graded  %d new today",
         len(all_entries),
         sum(1 for e in all_entries if not e.graded),
         total_graded,
         len(new_entries))
log.info("Book: equity=$%.2f  return=%.2f%%",
         snapshot["equity"], snapshot["total_return"] * 100)
if n_rep:
    log.info("Signal: n=%d  mean=%.1f%%  hit=%.0f%%",
             n_rep, (mr or 0) * 100, (hr or 0) * 100)
else:
    log.info("Signal: n=0 graded — accumulating data (horizon=365 days)")
