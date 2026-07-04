"""The Gauntlet phase (d) — the ONE holdout pass for stage-1 survivors.

Runs EXACTLY the five cells named by the in-sample screen (prereg
docs/lab_prereg_gauntlet_v1.md sections 6-7) on the holdout window
(executions 2016-01 .. 2025-12), plus the two bucket benchmarks. No
other cell touches this data, ever. Pass bar per prereg: holdout PSR
vs 0 >= 0.95 AND holdout net CAGR > matching benchmark's holdout CAGR.

Inputs in --scratch: trading_days.json, signal_exec_dates.json,
daily_mcap_ho.json.gz, sep_ho.zip, screen_results.json (for the
survivor list — read, never recomputed).
Outputs: holdout_results.json, universes_ho.json.gz.

PAPER ONLY; reads staged exports from disk, no network.
"""
from __future__ import annotations

import argparse
import gzip
import json

import numpy as np

from shared.gauntlet import probabilistic_sharpe_ratio
from shared.gauntlet_fast import carry_forward, equal_weights, run_cell, volatility_scores
from run_gauntlet_screen import (
    BENCH_COSTS,
    BUCKETS,
    COSTS,
    INITIAL_CASH,
    build_universes,
    load_sep_panel,
)

HO_FIRST_EXEC_MONTH = "2016-01"
HO_LAST_EXEC_MONTH = "2025-12"
HO_PANEL_START = "2014-10-01"
HO_PANEL_END = "2026-01-31"
TOP_K = 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    args = ap.parse_args()
    S = args.scratch

    screen = json.load(open(f"{S}/screen_results.json"))
    survivors = sorted(((v["dsr"], c) for c, v in screen.items()
                        if v["stage1_survivor"]), reverse=True)
    cells = [c for _, c in survivors[:TOP_K]]
    print("holdout cells (frozen by stage 1):", cells)
    for c in cells:
        sig = c.split("__")[0]
        assert sig in ("vol_L63", "vol_L126"), (
            f"{c}: this runner only implements the signals the actual "
            "survivors need — extend deliberately if the survivor set changes")

    trading_days = json.load(open(f"{S}/trading_days.json"))
    trading_days = [d for d in trading_days if HO_PANEL_START <= d <= HO_PANEL_END]
    sig_exec = json.load(open(f"{S}/signal_exec_dates.json"))
    pairs = [p for p in sig_exec
             if HO_FIRST_EXEC_MONTH <= p["execution"][:7] <= HO_LAST_EXEC_MONTH]
    assert len(pairs) == 120, f"expected 120 HO pairs, got {len(pairs)}"
    mcap_by_date = json.load(gzip.open(f"{S}/daily_mcap_ho.json.gz", "rt"))

    panel = load_sep_panel(f"{S}/sep_ho.zip", trading_days)
    prices = carry_forward(panel.closeadj)

    signal_dates = [p["signal"] for p in pairs]
    universes, coverage = build_universes(panel, mcap_by_date, signal_dates)
    json.dump({"universes": universes, "coverage": coverage},
              gzip.open(f"{S}/universes_ho.json.gz", "wt"))
    sizes = {b: [len(universes[d][b]) for d in signal_dates] for b in BUCKETS}
    for b in BUCKETS:
        print(f"universes {b}: {min(sizes[b])}-{max(sizes[b])} names/date")

    start_idx = panel.day_index[pairs[0]["execution"]]
    end_idx = panel.day_index["2025-12-31"]

    bench = {}
    for bucket in BUCKETS:
        schedule = [(panel.day_index[p["execution"]],
                     equal_weights(panel, universes[p["signal"]][bucket]))
                    for p in pairs]
        r = run_cell(panel, schedule, initial_cash=INITIAL_CASH,
                     cost=BENCH_COSTS[bucket], start_idx=start_idx,
                     end_idx=end_idx, prices=prices)
        bench[bucket] = r["stats"]
        print(f"benchmark {bucket}: cagr={r['stats']['cagr']:.2%} "
              f"sharpe={r['stats']['sharpe']:.2f}")

    vol_scores = {}
    for window in (63, 126):
        vol_scores[window] = {
            d: volatility_scores(panel.closeadj, panel.day_index[d], window)
            for d in signal_dates}

    results = {}
    for cell_id in cells:
        sig, n_part, bucket = cell_id.split("__")
        window = int(sig.split("_L")[1])
        N = int(n_part[1:])
        schedule = []
        short_dates = 0
        for p in pairs:
            d = p["signal"]
            scores = vol_scores[window][d]
            scored = []
            for name in universes[d][bucket]:
                v = scores[panel.ticker_index[name]]
                if not np.isnan(v):
                    scored.append((float(v), name))
            scored.sort()
            names = [name for _, name in scored[:N]]
            if len(names) < N:
                short_dates += 1
            schedule.append((panel.day_index[p["execution"]],
                             equal_weights(panel, names)))
        r = run_cell(panel, schedule, initial_cash=INITIAL_CASH,
                     cost=COSTS[bucket], start_idx=start_idx,
                     end_idx=end_idx, prices=prices)
        st = r["stats"]
        psr = probabilistic_sharpe_ratio(st["sharpe"], 0.0, st["n_obs"],
                                          skew=st["skew"], kurtosis=st["kurtosis"])
        beats = st["cagr"] > bench[bucket]["cagr"]
        results[cell_id] = {
            "stats": st, "psr_vs_zero": psr, "beats_benchmark": beats,
            "holdout_pass": bool(psr >= 0.95 and beats),
            "short_dates": short_dates,
            "final_equity": r["curve"][-1]["equity"],
        }
        print(f"{cell_id}: sharpe={st['sharpe']:.2f} cagr={st['cagr']:.2%} "
              f"maxDD={st['max_drawdown']:.1%} PSR={psr:.4f} beats={beats} "
              f"PASS={results[cell_id]['holdout_pass']}")

    out = {"cells": results, "benchmarks": bench,
           "prereg": "docs/lab_prereg_gauntlet_v1.md"}
    json.dump(out, open(f"{S}/holdout_results.json", "w"), indent=1)
    passers = [c for c, v in results.items() if v["holdout_pass"]]
    print("\nholdout passers:", passers or "NONE — factory refuted")


if __name__ == "__main__":
    main()
