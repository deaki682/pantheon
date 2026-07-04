#!/usr/bin/env python3
"""Quiet-cluster ghost — rolling fresh Form 4 cluster scan (backlog #1,
docs/lab_prereg_quiet_cluster_ghost.md).

Builds the FROZEN population from EDGAR daily form indexes (form.idx),
2026-06-01 onward, applies the frozen cluster rule (>=2 distinct insiders,
each >=$10k open-market buy, aggregate >=$50k, 60-calendar-day window,
grant-mill issuers excluded), then the frozen "quiet" filter (no 8-K,
no abnormal price move, no volume anomaly at the knowability date).
Opens paper entries for BOTH arms (quiet + loud comparison) via
shared.ghost, under source="quiet_cluster_ghost". No backtest, no
registry forward-test transition (prereg's documented gap) -- this is a
measurement study tracked outside the registry per the prereg's option
(b). NO broker orders, NO sleeve mutation.

State namespace: cache/lab_quiet_cluster_*, entries land in the shared
cache/lab_ghost_ledger.json / cache/lab_ghost_curve.json.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import edgar, insiders, sharadar, ghost

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("quiet_cluster_scan")

TODAY = date.today().isoformat()
WINDOW_START = "2026-06-01"  # frozen: day after the spent replay's window closes

CURSOR_PATH = "cache/lab_quiet_cluster_cursor.json"
CANDIDATES_PATH = "cache/lab_quiet_cluster_candidates.json"
PROGRESS_PATH = "cache/lab_quiet_cluster_progress.json"
EVENTS_PATH = "cache/lab_quiet_cluster_events.json"
GHOST_LEDGER_PATH = "cache/lab_ghost_ledger.json"
GHOST_CURVE_PATH = "cache/lab_ghost_curve.json"

STRATEGY = "quiet_cluster_ghost"

FORM4_RE = re.compile(
    r"^(4)\s{2,}(.{0,80}?)\s{2,}(\d+)\s+(\d{8})\s+(\S+)\s*$"
)


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


def _daterange(d0: str, d1: str):
    d = datetime.strptime(d0, "%Y-%m-%d").date()
    end = datetime.strptime(d1, "%Y-%m-%d").date()
    while d <= end:
        if d.weekday() < 5:
            yield d.isoformat()
        d += timedelta(days=1)


def fetch_form4_rows(day: str) -> list[dict]:
    """Rows from one day's form.idx where Form Type == '4' exactly."""
    d = datetime.strptime(day, "%Y-%m-%d").date()
    qtr = (d.month - 1) // 3 + 1
    url = (f"https://www.sec.gov/Archives/edgar/daily-index/{d.year}"
           f"/QTR{qtr}/form.{d.strftime('%Y%m%d')}.idx")
    try:
        text = edgar.http_get(url)
    except Exception as e:
        log.warning("skip %s: %s", day, e)
        return []
    out = []
    for line in text.splitlines():
        m = FORM4_RE.match(line)
        if not m:
            continue
        out.append({
            "name": m.group(2).strip(),
            "cik": edgar.cik10(m.group(3)),
            "date": day,
            "file": m.group(5),
        })
    return out


def build_candidates(rows: list[dict], cik_to_symbol: dict) -> dict:
    """Group daily-index rows by accession (File Name); split issuer vs
    owner by CIK->ticker registry membership (identical method to the
    frozen spent replay's prereg). Returns {issuer_cik: {"symbol", "name",
    "owner_events": [{"owner_cik","owner_name","date"}]}}.
    """
    # The daily index lists one row per FILER ROLE on an accession, and
    # each role's "File Name" uses ITS OWN CIK in the path
    # (edgar/data/<issuer_cik>/<accession>.txt for the issuer row,
    # edgar/data/<owner_cik>/<accession>.txt for the reporting-owner
    # row) -- same accession number, different path string. Group by
    # the accession number embedded in the filename, not the raw path.
    by_acc: dict[str, list[dict]] = {}
    for r in rows:
        acc = r["file"].rsplit("/", 1)[-1].removesuffix(".txt")
        by_acc.setdefault(acc, []).append(r)

    issuers: dict[str, dict] = {}
    for file_, group in by_acc.items():
        issuer_rows = [r for r in group if r["cik"] in cik_to_symbol]
        owner_rows = [r for r in group if r["cik"] not in cik_to_symbol]
        if not issuer_rows:
            continue  # deep-OTC issuer with no listed ticker -- same
            # exclusion the spent replay's prereg already disclosed
        issuer_row = issuer_rows[0]
        icik = issuer_row["cik"]
        entry = issuers.setdefault(icik, {
            "symbol": cik_to_symbol[icik],
            "name": issuer_row["name"],
            "owner_events": [],
            "accessions": set(),
        })
        entry["accessions"].add(file_)
        for orow in owner_rows:
            entry["owner_events"].append({
                "owner_cik": orow["cik"], "owner_name": orow["name"],
                "date": orow["date"], "file": file_,
            })
    return issuers


def passes_prefilter(owner_events: list[dict], window_days: int = 14) -> bool:
    """>=2 distinct owner CIKs with events within a window_days window,
    at least once -- the fetch-budget-honesty candidacy pre-filter."""
    by_owner: dict[str, list[str]] = {}
    for e in owner_events:
        by_owner.setdefault(e["owner_cik"], []).append(e["date"])
    distinct = list(by_owner.keys())
    if len(distinct) < 2:
        return False
    dates = sorted({datetime.strptime(e["date"], "%Y-%m-%d").date() for e in owner_events})
    for i, d0 in enumerate(dates):
        owners_in_window = set()
        for e in owner_events:
            ed = datetime.strptime(e["date"], "%Y-%m-%d").date()
            if d0 <= ed <= d0 + timedelta(days=window_days):
                owners_in_window.add(e["owner_cik"])
        if len(owners_in_window) >= 2:
            return True
    return False


def fetch_issuer_filings(cik: str) -> list:
    """One submissions.json fetch per issuer, reused for the grant-mill
    check, the Form 4 txn fetch, and the 8-K quiet check."""
    payload = edgar.fetch_submissions(cik)
    return edgar.parse_submissions_recent(payload)


def is_grant_mill(filings: list) -> bool:
    """>60 Form 4 filings in the trailing 12 months -- mega-cap
    compensation machinery, excluded by the frozen prereg rule."""
    cutoff = (date.today() - timedelta(days=365)).isoformat()
    n_form4_12mo = sum(1 for f in filings if f.form == "4" and f.filing_date >= cutoff)
    return n_form4_12mo > 60


def fetch_txns_for_issuer(filings: list, window_start: str) -> tuple[list[insiders.InsiderTxn], dict[str, str]]:
    """Fetch and parse Form 4 XML for an issuer's in-window accessions via
    its already-fetched submissions filings (primaryDocument -> exact
    archive URL). Returns (txns, {accession_no: filing_date})."""
    txns: list[insiders.InsiderTxn] = []
    filing_dates: dict[str, str] = {}
    seen_acc = set()
    for f in filings:
        if f.form != "4" or f.filing_date < window_start:
            continue
        acc_norm = f.acc_clean
        if acc_norm in seen_acc or not f.primary_url:
            continue
        seen_acc.add(acc_norm)
        filing_dates[f.accession_no] = f.filing_date
        # Filing.primary_url points at the xslF345X0*/ HUMAN-READABLE HTML
        # rendering for ownership forms (SEC serves the XSL-transformed
        # view at that path, not the raw XML) -- strip the xsl* rendering
        # subfolder to reach the actual ownershipDocument XML sitting
        # directly in the accession folder.
        raw_url = re.sub(r"/xslF345X\d+/", "/", f.primary_url)
        try:
            xml_text = edgar.http_get(raw_url)
        except Exception as e:
            log.warning("form4 fetch failed %s: %s", f.accession_no, e)
            continue
        txns.extend(insiders.parse_form4(xml_text, accession_no=f.accession_no))
    return txns, filing_dates


def completing_buy_date(txns: list[insiders.InsiderTxn], filing_dates: dict[str, str]) -> tuple[str, dict] | None:
    """Find the FIRST point (by knowability date) at which >=2 distinct
    insiders' cumulative qualifying buys (>=$10k each) reach an aggregate
    >=$50k within a 60-calendar-day window. Returns (knowability_date,
    cluster_summary) or None."""
    buys = [t for t in txns if t.is_open_market_buy and t.dollars >= 10_000]
    if not buys:
        return None
    # knowability per txn = max(transaction_date, filing_date-of-its-accession)
    events = []
    for t in buys:
        fd = filing_dates.get(t.accession_no, t.transaction_date)
        kd = max(t.transaction_date, fd)
        events.append((kd, t))
    events.sort(key=lambda x: x[0])

    by_insider_total: dict[str, float] = {}
    for i in range(len(events)):
        kd_i, t_i = events[i]
        window_start_dt = datetime.strptime(kd_i, "%Y-%m-%d") - timedelta(days=60)
        totals: dict[str, float] = {}
        for kd_j, t_j in events[: i + 1]:
            if datetime.strptime(kd_j, "%Y-%m-%d") < window_start_dt:
                continue
            if kd_j > kd_i:
                continue
            totals[t_j.insider_name] = totals.get(t_j.insider_name, 0.0) + t_j.dollars
        qualified = {n: d for n, d in totals.items() if d >= 10_000}
        if len(qualified) >= 2 and sum(qualified.values()) >= 50_000:
            return kd_i, {
                "insider_count": len(qualified),
                "insiders": sorted(qualified.keys()),
                "total_dollars": sum(qualified.values()),
                "earliest_date": min(kd for kd, t in events[: i + 1] if t.insider_name in qualified),
                "latest_date": kd_i,
            }
    return None


def trading_days_around(d: str, n: int) -> list[str]:
    """+/- n CALENDAR days as a cheap trading-day proxy (documented
    approximation -- see results doc)."""
    dt = datetime.strptime(d, "%Y-%m-%d")
    return [(dt + timedelta(days=off)).date().isoformat() for off in range(-n, n + 1)]


def check_8k(filings: list, kd: str) -> bool:
    """True iff >=1 8-K filed by this issuer within +/-3 trading days
    (approximated as +/-5 calendar days) of kd. NOTE: 'recent' filings
    only cover the issuer's most recent ~1000 submissions across ALL
    forms -- for a low-volume issuer this safely spans the fresh
    2026-06-01+ window; a high-volume filer would already have failed
    the grant-mill check upstream."""
    window = set(trading_days_around(kd, 5))
    return any(f.form.startswith("8-K") and f.filing_date in window for f in filings)


def check_price_volume(symbol: str, kd: str) -> tuple[bool, dict]:
    """(is_quiet_on_this_axis, detail). Uses Sharadar SEP bars."""
    try:
        row = sharadar.resolve_ticker(symbol, as_of=kd)
        final = row["ticker"]
        bars = sharadar.fetch_sep_bars(
            final,
            date_from=(datetime.strptime(kd, "%Y-%m-%d") - timedelta(days=45)).date().isoformat(),
            date_to=(datetime.strptime(kd, "%Y-%m-%d") + timedelta(days=10)).date().isoformat(),
        )
    except Exception as e:
        return False, {"error": str(e)}
    bars = sorted(bars, key=lambda b: b["date"])
    idx = next((i for i, b in enumerate(bars) if b["date"] >= kd), None)
    if idx is None or idx == 0 or idx + 1 >= len(bars):
        return False, {"error": "insufficient bars around kd"}
    kd_bar = bars[idx]
    next_bar = bars[idx + 1]
    prior = bars[max(0, idx - 21):idx]
    if len(prior) < 10:
        return False, {"error": "insufficient trailing volume history"}
    ret_kd = kd_bar["close"] / bars[idx - 1]["close"] - 1.0
    ret_next = next_bar["close"] / kd_bar["close"] - 1.0
    med_vol = sorted(b["volume"] for b in prior if b.get("volume"))[len(prior) // 2]
    vol_ratio = (kd_bar.get("volume") or 0) / med_vol if med_vol else 0.0
    quiet = abs(ret_kd) < 0.02 and abs(ret_next) < 0.02 and vol_ratio < 1.5
    return quiet, {
        "ret_kd": ret_kd, "ret_next": ret_next, "vol_ratio": vol_ratio,
        "kd_close": kd_bar["close"], "entry_ref_date": kd_bar["date"],
    }


def entry_price_after(symbol: str, kd: str) -> tuple[str, float] | None:
    """First Sharadar close on/after kd + 5 calendar days."""
    target = (datetime.strptime(kd, "%Y-%m-%d") + timedelta(days=5)).date().isoformat()
    try:
        row = sharadar.resolve_ticker(symbol, as_of=kd)
        bars = sharadar.fetch_sep_bars(row["ticker"], date_from=target,
                                       date_to=(datetime.strptime(target, "%Y-%m-%d") + timedelta(days=10)).date().isoformat())
    except Exception:
        return None
    bars = sorted(bars, key=lambda b: b["date"])
    if not bars:
        return None
    b = bars[0]
    return b["date"], b["close"]


def main():
    log.info("=== QUIET CLUSTER SCAN  %s ===", TODAY)
    # Always rescan the FULL window from WINDOW_START: the 14-day
    # co-filing pre-filter and the 60-day cluster window can straddle
    # any incremental cursor boundary, so a partial rescan risks
    # splitting a real cluster across two runs and missing it. Index
    # files are one cheap fetch per day -- full-window rescan stays
    # trivial even a year in (~250 fetches at 8 req/s).
    log.info("Step 1: fetching daily form indexes %s..%s", WINDOW_START, TODAY)
    symbol_to_cik = edgar.fetch_company_tickers()
    cik_to_symbol = {cik: sym for sym, cik in symbol_to_cik.items()}
    all_rows = []
    for day in _daterange(WINDOW_START, TODAY):
        rows = fetch_form4_rows(day)
        log.info("  %s: %d form-4 rows", day, len(rows))
        all_rows.extend(rows)
    _save_json(CURSOR_PATH, {"last_scanned_day": TODAY})

    log.info("Step 2: grouping %d rows into issuer candidates", len(all_rows))
    issuers = build_candidates(all_rows, cik_to_symbol)
    log.info("  %d distinct issuers touched", len(issuers))

    prefiltered = {cik: e for cik, e in issuers.items() if passes_prefilter(e["owner_events"])}
    log.info("Step 3: %d issuers pass the 14-day co-filing pre-filter", len(prefiltered))
    _save_json(CANDIDATES_PATH, {"as_of": TODAY, "prefiltered_ciks": sorted(prefiltered.keys())})

    events = _load_json(EVENTS_PATH, {"events": []})
    known_event_keys = {(ev["symbol"], ev["knowability_date"]) for ev in events["events"]}

    # Resumable per-CIK progress: skip an issuer only if it was already
    # fully checked AND its owner_events haven't grown since (so a later
    # insider buy that completes a cluster is still caught). Lets a
    # single session process a bounded slice of a large candidate pool
    # and a future /lab session resume exactly where this one stopped --
    # discovery order never affects grading, since every event's
    # entry/knowability date is its own fixed historical date regardless
    # of when the scan happens to find it.
    progress = _load_json(PROGRESS_PATH, {})
    todo = [(cik, e) for cik, e in prefiltered.items()
            if progress.get(cik) != len(e["owner_events"])]
    log.info("Step 3b: %d/%d candidates need a (re)check this run",
              len(todo), len(prefiltered))

    lock = threading.Lock()
    all_new_events: list[dict] = []
    n_done = 0

    def process(cik, entry):
        try:
            filings = fetch_issuer_filings(cik)
        except Exception as e:
            log.warning("submissions fetch failed for %s: %s", cik, e)
            return None
        if is_grant_mill(filings):
            return "done"
        txns, filing_dates = fetch_txns_for_issuer(filings, WINDOW_START)
        if not txns:
            return "done"
        result = completing_buy_date(txns, filing_dates)
        if not result:
            return "done"
        kd, summary = result
        symbol = entry["symbol"]
        if (symbol, kd) in known_event_keys:
            return "done"
        quiet_8k = not check_8k(filings, kd)
        quiet_pv, pv_detail = check_price_volume(symbol, kd)
        entry_info = entry_price_after(symbol, kd)
        return {
            "symbol": symbol, "issuer_name": entry["name"], "cik": cik,
            "knowability_date": kd, "insider_count": summary["insider_count"],
            "insiders": summary["insiders"], "total_dollars": summary["total_dollars"],
            "quiet": quiet_8k and quiet_pv, "quiet_8k": quiet_8k,
            "quiet_price_vol": quiet_pv, "pv_detail": pv_detail,
            "entry": entry_info, "found": TODAY,
        }

    with ThreadPoolExecutor(max_workers=6) as exe:
        futs = {exe.submit(process, cik, entry): (cik, entry) for cik, entry in todo}
        for fut in as_completed(futs):
            cik, entry = futs[fut]
            try:
                res = fut.result()
            except Exception as e:
                log.warning("candidate %s crashed: %s", cik, e)
                continue
            with lock:
                n_done += 1
                progress[cik] = len(entry["owner_events"])
                if isinstance(res, dict):
                    all_new_events.append(res)
                    known_event_keys.add((res["symbol"], res["knowability_date"]))
                    log.info("  EVENT %s kd=%s quiet=%s n_insiders=%d $%.0f",
                              res["symbol"], res["knowability_date"], res["quiet"],
                              res["insider_count"], res["total_dollars"])
                if n_done % 100 == 0:
                    log.info("  ... %d/%d candidates checked, %d events so far",
                              n_done, len(todo), len(all_new_events))
                    # Checkpoint so a resumed run never re-fetches a CIK
                    # already checked, even if this run is interrupted.
                    _save_json(PROGRESS_PATH, progress)
                    _save_json(EVENTS_PATH, {"events": events["events"] + all_new_events})

    _save_json(PROGRESS_PATH, progress)
    events["events"].extend(all_new_events)
    _save_json(EVENTS_PATH, events)

    log.info("Step 4: opening ghost entries for %d new events", len(all_new_events))
    existing = ghost.load_ledger(GHOST_LEDGER_PATH) if os.path.exists(GHOST_LEDGER_PATH) else []
    opened = 0
    for ev in all_new_events:
        if not ev["entry"]:
            log.warning("  no priceable entry for %s, skipping ghost open", ev["symbol"])
            continue
        entry_date, entry_price = ev["entry"]
        gentry = ghost.GhostEntry(
            symbol=ev["symbol"], entry_date=entry_date, entry_price=entry_price,
            horizon_days=365, source=STRATEGY,
            features={
                "strategy": STRATEGY, "quiet": ev["quiet"],
                "knowability_date": ev["knowability_date"],
                "insider_count": ev["insider_count"], "total_dollars": ev["total_dollars"],
                "quiet_8k": ev["quiet_8k"], "quiet_price_vol": ev["quiet_price_vol"],
            },
        )
        existing.append(gentry)
        opened += 1
    ghost.save_ledger(GHOST_LEDGER_PATH, existing)
    log.info("  opened %d ghost entries (ledger now %d total)", opened, len(existing))

    log.info("=== DONE: %d new events, %d quiet / %d loud, %d ghost entries opened, %d/%d candidates checked ===",
              len(all_new_events), sum(1 for e in all_new_events if e["quiet"]),
              sum(1 for e in all_new_events if not e["quiet"]), opened, n_done, len(todo))


if __name__ == "__main__":
    main()
