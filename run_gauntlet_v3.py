"""gauntlet_v3_value — docs/lab_prereg_gauntlet_v3_value.md. PAPER ONLY.
Phases: holdings (pull DAILY multiples + rank) | bars | screen | holdout."""
import bisect, gzip, json, math, os, sys, time
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PHASE, S = sys.argv[1], sys.argv[2]
OUT = "docs/data/gauntlet_v3"
# multiple -> (DAILY column, ascending? , positive-only?)
VALUE = {"value_pb_low": ("pb", True, True), "value_ps_low": ("ps", True, True),
         "value_ep_high": ("pe", True, True), "value_evebitda_low": ("evebitda", True, True)}
CELLS = [(sig, b) for sig in VALUE for b in ("LARGE", "SMALL")]
N = 50
BENCH_IS = {"LARGE": 0.0551, "SMALL": 0.0679}
BENCH_HO = {"LARGE": 0.1143, "SMALL": 0.0950}

def quarterly_snaps(window):
    pop = json.load(open("cache/shared_pop_gauntlet_v1_universes.json"))
    rows = [r for r in (pop["rows"] if isinstance(pop, dict) else pop) if r["window"] == window]
    by_q = {}
    for r in sorted(rows, key=lambda r: r["signal_date"]):
        q = (r["signal_date"][:4], (int(r["signal_date"][5:7]) - 1) // 3, r["bucket"])
        by_q.setdefault(q, r)
    return sorted(by_q.values(), key=lambda r: r["signal_date"])

if PHASE == "holdings":
    import shared.sharadar as sh
    window = sys.argv[3]  # in_sample | holdout
    snaps = quarterly_snaps(window)
    dates = sorted({s["signal_date"] for s in snaps})
    daily = {}   # date -> {ticker -> {col: val}}
    for D in dates:
        rows, tries = None, 0
        while rows is None:
            try:
                rows = sh._datatable("DAILY", **{"date.gte": D, "date.lte": D,
                    "qopts.columns": "ticker,pb,ps,pe,evebitda", "qopts.per_page": 10000})
            except Exception:
                tries += 1
                if tries >= 4: raise
                time.sleep(2 ** tries)
        daily[D] = {r["ticker"].upper(): r for r in rows}
        print(f"DAILY {D}: {len(rows)}", flush=True)
    holdings = {f"{sig}__{b}": {} for sig, b in CELLS}
    coverage = defaultdict(list)
    for snap in snaps:
        D, bucket, members = snap["signal_date"], snap["bucket"], set(snap["members"])
        dd = daily[D]
        for sig, b in CELLS:
            if b != bucket: continue
            col, asc, posonly = VALUE[sig]
            cand = []
            for m in members:
                r = dd.get(m)
                if not r: continue
                v = r.get(col)
                if v is None: continue
                v = float(v)
                if posonly and v <= 0: continue
                cand.append((v, m))
            coverage[f"{sig}__{b}"].append(len(cand) / max(1, len(members)))
            cand.sort(reverse=not asc)
            holdings[f"{sig}__{b}"][D] = [m for _, m in cand[:N]]
    tag = window
    with gzip.open(f"{S}/v3_holdings_{tag}.json.gz", "wt") as f:
        json.dump(holdings, f)
    union = sorted({m for cell in holdings.values() for names in cell.values() for m in names})
    with open(f"{S}/v3_union_{tag}.json", "w") as f:
        json.dump(union, f)
    with open(f"{S}/v3_coverage_{tag}.json", "w") as f:
        json.dump({c: sum(v)/len(v) for c, v in coverage.items()}, f, indent=1)
    print(f"{tag}: union {len(union)} | coverage",
          {c: round(sum(v)/len(v), 2) for c, v in coverage.items()})

elif PHASE == "bars":
    import shared.sharadar as sh
    window, gte, lte = sys.argv[3], sys.argv[4], sys.argv[5]
    union = json.load(open(f"{S}/v3_union_{window}.json"))
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
    with gzip.open(f"{S}/v3_bars_{window}.json.gz", "wt") as f:
        json.dump(bars, f)
    print(f"DONE {window} bars: {len(bars)}")

elif PHASE in ("screen", "holdout"):
    from shared.gauntlet import (CostModel, StrategySpec, simulate,
        deflated_sharpe_ratio, probabilistic_sharpe_ratio, expected_max_sharpe,
        parameter_cliff_report)
    window = "in_sample" if PHASE == "screen" else "holdout"
    gte, lte = (("2000-06-01", "2015-12-31") if PHASE == "screen"
                else ("2016-01-01", "2025-12-31"))
    BENCH = BENCH_IS if PHASE == "screen" else BENCH_HO
    with gzip.open(f"{S}/v3_holdings_{window}.json.gz", "rt") as f: holdings = json.load(f)
    with gzip.open(f"{S}/v3_bars_{window}.json.gz", "rt") as f: bars = json.load(f)
    COSTS = {"LARGE": CostModel(0, 5.0, 25.0), "SMALL": CostModel(0, 25.0, 25.0)}
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    all_days = sorted({b["date"] for bl in bars.values() for b in bl})
    def nxt(D):
        i = bisect.bisect_right(all_days, D)
        return all_days[i] if i < len(all_days) else None
    results = {}
    for cell, sh_ in holdings.items():
        if only and cell not in only: continue
        bucket = cell.rsplit("__", 1)[1]
        ex011 = {}
        for D, names in sh_.items():
            ed = nxt(D)
            if ed: ex011[ed] = [m for m in names if m in bars]
        snaps = {d: ns for d, ns in ex011.items() if ns}
        def mk(e=ex011):
            def sel(day, u, tr):
                ns = [m for m in e.get(day, []) if m in tr and tr.tail(m, 1)]
                return {m: 0.99/len(ns) for m in ns} if ns else {}
            return sel
        res = simulate(StrategySpec(cell, mk()), snaps, bars, initial_cash=10_000.0,
                       cost=COSTS[bucket], start=gte, end=lte)
        st = res["stats"]
        if PHASE == "screen":
            dsr = deflated_sharpe_ratio(st["sharpe"], n_trials=8, n_obs=st["n_obs"],
                                        skew=st["skew"], kurtosis=st["kurtosis"])
            surv = dsr >= 0.95 and st["cagr"] > BENCH[bucket]
            results[cell] = {"stats": st, "dsr": dsr, "beats": st["cagr"] > BENCH[bucket],
                             "survivor": surv}
            print(f"{cell}: CAGR {st['cagr']:+.2%} shrp {st['sharpe']:.2f} DSR {dsr:.3f} "
                  f"bench {BENCH[bucket]:.2%} {'** SURVIVOR' if surv else ''}", flush=True)
        else:
            psr = probabilistic_sharpe_ratio(st["sharpe"], 0.0, n_obs=st["n_obs"],
                                             skew=st["skew"], kurtosis=st["kurtosis"])
            passed = psr >= 0.95 and st["cagr"] > BENCH[bucket]
            results[cell] = {"stats": st, "psr": psr, "beats": st["cagr"] > BENCH[bucket],
                             "holdout_pass": passed}
            print(f"{cell}: HO CAGR {st['cagr']:+.2%} PSR {psr:.3f} bench {BENCH[bucket]:.2%} "
                  f"{'** PASS' if passed else 'fail'}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    fn = "insample_results.json" if PHASE == "screen" else "holdout_results.json"
    out = {"results": results, "benchmarks": BENCH}
    if PHASE == "screen":
        out["expected_max_sharpe_8"] = expected_max_sharpe(8)
        out["cliff"] = parameter_cliff_report([
            {"params": {"signal": c.split("__")[0], "bucket": c.rsplit("__",1)[1]},
             "metric": results[c]["stats"]["sharpe"], "cell": c} for c in results])
    with open(f"{OUT}/{fn}", "w") as f: json.dump(out, f, indent=1, default=str)
    if PHASE == "screen":
        surv = [c for c in results if results[c]["survivor"]]
        print("\nSTAGE-1 SURVIVORS:", surv or "NONE")
