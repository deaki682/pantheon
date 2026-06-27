#!/usr/bin/env python3
"""Oracle multi-lens universe screen — long-running CLI entry point.

Designed to be invoked from cron / GitHub Actions / a VPS rather than from
inside an interactive Claude session.

Features:
  - Lens-level resume: each lens writes its cache file on completion. On
    restart, completed lens cache files are skipped if --resume.
  - Intra-lens checkpointing: insider clusters and quality lens checkpoint
    every 200 names so a crash loses at most ~200 names of work.
  - Heartbeat file (`cache/oracle_screen_heartbeat.json`) updated every
    progress callback — operators can tail it to monitor.
  - Pantheon persist at the end (gated by --persist) pushes results to the
    `claude/live` state branch via CAS.

Usage:
  python run_oracle_screen.py --persist             # full run, persists state
  python run_oracle_screen.py --cap 200 --no-persist  # quick first run
  python run_oracle_screen.py --resume              # pick up after a crash
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make the repo root importable when invoked directly
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.edgar import fetch_company_tickers, set_rate_limit
from shared.insiders import scan_universe
from oracle.lenses import (
    combine_lenses,
    fetch_13f_information_table_xml,
    find_latest_13fhr_accession,
    make_form4_fetcher,
    scan_universe_quality,
    search_recent_13d,
)
from oracle.screener import rank_survivors
from oracle.smart_money import SMART_MONEY_FUNDS, parse_13f_information_table, smart_money_holders


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_heartbeat(cache_dir: Path, phase: str, done: int, total: int) -> None:
    p = cache_dir / "oracle_screen_heartbeat.json"
    payload = {
        "pid": os.getpid(),
        "phase": phase,
        "names_done": done,
        "names_total": total,
        "updated_at": _utc_now(),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(p)


def write_json_atomic(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True))
    tmp.replace(path)


def lens_done(cache_dir: Path, name: str) -> bool:
    return (cache_dir / name).exists()


def log(phase: str, msg: str) -> None:
    print(f"[{_utc_now()}] [{phase}] {msg}", flush=True)


# ---- Lens 1: insider clusters ----

def run_insider_clusters(sym_to_cik: dict, cache_dir: Path, *, max_workers: int, today: str | None) -> None:
    cache = cache_dir / "oracle_insider_clusters.json"
    fetcher = make_form4_fetcher(sym_to_cik, days_back=60, today=today)
    symbols = list(sym_to_cik.keys())
    total = len(symbols)

    def on_checkpoint(done, clusters):
        write_json_atomic(cache, {"clusters": clusters, "progress": {"done": done, "total": total}, "updated_at": _utc_now()})
        log("insiders", f"checkpoint {done}/{total} ({len(clusters)} clusters so far)")

    def on_progress(done, total_):
        if done % 50 == 0 or done == total_:
            write_heartbeat(cache_dir, "insider_clusters", done, total_)

    log("insiders", f"starting scan over {total} symbols, max_workers={max_workers}")
    clusters = scan_universe(
        symbols, fetcher,
        max_workers=max_workers, checkpoint_every=200,
        on_checkpoint=on_checkpoint, on_progress=on_progress,
    )
    write_json_atomic(cache, {"clusters": clusters, "progress": {"done": total, "total": total}, "updated_at": _utc_now()})
    log("insiders", f"DONE — {len(clusters)} clusters")


# ---- Lens 2: smart-money 13F ----

# Curated mapping of fund name -> CIK. Manual because SEC's ticker map is
# for issuers, not investment managers. Keep this in sync with
# oracle.smart_money.SMART_MONEY_FUNDS.
SMART_MONEY_CIKS = {
    "BERKSHIRE HATHAWAY": "0001067983",
    "BAUPOST GROUP":      "0001061768",
    "PERSHING SQUARE":    "0001336528",
    "GREENLIGHT CAPITAL": "0001079114",
    "OAKMARK":            "0000872323",
    "RUANE CUNNIFF":      "0000855886",
    "FIRST EAGLE":        "0001057706",
    "AKRE CAPITAL":       "0001112520",
    # WEDGEWOOD, TWEEDY BROWNE — fill in when known
}


def run_smart_money(cache_dir: Path) -> None:
    cache = cache_dir / "oracle_smart_money.json"
    holdings_by_manager: dict[str, list] = {}
    for manager, cik in SMART_MONEY_CIKS.items():
        log("13F", f"{manager} (CIK {cik})...")
        acc = find_latest_13fhr_accession(cik)
        if not acc:
            log("13F", f"  no 13F-HR found, skipping")
            continue
        xml = fetch_13f_information_table_xml(cik, acc)
        if not xml:
            log("13F", f"  no info table xml")
            continue
        holdings = parse_13f_information_table(xml, manager=manager)
        log("13F", f"  parsed {len(holdings)} holdings from acc {acc}")
        holdings_by_manager[manager] = holdings

    # 13F holdings are keyed by CUSIP + issuer name, not ticker. Resolve to
    # tickers (OpenFIGI authoritative, SEC name-match fallback) before grouping,
    # or every holding fails to join the ticker-keyed screen.
    from shared.cusip import build_name_ticker_index, resolve_cusips_openfigi
    from oracle.smart_money import resolve_holdings

    cusips = {h.cusip for hs in holdings_by_manager.values() for h in hs if h.cusip}
    log("13F", f"resolving {len(cusips)} CUSIPs via OpenFIGI...")
    cusip_map = resolve_cusips_openfigi(cusips)
    name_index = {}
    try:
        from shared.edgar import fetch_company_tickers_rows
        name_index = build_name_ticker_index(fetch_company_tickers_rows())
    except Exception as e:
        log("13F", f"  name-fallback index unavailable: {e}")
    resolve_holdings(holdings_by_manager, cusip_map=cusip_map, name_index=name_index)
    resolved = sum(1 for hs in holdings_by_manager.values() for h in hs if h.symbol)
    log("13F", f"  resolved {resolved} holdings ({len(cusip_map)} via CUSIP)")

    sm_holders = smart_money_holders(holdings_by_manager)
    payload = {
        "holders": {sym: list(managers) for sym, managers in sm_holders.items()},
        "by_manager_counts": {m: len(hs) for m, hs in holdings_by_manager.items()},
        "updated_at": _utc_now(),
    }
    write_json_atomic(cache, payload)
    log("13F", f"DONE — {len(sm_holders)} smart-money-held symbols")


# ---- Lens 3: activist 13D ----

def run_activist_13d(cache_dir: Path, *, lookback_days: int = 30) -> None:
    cache = cache_dir / "oracle_activist_13d.json"
    today = datetime.now(timezone.utc).date()
    start = (today - timedelta(days=lookback_days)).isoformat()
    end = today.isoformat()
    log("13D", f"searching {start} → {end}...")
    filings = search_recent_13d(date_from=start, date_to=end)
    symbols = sorted({(f.symbol or "").upper() for f in filings if f.symbol})
    payload = {
        "filings": [{
            "accession_no": f.accession_no, "form": f.form,
            "filing_date": f.filing_date, "cik": f.cik, "symbol": f.symbol,
        } for f in filings],
        "symbols": symbols,
        "lookback_days": lookback_days,
        "updated_at": _utc_now(),
    }
    write_json_atomic(cache, payload)
    log("13D", f"DONE — {len(filings)} fresh 13D filings, {len(symbols)} unique symbols")


# ---- Lens 4: quality screen ----

def run_quality(sym_to_cik: dict, cache_dir: Path) -> None:
    cache = cache_dir / "oracle_prescreener.json"
    total = len(sym_to_cik)

    def on_checkpoint(done, rows):
        write_json_atomic(cache, {"rows": rows, "progress": {"done": done, "total": total}, "updated_at": _utc_now()})
        passed = sum(1 for r in rows if r.get("pass"))
        log("quality", f"checkpoint {done}/{total} ({passed} passed)")

    def on_progress(done, total_):
        if done % 50 == 0 or done == total_:
            write_heartbeat(cache_dir, "quality_screen", done, total_)

    log("quality", f"starting scan over {total} symbols")
    rows = scan_universe_quality(
        sym_to_cik, checkpoint_every=200,
        on_checkpoint=on_checkpoint, on_progress=on_progress,
    )
    write_json_atomic(cache, {"rows": rows, "progress": {"done": total, "total": total}, "updated_at": _utc_now()})
    log("quality", f"DONE — {sum(1 for r in rows if r.get('pass'))}/{total} passed")


# ---- Combine + rank ----

def combine_and_rank(cache_dir: Path) -> None:
    insiders_data = json.loads((cache_dir / "oracle_insider_clusters.json").read_text())["clusters"]
    quality_data = json.loads((cache_dir / "oracle_prescreener.json").read_text())["rows"]
    sm_data = json.loads((cache_dir / "oracle_smart_money.json").read_text())["holders"]
    act_data = json.loads((cache_dir / "oracle_activist_13d.json").read_text())["symbols"]

    # Universe = anything that hit any lens or passed quality
    universe = set()
    for c in insiders_data:
        universe.add((c.get("symbol") or "").upper())
    for sym in sm_data.keys():
        universe.add(sym.upper())
    for sym in act_data:
        universe.add(sym.upper())
    for row in quality_data:
        if row.get("pass"):
            universe.add(row["symbol"].upper())

    rows = combine_lenses(
        universe=universe,
        insider_clusters=insiders_data,
        smart_money=sm_data,
        activist_symbols=act_data,
        quality_rows=quality_data,
    )
    top = rank_survivors(rows, top_n=100)
    write_json_atomic(cache_dir / "oracle_screen.json", {
        "top": top, "n_universe_hits": len(rows), "updated_at": _utc_now(),
    })
    log("combine", f"DONE — {len(rows)} universe hits, top {len(top)} ranked")


# ---- Persist via pantheon ----

def persist_all(cache_dir: Path, repo_dir: Path) -> None:
    from pantheon import persist
    files = {}
    for name in (
        "oracle_insider_clusters.json", "oracle_smart_money.json",
        "oracle_activist_13d.json", "oracle_prescreener.json",
        "oracle_screen.json", "oracle_cadence.json", "oracle_screen_heartbeat.json",
    ):
        p = cache_dir / name
        if p.exists():
            files[f"cache/{name}"] = p.read_text()
    if not files:
        log("persist", "nothing to persist")
        return
    log("persist", f"pushing {len(files)} files to claude/live...")
    sha = persist(
        "oracle", files,
        branch="claude/live", remote="origin", repo_dir=str(repo_dir),
        max_retries=6, base_backoff=1.0, backoff_factor=1.5,
        message="oracle-screen: lens caches refreshed",
    )
    log("persist", f"committed {sha[:10]}")


# ---- Main ----

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Oracle multi-lens universe screen")
    ap.add_argument("--cache-dir", default="cache", help="output directory (default: cache)")
    ap.add_argument("--cap", type=int, default=0, help="limit universe size for testing (0 = full)")
    ap.add_argument("--rate", type=float, default=8.0, help="SEC requests/sec (default 8)")
    ap.add_argument("--max-workers", type=int, default=4, help="insider-lens threading (default 4)")
    ap.add_argument("--lenses", default="insiders,smart_money,activist_13d,quality",
                     help="comma-separated lens list (default: all)")
    ap.add_argument("--resume", action="store_true", help="skip lenses whose cache already exists")
    ap.add_argument("--persist", action="store_true", help="push results to claude/live at the end")
    ap.add_argument("--repo-dir", default=".", help="path to git repo for persist (default: cwd)")
    args = ap.parse_args(argv)

    cache_dir = Path(args.cache_dir).resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = Path(args.repo_dir).resolve()

    set_rate_limit(args.rate)

    log("setup", f"cache_dir={cache_dir}")
    log("setup", "fetching ticker→CIK map...")
    sym_to_cik = fetch_company_tickers()
    log("setup", f"  {len(sym_to_cik)} tickers")
    if args.cap and args.cap > 0:
        sym_to_cik = dict(list(sym_to_cik.items())[: args.cap])
        log("setup", f"  capped to {len(sym_to_cik)}")

    lenses = {x.strip() for x in args.lenses.split(",") if x.strip()}

    t0 = time.monotonic()
    if "insiders" in lenses:
        if args.resume and lens_done(cache_dir, "oracle_insider_clusters.json"):
            log("insiders", "RESUME — cache present, skipping")
        else:
            run_insider_clusters(sym_to_cik, cache_dir, max_workers=args.max_workers, today=None)
    if "smart_money" in lenses:
        if args.resume and lens_done(cache_dir, "oracle_smart_money.json"):
            log("13F", "RESUME — cache present, skipping")
        else:
            run_smart_money(cache_dir)
    if "activist_13d" in lenses:
        if args.resume and lens_done(cache_dir, "oracle_activist_13d.json"):
            log("13D", "RESUME — cache present, skipping")
        else:
            run_activist_13d(cache_dir)
    if "quality" in lenses:
        if args.resume and lens_done(cache_dir, "oracle_prescreener.json"):
            log("quality", "RESUME — cache present, skipping")
        else:
            run_quality(sym_to_cik, cache_dir)

    # Combine + rank (always; pulls from whatever cache files exist)
    try:
        combine_and_rank(cache_dir)
    except (FileNotFoundError, KeyError) as e:
        log("combine", f"skipped — missing lens output: {e}")

    # Mark cadence
    from oracle.calendar import mark_run
    mark_run(str(cache_dir / "oracle_cadence.json"), "screen")

    elapsed = time.monotonic() - t0
    log("done", f"all lenses complete in {elapsed/60:.1f} min")

    if args.persist:
        persist_all(cache_dir, repo_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
