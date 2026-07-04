"""gauntlet_v2_fundamentals phases 2-4: signals -> holdings -> bars -> in-sample screen.
Usage: python3 run_gauntlet_v2_screen.py {holdings|bars|screen} SCRATCH. PAPER ONLY."""
import bisect, gzip, json, math, os, sys
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

S = sys.argv[2]
PHASE = sys.argv[1]
OUT = "docs/data/gauntlet_v2"
CELLS = [(sig, n, b) for sig in ("net_issuance_low", "asset_growth_low",
                                  "accruals_low", "gross_prof_high", "roa_high")
         for n in (25, 50) for b in ("LARGE", "SMALL")]

def load_sf1():
    rows = []
    for p in (0, 1, 2):
        rows += json.load(gzip.open(f"{S}/sf1_arq_part{p}.json.gz", "rt"))
    by_t = defaultdict(list)
    for r in rows:
        if r.get("assets") in (None, 0):
            continue
        by_t[r["ticker"]].append(r)
    for t in by_t:
        by_t[t].sort(key=lambda r: (r["calendardate"], r["datekey"]))
    return by_t

def signals_for(rows, D):
    """Latest 8 ARQ quarters with datekey <= D (filing-date PIT)."""
    usable = [r for r in rows if r["datekey"] <= D]
    if len(usable) < 8:
        return None
    last8 = usable[-8:]
    if last8[-1]["calendardate"] < (date(*map(int, D.split("-"))) -
                                     timedelta(days=400)).isoformat():
        return None  # stale filer
    cur4, prior4 = last8[4:], last8[:4]
    def s(rs, k):
        vs = [r[k] for r in rs if r.get(k) is not None]
        return sum(vs) if len(vs) == 4 else None
    assets = cur4[-1]["assets"]
    assets_yr_ago = prior4[-1]["assets"]
    sw_cur = s(cur4, "shareswa"); sw_prior = s(prior4, "shareswa")
    ni = s(cur4, "netinc"); cfo = s(cur4, "ncfo"); gp = s(cur4, "gp")
    out = {}
    if sw_cur and sw_prior and sw_prior > 0:
        out["net_issuance_low"] = sw_cur / sw_prior - 1.0        # low = buyback
    if assets and assets_yr_ago and assets_yr_ago > 0:
        out["asset_growth_low"] = assets / assets_yr_ago - 1.0   # low good
    if ni is not None and cfo is not None and assets:
        out["accruals_low"] = (ni - cfo) / assets                # low good
    if gp is not None and assets:
        out["gross_prof_high"] = gp / assets                     # high good
    if ni is not None and assets:
        out["roa_high"] = ni / assets                            # high good
    return out

def quarterly_snapshots(window):
    pop = json.load(open("cache/shared_pop_gauntlet_v1_universes.json"))
    rows = pop["rows"] if isinstance(pop, dict) else pop
    rows = [r for r in rows if r["window"] == window]
    by_q = {}
    for r in sorted(rows, key=lambda r: r["signal_date"]):
        q = (r["signal_date"][:4], (int(r["signal_date"][5:7]) - 1) // 3, r["bucket"])
        by_q.setdefault(q, r)  # first monthly snapshot of the quarter
    return sorted(by_q.values(), key=lambda r: r["signal_date"])

if PHASE == "holdings":
    sf1 = load_sf1()
    snaps = quarterly_snapshots("in_sample")
    holdings = {f"{sig}__N{n}__{b}": {} for sig, n, b in CELLS}
    coverage = defaultdict(list)
    for snap in snaps:
        D, bucket = snap["signal_date"], snap["bucket"]
        scored = {}
        for m in snap["members"]:
            rows = sf1.get(m)
            if not rows:
                continue
            sg = signals_for(rows, D)
            if sg:
                scored[m] = sg
        for sig, n, b in CELLS:
            if b != bucket:
                continue
            cand = [(v[sig], m) for m, v in scored.items() if sig in v]
            cov = len(cand) / max(1, len(snap["members"]))
            coverage[f"{sig}__N{n}__{b}"].append(cov)
            reverse = sig.endswith("_high")
            cand.sort(reverse=reverse)
            holdings[f"{sig}__N{n}__{b}"][D] = [m for _, m in cand[:n]]
    report = {"coverage_mean": {c: sum(v)/len(v) for c, v in coverage.items()},
              "coverage_min": {c: min(v) for c, v in coverage.items()},
              "n_snapshots": {c: len(v) for c, v in coverage.items()}}
    with gzip.open(f"{S}/holdings_insample.json.gz", "wt") as f:
        json.dump(holdings, f)
    with open(f"{S}/coverage_insample.json", "w") as f:
        json.dump(report, f, indent=1)
    union = sorted({m for cell in holdings.values() for names in cell.values() for m in names})
    with open(f"{S}/held_union.json", "w") as f:
        json.dump(union, f)
    print(json.dumps(report, indent=1)[:1200])
    print("held union:", len(union), "names")

elif PHASE == "bars":
    import shared.sharadar as sh
    union = json.load(open(f"{S}/held_union.json"))
    bars = {}
    CH = 30
    for i in range(0, len(union), CH):
        for r in sh._datatable("SEP", ticker=",".join(union[i:i+CH]), **{
                "date.gte": "2000-04-01", "date.lte": "2016-03-31",
                "qopts.columns": "ticker,date,close,closeadj",
                "qopts.per_page": 10000}):
            if r.get("close") is None:
                continue
            b = {"date": r["date"][:10], "close": float(r["close"])}
            if r.get("closeadj") is not None:
                b["close_total_return"] = float(r["closeadj"])
            bars.setdefault(r["ticker"], []).append(b)
        if (i // CH) % 10 == 0:
            print(f"bars {min(i+CH, len(union))}/{len(union)}", flush=True)
    for t in bars:
        bars[t].sort(key=lambda b: b["date"])
    with gzip.open(f"{S}/bars_insample.json.gz", "wt") as f:
        json.dump(bars, f)
    print(f"DONE bars for {len(bars)} names")

elif PHASE == "screen":
    from shared.gauntlet import (CostModel, StrategySpec, simulate,
                                  expected_max_sharpe, deflated_sharpe_ratio,
                                  parameter_cliff_report)
    with gzip.open(f"{S}/holdings_insample.json.gz", "rt") as f:
        holdings = json.load(f)
    with gzip.open(f"{S}/bars_insample.json.gz", "rt") as f:
        bars = json.load(f)
    BENCH = {"LARGE": 0.0551, "SMALL": 0.0679}  # v1 in-sample EW CAGR (frozen, reused)
    COSTS = {"LARGE": CostModel(0.0, 5.0, 25.0), "SMALL": CostModel(0.0, 25.0, 25.0)}
    # Global trading-day calendar from the full bars union, for the
    # prereg's signal_lag discipline: holdings are PIT at the signal
    # date D (datekey <= D); EXECUTION is at the close of the first
    # trading day strictly after D. Same convention as every study
    # tonight — no same-day signal-and-trade.
    all_days = sorted({b["date"] for bl in bars.values() for b in bl})
    def next_day(D):
        i = bisect.bisect_right(all_days, D)
        return all_days[i] if i < len(all_days) else None
    results = {}
    for cell, snap_holdings in holdings.items():
        bucket = cell.rsplit("__", 1)[1]
        exec_holdings = {}
        for D, names in snap_holdings.items():
            ed = next_day(D)
            if ed:
                exec_holdings[ed] = [m for m in names if m in bars]
        snaps = {d: names for d, names in exec_holdings.items() if names}
        def mk_select(sh_=exec_holdings):
            def select(day, universe, trimmed):
                names = [m for m in sh_.get(day, []) if m in trimmed and trimmed.tail(m, 1)]
                if not names:
                    return {}
                w = 0.99 / len(names)
                return {m: w for m in names}
            return select
        res = simulate(StrategySpec(cell, mk_select()), snaps, bars,
                       initial_cash=10_000.0, cost=COSTS[bucket],
                       start="2000-06-01", end="2015-12-31")
        st = res["stats"]
        dsr = deflated_sharpe_ratio(st["sharpe"], n_trials=20, n_obs=st["n_obs"],
                                     skew=st["skew"], kurtosis=st["kurtosis"])
        results[cell] = {"stats": st, "dsr": dsr,
                          "beats_benchmark": st["cagr"] > BENCH[bucket],
                          "stage1_survivor": dsr >= 0.95 and st["cagr"] > BENCH[bucket]}
        print(f"{cell}: CAGR {st['cagr']:+.2%} sharpe {st['sharpe']:.2f} "
              f"DSR {dsr:.3f} beats {results[cell]['beats_benchmark']} "
              f"SURVIVOR {results[cell]['stage1_survivor']}", flush=True)
    os.makedirs(OUT, exist_ok=True)
    cliff = parameter_cliff_report([
        {"params": {"signal": c.split("__")[0], "n": int(c.split("__")[1][1:]),
                     "bucket": c.rsplit("__", 1)[1]},
         "metric": results[c]["stats"]["sharpe"], "cell": c} for c in results])
    with open(f"{OUT}/insample_results.json", "w") as f:
        json.dump({"results": results, "cliff": cliff,
                    "benchmarks_cagr": BENCH,
                    "expected_max_sharpe_20": expected_max_sharpe(20)}, f,
                   indent=1, default=str)
    survivors = [c for c in results if results[c]["stage1_survivor"]]
    print("\nSTAGE-1 SURVIVORS:", survivors or "NONE")
