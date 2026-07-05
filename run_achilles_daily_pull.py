"""achilles_pead_gauntlet phase 1b: DAILY marketcap panel (for PIT universes).

Pulls ticker,date,marketcap for the whole window, one gzipped part PER YEAR
(bounded memory), so we can build monthly SMALL(501-2000)/MICRO(2001-3500)
point-in-time universes by marketcap rank. marketcap is USD millions; rows are
keyed to the ticker as it traded that day (correct for PIT). Delisted names
covered through their final trading day.
"""
import gzip, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.sharadar as sh
import requests

OUT = "data/achilles_gauntlet"
os.makedirs(OUT, exist_ok=True)
COLS = "ticker,date,marketcap"
grand = 0
for year in range(1999, 2027):
    part_path = f"{OUT}/daily_mcap_{year}.json.gz"
    if os.path.exists(part_path):
        print(f"DAILY {year}: exists, skip", flush=True)
        continue
    rows, cursor, yr_total = [], None, 0
    params = {"date.gte": f"{year}-01-01", "date.lte": f"{year}-12-31",
              "qopts.columns": COLS, "qopts.per_page": 10000, "api_key": sh._api_key()}
    while True:
        p = dict(params)
        if cursor:
            p["qopts.cursor_id"] = cursor
        r = requests.get(f"{sh.BASE_URL}/DAILY.json", params=p, timeout=120)
        r.raise_for_status()
        payload = r.json()
        dt = payload["datatable"]
        cols = [c["name"] for c in dt["columns"]]
        rows.extend(dict(zip(cols, row)) for row in dt["data"])
        yr_total += len(dt["data"])
        cursor = (payload.get("meta") or {}).get("next_cursor_id")
        if not cursor:
            break
        time.sleep(0.2)
    with gzip.open(part_path, "wt") as f:
        json.dump(rows, f)
    grand += yr_total
    print(f"DAILY {year}: {yr_total} rows (grand {grand})", flush=True)
open(f"{OUT}/daily_DONE", "w").write(str(grand))
print(f"DAILY DONE: {grand} rows", flush=True)
