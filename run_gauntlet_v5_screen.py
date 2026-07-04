"""gauntlet_v5_newfundamentals phases 2-5. PAPER ONLY.
Usage: python3 run_gauntlet_v5_screen.py {holdings|bars|screen|holdout} SCRATCH [args]

Signals (all pure SF1, datekey point-in-time; direction: high = good):
  cash_op    cash-based operating profitability (Ball et al 2016) = COP/assets
  delta_rnd  abnormal R&D increase (Eberhart-Maxwell-Siddique 2004) = dR&D_ttm/assets
  fund_mom   fundamental momentum (Novy-Marx 2015) = mean(zx(SUE), zx(dROE))
  gross_prof REFERENCE (already supported, gauntlet_v2) = gp_ttm/assets
Grid: 4 signals x {N25,N50} x {LARGE,SMALL} = 16 cells. DSR n_trials=16."""
import bisect, gzip, json, math, os, statistics, sys
from collections import defaultdict
from datetime import date, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PHASE = sys.argv[1]
S = sys.argv[2]
OUT = "docs/data/gauntlet_v5"
SIGS = ["cash_op", "delta_rnd", "fund_mom", "gross_prof"]
CELLS = [(sig, n, b) for sig in SIGS for n in (25, 50) for b in ("LARGE", "SMALL")]


def load_sf1():
    rows = []
    part = 0
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
    """Trailing-4Q sum, or None if fewer than 4 quarters carry the field."""
    vs = [r[k] for r in rs if r.get(k) is not None]
    return sum(vs) if len(vs) == 4 else None


def _sopt(rs, k):
    """Sum of present values (0.0 if none) — for optional lines (sgna/rnd)."""
    return float(sum(r[k] for r in rs if r.get(k) is not None))


def _lvl(rs, k):
    """Latest balance-sheet level in the group (0.0 if absent)."""
    v = rs[-1].get(k)
    return float(v) if v is not None else 0.0


def signals_for(rows, D):
    """Directly-rankable signals + raw fund_mom components (_sue,_droe) for a
    name as of signal date D. Latest 8 ARQ quarters with datekey <= D."""
    usable = [r for r in rows if r["datekey"] <= D]
    if len(usable) < 8:
        return None
    last8 = usable[-8:]
    if last8[-1]["calendardate"] < (date(*map(int, D.split("-"))) -
                                    timedelta(days=400)).isoformat():
        return None  # stale filer
    cur4, prior4 = last8[4:], last8[:4]
    assets = last8[-1].get("assets")
    out = {}
    if not assets or assets <= 0:
        return out
    # --- gross_prof (reference) ---
    gp = _s4(cur4, "gp")
    if gp is not None:
        out["gross_prof"] = gp / assets
    # --- cash_op: (rev - cor - sgna + rnd) - dRec - dInv + dPay + dDefRev, /assets
    rev, cor = _s4(cur4, "revenue"), _s4(cur4, "cor")
    if rev is not None and cor is not None:
        op = rev - cor - _sopt(cur4, "sgna") + _sopt(cur4, "rnd")
        d_rec = _lvl(cur4, "receivables") - _lvl(prior4, "receivables")
        d_inv = _lvl(cur4, "inventory") - _lvl(prior4, "inventory")
        d_pay = _lvl(cur4, "payables") - _lvl(prior4, "payables")
        d_dr = _lvl(cur4, "deferredrev") - _lvl(prior4, "deferredrev")
        cop = op - d_rec - d_inv + d_pay + d_dr
        out["cash_op"] = cop / assets
    # --- delta_rnd: R&D-active names only (rnd_ttm > 0 both periods) ---
    rd_cur, rd_prior = _sopt(cur4, "rnd"), _sopt(prior4, "rnd")
    if rd_cur > 0 and rd_prior > 0:
        out["delta_rnd"] = (rd_cur - rd_prior) / assets
    # --- fund_mom raw components ---
    ni_cur, ni_prior = _s4(cur4, "netinc"), _s4(prior4, "netinc")
    eq_now, eq_prior = last8[-1].get("equity"), prior4[-1].get("equity")
    if (ni_cur is not None and ni_prior is not None and eq_now and eq_now > 0
            and eq_prior and eq_prior > 0):
        out["_droe"] = ni_cur / eq_now - ni_prior / eq_prior
    eps_rows = [r for r in usable[-12:] if r.get("eps") is not None]
    if len(eps_rows) >= 8:
        diffs = [eps_rows[i]["eps"] - eps_rows[i - 4]["eps"]
                 for i in range(4, len(eps_rows))]
        if len(diffs) >= 4:
            sd = statistics.pstdev(diffs)
            if sd > 0:
                out["_sue"] = diffs[-1] / sd
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


def _zc(vals):
    mu = sum(vals) / len(vals)
    sd = (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5
    return [(v - mu) / sd if sd > 0 else 0.0 for v in vals]


if PHASE == "holdings":
    sf1 = load_sf1()
    window = sys.argv[3] if len(sys.argv) > 3 else "in_sample"
    snaps = quarterly_snapshots(window)
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
        # cross-sectional fund_mom for this snapshot/bucket
        fm = [m for m, v in scored.items() if "_sue" in v and "_droe" in v]
        if fm:
            zs = _zc([scored[m]["_sue"] for m in fm])
            zd = _zc([scored[m]["_droe"] for m in fm])
            for m, a, b_ in zip(fm, zs, zd):
                scored[m]["fund_mom"] = (a + b_) / 2.0
        for sig, n, b in CELLS:
            if b != bucket:
                continue
            cand = [(v[sig], m) for m, v in scored.items() if sig in v]
            coverage[f"{sig}__N{n}__{b}"].append(len(cand) / max(1, len(snap["members"])))
            cand.sort(reverse=True)  # all signals: high = good
            holdings[f"{sig}__N{n}__{b}"][D] = [m for _, m in cand[:n]]
    report = {"coverage_mean": {c: sum(v) / len(v) for c, v in coverage.items()},
              "coverage_min": {c: min(v) for c, v in coverage.items()},
              "n_snapshots": {c: len(v) for c, v in coverage.items()}}
    with gzip.open(f"{S}/holdings_{window}.json.gz", "wt") as f:
        json.dump(holdings, f)
    with open(f"{S}/coverage_{window}.json", "w") as f:
        json.dump(report, f, indent=1)
    union = sorted({m for cell in holdings.values() for names in cell.values() for m in names})
    with open(f"{S}/held_union_{window}.json", "w") as f:
        json.dump(union, f)
    print(json.dumps({c: round(report["coverage_mean"][c], 2)
                      for c in sorted(report["coverage_mean"])}, indent=1))
    print("held union:", len(union), "names")

elif PHASE == "bars":
    import shared.sharadar as sh
    import time as _time
    window = sys.argv[3] if len(sys.argv) > 3 else "in_sample"
    gte = sys.argv[4] if len(sys.argv) > 4 else "2000-04-01"
    lte = sys.argv[5] if len(sys.argv) > 5 else "2016-03-31"
    union = json.load(open(f"{S}/held_union_{window}.json"))
    bars, CH = {}, 30

    def _fetch(chunk, attempts=4):
        for a in range(attempts):
            try:
                return sh._datatable("SEP", ticker=",".join(chunk), **{
                    "date.gte": gte, "date.lte": lte,
                    "qopts.columns": "ticker,date,close,closeadj",
                    "qopts.per_page": 10000})
            except Exception:
                if a == attempts - 1:
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
            print(f"bars {min(i + CH, len(union))}/{len(union)}", flush=True)
    for t in bars:
        bars[t].sort(key=lambda b: b["date"])
    with gzip.open(f"{S}/bars_{window}.json.gz", "wt") as f:
        json.dump(bars, f)
    print(f"DONE bars for {len(bars)} names")

elif PHASE in ("screen", "holdout"):
    from shared.gauntlet import (CostModel, StrategySpec, simulate,
                                 expected_max_sharpe, deflated_sharpe_ratio,
                                 probabilistic_sharpe_ratio, parameter_cliff_report)
    is_screen = PHASE == "screen"
    window = "in_sample" if is_screen else "holdout"
    gte, lte = (("2000-06-01", "2015-12-31") if is_screen
                else ("2016-01-01", "2025-12-31"))
    # frozen v1 same-universe EW benchmarks (reused across v2/v3/v5)
    BENCH = ({"LARGE": 0.0551, "SMALL": 0.0679} if is_screen
             else {"LARGE": 0.1143, "SMALL": 0.0950})
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else None
    slip = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    COSTS = {"LARGE": CostModel(0.0, 5.0 * slip, 25.0),
             "SMALL": CostModel(0.0, 25.0 * slip, 25.0)}
    with gzip.open(f"{S}/holdings_{window}.json.gz", "rt") as f:
        holdings = json.load(f)
    with gzip.open(f"{S}/bars_{window}.json.gz", "rt") as f:
        bars = json.load(f)
    all_days = sorted({b["date"] for bl in bars.values() for b in bl})

    def next_day(D):
        i = bisect.bisect_right(all_days, D)
        return all_days[i] if i < len(all_days) else None

    results = {}
    for cell, snap_holdings in holdings.items():
        if only and cell not in only:
            continue
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
                return {m: 0.99 / len(names) for m in names} if names else {}
            return select

        res = simulate(StrategySpec(cell, mk_select()), snaps, bars,
                       initial_cash=10_000.0, cost=COSTS[bucket], start=gte, end=lte)
        st = res["stats"]
        results[cell] = {"stats": st, "bucket": bucket,
                         "beats_benchmark": st["cagr"] > BENCH[bucket]}
    os.makedirs(OUT, exist_ok=True)
    if is_screen:
        sharpes = [v["stats"]["sharpe"] for v in results.values()]
        mean_s = sum(sharpes) / len(sharpes)
        var_sr = sum((s - mean_s) ** 2 for s in sharpes) / len(sharpes)
        for cell, v in results.items():
            st = v["stats"]
            dsr = deflated_sharpe_ratio(st["sharpe"], n_trials=16, n_obs=st["n_obs"],
                                        skew=st["skew"], kurtosis=st["kurtosis"],
                                        variance_of_sr=var_sr)
            v["dsr"] = dsr
            v["stage1_survivor"] = dsr >= 0.95 and v["beats_benchmark"]
            print(f"{cell}: CAGR {st['cagr']:+.2%} shrp {st['sharpe']:.2f} "
                  f"DSR {dsr:.3f} beats {v['beats_benchmark']} "
                  f"{'** SURVIVOR' if v['stage1_survivor'] else ''}", flush=True)
        print(f"\nvariance_of_sr {var_sr:.5f}  emax_sharpe(16) {expected_max_sharpe(16, var_sr):.3f}")
        cliff = parameter_cliff_report([
            {"params": {"signal": c.split("__")[0], "n": int(c.split("__")[1][1:]),
                        "bucket": c.rsplit("__", 1)[1]},
             "metric": results[c]["stats"]["sharpe"], "cell": c} for c in results])
        with open(f"{OUT}/insample_results.json", "w") as f:
            json.dump({"results": results, "cliff": cliff, "benchmarks_cagr": BENCH,
                       "variance_of_sr": var_sr,
                       "expected_max_sharpe_16": expected_max_sharpe(16, var_sr)},
                      f, indent=1, default=str)
        surv = [c for c in results if results[c]["stage1_survivor"]]
        print("\nSTAGE-1 SURVIVORS:", surv or "NONE")
    else:
        for cell, v in results.items():
            st = v["stats"]
            psr = probabilistic_sharpe_ratio(st["sharpe"], 0.0, n_obs=st["n_obs"],
                                             skew=st["skew"], kurtosis=st["kurtosis"])
            v["psr"] = psr
            v["holdout_pass"] = psr >= 0.95 and v["beats_benchmark"]
            print(f"{cell}: HO CAGR {st['cagr']:+.2%} shrp {st['sharpe']:.2f} "
                  f"PSR {psr:.3f} bench {BENCH[v['bucket']]:.2%} "
                  f"{'** PASS' if v['holdout_pass'] else 'fail'}", flush=True)
        tag = "holdout" if slip == 1.0 else f"holdout_{slip:g}x"
        with open(f"{OUT}/{tag}_results.json", "w") as f:
            json.dump({"results": results, "benchmarks_cagr": BENCH, "slip_mult": slip},
                      f, indent=1, default=str)
        print("\nHOLDOUT PASSERS:", [c for c in results if results[c]["holdout_pass"]] or "NONE")
