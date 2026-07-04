"""gauntlet_v2_fundamentals phase 1: SF1 ARQ panel pull. PAPER ONLY."""
import gzip, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.sharadar as sh
import requests

S = sys.argv[1]
os.makedirs(S, exist_ok=True)
COLS = "ticker,datekey,calendardate,assets,netinc,ncfo,gp,shareswa"
rows, part, total = [], 0, 0
params = {"dimension": "ARQ", "calendardate.gte": "1998-12-31",
          "qopts.columns": COLS, "qopts.per_page": 10000,
          "api_key": sh._api_key()}
cursor = None
while True:
    p = dict(params)
    if cursor: p["qopts.cursor_id"] = cursor
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
        print(f"part {part}: {len(rows)} rows (total {total})", flush=True)
        rows, part = [], part + 1
    cursor = (payload.get("meta") or {}).get("next_cursor_id")
    if not cursor:
        break
    time.sleep(0.25)
if rows:
    with gzip.open(f"{S}/sf1_arq_part{part}.json.gz", "wt") as f:
        json.dump(rows, f)
    print(f"part {part}: {len(rows)} rows (total {total})", flush=True)
print(f"DONE: {total} SF1 ARQ rows in {part+1} parts", flush=True)
