"""achilles_pead_gauntlet phase 3: SEP daily bars for the SMALL/MICRO union.

Batched pull (fetch_sep_bulk_range with a ticker list per batch) over the full
window, closeadj (total-return) + close + low (for the intraday stop). Hardened
with request-retry so a reset doesn't abort. Writes gzip parts. PAPER ONLY.
"""
import gzip, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.sharadar as sh
import requests

OUT = "data/achilles_gauntlet"
COLS = "ticker,date,close,closeadj,low"
DATE_FROM, DATE_TO = "2000-01-01", "2025-12-31"
BATCH = 250

union = json.load(open(f"{OUT}/union_tickers.json"))
batches = [union[i:i+BATCH] for i in range(0, len(union), BATCH)]
print(f"{len(union)} tickers in {len(batches)} batches of {BATCH}", flush=True)


def _get(url, params, tries=6):
    for a in range(tries):
        try:
            r = requests.get(url, params=params, timeout=180)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if a == tries - 1:
                raise
            w = min(30, 2 ** a)
            print(f"  retry {a+1} after {type(e).__name__}: {w}s", flush=True)
            time.sleep(w)


done_batches = 0
grand = 0
for bi, batch in enumerate(batches):
    part_path = f"{OUT}/sep_part{bi:03d}.json.gz"
    if os.path.exists(part_path):
        done_batches += 1
        continue
    rows, cursor = [], None
    params = {"date.gte": DATE_FROM, "date.lte": DATE_TO, "ticker": ",".join(batch),
              "qopts.columns": COLS, "qopts.per_page": 10000, "api_key": sh._api_key()}
    while True:
        p = dict(params)
        if cursor:
            p["qopts.cursor_id"] = cursor
        payload = _get(f"{sh.BASE_URL}/SEP.json", p)
        dt = payload["datatable"]
        cols = [c["name"] for c in dt["columns"]]
        rows.extend(dict(zip(cols, row)) for row in dt["data"])
        cursor = (payload.get("meta") or {}).get("next_cursor_id")
        if not cursor:
            break
        time.sleep(0.15)
    with gzip.open(part_path, "wt") as f:
        json.dump(rows, f)
    grand += len(rows)
    done_batches += 1
    if bi % 5 == 0 or bi == len(batches) - 1:
        print(f"batch {bi+1}/{len(batches)}: {len(rows)} bars (grand {grand})", flush=True)
open(f"{OUT}/sep_DONE", "w").write(str(grand))
print(f"SEP DONE: {grand} bars in {len(batches)} parts", flush=True)
