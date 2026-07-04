"""Merger-arb COMPLETION-POPULATION probe (COMPLETION-BIASED — labeled).
Scans delisted domestic-common names for the cash-merger flatline signature,
measures the late-stage spread. Tells us power (deals/yr) + upside magnitude.
Does NOT capture deal breaks (they don't delist) — that left tail comes from
the live forward test, not this. Usage: python3 run_mergerarb_probe.py POOL_JSON OUT_JSON"""
import json, statistics, sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import shared.sharadar as sh
from datetime import date, timedelta
from shared.gauntlet import convexity_stats

pool = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
pool = [r for r in pool if (r.get("lastpricedate") or "") >= "2012-01-01"]
pool.sort(key=lambda r: r["lastpricedate"])
print(f"probing {len(pool)} delisted names (lastprice>=2012)", flush=True)


def fetch(chunk, gte, lte):
    for a in range(4):
        try:
            return sh._datatable("SEP", ticker=",".join(chunk), **{"date.gte": gte, "date.lte": lte,
                   "qopts.columns": "ticker,date,close", "qopts.per_page": 10000})
        except Exception:
            if a == 3:
                raise
            time.sleep(2 ** (a + 1))
    return []


deals = []
CH = 30
for i in range(0, len(pool), CH):
    chunk = pool[i:i + CH]
    lpds = [r["lastpricedate"] for r in chunk]
    gte = (date(*map(int, min(lpds).split("-"))) - timedelta(days=130)).isoformat()
    lte = max(lpds)
    by_t = {}
    for r in fetch([r["ticker"] for r in chunk], gte, lte):
        if r.get("close") is None:
            continue
        by_t.setdefault(r["ticker"], []).append((r["date"][:10], float(r["close"])))
    for r in chunk:
        b = sorted(by_t.get(r["ticker"], []))
        b = [x for x in b if x[0] <= r["lastpricedate"]]
        if len(b) < 40:
            continue
        closes = [c for _, c in b]
        win = closes[-60:]
        last30 = closes[-30:]
        cv = statistics.pstdev(last30) / statistics.mean(last30) if statistics.mean(last30) else 9
        final = closes[-1]
        wmax = max(win)
        # cash-merger completion signature: terminal flatline near the window ceiling
        if cv < 0.04 and final > 2.0 and final / wmax > 0.90:
            entry = closes[-31] if len(closes) >= 31 else closes[0]
            spread = final / entry - 1.0
            if -0.10 < spread < 0.60:   # sane spread band (drop data errors / non-mergers)
                deals.append({"ticker": r["ticker"], "delist": r["lastpricedate"],
                              "entry": round(entry, 2), "exit": round(final, 2),
                              "spread": round(spread, 4), "cv": round(cv, 4)})
    if (i // CH) % 15 == 0:
        print(f"  {min(i+CH,len(pool))}/{len(pool)} scanned, {len(deals)} deals", flush=True)

spreads = [d["spread"] for d in deals]
by_year = {}
for d in deals:
    by_year.setdefault(d["delist"][:4], 0)
    by_year[d["delist"][:4]] += 1
res = {"n_deals": len(deals), "deals_per_year": {y: by_year[y] for y in sorted(by_year)},
       "late_stage_spread_convexity": convexity_stats(spreads) if spreads else {},
       "sample_deals": deals[:20]}
json.dump(res, open(OUT, "w"), indent=1)
print(f"\nDONE: {len(deals)} completed cash deals detected", flush=True)
if spreads:
    print(f"late-stage (final-30d) spread: median {statistics.median(spreads):+.1%} "
          f"mean {statistics.mean(spreads):+.1%}", flush=True)
    print(f"deals/year: {res['deals_per_year']}", flush=True)
