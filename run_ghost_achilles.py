#!/usr/bin/env python3
"""Ghost Achilles — paper-only PEAD event-study shadow.

Runs Achilles's event detection but places NO orders and touches NO real
sleeve. Opens a paper position for EVERY classified event it can price —
including disqualified ones — marks the book to market, grades matured
positions, and emits a drift report.

State namespace: cache/ghost_achilles_*
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ghost_achilles")

TODAY = date.today().isoformat()

GHOST_LEDGER_PATH  = "cache/ghost_achilles_ledger.json"
GHOST_CURVE_PATH   = "cache/ghost_achilles_curve.json"
GHOST_REPORT_PATH  = "cache/ghost_achilles_report.json"
GHOST_CURSOR_PATH  = "cache/ghost_achilles_cursor.json"
GHOST_STAGED_PATH  = "cache/ghost_achilles_staged_briefs.json"
GHOST_QUOTES_PATH  = "cache/ghost_achilles_quotes.json"
GHOST_FUNDAMENTALS_PATH = "cache/ghost_achilles_fundamentals.json"

# Operator-staged MCP quotes/fundamentals, fetched *after* pantheon.hydrate()
# has already run (hydrate() restores the whole cache/ tree from git as step 0,
# so anything staged under cache/ before invocation gets clobbered). These live
# outside cache/ so hydrate() never touches them.
GHOST_QUOTES_PREFETCH_PATH = "cache_prefetch/ghost_achilles_quotes.json"
GHOST_FUNDAMENTALS_PREFETCH_PATH = "cache_prefetch/ghost_achilles_fundamentals.json"

SPY_SYMBOL = "SPY"
MIN_PRICE  = 1.0    # skip sub-$1 stocks (likely delistings / warrants)
MIN_MARKET_CAP = 50_000_000
MAX_MARKET_CAP = 50_000_000_000


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


# ── Step 0: Hydrate ───────────────────────────────────────────────────
log.info("=== GHOST ACHILLES  %s ===", TODAY)
log.info("Step 0: Hydrating from claude/live...")
import pantheon
hydrated = pantheon.hydrate()
log.info("Hydrate: %s", "OK — cache restored" if hydrated else "no live branch yet — starting fresh")

from achilles.ghost import (
    briefs_to_candidates, drift_report,
    load_ledger, save_ledger, open_entries,
    mark_to_market, grade_entries, append_equity_point,
    HORIZON_DAYS,
)
from achilles.scoring import pead_neglect, liquidity_score, score_beat, surprise_strength
from achilles.earnings import fetch_earnings_surprise
from shared import broker, edgar

# ── Step 1: Restore ghost ledger + cursor ─────────────────────────────
log.info("Step 1: Restoring ghost ledger from %s...", GHOST_LEDGER_PATH)
existing_entries = load_ledger(GHOST_LEDGER_PATH)
n_graded_start = sum(1 for e in existing_entries if e.graded)
log.info("Ghost ledger: %d total  %d graded  %d open",
         len(existing_entries), n_graded_start,
         len(existing_entries) - n_graded_start)

cursor_data = _load_json(GHOST_CURSOR_PATH, {"cursor_date": None, "seen": []})
seen_accessions: set[str] = set(cursor_data.get("seen", []))
cursor_date: Optional[str] = cursor_data.get("cursor_date")
log.info("Cursor: date=%s  seen=%d accessions", cursor_date, len(seen_accessions))

# Events from TODAY are always re-scanned regardless of cursor — the cursor guards
# against re-scanning old periods; same-day events need to be re-checked because a
# prior run may have recorded accession numbers without successfully opening entries
# (e.g. prices unavailable). The open_entries() call below deduplicates via
# (symbol, source, date) so there's no risk of double-counting.
RESCAN_TODAY = True

# Load oracle insider clusters for preactivity signal
oracle_clusters_data = _load_json("cache/oracle_insider_clusters.json", {})
clusters_list = oracle_clusters_data.get("clusters", [])
insider_cluster_symbols: set[str] = {
    c["symbol"].upper() for c in clusters_list if c.get("symbol")
}
log.info("Oracle insider cluster symbols: %d", len(insider_cluster_symbols))


# ── Step 2: Scan EDGAR for new 8-K events ─────────────────────────────
log.info("Step 2: Scanning EDGAR for new events since %s...", cursor_date or "beginning")

# Scan from the day after cursor_date, but always include today.
if cursor_date and cursor_date < TODAY:
    try:
        start_dt = (datetime.strptime(cursor_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    except ValueError:
        start_dt = TODAY
else:
    # cursor_date == TODAY means we already ran today, but RESCAN_TODAY bypasses seen filter
    start_dt = TODAY

scan_start = min(start_dt, (datetime.strptime(TODAY, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d"))
log.info("Scanning EDGAR 8-Ks from %s to %s  (rescan_today=%s)", scan_start, TODAY, RESCAN_TODAY)

new_briefs: list[dict] = []
new_seen: list[str] = []

import re as _re
_TICKER_FROM_NAME = _re.compile(r'\(([A-Z]{1,5})\)\s*\(CIK')


def _extract_ticker(display_names: list) -> Optional[str]:
    """Extract ticker from EDGAR display_names like 'Company Inc. (TICK) (CIK 0001234)'."""
    for name in (display_names or []):
        m = _TICKER_FROM_NAME.search(str(name))
        if m:
            return m.group(1)
    return None


try:
    # Search for 8-Ks with earnings (item 2.02) or M&A (item 2.01) or guidance (7.01, 8.01)
    raw = edgar.search_filings(
        query='"2.02" OR "2.01" OR "7.01" OR "8.01"',
        forms=["8-K"],
        date_from=scan_start,
        date_to=TODAY,
    )
    hits = raw.get("hits", {}).get("hits", [])
    total_count = raw.get("hits", {}).get("total", {}).get("value", 0)
    log.info("EDGAR EFTS returned %d hits (total=%s)", len(hits), total_count)

    for hit in hits:
        src = hit.get("_source", {})
        # EDGAR EFTS uses 'adsh' for accession number
        acc = src.get("adsh") or src.get("accession_no", "")
        if not acc:
            continue
        file_date = src.get("file_date", "")
        # Always re-scan today's events (RESCAN_TODAY); skip older seen ones
        is_today_filing = (file_date == TODAY)
        if not is_today_filing and acc in seen_accessions:
            continue
        new_seen.append(acc)
        seen_accessions.add(acc)

        # items is a list in EFTS; convert to comma-joined string for classify_8k
        items_raw = src.get("items", [])
        if isinstance(items_raw, list):
            items_str = ",".join(items_raw)
        else:
            items_str = str(items_raw)

        event_classes = edgar.classify_8k(items_str)
        if not event_classes:
            continue  # not a PEAD-relevant event

        filing_date = src.get("file_date", TODAY)

        # Resolve ticker from display_names: "Company Inc.  (TICK)  (CIK 0001234)"
        sym = _extract_ticker(src.get("display_names", []))
        if not sym:
            continue

        new_briefs.append({
            "symbol": sym,
            "event_class": event_classes[0],
            "event_classes": event_classes,
            "accession_no": acc,
            "filing_date": filing_date,
            "items": items_str,
        })

    log.info("New events found: %d (from %d new accessions)", len(new_briefs), len(new_seen))

except Exception as exc:
    log.warning("EDGAR EFTS scan failed: %s — using staged briefs only", exc)


# ── Broker login + quotes ─────────────────────────────────────────────
log.info("Connecting to broker...")
broker_ok = broker.login()
log.info("Broker: %s", "connected" if broker_ok else "unavailable")

# Collect all symbols needing quotes
need_symbols: set[str] = set()
for b in new_briefs:
    need_symbols.add(b["symbol"])
for e in existing_entries:
    if not e.graded:
        need_symbols.add(e.symbol.upper())
need_symbols.add(SPY_SYMBOL)
need_symbols.discard("")

quotes: dict[str, float] = {}
fundamentals: dict[str, dict] = {}

# Load pre-fetched quotes. Prefer the cache_prefetch/ copy (staged via MCP
# *after* hydrate() ran, so it's never clobbered by the cache/ checkout in
# Step 0); fall back to the cache/ copy persisted by a prior run.
for _qpath in (GHOST_QUOTES_PREFETCH_PATH, GHOST_QUOTES_PATH):
    try:
        with open(_qpath) as _f:
            _raw_q = json.load(_f)
        quotes.update({k.upper(): float(v) for k, v in _raw_q.items() if v})
    except (FileNotFoundError, ValueError):
        continue
log.info("Pre-fetched quotes loaded: %d", len(quotes))

# Same prefer-prefetch-then-cache pattern for fundamentals (market caps).
for _fpath in (GHOST_FUNDAMENTALS_PREFETCH_PATH, GHOST_FUNDAMENTALS_PATH):
    try:
        with open(_fpath) as _f:
            _raw_f = json.load(_f)
        for _sym, _mc in (_raw_f.get("market_caps") or {}).items():
            if _mc:
                fundamentals.setdefault(_sym.upper(), {"market_cap": float(_mc)})
    except (FileNotFoundError, ValueError):
        continue
log.info("Pre-fetched fundamentals loaded: %d", len(fundamentals))

if broker_ok and need_symbols:
    sym_list = sorted(need_symbols)
    for i in range(0, len(sym_list), 100):
        chunk = sym_list[i:i + 100]
        chunk_quotes = broker.get_quotes(chunk)
        if chunk_quotes:
            quotes.update({k.upper(): float(v) for k, v in chunk_quotes.items() if v})
    log.info("Quotes: %d", len(quotes))

    # Fetch fundamentals for new symbols only
    new_syms = sorted({b["symbol"] for b in new_briefs})
    if new_syms:
        for i in range(0, len(new_syms), 50):
            chunk = new_syms[i:i + 50]
            f = broker.get_fundamentals(chunk)
            if f:
                fundamentals.update(f)
        log.info("Fundamentals: %d", len(fundamentals))
else:
    log.warning("No quotes available — open and mark will use entry prices")


def price_lookup(sym: str) -> Optional[float]:
    return quotes.get(sym.upper())


def market_cap_of(sym: str) -> Optional[float]:
    f = fundamentals.get(sym.upper(), {})
    mc = f.get("market_cap")
    if mc is None:
        return None
    try:
        return float(mc)
    except (TypeError, ValueError):
        return None


# ── Step 2b: Enrich briefs with convergence signals ───────────────────
log.info("Step 2b: Enriching %d new briefs with convergence signals...", len(new_briefs))

enriched_briefs: list[dict] = []
for b in new_briefs:
    sym = b["symbol"]
    mc = market_cap_of(sym)
    px = price_lookup(sym)
    if px is None or px < MIN_PRICE:
        log.debug("Skip %s: no price or below min", sym)
        continue

    # Neglect factor (core PEAD thesis)
    neglect = pead_neglect(mc) if mc else None

    # Earnings surprise
    surprise_pct: Optional[float] = None
    revenue_beat = False
    is_beat = False
    if "earnings_reaction" in b.get("event_classes", []):
        try:
            surp = fetch_earnings_surprise(sym)
            if surp:
                surprise_pct = surp.surprise_pct
                is_beat = surp.is_beat
        except Exception as exc:
            log.debug("Surprise fetch failed for %s: %s", sym, exc)

    # Insider preactivity (oracle bridge — check cluster cache)
    insider_preactivity = sym in insider_cluster_symbols

    # Concurrent guidance (from 8-K items — 7.01/8.01 present)
    items_set = edgar.parse_items(b.get("items", ""))
    concurrent_guidance_present = bool(items_set & {"7.01", "8.01"})
    concurrent_guidance = "raised" if concurrent_guidance_present else None

    # Liquidity score
    liq = liquidity_score(mc) if mc else None

    # Score (using score_beat for earnings, simple scoring otherwise)
    event_class = b.get("event_class", "unknown")
    conviction = 1.0
    score = 0.0

    if event_class == "earnings_reaction" and mc:
        scored = score_beat(
            surprise_pct=surprise_pct or 5.0,  # default 5% if unavailable
            market_cap=mc,
            revenue_beat=revenue_beat,
            guidance_raised=concurrent_guidance_present,
            insider_prebuy=insider_preactivity,
        )
        score = scored.get("score", 0.0)
        conviction = scored.get("components", {}).get("surprise_strength", 1.0)
    elif mc and neglect is not None and liq is not None:
        # Non-earnings: simple neglect × liquidity signal
        score = neglect * liq
        conviction = 1.0

    # Disqualification check (mirror real Achilles rules)
    disqualified = False
    disqualify_reason = ""
    if mc and not (MIN_MARKET_CAP <= mc <= MAX_MARKET_CAP):
        disqualified = True
        disqualify_reason = "market_cap_out_of_range"
    elif event_class == "bankruptcy":
        disqualified = True
        disqualify_reason = "bankruptcy_event"
    elif event_class == "delisting":
        disqualified = True
        disqualify_reason = "delisting_event"
    elif event_class == "earnings_reaction" and not is_beat and surprise_pct is not None:
        disqualified = True
        disqualify_reason = "earnings_miss"

    enriched_briefs.append({
        **b,
        "price": px,
        "market_cap": mc,
        "neglect": neglect,
        "surprise_pct": surprise_pct,
        "is_beat": is_beat,
        "revenue_beat": revenue_beat,
        "guidance_raised": concurrent_guidance_present,
        "concurrent_guidance": concurrent_guidance,
        "insider_preactivity": insider_preactivity,
        "liquidity": liq,
        "conviction": conviction,
        "score": score,
        "disqualified": disqualified,
        "disqualify_reason": disqualify_reason,
    })
    log.debug(
        "%s  class=%s  score=%.3f  disq=%s  mc=%.0fM  surprise=%.1f%%",
        sym, event_class, score, disqualified,
        (mc or 0) / 1e6, surprise_pct or 0,
    )

log.info("Enriched briefs: %d (from %d raw)", len(enriched_briefs), len(new_briefs))

# Save staged briefs for auditing
_save_json(GHOST_STAGED_PATH, enriched_briefs)


# ── Step 2c: Open paper positions ─────────────────────────────────────
log.info("Step 2c: Opening paper positions (ALL events, incl. disqualified)...")
candidates = briefs_to_candidates(enriched_briefs, price_lookup)
log.info("Candidates (priced): %d / %d enriched", len(candidates), len(enriched_briefs))

new_entries = open_entries(candidates, existing_entries, today=TODAY)
log.info("New paper entries opened: %d", len(new_entries))
all_entries = existing_entries + new_entries


# ── Step 3: Mark to market ────────────────────────────────────────────
log.info("Step 3: Marking ghost book to market...")
snapshot = mark_to_market(all_entries, price_lookup)
log.info(
    "Ghost book: n=%d  open=%d  closed=%d  equity=$%.2f  return=%.2f%%",
    snapshot["n"], snapshot["n_open"], snapshot["n_closed"],
    snapshot["equity"], snapshot["total_return"] * 100,
)

ghost_curve = _load_json(GHOST_CURVE_PATH, [])
if not isinstance(ghost_curve, list):
    ghost_curve = []

spy_px = price_lookup(SPY_SYMBOL)
spy_return = 0.0
if ghost_curve and spy_px:
    first_spy = next(
        (p.get("benchmark", {}).get("SPY_price") for p in ghost_curve
         if p.get("benchmark", {}).get("SPY_price")),
        None,
    )
    if first_spy and float(first_spy) > 0:
        spy_return = spy_px / float(first_spy) - 1.0

bench = {"SPY": round(spy_return, 6), "SPY_price": spy_px or 0.0}
ghost_curve = append_equity_point(ghost_curve, TODAY, snapshot, benchmark=bench)


# ── Step 4: Grade matured positions ───────────────────────────────────
log.info("Step 4: Grading matured positions (%d-day horizon)...", HORIZON_DAYS)
n_newly_graded = grade_entries(all_entries, price_lookup, today=TODAY)
total_graded = sum(1 for e in all_entries if e.graded)
log.info("Graded: %d new  %d total", n_newly_graded, total_graded)


# ── Step 5: Drift report ──────────────────────────────────────────────
log.info("Step 5: Computing drift report...")
report = drift_report(all_entries)

log.info("=== GHOST ACHILLES DRIFT REPORT ===")
n_rep = report.get("n", 0)
mr    = report.get("mean_return")
hr    = report.get("hit_rate")
log.info("Graded: %d  mean_return: %s  hit_rate: %s",
         n_rep,
         f"{mr*100:.1f}%" if mr is not None else "N/A",
         f"{hr*100:.0f}%" if hr is not None else "N/A")

class_drift = report.get("class_drift", {})
if class_drift:
    log.info("Class drift:")
    for cls, stats in sorted(class_drift.items()):
        log.info("  %-20s n=%-3d mean=%+.1f%%",
                 cls, stats["n"], (stats.get("mean") or 0) * 100)

lens_lift = report.get("lens_lift", {})
if lens_lift:
    log.info("Lens lift:")
    for flag, stats in sorted(lens_lift.items()):
        lift = stats.get("lift")
        log.info("  %-30s on=%+.1f%%(n=%d)  off=%+.1f%%(n=%d)  lift=%s",
                 flag,
                 (stats.get("mean_on") or 0) * 100, stats.get("n_on", 0),
                 (stats.get("mean_off") or 0) * 100, stats.get("n_off", 0),
                 f"{lift*100:+.1f}%" if lift is not None else "N/A")

for key in ["neglect_terciles", "surprise_terciles", "conviction_terciles",
            "score_terciles", "liquidity_terciles"]:
    val = report.get(key, {})
    if isinstance(val, dict) and val.get("n", 0) >= 3:
        mono = val.get("monotonic")
        log.info("%s: n=%d  monotonic=%s", key, val["n"], mono)


# ── Step 6: Persist ───────────────────────────────────────────────────
log.info("Step 6: Saving and persisting...")
os.makedirs("cache", exist_ok=True)

save_ledger(GHOST_LEDGER_PATH, all_entries)
_save_json(GHOST_CURVE_PATH, ghost_curve)
_save_json(GHOST_REPORT_PATH, report)

# Update cursor
new_cursor = {
    "cursor_date": TODAY,
    "seen": sorted(seen_accessions),
}
_save_json(GHOST_CURSOR_PATH, new_cursor)
_save_json(GHOST_STAGED_PATH, enriched_briefs)

persist_files = {
    GHOST_LEDGER_PATH:  _read(GHOST_LEDGER_PATH),
    GHOST_CURVE_PATH:   _read(GHOST_CURVE_PATH),
    GHOST_REPORT_PATH:  _read(GHOST_REPORT_PATH),
    GHOST_CURSOR_PATH:  _read(GHOST_CURSOR_PATH),
    GHOST_STAGED_PATH:  _read(GHOST_STAGED_PATH),
    GHOST_QUOTES_PATH:  _read(GHOST_QUOTES_PATH),
    GHOST_FUNDAMENTALS_PATH: _read(GHOST_FUNDAMENTALS_PATH),
}

try:
    sha = pantheon.persist(
        "ghost_achilles",
        persist_files,
        branch="claude/live",
        message=(
            f"ghost_achilles: {TODAY}  "
            f"entries={len(all_entries)}  graded={total_graded}  "
            f"new={len(new_entries)}"
        ),
    )
    log.info("Persisted to claude/live  sha=%s", sha[:12] if sha else "?")
except Exception as exc:
    log.error("Persist failed: %s", exc)

log.info("=== GHOST ACHILLES COMPLETE ===")
log.info("Entries: %d total  %d open  %d graded  %d new today",
         len(all_entries),
         sum(1 for e in all_entries if not e.graded),
         total_graded,
         len(new_entries))
log.info("Book: equity=$%.2f  return=%.2f%%",
         snapshot["equity"], snapshot["total_return"] * 100)
log.info("Open positions sample: %s",
         ", ".join(e.symbol for e in all_entries if not e.graded)[:200])
if n_rep:
    log.info("Signal: n=%d  mean=%.1f%%  hit=%.0f%%",
             n_rep, (mr or 0) * 100, (hr or 0) * 100)
else:
    log.info("Signal: n=0 graded — accumulating (horizon=%d days, oldest entry due %s)",
             HORIZON_DAYS,
             min((e.entry_date for e in all_entries), default="?"))
