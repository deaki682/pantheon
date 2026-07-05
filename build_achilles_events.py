"""achilles_pead_gauntlet phase 4: SUE event table from SF1 + bucket assignment.

For each ticker's EPS series -> seasonal-random-walk SUE per quarter, keyed to
datekey (filing date = event date). Assign the marketcap bucket (SMALL/MICRO)
from the most recent PIT universe snapshot on/before datekey. The post-report
reaction + entry price get joined from SEP once that pull lands. PAPER ONLY.
"""
import gzip, json, os, sys, bisect
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from achilles.pead_gauntlet import seasonal_sue

OUT = "data/achilles_gauntlet"

# --- load SF1, group EPS by ticker ---
by_ticker = defaultdict(list)   # ticker -> [(calendardate, eps, datekey)]
n = 0
for part in sorted(os.listdir(OUT)):
    if not part.startswith("sf1_arq_part"):
        continue
    for r in json.load(gzip.open(f"{OUT}/{part}", "rt")):
        eps, cd, dk = r.get("eps"), r.get("calendardate"), r.get("datekey")
        if eps is None or not cd or not dk:
            continue
        by_ticker[r["ticker"]].append((cd, float(eps), dk))
        n += 1
print(f"SF1: {n} eps rows, {len(by_ticker)} tickers", flush=True)

# --- universe snapshots -> per-date bucket membership, sorted dates for lookup ---
U = json.load(open(f"{OUT}/universes.json"))["universes"]
udates = sorted(U)
small_sets = {d: set(U[d]["SMALL"]) for d in udates}
micro_sets = {d: set(U[d]["MICRO"]) for d in udates}

def bucket_at(ticker, datekey):
    i = bisect.bisect_right(udates, datekey) - 1   # latest snapshot on/before datekey
    if i < 0:
        return None
    d = udates[i]
    if ticker in small_sets[d]:
        return "SMALL"
    if ticker in micro_sets[d]:
        return "MICRO"
    return None

# --- compute SUE per ticker, emit events in the universe ---
events = []
for tkr, series in by_ticker.items():
    series.sort(key=lambda x: x[0])            # by fiscal quarter (calendardate)
    eps_series = [(cd, eps) for cd, eps, _ in series]
    dk_by_cd = {cd: dk for cd, _, dk in series}
    sue = seasonal_sue(eps_series, min_history=8)
    for cd, s in sue.items():
        dk = dk_by_cd.get(cd)
        if not dk:
            continue
        b = bucket_at(tkr, dk)
        if b is None:
            continue                            # not in the tradable SMALL/MICRO universe
        events.append({"symbol": tkr, "datekey": dk, "calendardate": cd,
                       "sue": round(s, 4), "bucket": b})

events.sort(key=lambda e: e["datekey"])
json.dump(events, open(f"{OUT}/events.json", "w"))
from collections import Counter
bc = Counter(e["bucket"] for e in events)
yr = Counter(e["datekey"][:4] for e in events)
print(f"DONE: {len(events)} SUE events in-universe | buckets {dict(bc)}")
print(f"  spread: {min(yr)}..{max(yr)}, e.g. 2010={yr.get('2010')}, 2020={yr.get('2020')}")
