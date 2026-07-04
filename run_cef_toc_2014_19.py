"""cef_toc_anchor_2014_19 — see docs/lab_prereg_cef_toc_anchor_2014_19.md. PAPER ONLY."""
from __future__ import annotations
import json, math, os, sys
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.edgar as edgar
import shared.sharadar as sh
from shared.gauntlet import event_car

OUT = "docs/data/cef_toc_2014_19"
def d(s):
    y, m, dd = map(int, s.split("-")); return date(y, m, dd)

edgar.set_rate_limit(5.0)
toi, toc = [], defaultdict(list)
for y in range(2014, 2020):
    for q in (1, 2, 3, 4):
        body = edgar.http_get(f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx")
        for line in body.splitlines():
            if line.startswith("SC TO-I "):
                p = line.split()
                toi.append({"cik": p[-3], "company": " ".join(p[2:-3]), "date": p[-2]})
            elif line.startswith("SC TO-C "):
                p = line.split()
                toc[str(int(p[-3]))].append(p[-2])
        print(f"{y}Q{q} done", flush=True)
toi = [r for r in toi if "2014-01-01" <= r["date"] <= "2019-12-31"]
print(f"raw SC TO-I: {len(toi)} | TO-C filers: {len(toc)}", flush=True)

# CEF matching: SFP TICKERS incl. delisted, CIK map + window-checked name fallback
tick_rows = edgar.fetch_company_tickers_rows()
by_cik = defaultdict(list)
for r in tick_rows:
    by_cik[str(int(r.get("cik_str", r.get("cik"))))].append(str(r["ticker"]).upper())
sfp = sh._datatable("TICKERS", table="SFP", **{
    "qopts.columns": "ticker,name,category,firstpricedate,lastpricedate",
    "qopts.per_page": 10000})
cef_rows = [r for r in sfp if r.get("category") == "CEF"]
cef_tickers = {str(r["ticker"]).upper() for r in cef_rows}
by_name = defaultdict(list)
for r in cef_rows:
    by_name[str(r.get("name", "")).upper()].append(r)

events, unmatched = [], 0
for r in toi:
    sym = None
    for t in by_cik.get(str(int(r["cik"])), []):
        if t in cef_tickers:
            sym = t; break
    if sym is None:
        rows = [x for x in by_name.get(r["company"].upper(), [])
                if (x.get("firstpricedate") or "0000") <= r["date"]
                <= (x.get("lastpricedate") or "9999")]
        if len(rows) == 1:
            sym = str(rows[0]["ticker"]).upper()
    if sym is None:
        unmatched += 1; continue
    events.append({**r, "symbol": sym})
events.sort(key=lambda e: (e["symbol"], e["date"]))
deduped, last = [], {}
for e in events:
    if e["symbol"] in last and (d(e["date"]) - last[e["symbol"]]).days < 180:
        continue
    last[e["symbol"]] = d(e["date"]); deduped.append(e)
print(f"CEF TO-I events (deduped): {len(deduped)} | non-CEF/unmatched: {unmatched}", flush=True)

a_events = []
for e in deduped:
    cands = [t for t in toc.get(str(int(e["cik"])), [])
             if t < e["date"] and 1 <= (d(e["date"]) - d(t)).days <= 90]
    if cands:
        a_events.append({**e, "public_date": min(cands), "toi_date": e["date"]})
print(f"with prior TO-C (1-90d): {len(a_events)}", flush=True)

syms = sorted({e["symbol"] for e in a_events})
bars = {}
for i in range(0, len(syms), 40):
    for r in sh._datatable("SFP", ticker=",".join(syms[i:i+40]), **{
            "date.gte": "2013-10-01", "date.lte": "2020-06-30",
            "qopts.columns": "ticker,date,close,closeadj", "qopts.per_page": 10000}):
        if r.get("close") is None: continue
        b = {"date": r["date"][:10], "close": float(r["close"])}
        if r.get("closeadj") is not None: b["close_total_return"] = float(r["closeadj"])
        bars.setdefault(r["ticker"], []).append(b)
for t in bars: bars[t].sort(key=lambda b: b["date"])
spy = [{"date": r["date"][:10], "close": float(r["close"]), "close_total_return": float(r["closeadj"])}
       for r in sh._datatable("SFP", ticker="SPY", **{"date.gte": "2013-10-01", "date.lte": "2020-06-30",
       "qopts.columns": "ticker,date,close,closeadj", "qopts.per_page": 10000}) if r.get("closeadj")]

no_bars = [e for e in a_events if e["symbol"] not in bars]
keep, drop = [], []
for e in a_events:
    if e["symbol"] not in bars:
        continue
    lo = (d(e["public_date"]) - timedelta(days=30)).isoformat()
    n_pre = sum(1 for b in bars[e["symbol"]] if lo <= b["date"] < e["public_date"])
    (keep if n_pre >= 15 else drop).append(e)
print(f"no SFP bars at all: {len(no_bars)} | screened out: {len(drop)} | kept: {len(keep)}", flush=True)

car = event_car(keep, bars, spy, max_offset=40)
singles = []
for e in keep:
    one = event_car([e], bars, spy, max_offset=25)
    if one["n"][25] == 1:
        singles.append({"symbol": e["symbol"], "date": e["public_date"], "car25": one["mean_car"][25]})
xs = [s["car25"] for s in singles]
n = len(xs); mean = sum(xs)/n if n else 0.0
var = sum((x-mean)**2 for x in xs)/(n-1) if n > 1 else 0.0
t = mean/math.sqrt(var/n) if n > 1 and var > 0 else 0.0
os.makedirs(OUT, exist_ok=True)
report = {
    "prereg": "docs/lab_prereg_cef_toc_anchor_2014_19.md",
    "verdict_inputs": {"n": n, "mean25": mean, "shrunk25": mean*n/(n+20) if n else 0.0,
                        "t": t, "win": sum(1 for x in xs if x > 0)/n if n else 0.0},
    "curve": {"offsets": car["offsets"], "n": car["n"], "mean_car": car["mean_car"],
               "median_car": car["median_car"]},
    "per_event": singles,
    "per_year": {},
    "coverage": {"toi_events": len(deduped), "with_toc": len(a_events),
                  "no_bars": [e["symbol"] for e in no_bars],
                  "screened_out": len(drop), "unpriceable": car["unpriceable"]},
}
for y in range(2014, 2020):
    evs = [e for e in keep if e["public_date"].startswith(str(y))]
    if evs:
        cy = event_car(evs, bars, spy, max_offset=25)
        report["per_year"][str(y)] = {"n": cy["n"][25], "mean25": cy["mean_car"][25],
                                        "median25": cy["median_car"][25]}
with open(f"{OUT}/results.json", "w") as f:
    json.dump(report, f, indent=1, default=str)
print(json.dumps(report["verdict_inputs"], indent=1))
print("curve mean (0,5,10,15,20,25,30,35,40):",
      [None if car["mean_car"][i] is None else round(car["mean_car"][i], 4)
       for i in (0,5,10,15,20,25,30,35,40)])
print("curve median at 25/30/40:", [round(car["median_car"][i],4) for i in (25,30,40)])
print("per_year:", json.dumps(report["per_year"]))
