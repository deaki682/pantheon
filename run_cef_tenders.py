"""Backlog #7 — CEF issuer-tender convergence (cef_tender_convergence).

Executes docs/lab_prereg_cef_tender_convergence.md. Two phases:

  python3 run_cef_tenders.py catalog  --scratch DIR
  python3 run_cef_tenders.py outcomes --scratch DIR --out docs/data/cef_tenders

Phase `catalog`: quarterly EDGAR full-index form.idx sweeps (the
canonical complete listing — no full-text-search query bias) for form
type exactly "SC TO-I" (amendments are "SC TO-I/A" and thus excluded
by construction), 2020Q1..2026Q2, then CIK→ticker via SEC
company_tickers, ticker ∈ Sharadar SFP category "CEF", one event per
fund per 180 days. Unmatched filers disclosed, never dropped silently.

Phase `outcomes`: SFP daily bars for matched funds + SPY,
shared.gauntlet.event_car at offsets 0..25 (entry first close strictly
after filing date), per-year cuts, verdict inputs per the frozen prereg.
PAPER ONLY.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shared.edgar as edgar
import shared.sharadar as sh
from shared.gauntlet import event_car, sharpe_ci  # noqa: F401 (sharpe_ci unused; event study)

WINDOW_FROM = "2020-01-01"
WINDOW_TO = "2026-05-15"
DEDUP_DAYS = 180
MAX_OFFSET = 25


def _quarters():
    for y in range(2020, 2027):
        for q in (1, 2, 3, 4):
            if y == 2026 and q > 2:
                continue
            yield y, q


def phase_catalog(scratch: str) -> None:
    edgar.set_rate_limit(5.0)
    raw: list[dict] = []
    for y, q in _quarters():
        url = f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx"
        body = edgar.http_get(url)
        n_q = 0
        for line in body.splitlines():
            if not line.startswith("SC TO-I "):
                continue  # exact form type; "SC TO-I/A" fails this prefix+space test
            # form.idx is fixed-width-ish: FormType Company CIK Date Filename
            parts = line.split()
            fname = parts[-1]
            fdate = parts[-2]
            cik = parts[-3]
            company = " ".join(parts[2:-3])  # parts[0:2] == ["SC", "TO-I"]
            if not (WINDOW_FROM <= fdate <= WINDOW_TO):
                continue
            raw.append({"cik": cik, "company": company, "date": fdate,
                        "file": fname})
            n_q += 1
        print(f"{y}Q{q}: {n_q} SC TO-I rows", flush=True)

    # CIK -> tickers via SEC's own map
    tick_rows = edgar.fetch_company_tickers_rows()
    by_cik: dict[str, list[str]] = defaultdict(list)
    for r in tick_rows:
        by_cik[str(int(r["cik_str"] if "cik_str" in r else r["cik"]))].append(
            str(r["ticker"]).upper())

    sfp = sh._datatable("TICKERS", table="SFP", **{
        "qopts.columns": "ticker,name,category", "qopts.per_page": 10000})
    cef_tickers = {str(r["ticker"]).upper() for r in sfp
                   if r.get("category") == "CEF"}
    cef_names = {str(r.get("name", "")).upper(): str(r["ticker"]).upper()
                 for r in sfp if r.get("category") == "CEF"}

    events, unmatched = [], []
    for r in raw:
        cands = [t for t in by_cik.get(str(int(r["cik"])), [])
                 if t in cef_tickers]
        if not cands:
            byname = cef_names.get(r["company"].upper())
            if byname:
                cands = [byname]
        if not cands:
            unmatched.append(r)
            continue
        events.append({**r, "symbol": sorted(cands)[0],
                       "public_date": r["date"]})

    # one event per fund per DEDUP_DAYS
    def _d(s):
        y, m, dd = map(int, s.split("-"))
        return date(y, m, dd)

    events.sort(key=lambda e: (e["symbol"], e["date"]))
    deduped, dropped_dupes = [], 0
    last: dict[str, date] = {}
    for e in events:
        d0 = _d(e["date"])
        if e["symbol"] in last and (d0 - last[e["symbol"]]).days < DEDUP_DAYS:
            dropped_dupes += 1
            continue
        last[e["symbol"]] = d0
        deduped.append(e)

    os.makedirs(scratch, exist_ok=True)
    with gzip.open(f"{scratch}/cef_tender_catalog.json.gz", "wt") as f:
        json.dump({"events": deduped, "unmatched_filers": unmatched,
                   "raw_sc_to_i_rows": len(raw),
                   "dropped_same_tender_dupes": dropped_dupes}, f)
    print(f"raw SC TO-I: {len(raw)} | CEF-matched events: {len(deduped)} "
          f"(+{dropped_dupes} same-tender dupes) | unmatched filers: "
          f"{len(unmatched)}")


def phase_outcomes(scratch: str, out_dir: str) -> None:
    with gzip.open(f"{scratch}/cef_tender_catalog.json.gz", "rt") as f:
        cat = json.load(f)
    events = cat["events"]
    syms = sorted({e["symbol"] for e in events})
    print(f"{len(events)} events across {len(syms)} funds; pulling SFP bars")

    bars: dict[str, list[dict]] = {}
    CH = 40
    for i in range(0, len(syms), CH):
        rows = sh._datatable("SFP", ticker=",".join(syms[i:i + CH]), **{
            "date.gte": "2019-12-01",
            "qopts.columns": "ticker,date,close,closeadj",
            "qopts.per_page": 10000})
        for r in rows:
            if r.get("close") is None:
                continue
            b = {"date": r["date"][:10], "close": float(r["close"])}
            if r.get("closeadj") is not None:
                b["close_total_return"] = float(r["closeadj"])
            bars.setdefault(r["ticker"], []).append(b)
        print(f"  {min(i + CH, len(syms))}/{len(syms)}", flush=True)
    for t in bars:
        bars[t].sort(key=lambda b: b["date"])

    spy_rows = sh._datatable("SFP", ticker="SPY", **{
        "date.gte": "2019-12-01",
        "qopts.columns": "ticker,date,close,closeadj",
        "qopts.per_page": 10000})
    spy_bars = [{"date": r["date"][:10], "close": float(r["close"]),
                 "close_total_return": float(r["closeadj"])}
                for r in spy_rows if r.get("closeadj") is not None]

    car = event_car(events, bars, spy_bars, max_offset=MAX_OFFSET)

    # per-year cuts (regime table) — same engine, filtered populations
    by_year = {}
    for y in range(2020, 2027):
        evs = [e for e in events if e["date"].startswith(str(y))]
        if evs:
            by_year[str(y)] = event_car(evs, bars, spy_bars,
                                         max_offset=MAX_OFFSET)

    # verdict inputs at offset 25 per the frozen prereg
    import math
    k = MAX_OFFSET
    cars_25_n = car["n"][k]
    mean_25 = car["mean_car"][k]
    # recompute per-event CARs at 25 for t-stat / win rate / shrinkage
    per_event = event_car(events, bars, spy_bars, max_offset=MAX_OFFSET)
    # event_car returns aggregates; derive t from the stored n/mean via a
    # second pass over individual events
    singles = []
    for e in events:
        one = event_car([e], bars, spy_bars, max_offset=MAX_OFFSET)
        if one["n"][k] == 1:
            singles.append({"symbol": e["symbol"], "date": e["date"],
                            "car25": one["mean_car"][k]})
    xs = [s["car25"] for s in singles]
    n = len(xs)
    mean = sum(xs) / n if n else 0.0
    var = sum((x - mean) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    t = mean / math.sqrt(var / n) if n > 1 and var > 0 else 0.0
    win = sum(1 for x in xs if x > 0) / n if n else 0.0
    # same shrinkage the lab applies (shared.lab._shrunk): n/(n+20)
    shrunk = mean * (n / (n + 20)) if n else 0.0

    os.makedirs(out_dir, exist_ok=True)
    report = {
        "prereg": "docs/lab_prereg_cef_tender_convergence.md",
        "window": [WINDOW_FROM, WINDOW_TO],
        "curve": {"offsets": car["offsets"], "n": car["n"],
                   "mean_car": car["mean_car"], "median_car": car["median_car"]},
        "verdict_inputs": {"n_events_priced_at_25": n, "mean_car25": mean,
                            "shrunk_mean_car25": shrunk, "t_stat": t,
                            "win_rate": win},
        "per_year": {y: {"n25": v["n"][k], "mean_car25": v["mean_car"][k],
                          "median_car25": v["median_car"][k]}
                     for y, v in by_year.items()},
        "per_event": singles,
        "unpriceable": car["unpriceable"],
        "coverage_note": car["coverage_note"],
        "catalog_stats": {kk: cat[kk] for kk in
                           ("raw_sc_to_i_rows", "dropped_same_tender_dupes")},
        "unmatched_filers_n": len(cat["unmatched_filers"]),
    }
    with open(f"{out_dir}/results.json", "w") as f:
        json.dump(report, f, indent=1, default=str)
    print(json.dumps(report["verdict_inputs"], indent=1))
    print("per-offset mean CAR (0,5,10,15,20,25):",
          [None if car["mean_car"][i] is None else round(car["mean_car"][i], 4)
           for i in (0, 5, 10, 15, 20, 25)])
    print(f"wrote {out_dir}/results.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["catalog", "outcomes"])
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", default="docs/data/cef_tenders")
    a = ap.parse_args()
    if a.phase == "catalog":
        phase_catalog(a.scratch)
    else:
        phase_outcomes(a.scratch, a.out)
