"""The Gauntlet — prereg section 9.6 robustness disclosure.

Reruns ONLY the five holdout cells at 2x slippage (LARGE 10 bps, SMALL
50 bps) on both windows. This is a cost-sensitivity DISCLOSURE mandated
by the prereg, not a pass bar and not a re-cut: the cells, windows, and
every other parameter are unchanged, and the factory verdict is already
settled by run_gauntlet_holdout.py.
"""
from __future__ import annotations

import argparse
import gzip
import json

import numpy as np

from shared.gauntlet import CostModel
from shared.gauntlet_fast import carry_forward, equal_weights, run_cell, volatility_scores
from run_gauntlet_screen import INITIAL_CASH, load_sep_panel

DOUBLED = {"LARGE": CostModel(0.0, 10.0, 25.0), "SMALL": CostModel(0.0, 50.0, 25.0)}
WINDOWS = {
    "IS": {"sep": "sep_is.zip", "universes": "universes_is.json.gz",
           "panel": ("1998-12-01", "2016-01-31"),
           "exec_months": ("2000-07", "2015-12"), "last_day": "2015-12-31"},
    "HO": {"sep": "sep_ho.zip", "universes": "universes_ho.json.gz",
           "panel": ("2014-10-01", "2026-01-31"),
           "exec_months": ("2016-01", "2025-12"), "last_day": "2025-12-31"},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    args = ap.parse_args()
    S = args.scratch

    screen = json.load(open(f"{S}/screen_results.json"))
    survivors = sorted(((v["dsr"], c) for c, v in screen.items()
                        if v["stage1_survivor"]), reverse=True)
    cells = [c for _, c in survivors[:5]]

    all_days = json.load(open(f"{S}/trading_days.json"))
    sig_exec = json.load(open(f"{S}/signal_exec_dates.json"))
    out = {}
    for wname, W in WINDOWS.items():
        days = [d for d in all_days if W["panel"][0] <= d <= W["panel"][1]]
        pairs = [p for p in sig_exec
                 if W["exec_months"][0] <= p["execution"][:7] <= W["exec_months"][1]]
        universes = json.load(gzip.open(f"{S}/{W['universes']}", "rt"))["universes"]
        panel = load_sep_panel(f"{S}/{W['sep']}", days)
        prices = carry_forward(panel.closeadj)
        signal_dates = [p["signal"] for p in pairs]
        vol_scores = {w: {d: volatility_scores(panel.closeadj, panel.day_index[d], w)
                          for d in signal_dates} for w in (63, 126)}
        start_idx = panel.day_index[pairs[0]["execution"]]
        end_idx = panel.day_index[W["last_day"]]
        for cell_id in cells:
            sig, n_part, bucket = cell_id.split("__")
            window, N = int(sig.split("_L")[1]), int(n_part[1:])
            schedule = []
            for p in pairs:
                d = p["signal"]
                scores = vol_scores[window][d]
                scored = sorted(
                    (float(scores[panel.ticker_index[nm]]), nm)
                    for nm in universes[d][bucket]
                    if not np.isnan(scores[panel.ticker_index[nm]]))
                schedule.append((panel.day_index[p["execution"]],
                                 equal_weights(panel, [nm for _, nm in scored[:N]])))
            r = run_cell(panel, schedule, initial_cash=INITIAL_CASH,
                         cost=DOUBLED[bucket], start_idx=start_idx,
                         end_idx=end_idx, prices=prices)
            st = r["stats"]
            out.setdefault(cell_id, {})[wname] = {
                "cagr_2x": st["cagr"], "sharpe_2x": st["sharpe"]}
            print(f"{wname} {cell_id} @2x slippage: "
                  f"cagr={st['cagr']:.2%} sharpe={st['sharpe']:.2f}")
    json.dump(out, open(f"{S}/robustness_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
