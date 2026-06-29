#!/usr/bin/env python3
"""Ghost Achilles — paper-only event-study shadow.

Runs Achilles's full event detection pipeline but places NO orders and touches
NO real sleeve. Opens paper positions for every classified event (including
disqualified ones), grades matured positions, and produces a signal validation
report (class drift, lens lift, tercile monotonicity).

State namespace: cache/ghost_achilles_*

Usage:
    python run_ghost_achilles.py                  # full EDGAR scan + price
    python run_ghost_achilles.py --reprice-only   # re-open from saved briefs,
                                                  # skip EDGAR (needs fresh quotes
                                                  # in cache/ghost_achilles_quotes.json)
    python run_ghost_achilles.py --reset-cursor   # clear cursor before running
                                                  # (re-detects historical events)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime
from typing import Optional

# ── bootstrap ─────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("--reprice-only", action="store_true",
                    help="Skip EDGAR; re-open existing staged briefs with fresh quotes")
parser.add_argument("--reset-cursor", action="store_true",
                    help="Clear ghost cursor before running (re-detects all history)")
args = parser.parse_args()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ghost_achilles")

TODAY = date.today().isoformat()
NOW_ISO = datetime.utcnow().isoformat()

# ── paths ─────────────────────────────────────────────────────────────
GHOST_LEDGER_PATH  = "cache/ghost_achilles_ledger.json"
GHOST_CURVE_PATH   = "cache/ghost_achilles_curve.json"
GHOST_REPORT_PATH  = "cache/ghost_achilles_report.json"
GHOST_CURSOR_PATH  = "cache/ghost_achilles_cursor.json"
GHOST_BRIEFS_PATH  = "cache/ghost_achilles_staged_briefs.json"  # save for repricing

ACTIVIST_PATH    = "cache/oracle_activist_13d.json"
INSIDER_PATH     = "cache/oracle_insider_clusters.json"
SMART_MONEY_PATH = "cache/oracle_smart_money.json"
SCREEN_PATH      = "cache/oracle_screen.json"
PRESCREENER_PATH = "cache/oracle_prescreener.json"
QUOTES_PATH      = "cache/ghost_achilles_quotes.json"

POLL_CAP = 250


# ── helpers ───────────────────────────────────────────────────────────

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


def _symbols_from_cache(path):
    data = _load_json(path, [])
    if isinstance(data, list):
        return [d.get("symbol", d.get("ticker", "")) for d in data if isinstance(d, dict)]
    if isinstance(data, dict):
        if "holders" in data:
            return list(data["holders"].keys())
        if "clusters" in data:
            return [c.get("symbol", "") for c in data["clusters"] if isinstance(c, dict)]
        if "symbols" in data and isinstance(data["symbols"], list):
            return list(data["symbols"])
        if "top" in data:
            return [r.get("symbol", "") for r in data["top"] if isinstance(r, dict)]
        return list(data.keys())
    return []


# ── Step 0: Hydrate ───────────────────────────────────────────────────

log.info("=== GHOST ACHILLES  %s ===", TODAY)
log.info("Step 0: Hydrating from claude/live...")
import pantheon
hydrated = pantheon.hydrate()
log.info("Hydrate: %s", "OK — cache restored from live branch" if hydrated
         else "no live branch yet — starting fresh")

# ── imports that need the hydrated code path ─────────────────────────
from achilles import cursor as cursor_mod
from achilles.classify import classify_filing
from achilles.convergence import conviction_multiplier, neglect_premium
from achilles.earnings import fetch_earnings_surprise, is_actionable_beat
from achilles.events import Event, aggregate_insider_clusters, build_event_for_filing
from achilles.ghost import briefs_to_candidates, drift_report
from achilles.oracle_bridge import (
    company_quality as oracle_company_quality,
    has_insider_preactivity,
    load_dossier_convictions,
    load_insider_activity,
    load_prescreener_quality,
    load_screen_scores,
)
from achilles.playbooks import build_playbooks
from achilles.scoring import liquidity_score, score_event
from achilles.watchlist import build_watchlist
from shared import broker
from shared.edgar import (
    fetch_body, fetch_company_tickers, fetch_submissions,
    parse_submissions_recent,
)
from shared.ghost import (
    append_equity_point, grade_entries, load_ledger,
    mark_to_market, open_entries, save_ledger,
)
from shared.insiders import parse_form4

# ── Step 1: Restore ghost ledger ──────────────────────────────────────

log.info("Step 1: Restoring ghost ledger...")
existing_entries = load_ledger(GHOST_LEDGER_PATH)
n_graded_start = sum(1 for e in existing_entries if e.graded)
log.info("Ghost ledger: %d total  %d graded  %d open",
         len(existing_entries), n_graded_start,
         len(existing_entries) - n_graded_start)

if args.reset_cursor:
    log.info("--reset-cursor: clearing ghost cursor")
    ghost_cursor = cursor_mod.Cursor()
else:
    ghost_cursor = cursor_mod.load(GHOST_CURSOR_PATH)
log.info("Ghost cursor: date=%s  seen=%d", ghost_cursor.cursor_date, len(ghost_cursor.seen))

# ── Load Oracle research data ─────────────────────────────────────────
log.info("Loading Oracle research data...")
dossier_convictions  = load_dossier_convictions()
prescreener_quality  = load_prescreener_quality()
oracle_insider_act   = load_insider_activity()
screen_scores        = load_screen_scores()
log.info("Oracle: %d dossiers  %d prescreener  %d insider clusters  %d screen",
         len(dossier_convictions), len(prescreener_quality),
         len(oracle_insider_act), len(screen_scores))

playbooks = build_playbooks()

# ── Market caps from prescreener ──────────────────────────────────────
market_caps: dict[str, float] = {}
prescreener_raw = _load_json(PRESCREENER_PATH, {})
if isinstance(prescreener_raw, dict):
    for sym_key, info in prescreener_raw.items():
        if isinstance(info, dict) and "market_cap" in info:
            try:
                market_caps[sym_key.upper()] = float(info["market_cap"])
            except (TypeError, ValueError):
                pass

# ── Step 2: Detect events (or load from staging cache) ───────────────
ghost_briefs: list[dict] = []

if args.reprice_only:
    # ── Reprice mode: load previously staged briefs ──────────────────
    log.info("Step 2 (reprice-only): Loading staged briefs from %s...", GHOST_BRIEFS_PATH)
    staged = _load_json(GHOST_BRIEFS_PATH, [])
    if not staged:
        log.warning("No staged briefs found — run without --reprice-only first")
        sys.exit(1)
    ghost_briefs = staged
    log.info("Loaded %d staged briefs", len(ghost_briefs))
else:
    # ── Full EDGAR scan ───────────────────────────────────────────────
    log.info("Step 2a: Building watchlist...")
    watchlist = build_watchlist(
        activist_13d     = _symbols_from_cache(ACTIVIST_PATH),
        insider_clusters = _symbols_from_cache(INSIDER_PATH),
        smart_money      = _symbols_from_cache(SMART_MONEY_PATH),
        broad_screen     = _symbols_from_cache(SCREEN_PATH),
    )
    poll_list = watchlist[:POLL_CAP]
    log.info("Watchlist: %d symbols  polling top %d", len(watchlist), len(poll_list))

    log.info("Step 2b: Connecting to broker...")
    broker_ok = broker.login()
    log.info("Broker: %s", "connected" if broker_ok else "unavailable — cached quotes only")

    log.info("Step 2c: Polling EDGAR for recent filings...")
    try:
        all_tickers = fetch_company_tickers()
        cik_map = {s: all_tickers[s] for s in poll_list if s in all_tickers}
    except Exception as exc:
        log.warning("CIK lookup failed: %s", exc)
        cik_map = {}
    log.info("CIK resolved: %d / %d", len(cik_map), len(poll_list))

    all_filings: list = []
    poll_errors = 0
    for i, sym in enumerate(poll_list):
        cik = cik_map.get(sym)
        if not cik:
            continue
        try:
            payload  = fetch_submissions(cik)
            filings  = parse_submissions_recent(payload, symbol=sym)
            all_filings.extend(filings)
        except Exception as exc:
            poll_errors += 1
            if poll_errors <= 5:
                log.debug("Poll %s failed: %s", sym, exc)
        if (i + 1) % 50 == 0:
            log.info("  polled %d / %d...", i + 1, len(poll_list))

    log.info("Filings scanned: %d  poll errors: %d", len(all_filings), poll_errors)

    # Filter via ghost cursor (independent from real Achilles cursor)
    new_filings = cursor_mod.filter_new(ghost_cursor, all_filings)
    new_filings = cursor_mod.register_events(ghost_cursor, new_filings)
    log.info("New filings for ghost: %d  (cursor now at %s)",
             len(new_filings), ghost_cursor.cursor_date)

    log.info("Step 2d: Classifying events...")
    events: list[Event] = []
    form4_txns: list = []

    for filing in new_filings:
        try:
            if filing.form.strip() in ("4", "4/A"):
                # Ghost skips Form 4 body fetches — insider clusters are read
                # from Oracle's cached oracle_insider_clusters.json instead.
                continue

            labels = classify_filing(filing)
            if not labels:
                continue

            # Ghost skips body fetches — guidance direction metadata is left
            # empty (None). This makes ghost classification much faster; the
            # trade-off is that concurrent_guidance lift won't be populated
            # until a body-fetching pass is added.
            body_text = ""

            earnings_surprise = None
            surprise_pct = None
            insider_boost = 1.0
            # Ghost skips live earnings fetches (no broker) — surprise_pct
            # will be enriched from metadata in the enrich loop below.

            filing_events = build_event_for_filing(
                filing,
                body_text=body_text,
                today=TODAY,
                surprise_pct=surprise_pct,
                earnings_surprise=earnings_surprise,
                insider_boost=insider_boost,
            )
            events.extend(filing_events)

        except Exception as exc:
            log.warning("Classify %s: %s", getattr(filing, "accession_no", "?"), exc)

    if form4_txns:
        clusters = aggregate_insider_clusters(form4_txns)
        events.extend(clusters)
        log.info("Form 4: %d txns → %d clusters", len(form4_txns), len(clusters))

    log.info("Events detected: %d", len(events))
    by_class: dict[str, int] = {}
    for ev in events:
        by_class[ev.event_class] = by_class.get(ev.event_class, 0) + 1
    for cls, n in sorted(by_class.items()):
        log.info("  %-22s %d", cls, n)

    # ── Enrich events into ghost brief dicts ─────────────────────────
    log.info("Enriching events with convergence signals...")
    for ev in events:
        sym = (ev.symbol or "").upper()
        if not sym:
            continue

        oq = oracle_company_quality(
            sym,
            dossier_convictions=dossier_convictions,
            prescreener_quality=prescreener_quality,
            screen_scores=screen_scores,
        )
        neglect = neglect_premium(oq)

        surprise_pct_val = ev.metadata.get("surprise_pct")

        has_ins, _ = has_insider_preactivity(
            sym,
            insider_activity=oracle_insider_act,
            filing_date=ev.filing_date,
        )

        cg_raw = ev.metadata.get("concurrent_guidance", "")
        if cg_raw == "raised":
            concurrent_guidance: Optional[bool] = True
        elif cg_raw in ("lowered", "withdrawn"):
            concurrent_guidance = False
        else:
            concurrent_guidance = None

        conviction = conviction_multiplier(
            surprise_pct=surprise_pct_val,
            insider_preactivity=bool(has_ins),
            concurrent_guidance=bool(concurrent_guidance) if concurrent_guidance is not None else False,
            oracle_quality=oq,
        )

        mcap = market_caps.get(sym, 500_000_000)
        liq = liquidity_score(mcap)

        pb = playbooks.get(ev.event_class)
        if pb:
            was_disabled = pb.disabled
            pb.disabled = False
            score_out = score_event(
                playbook=pb,
                event_strength=ev.strength,
                company_quality=oq,
                neglect=neglect,
                market_cap=mcap,
                first_seen_iso=NOW_ISO,
                disqualifier_flags=ev.metadata.get("disqualifiers", []),
            )
            pb.disabled = was_disabled
            score_val = score_out.get("score", 0.0)
        else:
            score_val = 0.0

        disq_flags = list(ev.metadata.get("disqualifiers", []))

        ghost_briefs.append({
            "symbol": sym,
            "event_class": ev.event_class,
            "score": score_val,
            "disqualifiers": disq_flags,
            "neglect": neglect,
            "surprise_pct": surprise_pct_val,
            "insider_preactivity": has_ins,
            "concurrent_guidance": concurrent_guidance,
            "conviction": conviction,
            "liquidity": liq,
            "horizon_days": 10,
            "filing_date": ev.filing_date,
        })

    log.info("Ghost briefs enriched: %d", len(ghost_briefs))

    # ── Save staged briefs for --reprice-only mode ────────────────────
    _save_json(GHOST_BRIEFS_PATH, ghost_briefs)
    log.info("Staged briefs saved to %s", GHOST_BRIEFS_PATH)

# ── Fetch quotes ──────────────────────────────────────────────────────
need_quotes: set[str] = {b["symbol"] for b in ghost_briefs if b.get("symbol")}
for entry in existing_entries:
    if not entry.graded and entry.symbol:
        need_quotes.add(entry.symbol)
need_quotes.discard("")

cached_quotes: dict[str, float] = _load_json(QUOTES_PATH, {})
quotes: dict[str, float] = {k.upper(): float(v) for k, v in cached_quotes.items() if v}

if not args.reprice_only:
    broker_ok = broker.login()
    if need_quotes and broker_ok:
        live_quotes = broker.get_quotes(sorted(need_quotes))
        if live_quotes:
            quotes.update({k.upper(): float(v) for k, v in live_quotes.items() if v})
            log.info("Fresh quotes: %d", len(live_quotes))

    missing_caps = need_quotes - set(market_caps)
    if missing_caps and broker_ok:
        live_caps = broker.get_market_caps(sorted(missing_caps))
        if live_caps:
            market_caps.update({k.upper(): float(v) for k, v in live_caps.items() if v})

# Save quotes cache
_save_json(QUOTES_PATH, quotes)
log.info("Quotes available: %d symbols", len(quotes))

def price_lookup(sym: str) -> Optional[float]:
    return quotes.get(sym.upper())

# ── Open paper positions ──────────────────────────────────────────────
log.info("Opening paper positions for every priceable event...")
candidates = briefs_to_candidates(ghost_briefs, price_lookup)
log.info("Priceable candidates: %d / %d briefs", len(candidates), len(ghost_briefs))

new_entries = open_entries(candidates, existing_entries, today=TODAY)
log.info("New ghost entries opened: %d", len(new_entries))
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

ghost_curve = append_equity_point(ghost_curve, TODAY, snapshot, benchmark={"SPY": 0.0})

# ── Step 4: Grade matured positions ──────────────────────────────────
log.info("Step 4: Grading matured positions (10-day horizon)...")
n_newly_graded = grade_entries(all_entries, price_lookup, today=TODAY)
total_graded = sum(1 for e in all_entries if e.graded)
log.info("Graded: %d new  %d total", n_newly_graded, total_graded)

# ── Step 5: Drift report ──────────────────────────────────────────────
log.info("Step 5: Computing drift report...")
report = drift_report(all_entries)

log.info("=== GHOST ACHILLES SIGNAL REPORT ===")
n_rep = report.get("n", 0)
mr    = report.get("mean_return")
hr    = report.get("hit_rate")
log.info("Graded: %d  mean_return: %s  hit_rate: %s",
         n_rep,
         f"{mr*100:.1f}%" if mr is not None else "N/A",
         f"{hr*100:.0f}%" if hr is not None else "N/A")

class_drift = report.get("class_drift", {})
if class_drift:
    log.info("Class drift (measured vs literature priors):")
    lit_priors = {
        "earnings_reaction": 0.55,
        "insider_cluster":   0.58,
        "activist_13d":      0.60,
        "ma_target":         0.65,
        "spinoff_window":    0.55,
        "guidance_revision": 0.55,
    }
    for cls, stats in class_drift.items():
        prior = lit_priors.get(cls, 0.0)
        measured = stats.get("mean") or 0.0
        log.info("  %-22s n=%-3d measured=%+.1f%%  prior=%.0f%%  delta=%+.1f%%",
                 cls, stats["n"], measured * 100, prior * 100,
                 (measured - (prior - 1.0)) * 100)

lens_lift = report.get("lens_lift", {})
if lens_lift:
    log.info("Lens lift (boolean signals):")
    for flag, stats in lens_lift.items():
        lift = stats.get("lift")
        log.info("  %-26s on=%+.1f%% (n=%d)  off=%+.1f%% (n=%d)  lift=%s",
                 flag,
                 (stats.get("mean_on") or 0) * 100, stats.get("n_on", 0),
                 (stats.get("mean_off") or 0) * 100, stats.get("n_off", 0),
                 f"{lift*100:+.1f}%" if lift is not None else "N/A")

neglect_t = report.get("neglect_terciles", {})
log.info("Neglect terciles (CORE THESIS — monotonic=%s):",
         neglect_t.get("monotonic", "N/A") if neglect_t.get("n", 0) >= 3 else "insufficient data")
if neglect_t.get("n", 0) >= 3:
    for tier, stats in neglect_t.get("terciles", {}).items():
        log.info("  %-5s n=%-3d mean=%+.1f%%", tier, stats["n"],
                 (stats["mean"] or 0) * 100)

for key, label in [
    ("surprise_terciles",   "Surprise terciles"),
    ("conviction_terciles", "Conviction terciles"),
    ("score_terciles",      "Score terciles"),
    ("liquidity_terciles",  "Liquidity terciles"),
]:
    t = report.get(key, {})
    if t.get("n", 0) >= 3:
        log.info("%s: monotonic=%s  n=%d", label, t.get("monotonic"), t["n"])
    else:
        log.info("%s: insufficient data (n=%d)", label, t.get("n", 0))

# ── Step 6: Persist ───────────────────────────────────────────────────
log.info("Step 6: Saving and persisting to claude/live...")
os.makedirs("cache", exist_ok=True)

save_ledger(GHOST_LEDGER_PATH, all_entries)
log.info("Ledger saved: %d entries", len(all_entries))

if not args.reprice_only:
    cursor_mod.save(GHOST_CURSOR_PATH, ghost_cursor)
    log.info("Ghost cursor saved: %s", ghost_cursor.cursor_date)

_save_json(GHOST_CURVE_PATH, ghost_curve)
log.info("Curve saved: %d points", len(ghost_curve))

_save_json(GHOST_REPORT_PATH, report)
log.info("Report saved")

def _read(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return "{}"

persist_files = {
    GHOST_LEDGER_PATH:  _read(GHOST_LEDGER_PATH),
    GHOST_CURVE_PATH:   _read(GHOST_CURVE_PATH),
    GHOST_REPORT_PATH:  _read(GHOST_REPORT_PATH),
    GHOST_CURSOR_PATH:  _read(GHOST_CURSOR_PATH),
    GHOST_BRIEFS_PATH:  _read(GHOST_BRIEFS_PATH),
}

try:
    sha = pantheon.persist(
        "ghost_achilles",
        persist_files,
        branch="claude/live",
        message=(
            f"ghost_achilles: {TODAY}  "
            f"entries={len(all_entries)}  graded={total_graded}  "
            f"briefs={len(ghost_briefs)}"
        ),
    )
    log.info("Persisted to claude/live  sha=%s", sha[:12])
except Exception as exc:
    log.error("Persist failed: %s", exc)

# ── Summary ───────────────────────────────────────────────────────────
log.info("=== GHOST ACHILLES COMPLETE ===")
log.info(
    "Entries: %d total  %d open  %d graded  %d new today",
    len(all_entries),
    sum(1 for e in all_entries if not e.graded),
    total_graded,
    len(new_entries),
)
log.info(
    "Book: equity=$%.2f  return=%.2f%%",
    snapshot["equity"], snapshot["total_return"] * 100
)
log.info("Report: n=%d  mean=%.1f%%  hit=%.0f%%",
         n_rep,
         (mr or 0) * 100,
         (hr or 0) * 100)
if neglect_t.get("n", 0) >= 3:
    mono_val = neglect_t.get("monotonic", False)
    log.info("NEGLECT THESIS: %s", "VALIDATED" if mono_val else "NEEDS REVIEW")
