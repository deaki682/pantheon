"""Slugs cef_tender_toc_anchor + issuer_tender_operating — see
docs/lab_prereg_tender_followups.md. PAPER ONLY."""
from __future__ import annotations
import gzip, json, math, os, sys
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.edgar as edgar
import shared.sharadar as sh
from shared.gauntlet import event_car

S = sys.argv[1]
OUT = "docs/data/tender_followups"
COMMON = {"Domestic Common Stock", "Domestic Common Stock Primary Class",
          "Domestic Common Stock Secondary Class"}

def d(s):
    y, m, dd = map(int, s.split("-")); return date(y, m, dd)

def listing_screen(events, bars):
    keep, drop = [], []
    for e in events:
        lo = (d(e["public_date"]) - timedelta(days=30)).isoformat()
        n_pre = sum(1 for b in bars.get(e["symbol"], [])
                    if lo <= b["date"] < e["public_date"])
        (keep if n_pre >= 15 else drop).append(e)
    return keep, drop

def stats25(events, bars, spy):
    xs = []
    for e in events:
        one = event_car([e], bars, spy, max_offset=25)
        if one["n"][25] == 1:
            xs.append({"symbol": e["symbol"], "date": e["public_date"],
                       "car25": one["mean_car"][25]})
    vals = [x["car25"] for x in xs]
    n = len(vals)
    if n < 2:
        return {"n": n, "per_event": xs}
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)
    t = mean / math.sqrt(var / n) if var > 0 else 0.0
    return {"n": n, "mean25": mean, "shrunk25": mean * n / (n + 20),
            "t": t, "win": sum(1 for v in vals if v > 0) / n, "per_event": xs}

cat = json.load(gzip.open(f"{S}/cef_tender_catalog.json.gz", "rt"))
os.makedirs(OUT, exist_ok=True)
report = {}

# ---------- A: TO-C anchor for the 153 CEF events ----------
edgar.set_rate_limit(5.0)
toc = defaultdict(list)   # cik(int str) -> [dates]
for y in range(2020, 2027):
    for q in (1, 2, 3, 4):
        if y == 2026 and q > 2: continue
        body = edgar.http_get(
            f"https://www.sec.gov/Archives/edgar/full-index/{y}/QTR{q}/form.idx")
        for line in body.splitlines():
            if line.startswith("SC TO-C "):
                parts = line.split()
                toc[str(int(parts[-3]))].append(parts[-2])
print("TO-C filers:", len(toc), flush=True)

a_events = []
for e in cat["events"]:
    cands = [t for t in toc.get(str(int(e["cik"])), [])
             if t < e["date"] and t >= "2020-01-01"]
    # earliest TO-C within 90 days before the TO-I (same tender, not stale)
    cands = [t for t in cands if (d(e["date"]) - d(t)).days <= 90]
    if cands:
        a_events.append({**e, "public_date": min(cands), "toi_date": e["date"]})
print(f"A: CEF events with a prior TO-C (<=90d): {len(a_events)} / {len(cat['events'])}")

syms_a = sorted({e["symbol"] for e in a_events})
bars_a = {}
for i in range(0, len(syms_a), 40):
    for r in sh._datatable("SFP", ticker=",".join(syms_a[i:i+40]), **{
            "date.gte": "2019-12-01", "qopts.columns": "ticker,date,close,closeadj",
            "qopts.per_page": 10000}):
        if r.get("close") is None: continue
        b = {"date": r["date"][:10], "close": float(r["close"])}
        if r.get("closeadj") is not None: b["close_total_return"] = float(r["closeadj"])
        bars_a.setdefault(r["ticker"], []).append(b)
for t in bars_a: bars_a[t].sort(key=lambda b: b["date"])
spy = [{"date": r["date"][:10], "close": float(r["close"]),
        "close_total_return": float(r["closeadj"])}
       for r in sh._datatable("SFP", ticker="SPY", **{"date.gte": "2019-12-01",
       "qopts.columns": "ticker,date,close,closeadj", "qopts.per_page": 10000})
       if r.get("closeadj")]
keep_a, drop_a = listing_screen(a_events, bars_a)
report["cef_tender_toc_anchor"] = {
    "n_with_toc": len(a_events), "screened_out": len(drop_a),
    "stats_screened": {k: v for k, v in stats25(keep_a, bars_a, spy).items()
                        if k != "per_event"},
    "per_event": stats25(keep_a, bars_a, spy)["per_event"],
}
print("A verdict inputs:", json.dumps(report["cef_tender_toc_anchor"]["stats_screened"]), flush=True)

# ---------- B: operating-company self-tenders ----------
cef_keys = {(e["cik"], e.get("toi_date", e["date"])) for e in cat["events"]}
raw_ops = [u for u in cat["unmatched_filers"]]
tick_rows = edgar.fetch_company_tickers_rows()
by_cik = defaultdict(list)
for r in tick_rows:
    by_cik[str(int(r.get("cik_str", r.get("cik"))))].append(str(r["ticker"]).upper())
tuniv = sh.load_ticker_universe()
sep_cat = {}
name_map = {}
for r in tuniv:
    tt = str(r.get("ticker", "")).upper()
    sep_cat[tt] = r
    nm = str(r.get("name", "")).upper()
    if r.get("category") in COMMON:
        name_map.setdefault(nm, []).append(r)

b_events, unmatched_b = [], 0
for u in raw_ops:
    nm = u["company"]
    if nm.startswith("TO-I "): nm = nm[5:]
    sym = None
    for t in by_cik.get(str(int(u["cik"])), []):
        row = sep_cat.get(t)
        if row and row.get("category") in COMMON:
            sym = t; break
    if sym is None:
        rows = name_map.get(nm.upper(), [])
        rows = [r for r in rows
                if (r.get("firstpricedate") or "0000") <= u["date"]
                <= (r.get("lastpricedate") or "9999")]
        if len(rows) == 1:
            sym = str(rows[0]["ticker"]).upper()
    if sym is None:
        unmatched_b += 1; continue
    b_events.append({**u, "company": nm, "symbol": sym, "public_date": u["date"]})

b_events.sort(key=lambda e: (e["cik"], e["date"]))
deduped, last = [], {}
for e in b_events:
    if e["cik"] in last and (d(e["date"]) - last[e["cik"]]).days < 180:
        continue
    last[e["cik"]] = d(e["date"]); deduped.append(e)
b_events = deduped
print(f"B: operating events matched {len(b_events)}, unmatched {unmatched_b}", flush=True)

syms_b = sorted({e["symbol"] for e in b_events})
bars_b = {}
for i in range(0, len(syms_b), 30):
    for r in sh._datatable("SEP", ticker=",".join(syms_b[i:i+30]), **{
            "date.gte": "2019-12-01", "qopts.columns": "ticker,date,close,closeadj",
            "qopts.per_page": 10000}):
        if r.get("close") is None: continue
        b = {"date": r["date"][:10], "close": float(r["close"])}
        if r.get("closeadj") is not None: b["close_total_return"] = float(r["closeadj"])
        bars_b.setdefault(r["ticker"], []).append(b)
    print(f"  SEP bars {min(i+30, len(syms_b))}/{len(syms_b)}", flush=True)
for t in bars_b: bars_b[t].sort(key=lambda b: b["date"])
keep_b, drop_b = listing_screen(b_events, bars_b)
st_b = stats25(keep_b, bars_b, spy)

# secondary: $2B marketcap split (DAILY nearest filing date)
mcap = {}
for i in range(0, len(syms_b), 30):
    for r in sh._datatable("DAILY", ticker=",".join(syms_b[i:i+30]), **{
            "date.gte": "2019-12-01", "qopts.columns": "ticker,date,marketcap",
            "qopts.per_page": 10000}):
        if r.get("marketcap") is not None:
            mcap.setdefault(r["ticker"], []).append((r["date"][:10], float(r["marketcap"])))
    print(f"  DAILY mcap {min(i+30, len(syms_b))}/{len(syms_b)}", flush=True)
for t in mcap: mcap[t].sort()
import bisect
def mcap_at(sym, day):
    rows = mcap.get(sym, [])
    if not rows: return None
    i = bisect.bisect_right([r[0] for r in rows], day) - 1
    return rows[i][1] if i >= 0 else None
small = [e for e in keep_b if (mcap_at(e["symbol"], e["public_date"]) or 9e9) < 2000]
large = [e for e in keep_b if (mcap_at(e["symbol"], e["public_date"]) or 0) >= 2000]
report["issuer_tender_operating"] = {
    "n_matched": len(b_events), "unmatched": unmatched_b,
    "screened_out": len(drop_b),
    "stats_screened": {k: v for k, v in st_b.items() if k != "per_event"},
    "small_under_2B": {k: v for k, v in stats25(small, bars_b, spy).items() if k != "per_event"},
    "large_over_2B": {k: v for k, v in stats25(large, bars_b, spy).items() if k != "per_event"},
    "per_event": st_b["per_event"],
}
print("B verdict inputs:", json.dumps(report["issuer_tender_operating"]["stats_screened"]))
print("B small:", json.dumps(report["issuer_tender_operating"]["small_under_2B"]))
print("B large:", json.dumps(report["issuer_tender_operating"]["large_over_2B"]))
with open(f"{OUT}/results.json", "w") as f:
    json.dump(report, f, indent=1, default=str)
print(f"wrote {OUT}/results.json")
