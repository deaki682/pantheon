"""Neglect-leg data pull (2026-07-06). Pulls the balance-sheet panel + ticker
metadata the neglect screen needs — the family the forced-seller event net can't
see (names quietly trading below a real floor: net cash / net-net / tangible book).

Sharadar SF1 ARQ (recent quarters only — we want the LATEST balance sheet per
name, not history) with the balance-sheet columns, plus TICKERS with sector
(to exclude banks/financials where these screens are meaningless). Current
marketcap comes from the DAILY panel already on disk. Writes gzipped parts.
"""
import gzip, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared.sharadar as sh
import requests

OUT = "data/oracle_neglect"
os.makedirs(OUT, exist_ok=True)


def _get(url, params, tries=6):
    for a in range(tries):
        try:
            r = requests.get(url, params=params, timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if a == tries - 1:
                raise
            w = min(30, 2 ** a)
            print(f"  retry {a+1} after {type(e).__name__}: {w}s", flush=True)
            time.sleep(w)


# ---- 1. TICKERS with sector (exclude financials; identify common stock / exchange) ----
print("pulling TICKERS metadata (sector/category/exchange)...", flush=True)
# currency + location are REQUIRED by oracle.neglect_screen.is_common_tradable
# (the FX-artifact guard hard-rejects non-USD reporters; location drives the
# China/HK unreachable-floor exclusion). Omitting them made the screen reject
# EVERY name -> 0 candidates (2026-07-06 fresh-run bug).
tk_cols = "ticker,name,exchange,category,isdelisted,sector,industry,scalemarketcap,currency,location"
rows, cursor = [], None
while True:
    p = {"qopts.columns": tk_cols, "qopts.per_page": 10000, "api_key": sh._api_key()}
    if cursor:
        p["qopts.cursor_id"] = cursor
    payload = _get(f"{sh.BASE_URL}/TICKERS.json", p)
    dt = payload["datatable"]
    cols = [c["name"] for c in dt["columns"]]
    rows.extend(dict(zip(cols, row)) for row in dt["data"])
    cursor = (payload.get("meta") or {}).get("next_cursor_id")
    if not cursor:
        break
json.dump(rows, open(f"{OUT}/tickers_meta.json", "w"))
print(f"  {len(rows)} ticker rows -> {OUT}/tickers_meta.json", flush=True)

# ---- 2. SF1 ARQ recent balance sheets ----
# net cash needs cashneq + investmentsc (current marketable securities) - debt;
# net-net needs assetsc - liabilities; tangible book needs equity - intangibles.
COLS = ("ticker,datekey,calendardate,cashneq,investmentsc,debt,assetsc,assets,"
        "liabilities,liabilitiesc,equity,intangibles,sharesbas,netinc,ncfo,revenue")
print(f"pulling SF1 ARQ balance sheets (calendardate>=2025-09-01)...", flush=True)
rows, part, total, cursor = [], 0, 0, None
while True:
    p = {"dimension": "ARQ", "calendardate.gte": "2025-09-01",
         "qopts.columns": COLS, "qopts.per_page": 10000, "api_key": sh._api_key()}
    if cursor:
        p["qopts.cursor_id"] = cursor
    payload = _get(f"{sh.BASE_URL}/SF1.json", p)
    dt = payload["datatable"]
    cols = [c["name"] for c in dt["columns"]]
    rows.extend(dict(zip(cols, row)) for row in dt["data"])
    total += len(dt["data"])
    if len(rows) >= 200_000:
        with gzip.open(f"{OUT}/sf1_bs_part{part}.json.gz", "wt") as f:
            json.dump(rows, f)
        print(f"  SF1 part {part}: {len(rows)} rows (total {total})", flush=True)
        rows, part = [], part + 1
    cursor = (payload.get("meta") or {}).get("next_cursor_id")
    if not cursor:
        break
if rows:
    with gzip.open(f"{OUT}/sf1_bs_part{part}.json.gz", "wt") as f:
        json.dump(rows, f)
    print(f"  SF1 part {part}: {len(rows)} rows (total {total})", flush=True)
open(f"{OUT}/DONE", "w").write(str(total))
print(f"SF1 balance-sheet pull DONE: {total} rows", flush=True)
