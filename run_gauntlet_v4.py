"""gauntlet_v4_composite — docs/lab_prereg_gauntlet_v4_composite.md. PAPER ONLY.
Phases: holdings WINDOW | bars WINDOW GTE LTE | screen | holdout [only] [slipmult]"""
import bisect, gzip, json, math, os, sys, time
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gauntlet_v2_screen import load_sf1, signals_for, quarterly_snapshots

PHASE, S = sys.argv[1], sys.argv[2]
OUT = "docs/data/gauntlet_v4"
CELLS = [("composite", b, n) for b in ("LARGE", "SMALL") for n in (25, 50)]
BENCH_IS = {"LARGE": 0.0551, "SMALL": 0.0679}
BENCH_HO = {"LARGE": 0.1143, "SMALL": 0.0950}

def pctranks(pairs, better_low):
    """[(value, member)] -> {member: percentile in [0,1], 1=best}."""
    xs = sorted(pairs, key=lambda p: p[0], reverse=not better_low)
    n = len(xs)
    return {m: (i / (n - 1) if n > 1 else 1.0) for i, (_, m) in enumerate(xs)}

if PHASE == "holdings":
    import shared.sharadar as sh
    window = sys.argv[3]
    sf1 = load_sf1()
    snaps = quarterly_snapshots(window)
    dates = sorted({s["signal_date"] for s in snaps})
    daily = {}
    for D in dates:
        for a in range(4):
            try:
                rows = sh._datatable("DAILY", **{"date.gte": D, "date.lte": D,
                    "qopts.columns": "ticker,ps", "qopts.per_page": 10000}); break
            except Exception:
                if a == 3: raise
                time.sleep(2 ** (a + 1))
        daily[D] = {r["ticker"].upper(): r.get("ps") for r in rows}
        print(f"DAILY {D}: {len(rows)}", flush=True)
    holdings = {f"composite__{b}__N{n}": {} for _, b, n in CELLS}
    coverage = defaultdict(list)
    for snap in snaps:
        D, bucket, members = snap["signal_date"], snap["bucket"], snap["members"]
        ni, gp, ps = [], [], []
        for m in members:
            sg = signals_for(sf1.get(m, []), D) if sf1.get(m) else None
            if sg and "net_issuance_low" in sg: ni.append((sg["net_issuance_low"], m))
            if sg and "gross_prof_high" in sg: gp.append((sg["gross_prof_high"], m))
            pv = daily[D].get(m)
            if pv is not None and float(pv) > 0: ps.append((float(pv), m))
        rk_ni = pctranks(ni, True)      # low issuance = best
        rk_gp = pctranks(gp, False)     # high profitability = best
        rk_ps = pctranks(ps, True)      # low price/sales = best
        comp = {}
        for m in members:
            parts = [r[m] for r in (rk_ni, rk_gp, rk_ps) if m in r]
            if len(parts) >= 2:
                comp[m] = sum(parts) / len(parts)
        ranked = sorted(comp.items(), key=lambda kv: -kv[1])
        for _, b, n in CELLS:
            if b != bucket: continue
            coverage[f"composite__{b}__N{n}"].append(len(comp) / max(1, len(members)))
            holdings[f"composite__{b}__N{n}"][D] = [m for m, _ in ranked[:n]]
    with gzip.open(f"{S}/v4_holdings_{window}.json.gz", "wt") as f: json.dump(holdings, f)
    union = sorted({m for c in holdings.values() for ns in c.values() for m in ns})
    with open(f"{S}/v4_union_{window}.json", "w") as f: json.dump(union, f)
    print(f"{window}: union {len(union)} | coverage",
          {c: round(sum(v)/len(v), 2) for c, v in coverage.items()})

elif PHASE == "bars":
    import shared.sharadar as sh
    window, gte, lte = sys.argv[3], sys.argv[4], sys.argv[5]
    union = json.load(open(f"{S}/v4_union_{window}.json"))
    bars = {}
    def fetch(ch):
        for a in range(4):
            try:
                return sh._datatable("SEP", ticker=",".join(ch), **{"date.gte": gte,
                    "date.lte": lte, "qopts.columns": "ticker,date,close,closeadj",
                    "qopts.per_page": 10000})
            except Exception:
                if a == 3: raise
                time.sleep(2 ** (a + 1))
    for i in range(0, len(union), 30):
        for r in fetch(union[i:i+30]):
            if r.get("close") is None: continue
            b = {"date": r["date"][:10], "close": float(r["close"])}
            if r.get("closeadj") is not None: b["close_total_return"] = float(r["closeadj"])
            bars.setdefault(r["ticker"], []).append(b)
        if (i//30) % 10 == 0: print(f"bars {min(i+30,len(union))}/{len(union)}", flush=True)
    for t in bars: bars[t].sort(key=lambda b: b["date"])
    with gzip.open(f"{S}/v4_bars_{window}.json.gz", "wt") as f: json.dump(bars, f)
    print(f"DONE {window} bars: {len(bars)}")

elif PHASE in ("screen", "holdout"):
    from shared.gauntlet import (CostModel, StrategySpec, simulate, deflated_sharpe_ratio,
        probabilistic_sharpe_ratio, expected_max_sharpe)
    window = "in_sample" if PHASE == "screen" else "holdout"
    gte, lte = (("2000-06-01","2015-12-31") if PHASE=="screen" else ("2016-01-01","2025-12-31"))
    BENCH = BENCH_IS if PHASE == "screen" else BENCH_HO
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else None
    slip = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    with gzip.open(f"{S}/v4_holdings_{window}.json.gz", "rt") as f: holdings = json.load(f)
    with gzip.open(f"{S}/v4_bars_{window}.json.gz", "rt") as f: bars = json.load(f)
    COSTS = {"LARGE": CostModel(0, 5.0*slip, 25.0), "SMALL": CostModel(0, 25.0*slip, 25.0)}
    all_days = sorted({b["date"] for bl in bars.values() for b in bl})
    def nxt(D):
        i = bisect.bisect_right(all_days, D); return all_days[i] if i < len(all_days) else None
    results = {}
    for cell, sh_ in holdings.items():
        if only and cell not in only: continue
        bucket = cell.split("__")[1]
        ex = {}
        for D, names in sh_.items():
            ed = nxt(D)
            if ed: ex[ed] = [m for m in names if m in bars]
        snaps = {d: ns for d, ns in ex.items() if ns}
        def mk(e=ex):
            def sel(day, u, tr):
                ns = [m for m in e.get(day, []) if m in tr and tr.tail(m, 1)]
                return {m: 0.99/len(ns) for m in ns} if ns else {}
            return sel
        res = simulate(StrategySpec(cell, mk()), snaps, bars, initial_cash=10_000.0,
                       cost=COSTS[bucket], start=gte, end=lte)
        results[cell] = {"stats": res["stats"], "bucket": bucket,
                         "beats": res["stats"]["cagr"] > BENCH[bucket]}
    if PHASE == "screen":
        sharpes = [v["stats"]["sharpe"] for v in results.values()]
        ms = sum(sharpes)/len(sharpes); var_sr = sum((x-ms)**2 for x in sharpes)/len(sharpes)
        for cell, v in results.items():
            st = v["stats"]
            v["dsr"] = deflated_sharpe_ratio(st["sharpe"], n_trials=4, n_obs=st["n_obs"],
                skew=st["skew"], kurtosis=st["kurtosis"], variance_of_sr=var_sr)
            v["survivor"] = v["dsr"] >= 0.95 and v["beats"]
            print(f"{cell}: CAGR {st['cagr']:+.2%} shrp {st['sharpe']:.2f} DSR {v['dsr']:.3f} "
                  f"bench {BENCH[v['bucket']]:.2%} {'** SURVIVOR' if v['survivor'] else ''}", flush=True)
        print(f"var_sr {var_sr:.5f}")
    else:
        for cell, v in results.items():
            st = v["stats"]
            v["psr"] = probabilistic_sharpe_ratio(st["sharpe"], 0.0, n_obs=st["n_obs"],
                skew=st["skew"], kurtosis=st["kurtosis"])
            v["holdout_pass"] = v["psr"] >= 0.95 and v["beats"]
            print(f"{cell}: HO CAGR {st['cagr']:+.2%} PSR {v['psr']:.3f} bench {BENCH[v['bucket']]:.2%} "
                  f"{'** PASS' if v['holdout_pass'] else 'fail'}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    sfx = "" if slip == 1.0 else f"_{slip:g}x"
    fn = "insample_results.json" if PHASE=="screen" else f"holdout{sfx}_results.json"
    with open(f"{OUT}/{fn}", "w") as f: json.dump({"results": results, "bench": BENCH}, f, indent=1, default=str)
