"""achilles_pead_gauntlet phase 2: build monthly PIT SMALL/MICRO universes from
DAILY marketcaps, with the survivorship-honest ticker filter. Emits the universe
catalog + the union ticker set (the SEP-pull target). PAPER ONLY.
"""
import gzip, json, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from achilles.pead_gauntlet import build_entity_map, is_tradable_common, in_listing_window

OUT = "data/achilles_gauntlet"
# tradable-common + listing-window filter from the TICKERS metadata
tk = json.load(open("cache/shared_sharadar_tickers.json"))
tk_rows = tk if isinstance(tk, list) else next(v for v in tk.values() if isinstance(v, list))
emap = build_entity_map(tk_rows)
print(f"entity map: {len(emap)} tickers")

SMALL_LO, SMALL_HI = 501, 2000      # marketcap rank (1 = biggest), inclusive
MICRO_LO, MICRO_HI = 2001, 3500

universes = {}          # month_end_date -> {"SMALL":[...], "MICRO":[...]}
union = set()
dropped_window = 0
kept = 0

for year in range(2000, 2026):   # in-sample 2000-2015 + holdout 2016-2025 (+2000-01 warmup)
    path = f"{OUT}/daily_mcap_{year}.json.gz"
    if not os.path.exists(path):
        continue
    rows = json.load(gzip.open(path, "rt"))
    # group rows by date
    by_date = defaultdict(list)
    for r in rows:
        by_date[r["date"]].append((r["ticker"], r["marketcap"]))
    # month-end = last available trading date in each (year, month)
    dates = sorted(by_date)
    monthend = {}
    for d in dates:
        ym = d[:7]
        monthend[ym] = d       # last one wins (dates sorted asc)
    for ym, d in sorted(monthend.items()):
        # filter to tradable common equity, in its listing window on date d, positive mcap
        cross = []
        for tkr, mc in by_date[d]:
            if mc is None or mc <= 0:
                continue
            if not is_tradable_common(tkr, emap):
                continue
            if not in_listing_window(tkr, d, emap):
                dropped_window += 1
                continue
            cross.append((tkr, mc))
        cross.sort(key=lambda x: -x[1])   # rank 1 = biggest
        small = [t for t, _ in cross[SMALL_LO-1:SMALL_HI]]
        micro = [t for t, _ in cross[MICRO_LO-1:MICRO_HI]]
        universes[d] = {"SMALL": small, "MICRO": micro}
        union.update(small); union.update(micro)
        kept += len(small) + len(micro)
    print(f"{year}: {len([k for k in universes if k[:4]==str(year)])} months, union now {len(union)}", flush=True)

json.dump({"universes": universes, "definition": "monthly PIT marketcap-rank buckets: SMALL=501-2000, MICRO=2001-3500, tradable common equity on major US exchanges, in listing window (recycled-ticker guard)"},
          open(f"{OUT}/universes.json", "w"))
json.dump(sorted(union), open(f"{OUT}/union_tickers.json", "w"))
print(f"\nDONE: {len(universes)} monthly snapshots, {len(union)} unique tickers in the SMALL+MICRO union")
print(f"(dropped {dropped_window} rows on the recycled-ticker/window guard, kept {kept} slots)")
