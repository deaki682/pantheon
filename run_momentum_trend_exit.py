"""Lab hypothesis #92 — momentum_trend_exit_largecap, the one test.

Executes docs/lab_prereg_momentum_trend_exit_largecap.md: Delphi's
shipped mechanics (with the delisting-exit fix) on a point-in-time
top-119 large-cap universe, executions 2000-07-03..2021-06-30, net of
5 bps/side, vs SPY and vs the quarterly equal-weight-119. One run.
Reads staged Sharadar data from --scratch; resolve_ticker is the only
network access (rename resolution). PAPER ONLY.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import math
import zipfile

import numpy as np

from delphi.backtest import BacktestConfig, run_backtest
from shared.gauntlet import CostModel
from shared.gauntlet_fast import build_panel, equal_weights, run_cell

START = "2000-07-03"
END = "2021-06-30"
TOP_N = 119
COST_BPS = 5.0
COMMON = {"Domestic Common Stock", "Domestic Common Stock Primary Class",
          "Domestic Common Stock Secondary Class"}


def quarter_end_dates(mcap_is: dict, mcap_ho: dict) -> list[str]:
    """84 quarter-end signal dates 2000-06-30..2021-03-31 from the
    month-end house caches (last trading day of Mar/Jun/Sep/Dec)."""
    all_dates = sorted(set(mcap_is) | set(mcap_ho))
    qes = [d for d in all_dates if d[5:7] in ("03", "06", "09", "12")]
    qes = [d for d in qes if "2000-06-30" <= d <= "2021-03-31"]
    return qes


def build_pit_lists(S: str) -> tuple[dict[str, list[str]], list[str]]:
    cats = json.load(gzip.open(f"{S}/ticker_categories.json.gz", "rt"))
    mcap_is = json.load(gzip.open(f"{S}/daily_mcap_is.json.gz", "rt"))
    mcap_ho = json.load(gzip.open(f"{S}/daily_mcap_ho.json.gz", "rt"))
    mcap = {**mcap_is, **mcap_ho}
    qes = quarter_end_dates(mcap_is, mcap_ho)
    assert len(qes) == 84, f"expected 84 quarter-ends, got {len(qes)}"
    lists = {}
    for d in qes:
        pool = [(m, t) for t, m in mcap[d].items() if cats.get(t) in COMMON]
        pool.sort(reverse=True)
        lists[d] = [t for _, t in pool[:TOP_N]]
    return lists, qes


def resolve_renames(union: set[str], loaded: set[str], pit: dict) -> dict[str, str]:
    """Map zero-bar tickers to Sharadar final tickers (network)."""
    from shared.sharadar import resolve_ticker
    aliases: dict[str, str] = {}
    unresolved: list[str] = []
    for t in sorted(union - loaded):
        as_of = next((d for d, names in sorted(pit.items()) if t in names), None)
        try:
            r = resolve_ticker(t, as_of=as_of)
            final = r["ticker"] if isinstance(r, dict) else str(r)
            if final and final != t:
                aliases[t] = final
            else:
                unresolved.append(t)
        except Exception:
            unresolved.append(t)
    print(f"renames resolved: {len(aliases)} {dict(list(aliases.items())[:12])}")
    print(f"unresolved (disclosed): {len(unresolved)} {unresolved[:15]}")
    return aliases


def load_bars(S: str, needed: set[str]) -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = {t: {} for t in needed}
    for zname in ("sep_is.zip", "sep_ho.zip"):
        with zipfile.ZipFile(f"{S}/{zname}") as z:
            with z.open(z.namelist()[0]) as f:
                reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
                header = next(reader)
                ti, di, cai = (header.index("ticker"), header.index("date"),
                               header.index("closeadj"))
                for row in reader:
                    t = row[ti]
                    if t in out and "2000-01-01" <= row[di] <= END:
                        try:
                            out[t][row[di]] = {"close": float(row[cai])}
                        except ValueError:
                            pass
    for r in json.load(gzip.open(f"{S}/spy_sfp_2000_2021.json.gz", "rt")):
        if r.get("closeadj") is not None:
            d = r["date"][:10]
            if d <= END:
                out.setdefault("SPY", {})[d] = {"close": float(r["closeadj"])}
    return out


def monthly_excess_t(curve: list[dict]) -> tuple[float, float, int]:
    """Mean and t-stat of calendar-month strategy-minus-SPY returns."""
    by_month: dict[str, list[dict]] = {}
    for p in curve:
        by_month.setdefault(p["date"][:7], []).append(p)
    months = sorted(by_month)
    ex = []
    prev = None
    for m in months:
        last = by_month[m][-1]
        if prev is not None and prev["equity"] > 0 and prev["spy_price"] > 0:
            r_s = last["equity"] / prev["equity"] - 1.0
            r_b = last["spy_price"] / prev["spy_price"] - 1.0
            ex.append(r_s - r_b)
        prev = last
    n = len(ex)
    mean = sum(ex) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in ex) / (n - 1))
    t = mean / (sd / math.sqrt(n))
    return mean, t, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    args = ap.parse_args()
    S = args.scratch

    pit, qes = build_pit_lists(S)
    union = {t for names in pit.values() for t in names} | {"SPY"}
    print(f"84 quarter-ends; ticker union {len(union)}")

    bars = load_bars(S, union)
    loaded = {t for t, v in bars.items() if v}
    aliases = resolve_renames(union, loaded, pit)
    if aliases:
        extra = load_bars(S, set(aliases.values()))
        for old, final in aliases.items():
            if extra.get(final):
                bars[old] = extra[final]
    still_missing = sorted(t for t in union if not bars.get(t))
    print(f"members with no bars after resolution (disclosed): "
          f"{len(still_missing)} {still_missing[:15]}")
    bars = {t: v for t, v in bars.items() if v}

    def universe_fn(day: str) -> list[str]:
        eff = [d for d in qes if d < day]
        return pit[eff[-1]] if eff else pit[qes[0]]

    cfg = BacktestConfig(initial_cash=10_000.0)
    r = run_backtest(bars, cfg, start_date=START, end_date=END,
                     universe_fn=universe_fn)
    perf = r["results"]["performance"]
    gross_total = perf["total_return_pct"] / 100.0
    turnover = r["results"]["trades"]["turnover"]
    cost = turnover * COST_BPS / 10_000.0
    net_total = gross_total - cost / cfg.initial_cash
    years = len(r["equity_curve"]) / 252.0
    net_cagr = (1 + net_total) ** (1 / years) - 1
    spy_total = perf["spy_return_pct"] / 100.0
    spy_cagr = (1 + spy_total) ** (1 / years) - 1
    mean_ex, t_ex, n_ex = monthly_excess_t(r["equity_curve"])

    # EW-119 benchmark: quarterly rebalance, 5 bps, via the gauntlet engine.
    ew_bars = {t: [{"date": d, "close": v["close"], "closeadj": v["close"],
                    "volume": 0.0} for d, v in sorted(bd.items())]
               for t, bd in bars.items() if t != "SPY"}
    panel = build_panel(ew_bars)
    exec_days = {}
    for q in qes:
        nxt = next((d for d in panel.days if d > q), None)
        if nxt and START <= nxt <= END:
            exec_days[nxt] = q
    first_exec = min(exec_days)
    schedule = [(panel.day_index[d], equal_weights(
                    panel, [t for t in pit[q] if t in panel.ticker_index]))
                for d, q in sorted(exec_days.items())]
    ew = run_cell(panel, schedule, initial_cash=10_000.0,
                  cost=CostModel(0.0, COST_BPS, 0.0),
                  start_idx=panel.day_index[first_exec],
                  end_idx=panel.day_index[max(d for d in panel.days if d <= END)])
    ew_stats = ew["stats"]

    out = {
        "prereg": "docs/lab_prereg_momentum_trend_exit_largecap.md",
        "window": {"start": START, "end": END, "years": years},
        "strategy": {
            "gross_total_return": gross_total, "turnover": turnover,
            "cost_first_order": cost, "net_total_return": net_total,
            "net_cagr": net_cagr, "sharpe_gross": perf["sharpe"],
            "max_drawdown_pct": perf["max_drawdown_pct"],
            "trades": r["results"]["trades"]["total"],
            "monthly_excess_vs_spy": {"mean": mean_ex, "t": t_ex, "n": n_ex},
        },
        "spy": {"total_return": spy_total, "cagr": spy_cagr},
        "ew119": {"net_cagr": ew_stats["cagr"], "sharpe": ew_stats["sharpe"],
                   "max_drawdown": ew_stats["max_drawdown"]},
    }
    supported = (net_cagr > spy_cagr and net_cagr > ew_stats["cagr"]
                 and t_ex >= 1.5)
    refuted = (net_cagr <= spy_cagr) or (net_cagr <= ew_stats["cagr"])
    out["verdict"] = ("supported" if supported
                       else "refuted" if refuted else "inconclusive")
    json.dump(out, open(f"{S}/mte_results.json", "w"), indent=1)
    json.dump(r["equity_curve"], open(f"{S}/mte_curve.json", "w"))

    print(f"\nstrategy: gross {gross_total:+.1%}, cost {cost/cfg.initial_cash:.1%}, "
          f"net {net_total:+.1%}, net CAGR {net_cagr:.2%}, "
          f"Sharpe(gross) {perf['sharpe']}, maxDD {perf['max_drawdown_pct']}%")
    print(f"SPY: {spy_total:+.1%} total, CAGR {spy_cagr:.2%}")
    print(f"EW-119: net CAGR {ew_stats['cagr']:.2%}, Sharpe {ew_stats['sharpe']:.2f}, "
          f"maxDD {ew_stats['max_drawdown']:.1%}")
    print(f"monthly excess vs SPY: mean {mean_ex:+.3%}, t={t_ex:.2f}, n={n_ex}")
    print(f"\nVERDICT: {out['verdict']}")


if __name__ == "__main__":
    main()
