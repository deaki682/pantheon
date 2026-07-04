"""tender_target_14d9 — docs/lab_prereg_tender_target_14d9.md. PAPER ONLY."""
from __future__ import annotations
import json, math, os, re, sys
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.edgar as edgar
import shared.sharadar as sh
from shared.gauntlet import event_car

OUT = "docs/data/tender_target_14d9"
COMMON = {"Domestic Common Stock", "Domestic Common Stock Primary Class",
          "Domestic Common Stock Secondary Class"}
def d(s):
    y, m, dd = map(int, s.split("-")); return date(y, m, dd)

edgar.set_rate_limit(5.0)
raw = []
for y in range(2016, 2026):
    for q in (1, 2, 3, 4):
        body = edgar.http_get(f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx")
        for line in body.splitlines():
            if line.startswith("SC 14D9 "):
                p = line.split()
                raw.append({"cik": str(int(p[-3])), "date": p[-2],
                            "company": " ".join(p[2:-3])})
        print(f"{y}Q{q}", flush=True)
print(f"raw SC 14D9: {len(raw)}", flush=True)

# CIK map from Sharadar TICKERS secfilings (delisted INCLUDED)
tick = sh._datatable("TICKERS", table="SEP", **{
    "qopts.columns": "ticker,name,category,firstpricedate,lastpricedate,secfilings",
    "qopts.per_page": 10000})
by_cik = defaultdict(list)
for r in tick:
    m = re.search(r"CIK=0*(\d+)", r.get("secfilings") or "")
    if m:
        by_cik[m.group(1)].append(r)
print(f"TICKERS rows with CIK: {sum(len(v) for v in by_cik.values())}", flush=True)

events, unmatched = [], 0
for r in raw:
    rows = [x for x in by_cik.get(r["cik"], [])
            if x.get("category") in COMMON
            and (x.get("firstpricedate") or "0000") <= r["date"]
            <= (x.get("lastpricedate") or "9999")]
    if len(rows) != 1:
        # allow primary-class disambiguation among multiple share classes
        prim = [x for x in rows if "Primary" in (x.get("category") or "")]
        rows = prim if len(prim) == 1 else rows
    if len(rows) != 1:
        unmatched += 1; continue
    events.append({**r, "symbol": str(rows[0]["ticker"]).upper(),
                   "public_date": r["date"]})
events.sort(key=lambda e: (e["cik"], e["date"]))
deduped, last = [], {}
for e in events:
    if e["cik"] in last and (d(e["date"]) - last[e["cik"]]).days < 180:
        continue
    last[e["cik"]] = d(e["date"]); deduped.append(e)
print(f"matched targets: {len(deduped)} (deduped) | unmatched: {unmatched}", flush=True)

syms = sorted({e["symbol"] for e in deduped})
bars = {}
CH = 30
for i in range(0, len(syms), CH):
    for r in sh._datatable("SEP", ticker=",".join(syms[i:i+CH]), **{
            "date.gte": "2015-10-01", "date.lte": "2026-06-30",
            "qopts.columns": "ticker,date,close,closeadj", "qopts.per_page": 10000}):
        if r.get("close") is None: continue
        b = {"date": r["date"][:10], "close": float(r["close"])}
        if r.get("closeadj") is not None: b["close_total_return"] = float(r["closeadj"])
        bars.setdefault(r["ticker"], []).append(b)
    print(f"  bars {min(i+CH, len(syms))}/{len(syms)}", flush=True)
for t in bars: bars[t].sort(key=lambda b: b["date"])
spy = [{"date": r["date"][:10], "close": float(r["close"]), "close_total_return": float(r["closeadj"])}
       for r in sh._datatable("SFP", ticker="SPY", **{"date.gte": "2015-10-01",
       "qopts.columns": "ticker,date,close,closeadj", "qopts.per_page": 10000}) if r.get("closeadj")]

keep, drop, nobars = [], 0, 0
for e in deduped:
    bl = bars.get(e["symbol"])
    if not bl:
        nobars += 1; continue
    lo = (d(e["date"]) - timedelta(days=30)).isoformat()
    n_pre = sum(1 for b in bl if lo <= b["date"] < e["date"])
    if n_pre >= 15: keep.append(e)
    else: drop += 1
print(f"kept {len(keep)} | screened {drop} | no bars {nobars}", flush=True)

car = event_car(keep, bars, spy, max_offset=40)
singles = []
for e in keep:
    one = event_car([e], bars, spy, max_offset=25)
    if one["n"][25] == 1:
        singles.append({"symbol": e["symbol"], "date": e["date"], "car25": one["mean_car"][25]})
xs = [s["car25"] for s in singles]
n = len(xs); mean = sum(xs)/n
var = sum((x-mean)**2 for x in xs)/(n-1)
t = mean/math.sqrt(var/n)
win = sum(1 for x in xs if x > 0)/n
os.makedirs(OUT, exist_ok=True)
per_year = {}
for y in range(2016, 2026):
    evs = [e for e in keep if e["date"].startswith(str(y))]
    if evs:
        cy = event_car(evs, bars, spy, max_offset=25)
        per_year[str(y)] = {"n": cy["n"][25], "mean25": cy["mean_car"][25],
                             "median25": cy["median_car"][25]}
report = {"prereg": "docs/lab_prereg_tender_target_14d9.md",
          "verdict_inputs": {"n": n, "mean25": mean, "shrunk25": mean*n/(n+20),
                              "t": t, "win": win},
          "curve": {"offsets": car["offsets"], "n": car["n"],
                     "mean_car": car["mean_car"], "median_car": car["median_car"]},
          "per_event": singles, "per_year": per_year,
          "coverage": {"raw_14d9": len(raw), "matched_deduped": len(deduped),
                        "unmatched": unmatched, "no_bars": nobars, "screened": drop},
          "unpriceable": car["unpriceable"]}
with open(f"{OUT}/results.json", "w") as f:
    json.dump(report, f, indent=1, default=str)
print(json.dumps(report["verdict_inputs"], indent=1))
print("curve mean (0,3,5,10,15,20,25,30,40):",
      [None if car["mean_car"][i] is None else round(car["mean_car"][i], 4)
       for i in (0,3,5,10,15,20,25,30,40)])
print("median at 5/15/25/40:", [round(car["median_car"][i],4) for i in (5,15,25,40)])
print("per_year:", json.dumps(per_year))
