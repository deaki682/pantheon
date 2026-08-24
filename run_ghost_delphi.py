#!/usr/bin/env python3
"""Ghost Delphi — momentum compounder learning shadow.

Shadows Delphi's momentum strategy against the full 118-name universe but
places NO orders and touches NO real sleeve. Opens a paper position for the
ENTIRE universe — including names BELOW their 20-day MA (the control group for
the MA-exit premise) and names the top-10 selection passed over (tagged
`selected`) — marks the book to market, grades matured positions (~90-day
momentum holding window), and emits a signal report (momentum terciles +
above_ma / selected lift).

NOTE: Delphi was retooled from a sector-rotation strategy to a pure momentum
compounder on 2026-06-30 (see delphi/rotation.py, delphi/screener.py). There
are no sectors or regime states in the current implementation, so this ghost
does not compute sector_return / regime_return / rotation_lift — those were
removed from delphi/ghost.py in the same retool and no longer apply.

State namespace: cache/ghost_delphi_*
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
log = logging.getLogger("ghost_delphi")

TODAY = date.today().isoformat()

GHOST_LEDGER_PATH = "cache/ghost_delphi_ledger.json"
GHOST_CURVE_PATH  = "cache/ghost_delphi_curve.json"
GHOST_REPORT_PATH = "cache/ghost_delphi_report.json"

# Universe prices staged via MCP get_equity_historicals *after* hydrate() ran
# (hydrate() restores the whole cache/ tree from git as step 0, so anything
# staged under cache/ before invocation would get clobbered). Lives outside
# cache/ so hydrate() never touches it.
UNIVERSE_PRICES_PREFETCH_PATH = "cache_prefetch/ghost_delphi_universe_prices.json"

MIN_PRICE = 2.0
SPY_SYMBOL = "SPY"

# Minimum share of the OPEN ghost book that must be priceable before a mark may
# be persisted.  Matches run_ghost_oracle.py — below this, mark_to_market's
# entry-price fallback writes fiction into the curve.
MIN_MARK_COVERAGE = 0.90


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


def main() -> None:
    # ── Step 0: Hydrate ───────────────────────────────────────────────────
    log.info("=== GHOST DELPHI  %s ===", TODAY)
    log.info("Step 0: Hydrating from claude/live...")
    import pantheon
    hydrated = pantheon.hydrate()
    log.info("Hydrate: %s", "OK — cache restored" if hydrated else "no live branch yet — starting fresh")

    from delphi.ghost import (
        universe_to_ghost, signal_report,
        load_ledger, save_ledger, open_entries,
        mark_to_market, grade_entries, append_equity_point,
        DEFAULT_DELPHI_HORIZON_DAYS,
    )
    from delphi.screener import score_universe
    from delphi.rotation import rotation_plan

    # ── Step 1: Restore ghost ledger ──────────────────────────────────────
    log.info("Step 1: Restoring ghost ledger from %s...", GHOST_LEDGER_PATH)
    existing_entries = load_ledger(GHOST_LEDGER_PATH)
    n_graded_start = sum(1 for e in existing_entries if e.graded)
    log.info("Ghost ledger: %d total  %d graded  %d open",
             len(existing_entries), n_graded_start,
             len(existing_entries) - n_graded_start)

    # ── Step 2: Universe prices + momentum ranking ────────────────────────
    log.info("Step 2: Loading universe daily-close series...")
    universe_prices = _load_json(UNIVERSE_PRICES_PREFETCH_PATH, {})
    log.info("Universe price series loaded: %d symbols", len(universe_prices))

    overrides = _load_json("cache/delphi_universe_overrides.json", {})
    additions = set(overrides.get("additions") or [])
    removals = set(overrides.get("removals") or [])

    # score_universe needs {symbol: [closes...]}; SPY isn't part of the momentum
    # universe itself, keep it aside for the benchmark.
    universe_only = {s: px for s, px in universe_prices.items() if s != SPY_SYMBOL}
    ranked = score_universe(universe_only, additions=additions, removals=removals)
    log.info("Momentum-ranked (above 20d MA): %d / %d universe names", len(ranked), len(universe_only))

    plan = rotation_plan()
    log.info("Rotation plan: regime=%s  risk_budget=%.2f", plan["regime"], plan["risk_budget"])

    # Current spot price = last close in the series (today's daily bar).
    def price_lookup(sym: str) -> Optional[float]:
        series = universe_prices.get(sym.upper())
        if not series:
            return None
        px = series[-1]
        return float(px) if px else None

    # ── Build candidates: the FULL universe, below-MA names included ──
    # Deliberately NOT the ranked (MA-filtered) list: below-MA names are the
    # control group for the MA-exit premise, and the live book's symbols are
    # tagged `selected` so the top-10 selection is testable against the
    # above-MA names it passed over.
    live_book = set((_load_json("cache/delphi_sleeve.json", {}) or {}).get("positions", {}).keys())
    effective = {s: px for s, px in universe_only.items()
                 if (s in additions or s not in removals)}
    candidates = universe_to_ghost(
        effective,
        selected=live_book,
        horizon_days=DEFAULT_DELPHI_HORIZON_DAYS,
    )
    candidates = [c for c in candidates if c["price"] >= MIN_PRICE]
    n_below_ma = sum(1 for c in candidates if not c["features"]["above_ma"])
    log.info("Priced candidates (>= $%.0f): %d  (above MA: %d, below MA: %d, live book tagged: %d)",
             MIN_PRICE, len(candidates), len(candidates) - n_below_ma, n_below_ma, len(live_book))

    # ── Step 2b: Open new paper positions (skip_open=True for recurring) ──
    new_entries = open_entries(candidates, existing_entries, today=TODAY, skip_open=True)
    log.info("New paper entries opened: %d", len(new_entries))
    all_entries = existing_entries + new_entries

    # ── Step 3: Mark to market ────────────────────────────────────────────
    log.info("Step 3: Marking ghost book to market...")

    # A mark is only meaningful if we can actually price the open book.  Without
    # a populated price prefetch, price_lookup returns None for every name,
    # mark_to_market falls back to each entry's ENTRY price, and the run reports
    # equity == cost basis with a flawless 0.00% return — indistinguishable from
    # a real flat day once it lands in the curve.  That is exactly what happened
    # on 2026-08-24: the prefetch was absent, and the run overwrote a book that
    # had marked $18,739.39 on 08-20 with a fabricated $18,000.00 / 0.00% point
    # carrying SPY_price 0.0.  Ghost Oracle has carried this guard since the
    # 2026-08-11 incident; Ghost Delphi did not, so it fabricated silently.
    # Refuse to fabricate: bail before anything persists.
    _open_syms = {e.symbol.upper() for e in all_entries if not e.graded and e.symbol}
    _priced = {s for s in _open_syms if price_lookup(s)}
    _coverage = (len(_priced) / len(_open_syms)) if _open_syms else 1.0
    log.info("Price coverage of open book: %d/%d (%.1f%%)",
             len(_priced), len(_open_syms), _coverage * 100)
    if _open_syms and _coverage < MIN_MARK_COVERAGE:
        log.error(
            "ABORT before persist: only %.1f%% of the open book is priceable "
            "(need >=%.0f%%). Marking now would write entry-price fiction into "
            "%s. Repopulate %s and re-run.",
            _coverage * 100, MIN_MARK_COVERAGE * 100,
            GHOST_CURVE_PATH, UNIVERSE_PRICES_PREFETCH_PATH)
        sys.exit(2)

    # The benchmark leg is what makes the curve interpretable — a point carrying
    # SPY_price 0.0 cannot be compared to any other point, and the 2026-08-24
    # fabrication carried exactly that.  Refuse to write an uninterpretable point.
    _spy_check = price_lookup(SPY_SYMBOL)
    if not _spy_check or float(_spy_check) <= 0:
        log.error(
            "ABORT before persist: no usable %s price (%r). The benchmark leg is "
            "required — a curve point with SPY_price 0.0 is uninterpretable and "
            "silently breaks every excess-return reading after it.",
            SPY_SYMBOL, _spy_check)
        sys.exit(4)

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
    log.info("Step 4: Grading matured positions (%d-day horizon)...", DEFAULT_DELPHI_HORIZON_DAYS)
    n_newly_graded = grade_entries(all_entries, price_lookup, today=TODAY)
    total_graded = sum(1 for e in all_entries if e.graded)
    log.info("Graded: %d new  %d total", n_newly_graded, total_graded)

    # ── Step 5: Signal report ─────────────────────────────────────────────
    log.info("Step 5: Computing signal report...")
    report = signal_report(all_entries)

    log.info("=== GHOST DELPHI SIGNAL REPORT ===")
    n_rep = report.get("n", 0)
    mr    = report.get("mean_return")
    hr    = report.get("hit_rate")
    log.info("Graded: %d  mean_return: %s  hit_rate: %s",
             n_rep,
             f"{mr*100:.1f}%" if mr is not None else "N/A",
             f"{hr*100:.0f}%" if hr is not None else "N/A")

    terciles = report.get("momentum_terciles", {})
    if terciles:
        log.info("Momentum terciles: n=%d monotonic=%s", terciles.get("n", 0), terciles.get("monotonic"))
        for t in ("high", "mid", "low"):
            stats = terciles.get("terciles", {}).get(t, {})
            mean = stats.get("mean")
            log.info("  %-5s n=%-3d mean=%s", t, stats.get("n", 0),
                     f"{mean*100:+.1f}%" if mean is not None else "N/A")

    # ── Step 6: Persist ───────────────────────────────────────────────────
    log.info("Step 6: Saving and persisting...")
    os.makedirs("cache", exist_ok=True)

    save_ledger(GHOST_LEDGER_PATH, all_entries)
    _save_json(GHOST_CURVE_PATH, ghost_curve)
    _save_json(GHOST_REPORT_PATH, report)

    persist_files = {
        GHOST_LEDGER_PATH: _read(GHOST_LEDGER_PATH),
        GHOST_CURVE_PATH:  _read(GHOST_CURVE_PATH),
        GHOST_REPORT_PATH: _read(GHOST_REPORT_PATH),
    }

    try:
        sha = pantheon.persist(
            "ghost_delphi",
            persist_files,
            branch="claude/live",
            message=(
                f"ghost_delphi: {TODAY}  "
                f"n={snapshot['n']}  new={len(new_entries)}  graded+={n_newly_graded}  "
                f"total_graded={total_graded}"
            ),
        )
        log.info("Persisted: %s", sha)
    except Exception as exc:
        log.error("Persist FAILED: %s", exc)
        raise

    log.info("=== DONE ===")


if __name__ == "__main__":
    main()
