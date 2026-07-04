"""The Gauntlet phase (c) — the 90-cell in-sample screen.

Executes docs/lab_prereg_gauntlet_v1.md EXACTLY: universes (section 3),
execution model (section 4), the 90-cell grid (section 5), in-sample
window (section 6), stage-1 pass bar inputs (section 7). Anything this
script does that the prereg does not specify is an operational default,
and each one is emitted into the run manifest so the results doc can
disclose it:

- initial capital $10,000 per cell (min_ticket $25 then binds only on
  sub-0.25% rebalance deltas);
- benchmarks run with min_ticket=0 (a 500-name equal-weight benchmark
  at $10k has $20 tickets; the benchmark is a measuring stick, not a
  tradable cell);
- if fewer than N names are eligible for a cell on a signal date, the
  cell holds all eligible names at 1/n_eligible (fully invested);
- ranking ties break by ticker (deterministic).

Inputs (produced by the session's pull scripts from Sharadar):
  --scratch DIR   with trading_days.json, signal_exec_dates.json,
                  daily_mcap_is.json.gz, sep_is.zip
Outputs (written back to DIR):
  universes_is.json.gz     per signal date: LARGE/SMALL member lists
  screen_results.json      per cell: stats, DSR inputs, curve tail
  screen_manifest.json     frozen params + operational defaults + coverage

PAPER ONLY. No broker calls, no live state. Reads Sharadar exports from
disk; makes no network requests at all.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import zipfile

import numpy as np

from shared.gauntlet import CostModel, deflated_sharpe_ratio
from shared.gauntlet_fast import (
    Panel,
    carry_forward,
    equal_weights,
    median_dollar_volume,
    momentum_scores,
    run_cell,
    volatility_scores,
)

IS_FIRST_EXEC_MONTH = "2000-07"
IS_LAST_EXEC_MONTH = "2015-12"
PANEL_START = "1998-12-01"
PANEL_END = "2016-01-31"
INITIAL_CASH = 10_000.0
COSTS = {"LARGE": CostModel(0.0, 5.0, 25.0), "SMALL": CostModel(0.0, 25.0, 25.0)}
BENCH_COSTS = {"LARGE": CostModel(0.0, 5.0, 0.0), "SMALL": CostModel(0.0, 25.0, 0.0)}
PRICE_FLOOR = 3.0
DV_FLOOR = 1_000_000.0
DV_WINDOW = 21
LARGE_RANKS = (1, 500)
SMALL_RANKS = (501, 2000)
N_TRIALS = 90

SIGNALS = (
    [(f"mom_L{L}_S{S}", "momentum", {"lookback": L, "skip": S})
     for L in (21, 63, 126, 252) for S in (0, 21)]
    + [(f"rev_L{L}", "reversal", {"lookback": L}) for L in (5, 10, 21)]
    + [(f"vol_L{L}", "lowvol", {"window": L}) for L in (63, 126)]
    + [("size", "size", {}), ("neglect", "neglect", {})]
)
PORTFOLIO_NS = (10, 25, 50)
BUCKETS = ("LARGE", "SMALL")


def load_sep_panel(zip_path: str, trading_days: list[str]) -> Panel:
    """Stream the SEP export zip into a Panel (float32 matrices)."""
    day_index = {d: i for i, d in enumerate(trading_days)}
    tickers: set[str] = set()
    with zipfile.ZipFile(zip_path) as z:
        inner = z.namelist()[0]
        with z.open(inner) as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
            header = next(reader)
            ti = header.index("ticker")
            for row in reader:
                tickers.add(row[ti])
    ticker_list = sorted(tickers)
    ticker_index = {t: j for j, t in enumerate(ticker_list)}
    shape = (len(trading_days), len(ticker_list))
    closeadj = np.full(shape, np.nan, dtype=np.float32)
    close = np.full(shape, np.nan, dtype=np.float32)
    volume = np.full(shape, np.nan, dtype=np.float32)
    n_rows = n_skipped = 0
    with zipfile.ZipFile(zip_path) as z:
        inner = z.namelist()[0]
        with z.open(inner) as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
            header = next(reader)
            ti, di = header.index("ticker"), header.index("date")
            ci, cai, vi = (header.index("close"), header.index("closeadj"),
                           header.index("volume"))
            for row in reader:
                i = day_index.get(row[di])
                if i is None:
                    n_skipped += 1
                    continue
                j = ticker_index[row[ti]]
                try:
                    closeadj[i, j] = float(row[cai])
                    close[i, j] = float(row[ci])
                    volume[i, j] = float(row[vi])
                except ValueError:
                    n_skipped += 1
                    continue
                n_rows += 1
    print(f"panel: {n_rows:,} rows, {len(ticker_list):,} tickers, "
          f"{n_skipped:,} skipped (off-calendar or unparsable)")
    return Panel(trading_days, ticker_list,
                 closeadj.astype(np.float64), close.astype(np.float64),
                 volume.astype(np.float64))


def build_universes(panel: Panel, mcap_by_date: dict, signal_dates: list[str]):
    """Prereg section 3. Returns (universes, coverage) where universes =
    {signal_date: {"LARGE": [...], "SMALL": [...]}}."""
    dv = panel.dollar_volume()
    universes: dict[str, dict[str, list[str]]] = {}
    coverage: dict[str, dict] = {}
    for d in signal_dates:
        t = panel.day_index[d]
        mcaps = mcap_by_date[d]
        med_dv = median_dollar_volume(dv, t, DV_WINDOW)
        eligible: list[tuple[float, str]] = []
        n_no_sep = n_price = n_dv = 0
        for name, mc in mcaps.items():
            j = panel.ticker_index.get(name)
            if j is None or np.isnan(panel.close[t, j]):
                n_no_sep += 1
                continue
            if panel.close[t, j] < PRICE_FLOOR:
                n_price += 1
                continue
            if np.isnan(med_dv[j]) or med_dv[j] < DV_FLOOR:
                n_dv += 1
                continue
            eligible.append((-float(mc), name))
        eligible.sort()
        ranked = [name for _, name in eligible]
        universes[d] = {
            "LARGE": ranked[LARGE_RANKS[0] - 1: LARGE_RANKS[1]],
            "SMALL": ranked[SMALL_RANKS[0] - 1: SMALL_RANKS[1]],
        }
        coverage[d] = {"daily_names": len(mcaps), "no_sep_bar": n_no_sep,
                       "price_floor": n_price, "dv_floor": n_dv,
                       "eligible": len(ranked)}
    return universes, coverage


def signal_scores(sig_kind: str, params: dict, panel: Panel,
                  raw_closeadj: np.ndarray, dv: np.ndarray,
                  mcaps: dict, t: int) -> tuple[np.ndarray, bool]:
    """(scores, ascending). NaN = ineligible for this cell today.

    Signals see RAW closeadj (NaN where no bar) — the prereg's
    full-window eligibility rule must not be satisfied by carry-forward
    fills; only execution pricing uses carried prices.
    """
    if sig_kind == "momentum":
        return momentum_scores(raw_closeadj, t, params["lookback"], params["skip"]), False
    if sig_kind == "reversal":
        return momentum_scores(raw_closeadj, t, params["lookback"], 0), True
    if sig_kind == "lowvol":
        return volatility_scores(raw_closeadj, t, params["window"]), True
    if sig_kind == "size":
        scores = np.full(len(panel.tickers), np.nan)
        for name, mc in mcaps.items():
            j = panel.ticker_index.get(name)
            if j is not None:
                scores[j] = float(mc)
        return scores, True
    if sig_kind == "neglect":
        return median_dollar_volume(dv, t, DV_WINDOW), True
    raise ValueError(sig_kind)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    args = ap.parse_args()
    S = args.scratch

    trading_days = json.load(open(f"{S}/trading_days.json"))
    trading_days = [d for d in trading_days if PANEL_START <= d <= PANEL_END]
    sig_exec = json.load(open(f"{S}/signal_exec_dates.json"))
    pairs = [p for p in sig_exec
             if IS_FIRST_EXEC_MONTH <= p["execution"][:7] <= IS_LAST_EXEC_MONTH]
    assert len(pairs) == 186, f"expected 186 IS pairs, got {len(pairs)}"
    mcap_by_date = json.load(gzip.open(f"{S}/daily_mcap_is.json.gz", "rt"))

    panel = load_sep_panel(f"{S}/sep_is.zip", trading_days)
    prices = carry_forward(panel.closeadj)
    dv = panel.dollar_volume()

    signal_dates = [p["signal"] for p in pairs]
    universes, coverage = build_universes(panel, mcap_by_date, signal_dates)
    json.dump({"universes": universes, "coverage": coverage},
              gzip.open(f"{S}/universes_is.json.gz", "wt"))
    sizes_l = [len(universes[d]["LARGE"]) for d in signal_dates]
    sizes_s = [len(universes[d]["SMALL"]) for d in signal_dates]
    print(f"universes: LARGE {min(sizes_l)}-{max(sizes_l)}, "
          f"SMALL {min(sizes_s)}-{max(sizes_s)} names/date")

    start_idx = panel.day_index[pairs[0]["execution"]]
    end_idx = panel.day_index["2015-12-31"]

    # Pre-rank each (signal, bucket) once; cells share the ordering.
    ranked_by_cell: dict[tuple[str, str], dict[str, list[str]]] = {}
    for sig_name, kind, params in SIGNALS:
        for d in signal_dates:
            t = panel.day_index[d]
            scores, ascending = signal_scores(kind, params, panel,
                                               panel.closeadj, dv,
                                               mcap_by_date[d], t)
            for bucket in BUCKETS:
                members = universes[d][bucket]
                scored = []
                for name in members:
                    v = scores[panel.ticker_index[name]]
                    if not np.isnan(v):
                        scored.append((float(v) if ascending else -float(v), name))
                scored.sort()
                ranked_by_cell.setdefault((sig_name, bucket), {})[d] = \
                    [name for _, name in scored]
        print(f"ranked {sig_name}")

    results = {}
    bench_curves = {}
    for bucket in BUCKETS:
        schedule = [(panel.day_index[p["execution"]],
                     equal_weights(panel, universes[p["signal"]][bucket]))
                    for p in pairs]
        r = run_cell(panel, schedule, initial_cash=INITIAL_CASH,
                     cost=BENCH_COSTS[bucket], start_idx=start_idx,
                     end_idx=end_idx, prices=prices)
        bench_curves[bucket] = r
        print(f"benchmark {bucket}: {r['stats']}")

    for sig_name, kind, params in SIGNALS:
        for bucket in BUCKETS:
            ranked = ranked_by_cell[(sig_name, bucket)]
            for N in PORTFOLIO_NS:
                cell_id = f"{sig_name}__N{N}__{bucket}"
                schedule = []
                short_dates = 0
                for p in pairs:
                    names = ranked[p["signal"]][:N]
                    if len(names) < N:
                        short_dates += 1
                    schedule.append((panel.day_index[p["execution"]],
                                     equal_weights(panel, names)))
                r = run_cell(panel, schedule, initial_cash=INITIAL_CASH,
                             cost=COSTS[bucket], start_idx=start_idx,
                             end_idx=end_idx, prices=prices)
                results[cell_id] = {
                    "stats": r["stats"],
                    "short_dates": short_dates,
                    "final_equity": r["curve"][-1]["equity"],
                }
                print(f"{cell_id}: sharpe={r['stats']['sharpe']:.2f} "
                      f"cagr={r['stats']['cagr']:.2%} short={short_dates}")

    # DSR per prereg: n_trials=90, variance_of_sr = cross-sectional
    # variance of the 90 IS Sharpes.
    sharpes = [v["stats"]["sharpe"] for v in results.values()]
    var_sr = float(np.var(sharpes))
    for cell_id, v in results.items():
        st = v["stats"]
        v["dsr"] = deflated_sharpe_ratio(
            st["sharpe"], n_trials=N_TRIALS, n_obs=st["n_obs"],
            skew=st["skew"], kurtosis=st["kurtosis"], variance_of_sr=var_sr)
        bucket = cell_id.rsplit("__", 1)[1]
        v["beats_benchmark"] = st["cagr"] > bench_curves[bucket]["stats"]["cagr"]
        v["stage1_survivor"] = bool(v["dsr"] >= 0.95 and v["beats_benchmark"])

    manifest = {
        "prereg": "docs/lab_prereg_gauntlet_v1.md",
        "n_cells": len(results),
        "n_trials": N_TRIALS,
        "variance_of_sr": var_sr,
        "initial_cash": INITIAL_CASH,
        "operational_defaults": [
            "initial capital $10,000/cell",
            "benchmarks min_ticket=0",
            "fewer than N eligible -> hold all eligible at 1/n",
            "ranking ties break by ticker",
        ],
        "benchmarks": {b: bench_curves[b]["stats"] for b in BUCKETS},
    }
    json.dump(results, open(f"{S}/screen_results.json", "w"), indent=1)
    json.dump(manifest, open(f"{S}/screen_manifest.json", "w"), indent=1)

    survivors = sorted(((v["dsr"], c) for c, v in results.items()
                        if v["stage1_survivor"]), reverse=True)
    print("\nstage-1 survivors (DSR >= 0.95 AND beats benchmark):")
    for dsr, c in survivors:
        print(f"  {c}: DSR={dsr:.4f}")
    print(f"\ntop-5 advance to holdout: {[c for _, c in survivors[:5]]}")


if __name__ == "__main__":
    main()
