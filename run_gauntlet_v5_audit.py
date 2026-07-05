"""gauntlet_v5 audit: regime breakdown + holdings spot-check for the survivors.
A positive result gets audited HARDER. Usage: python3 run_gauntlet_v5_audit.py SCRATCH"""
import bisect, gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shared.gauntlet import CostModel, StrategySpec, simulate, summarize_by_period

S = sys.argv[1]
COSTS = {"LARGE": CostModel(0.0, 5.0, 25.0), "SMALL": CostModel(0.0, 25.0, 25.0)}
CHECK = ["cash_op__N50__LARGE", "cash_op__N50__SMALL",
         "gross_prof__N50__LARGE", "gross_prof__N50__SMALL",
         "fund_mom__N50__LARGE"]


def sim_cell(cell, holdings, bars, gte, lte):
    bucket = cell.rsplit("__", 1)[1]
    all_days = sorted({b["date"] for bl in bars.values() for b in bl})
    def nd(D):
        i = bisect.bisect_right(all_days, D)
        return all_days[i] if i < len(all_days) else None
    ex = {}
    for D, names in holdings[cell].items():
        ed = nd(D)
        if ed:
            ex[ed] = [m for m in names if m in bars]
    snaps = {d: n for d, n in ex.items() if n}
    def mk(sh_=ex):
        def sel(day, u, tr):
            names = [m for m in sh_.get(day, []) if m in tr and tr.tail(m, 1)]
            return {m: 0.99 / len(names) for m in names} if names else {}
        return sel
    return simulate(StrategySpec(cell, mk()), snaps, bars, initial_cash=10_000.0,
                    cost=COSTS[bucket], start=gte, end=lte)


for window, gte, lte, cuts in [
    ("in_sample", "2000-06-01", "2015-12-31", ["2004-01-01", "2008-01-01", "2010-01-01"]),
    ("holdout", "2016-01-01", "2025-12-31", ["2020-04-01"]),
]:
    with gzip.open(f"{S}/holdings_{window}.json.gz", "rt") as f:
        holdings = json.load(f)
    with gzip.open(f"{S}/bars_{window}.json.gz", "rt") as f:
        bars = json.load(f)
    print(f"\n===== {window.upper()} regime breakdown (CAGR per segment) =====")
    for cell in CHECK:
        res = sim_cell(cell, holdings, bars, gte, lte)
        segs = summarize_by_period(res["curve"], cuts)
        line = "  ".join(f"{k.split('..')[0][:7]}-{k.split('..')[1][:7]}:{v['cagr']:+.1%}"
                         for k, v in segs.items())
        print(f"{cell:26s} full {res['stats']['cagr']:+.2%} | {line}")

# holdings spot-check: are cash_op's large-cap picks real, sensible names?
print("\n===== cash_op__N50__LARGE holdings spot-check =====")
with gzip.open(f"{S}/holdings_holdout.json.gz", "rt") as f:
    hh = json.load(f)
dates = sorted(hh["cash_op__N50__LARGE"].keys())
for D in (dates[0], dates[len(dates) // 2], dates[-1]):
    names = hh["cash_op__N50__LARGE"][D]
    print(f"{D}: {', '.join(names[:18])} ... (n={len(names)})")
