"""gauntlet_v6_combinations phases 2-4. PAPER ONLY.
Usage: python3 run_gauntlet_v6_screen.py {holdings|bars|screen|holdout} SCRATCH [args]

8 signals x {LARGE,SMALL} x {N25,N50} = 32 cells. Intersection operator for
combinations = max(rankA, rankB) minimized ("deep in both"). DSR n_trials=32."""
import bisect, gzip, json, math, os, sys
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PHASE, S = sys.argv[1], sys.argv[2]
OUT = "docs/data/gauntlet_v6"
# combos: (legA_key, legA_ascending, legB_key, legB_ascending)  ascending=True => low value best
COMBOS = {
    "quality_at_price":   ("gross_prof", False, "ps", True),
    "capreturn_at_price": ("netiss",     True,  "ps", True),
    "netiss_x_grossprof": ("netiss",     True,  "gross_prof", False),
}
# singles: (component_key, ascending)
SINGLES = {
    "delta_gpoa": ("delta_gpoa", False), "delta_ato": ("delta_ato", False),
    "gross_prof": ("gross_prof", False), "netiss_low": ("netiss", True),
    "ps_low": ("ps", True),
}
SIGS = list(COMBOS) + list(SINGLES)
CELLS = [(sig, n, b) for sig in SIGS for n in (25, 50) for b in ("LARGE", "SMALL")]


def load_sf1():
    rows, part = [], 0
    while os.path.exists(f"{S}/sf1_arq_part{part}.json.gz"):
        rows += json.load(gzip.open(f"{S}/sf1_arq_part{part}.json.gz", "rt"))
        part += 1
    by_t = defaultdict(list)
    for r in rows:
        if r.get("assets") in (None, 0):
            continue
        by_t[r["ticker"]].append(r)
    for t in by_t:
        by_t[t].sort(key=lambda r: (r["calendardate"], r["datekey"]))
    return by_t


def _s4(rs, k):
    vs = [r[k] for r in rs if r.get(k) is not None]
    return sum(vs) if len(vs) == 4 else None


def _noa(rs):
    r = rs[-1]
    for k in ("assets", "liabilities"):
        if r.get(k) is None:
            return None
    op_assets = float(r["assets"]) - float(r.get("cashneq") or 0) - float(r.get("investments") or 0)
    op_liab = float(r["liabilities"]) - float(r.get("debt") or 0)
    noa = op_assets - op_liab
    return noa if noa > 0 else None


def components(rows, D, ps):
    """Per-name component values as of signal date D (SF1 datekey<=D + DAILY ps)."""
    usable = [r for r in rows if r["datekey"] <= D]
    if len(usable) < 8:
        return None
    last8 = usable[-8:]
    if last8[-1]["calendardate"] < (date(*map(int, D.split("-"))) - timedelta(days=400)).isoformat():
        return None
    cur4, prior4 = last8[4:], last8[:4]
    assets = last8[-1].get("assets")
    if not assets or assets <= 0:
        return {}
    out = {}
    gp = _s4(cur4, "gp")
    if gp is not None:
        out["gross_prof"] = gp / assets
    sw_cur, sw_prior = _s4(cur4, "shareswa"), _s4(prior4, "shareswa")
    if sw_cur and sw_prior and sw_prior > 0:
        out["netiss"] = sw_cur / sw_prior - 1.0            # low = buyback = good
    if ps is not None and ps > 0:
        out["ps"] = ps                                     # low = cheap = good
    # delta_gpoa
    gp_prior = _s4(prior4, "gp")
    a_prior = prior4[-1].get("assets")
    if gp is not None and gp_prior is not None and a_prior and a_prior > 0:
        out["delta_gpoa"] = gp / assets - gp_prior / a_prior
    # delta_ato = rev_ttm/NOA change
    rev_cur, rev_prior = _s4(cur4, "revenue"), _s4(prior4, "revenue")
    noa_cur, noa_prior = _noa(cur4), _noa(prior4)
    if rev_cur is not None and rev_prior is not None and noa_cur and noa_prior:
        out["delta_ato"] = rev_cur / noa_cur - rev_prior / noa_prior
    return out


def quarterly_snapshots(window):
    pop = json.load(open("cache/shared_pop_gauntlet_v1_universes.json"))
    rows = pop["rows"] if isinstance(pop, dict) else pop
    rows = [r for r in rows if r["window"] == window]
    by_q = {}
    for r in sorted(rows, key=lambda r: r["signal_date"]):
        q = (r["signal_date"][:4], (int(r["signal_date"][5:7]) - 1) // 3, r["bucket"])
        by_q.setdefault(q, r)
    return sorted(by_q.values(), key=lambda r: r["signal_date"])


def _rank(names, valfn, ascending):
    order = sorted(names, key=lambda m: valfn(m), reverse=not ascending)
    return {m: i for i, m in enumerate(order)}


if PHASE == "holdings":
    sf1 = load_sf1()
    daily_ps = json.load(gzip.open(f"{S}/daily_ps.json.gz", "rt"))
    window = sys.argv[3] if len(sys.argv) > 3 else "in_sample"
    snaps = quarterly_snapshots(window)
    holdings = {f"{sig}__N{n}__{b}": {} for sig, n, b in CELLS}
    coverage = defaultdict(list)
    for snap in snaps:
        D, bucket = snap["signal_date"], snap["bucket"]
        psmap = daily_ps.get(D, {})
        scored = {}
        for m in snap["members"]:
            rows = sf1.get(m)
            if not rows:
                continue
            c = components(rows, D, psmap.get(m.upper()))
            if c:
                scored[m] = c
        # per-component populations + ranks
        has = lambda key: [m for m, v in scored.items() if key in v]
        rk = {}
        for key, asc in [("gross_prof", False), ("netiss", True), ("ps", True),
                         ("delta_gpoa", False), ("delta_ato", False)]:
            nm = has(key)
            rk[key] = _rank(nm, lambda m, k=key: scored[m][k], asc)
        for sig, n, b in CELLS:
            if b != bucket:
                continue
            if sig in COMBOS:
                aK, _, bK, _ = COMBOS[sig]
                names = [m for m in scored if aK in scored[m] and bK in scored[m]]
                score = {m: max(rk[aK][m], rk[bK][m]) for m in names}
                order = sorted(names, key=lambda m: score[m])
            else:
                cK, _ = SINGLES[sig]
                names = has(cK)
                order = sorted(names, key=lambda m: rk[cK][m])
            coverage[f"{sig}__N{n}__{b}"].append(len(order) / max(1, len(snap["members"])))
            holdings[f"{sig}__N{n}__{b}"][D] = order[:n]
    report = {"coverage_mean": {c: sum(v) / len(v) for c, v in coverage.items()}}
    with gzip.open(f"{S}/holdings_{window}.json.gz", "wt") as f:
        json.dump(holdings, f)
    with open(f"{S}/coverage_{window}.json", "w") as f:
        json.dump(report, f, indent=1)
    union = sorted({m for cell in holdings.values() for names in cell.values() for m in names})
    with open(f"{S}/held_union_{window}.json", "w") as f:
        json.dump(union, f)
    print(json.dumps({c: round(report["coverage_mean"][c], 2) for c in sorted(report["coverage_mean"])
                      if c.endswith("N50__LARGE")}, indent=1))
    print("held union:", len(union))

elif PHASE == "bars":
    import shared.sharadar as sh
    import time as _time
    window = sys.argv[3]
    gte, lte = sys.argv[4], sys.argv[5]
    union = json.load(open(f"{S}/held_union_{window}.json"))
    bars, CH = {}, 30

    def _fetch(chunk):
        for a in range(4):
            try:
                return sh._datatable("SEP", ticker=",".join(chunk), **{"date.gte": gte, "date.lte": lte,
                       "qopts.columns": "ticker,date,close,closeadj", "qopts.per_page": 10000})
            except Exception:
                if a == 3:
                    raise
                _time.sleep(2 ** (a + 1))
        return []
    for i in range(0, len(union), CH):
        for r in _fetch(union[i:i + CH]):
            if r.get("close") is None:
                continue
            b = {"date": r["date"][:10], "close": float(r["close"])}
            if r.get("closeadj") is not None:
                b["close_total_return"] = float(r["closeadj"])
            bars.setdefault(r["ticker"], []).append(b)
        if (i // CH) % 10 == 0:
            print(f"bars {min(i+CH,len(union))}/{len(union)}", flush=True)
    for t in bars:
        bars[t].sort(key=lambda b: b["date"])
    with gzip.open(f"{S}/bars_{window}.json.gz", "wt") as f:
        json.dump(bars, f)
    print(f"DONE bars {len(bars)}")

elif PHASE in ("screen", "holdout"):
    from shared.gauntlet import (CostModel, StrategySpec, simulate, expected_max_sharpe,
                                 deflated_sharpe_ratio, probabilistic_sharpe_ratio, parameter_cliff_report)
    is_screen = PHASE == "screen"
    window = "in_sample" if is_screen else "holdout"
    gte, lte = (("2000-06-01", "2015-12-31") if is_screen else ("2016-01-01", "2025-12-31"))
    BENCH = ({"LARGE": 0.0551, "SMALL": 0.0679} if is_screen else {"LARGE": 0.1143, "SMALL": 0.0950})
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else None
    slip = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    COSTS = {"LARGE": CostModel(0.0, 5.0 * slip, 25.0), "SMALL": CostModel(0.0, 25.0 * slip, 25.0)}
    with gzip.open(f"{S}/holdings_{window}.json.gz", "rt") as f:
        holdings = json.load(f)
    with gzip.open(f"{S}/bars_{window}.json.gz", "rt") as f:
        bars = json.load(f)
    all_days = sorted({b["date"] for bl in bars.values() for b in bl})

    def next_day(D):
        i = bisect.bisect_right(all_days, D)
        return all_days[i] if i < len(all_days) else None

    def maxdd(curve):
        peak, mdd = -1e18, 0.0
        for c in curve:
            peak = max(peak, c["equity"])
            if peak > 0:
                mdd = max(mdd, 1.0 - c["equity"] / peak)
        return mdd

    results = {}
    for cell, snap_holdings in holdings.items():
        if only and cell not in only:
            continue
        bucket = cell.rsplit("__", 1)[1]
        exec_h = {}
        for D, names in snap_holdings.items():
            ed = next_day(D)
            if ed:
                exec_h[ed] = [m for m in names if m in bars]
        snaps = {d: n for d, n in exec_h.items() if n}

        def mk(sh_=exec_h):
            def sel(day, u, tr):
                names = [m for m in sh_.get(day, []) if m in tr and tr.tail(m, 1)]
                return {m: 0.99 / len(names) for m in names} if names else {}
            return sel
        res = simulate(StrategySpec(cell, mk()), snaps, bars, initial_cash=10_000.0,
                       cost=COSTS[bucket], start=gte, end=lte)
        st = res["stats"]
        results[cell] = {"stats": st, "bucket": bucket, "maxdd": round(maxdd(res["curve"]), 4),
                         "beats_benchmark": st["cagr"] > BENCH[bucket]}
    os.makedirs(OUT, exist_ok=True)
    if is_screen:
        sharpes = [v["stats"]["sharpe"] for v in results.values()]
        mean_s = sum(sharpes) / len(sharpes)
        var_sr = sum((s - mean_s) ** 2 for s in sharpes) / len(sharpes)
        for cell, v in results.items():
            st = v["stats"]
            dsr = deflated_sharpe_ratio(st["sharpe"], n_trials=32, n_obs=st["n_obs"],
                                        skew=st["skew"], kurtosis=st["kurtosis"], variance_of_sr=var_sr)
            v["dsr"] = dsr
            v["stage1_survivor"] = dsr >= 0.95 and v["beats_benchmark"]
            print(f"{cell}: CAGR {st['cagr']:+.2%} shrp {st['sharpe']:.2f} DSR {dsr:.3f} "
                  f"mDD {v['maxdd']:.0%} {'** SURV' if v['stage1_survivor'] else ''}", flush=True)
        print(f"\nvar_sr {var_sr:.5f} emax(32) {expected_max_sharpe(32, var_sr):.3f}")
        with open(f"{OUT}/insample_results.json", "w") as f:
            json.dump({"results": results, "variance_of_sr": var_sr,
                       "cliff": parameter_cliff_report([
                           {"params": {"signal": c.split("__")[0], "n": int(c.split("__")[1][1:]),
                                       "bucket": c.rsplit("__", 1)[1]},
                            "metric": results[c]["stats"]["sharpe"], "cell": c} for c in results])},
                      f, indent=1, default=str)
        print("\nSTAGE-1 SURVIVORS:", [c for c in results if results[c]["stage1_survivor"]] or "NONE")
    else:
        for cell, v in results.items():
            st = v["stats"]
            psr = probabilistic_sharpe_ratio(st["sharpe"], 0.0, n_obs=st["n_obs"], skew=st["skew"], kurtosis=st["kurtosis"])
            v["psr"] = psr
            v["holdout_pass"] = psr >= 0.95 and v["beats_benchmark"]
            print(f"{cell}: HO CAGR {st['cagr']:+.2%} shrp {st['sharpe']:.2f} PSR {psr:.3f} "
                  f"mDD {v['maxdd']:.0%} bench {BENCH[v['bucket']]:.1%} {'** PASS' if v['holdout_pass'] else 'fail'}", flush=True)
        tag = "holdout" if slip == 1.0 else f"holdout_{slip:g}x"
        with open(f"{OUT}/{tag}_results.json", "w") as f:
            json.dump({"results": results, "benchmarks_cagr": BENCH, "slip_mult": slip}, f, indent=1, default=str)
        print("\nHOLDOUT PASSERS:", [c for c in results if results[c]["holdout_pass"]] or "NONE")
