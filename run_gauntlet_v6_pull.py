"""gauntlet_v6_combinations phase 1: SF1 ARQ panel (NOA + net-issuance fields)
+ DAILY price-to-sales per signal date. PAPER ONLY.
Usage: python3 run_gauntlet_v6_pull.py SCRATCH"""
import gzip, json, os, sys, time
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.sharadar as sh
import requests

S = sys.argv[1]
os.makedirs(S, exist_ok=True)

# ---- SF1 bulk panel ----
COLS = ("ticker,datekey,calendardate,assets,revenue,gp,shareswa,netinc,"
        "cashneq,investments,debt,liabilities")
rows, part, total = [], 0, 0
params = {"dimension": "ARQ", "calendardate.gte": "1998-12-31",
          "qopts.columns": COLS, "qopts.per_page": 10000, "api_key": sh._api_key()}
cursor = None
while True:
    p = dict(params)
    if cursor:
        p["qopts.cursor_id"] = cursor
    r = requests.get(f"{sh.BASE_URL}/SF1.json", params=p, timeout=120)
    r.raise_for_status()
    payload = r.json()
    dt = payload["datatable"]
    cols = [c["name"] for c in dt["columns"]]
    rows.extend(dict(zip(cols, row)) for row in dt["data"])
    total += len(dt["data"])
    if len(rows) >= 400_000:
        with gzip.open(f"{S}/sf1_arq_part{part}.json.gz", "wt") as f:
            json.dump(rows, f)
        print(f"SF1 part {part}: {len(rows)} (total {total})", flush=True)
        rows, part = [], part + 1
    cursor = (payload.get("meta") or {}).get("next_cursor_id")
    if not cursor:
        break
    time.sleep(0.25)
if rows:
    with gzip.open(f"{S}/sf1_arq_part{part}.json.gz", "wt") as f:
        json.dump(rows, f)
    print(f"SF1 part {part}: {len(rows)} (total {total})", flush=True)
print(f"SF1 DONE: {total} rows", flush=True)

# ---- DAILY price-to-sales per unique signal date ----
pop = json.load(open("cache/shared_pop_gauntlet_v1_universes.json"))
prows = pop["rows"] if isinstance(pop, dict) else pop
by_q = {}
for r in sorted(prows, key=lambda r: r["signal_date"]):
    q = (r["signal_date"][:4], (int(r["signal_date"][5:7]) - 1) // 3, r["window"])
    by_q.setdefault(q, r["signal_date"])
dates = sorted(set(by_q.values()))
daily_ps = {}
for i, D in enumerate(dates):
    for a in range(4):
        try:
            got = sh._datatable("DAILY", **{"date.gte": D, "date.lte": D,
                  "qopts.columns": "ticker,ps", "qopts.per_page": 10000})
            break
        except Exception:
            if a == 3:
                raise
            time.sleep(2 ** (a + 1))
    daily_ps[D] = {r["ticker"].upper(): float(r["ps"]) for r in got
                   if r.get("ps") is not None}
    if i % 10 == 0:
        print(f"DAILY ps {i+1}/{len(dates)} ({D}: {len(daily_ps[D])})", flush=True)
    time.sleep(0.15)
with gzip.open(f"{S}/daily_ps.json.gz", "wt") as f:
    json.dump(daily_ps, f)
print(f"DAILY ps DONE: {len(dates)} signal dates", flush=True)
