"""Backlog #11 — Delphi's frozen ruleset, full window (1999→2026).

Executes docs/lab_prereg_delphi_ruleset_fullwindow.md. Three phases:

  python3 run_delphi_fullwindow.py universes --scratch DIR
  python3 run_delphi_fullwindow.py bars      --scratch DIR
  python3 run_delphi_fullwindow.py cells     --scratch DIR --out docs/data/delphi_fullwindow

Phase `universes` pulls quarter-end DAILY marketcap cross-sections and
builds the PIT top-119 lists (the #4 construction extended: US common
stock categories, top 119 by marketcap, no further dedup). DAILY rows
carry the AS-TRADED ticker; SEP keys history to the FINAL ticker
(shared.sharadar THE LAW), so every member is resolved to its final
ticker via a window-aware sweep of the local TICKERS universe —
unresolvable or ambiguous names are EXCLUDED and disclosed, never
guessed.

Phase `bars` pulls SEP (close, closeadj, volume) for the union of all
resolved members from 1998-12-01, plus SPY from SFP, into gzipped
scratch files. Phase `cells` runs the three preregistered cells + the
EW-universe benchmark through shared.gauntlet.simulate and writes every
preregistered artifact. PAPER ONLY — no sleeve, no broker, no cache
state; results land in docs/, data stays in --scratch.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shared.sharadar as sh
from shared.gauntlet import (
    CostModel, ExitRules, StrategySpec, benchmark_curve, capacity_stats,
    draft_bias_checklist, drawdown_distribution, excess_stats,
    periodic_dates, sharpe_ci, simulate, summarize_by_period, trade_stats,
    turnover_stats,
)

TOP_N = 119
BAR_START = "1998-12-01"
SIM_START = "1999-01-04"
SIM_END = "2026-06-30"
COMMON = {"Domestic Common Stock", "Domestic Common Stock Primary Class",
          "Domestic Common Stock Secondary Class"}
REGIME_BOUNDARIES = ["2003-01-01", "2008-01-01", "2013-01-01",
                     "2020-01-01", "2021-06-01"]
COST = CostModel(commission_bps=0.0, slippage_bps=5.0, min_ticket=25.0)
COST_2X = CostModel(commission_bps=0.0, slippage_bps=10.0, min_ticket=25.0)
BENCH_COST = CostModel(commission_bps=0.0, slippage_bps=5.0, min_ticket=0.0)


def quarter_ends() -> list[str]:
    out = []
    for y in range(1999, 2027):
        for m, d in ((3, 31), (6, 30), (9, 30), (12, 31)):
            q = f"{y}-{m:02d}-{d:02d}"
            if "1999-03-31" <= q <= "2026-06-30":
                out.append(q)
    return out


def _resolver(ticker_rows: list[dict]):
    """Window-aware as-traded -> TICKERS-row resolver (US common only).

    Layered disambiguation, each layer motivated by a real failure the
    boundary audit caught on the first build:
      1. COMMON-category filter FIRST — a mega-cap's preferred series
         (JPM-PM, ...) all list the common's symbol in relatedtickers
         and made JPM/BAC/T look 'ambiguous' in 2020.
      2. Price-window filter; a unique survivor wins.
      3. Dead-holder rule: Sharadar suffixes a digit onto companies
         that DIED holding a recycled symbol (JPM1 = J.P. Morgan & Co,
         T1 = AT&T Corp). A suffixed holder alive at `day` owns the
         symbol (as-traded JPM in 1999 is J.P. Morgan & Co, not the
         Chase lineage whose backdated window also covers 1999).
      4. Exact-final match: if the lineage whose FINAL ticker is the
         symbol was itself pricing at `day`, it owns it (AA after the
         2016 Alcoa split — Howmet/Arconic still prices, but under a
         different as-traded name).
      5. One remaining related holder wins; anything still ambiguous
         returns None and is EXCLUDED + logged, never guessed.
    Returns (row, why) where why is None on success.
    """
    import re
    exact: dict[str, list[dict]] = {}
    related: dict[str, list[dict]] = {}
    for r in ticker_rows:
        exact.setdefault(str(r.get("ticker", "")).upper(), []).append(r)
        for rt in (r.get("relatedtickers") or "").split():
            related.setdefault(rt.upper(), []).append(r)

    def resolve(sym: str, day: str):
        cands = list(exact.get(sym, [])) + [
            r for r in related.get(sym, []) if r not in exact.get(sym, [])]
        common = [r for r in cands if r.get("category") in COMMON]
        if not common:
            return None, ("category" if cands else "no_tickers_match")
        windowed = [r for r in common
                    if (r.get("firstpricedate") or "0000") <= day
                    <= (r.get("lastpricedate") or "9999")]
        if len(windowed) == 1:
            return windowed[0], None
        if not windowed:
            return None, "no_window_match"
        dead_holders = [r for r in windowed
                        if re.fullmatch(re.escape(sym) + r"\d",
                                         str(r.get("ticker", "")).upper())]
        if len(dead_holders) == 1:
            return dead_holders[0], None
        exacts = [r for r in windowed
                  if str(r.get("ticker", "")).upper() == sym]
        if len(exacts) == 1:
            return exacts[0], None
        others = [r for r in windowed
                  if str(r.get("ticker", "")).upper() != sym]
        if len(others) == 1:
            return others[0], None
        return None, "ambiguous"

    return resolve


def phase_universes(scratch: str) -> None:
    ticker_rows = sh.load_ticker_universe()
    resolve = _resolver(ticker_rows)
    universes: dict = {}
    excluded: list[dict] = []
    for qe in quarter_ends():
        rows = sh._datatable("DAILY", **{
            "date.gte": qe, "date.lte": qe,
            "qopts.columns": "ticker,date,marketcap",
            "qopts.per_page": 10000})
        if not rows:  # quarter-end fell on a weekend/holiday
            rows = sh._datatable("DAILY", **{
                "date.gte": _minus_days(qe, 6), "date.lte": qe,
                "qopts.columns": "ticker,date,marketcap",
                "qopts.per_page": 10000})
            if not rows:
                raise SystemExit(f"{qe}: no DAILY rows in trailing week")
            last = max(r["date"] for r in rows)
            rows = [r for r in rows if r["date"] == last]
        as_of = rows[0]["date"][:10]
        pool = []
        for r in rows:
            t = str(r["ticker"]).upper()
            m = r.get("marketcap")
            if m is None:
                continue
            row, why = resolve(t, as_of)
            if row is None:
                if why != "category":  # ADRs/funds are excluded by design
                    excluded.append({"qe": qe, "ticker": t, "why": why,
                                     "marketcap": float(m)})
                continue
            pool.append((float(m), t, str(row["ticker"]).upper()))
        pool.sort(reverse=True)
        members = pool[:TOP_N]
        universes[qe] = {
            "as_of": as_of,
            "members": [{"traded": t, "final": f, "marketcap": m}
                        for m, t, f in members],
        }
        # Boundary audit: an excluded name big enough for the top-119
        # means the universe is WRONG, not just less covered.
        floor_m = members[-1][0] if members else 0.0
        boundary = [e for e in excluded if e["qe"] == qe
                    and e["marketcap"] >= floor_m]
        flag = f"  !! BOUNDARY: {[(e['ticker'], e['why']) for e in boundary]}" \
            if boundary else ""
        print(f"{qe} (as_of {as_of}): {len(members)} members, "
              f"pool {len(pool)}{flag}", flush=True)
    os.makedirs(scratch, exist_ok=True)
    boundary_all = []
    for qe, u in universes.items():
        floor_m = u["members"][-1]["marketcap"] if u["members"] else 0.0
        boundary_all += [e for e in excluded if e["qe"] == qe
                          and e["marketcap"] >= floor_m]
    with gzip.open(f"{scratch}/universes.json.gz", "wt") as f:
        json.dump({"universes": universes, "excluded": excluded,
                   "boundary_violations": boundary_all}, f)
    union = sorted({m["final"] for u in universes.values()
                    for m in u["members"]})
    print(f"quarters: {len(universes)}, union of final tickers: {len(union)}, "
          f"excluded rows: {len(excluded)}, "
          f"BOUNDARY VIOLATIONS: {len(boundary_all)}")


def _minus_days(day: str, n: int) -> str:
    from datetime import date, timedelta
    y, m, d = map(int, day.split("-"))
    return (date(y, m, d) - timedelta(days=n)).isoformat()


def phase_bars(scratch: str) -> None:
    with gzip.open(f"{scratch}/universes.json.gz", "rt") as f:
        data = json.load(f)
    union = sorted({m["final"] for u in data["universes"].values()
                    for m in u["members"]})
    print(f"pulling SEP bars for {len(union)} final tickers from {BAR_START}")
    bars: dict[str, list] = {}
    CHUNK = 25
    for i in range(0, len(union), CHUNK):
        chunk = union[i:i + CHUNK]
        rows = sh._datatable("SEP", ticker=",".join(chunk), **{
            "date.gte": BAR_START,
            "qopts.columns": "ticker,date,close,closeadj,volume",
            "qopts.per_page": 10000})
        for r in rows:
            if r.get("close") is None:
                continue
            bars.setdefault(r["ticker"], []).append(
                [r["date"][:10], float(r["close"]),
                 float(r["closeadj"]) if r.get("closeadj") is not None else None,
                 float(r["volume"]) if r.get("volume") is not None else None])
        print(f"  {i + len(chunk)}/{len(union)} tickers, "
              f"{sum(len(v) for v in bars.values())} rows", flush=True)
    for t in bars:
        bars[t].sort()
    missing = [t for t in union if t not in bars]
    spy = sh._datatable("SFP", ticker="SPY", **{
        "date.gte": BAR_START,
        "qopts.columns": "ticker,date,close,closeadj",
        "qopts.per_page": 10000})
    with gzip.open(f"{scratch}/bars.json.gz", "wt") as f:
        json.dump({"bars": bars, "missing": missing}, f)
    with gzip.open(f"{scratch}/spy.json.gz", "wt") as f:
        json.dump(spy, f)
    print(f"symbols with bars: {len(bars)}, MISSING (disclose): {missing}, "
          f"spy rows: {len(spy)}")


def _to_bar_dicts(raw: dict[str, list]) -> dict[str, list[dict]]:
    out = {}
    for sym, rows in raw.items():
        bl = []
        for d, close, closeadj, volume in rows:
            b = {"date": d, "close": close}
            if closeadj is not None:
                b["close_total_return"] = closeadj
            if volume is not None:
                b["volume"] = volume
            bl.append(b)
        out[sym] = bl
    return out


def _tr(bar: dict) -> float:
    return bar.get("close_total_return", bar["close"])


def _momentum_select(top_n: int, weight: float, lookback: int = 65):
    def select(day, universe, trimmed):
        scored = []
        for sym in universe:
            if sym not in trimmed:
                continue
            tail = (trimmed.tail(sym, lookback + 1)
                    if hasattr(trimmed, "tail") else trimmed[sym][-(lookback + 1):])
            if len(tail) < lookback + 1:
                continue
            p0, p1 = _tr(tail[0]), _tr(tail[-1])
            if p0 <= 0:
                continue
            scored.append((p1 / p0 - 1.0, sym))
        scored.sort(reverse=True)
        return {sym: weight for _, sym in scored[:top_n]}
    return select


def _ma_filtered_momentum_select(top_n: int, weight: float,
                                  lookback: int = 65, ma_period: int = 20):
    """rank_by_momentum semantics exactly: momentum AND the 20d-MA
    entry filter computed on the same split-adjusted close series;
    only names with close >= SMA(ma_period) are ranked at all."""
    need = max(lookback + 1, ma_period)

    def select(day, universe, trimmed):
        scored = []
        for sym in universe:
            if sym not in trimmed:
                continue
            tail = (trimmed.tail(sym, need)
                    if hasattr(trimmed, "tail") else trimmed[sym][-need:])
            if len(tail) < need:
                continue
            closes = [b["close"] for b in tail]
            ma = sum(closes[-ma_period:]) / ma_period
            price = closes[-1]
            if price < ma:
                continue  # the entry filter — her actual MA rule
            base = closes[-(lookback + 1)]
            if base <= 0:
                continue
            scored.append((price / base - 1.0, sym))
        scored.sort(reverse=True)
        return {sym: weight for _, sym in scored[:top_n]}
    return select


def _ew_select():
    def select(day, universe, trimmed):
        live = [s for s in universe if s in trimmed and trimmed.tail(s, 1)]
        if not live:
            return {}
        w = 1.0 / len(live)
        return {s: w for s in live}
    return select


def _build_snapshots(universes: dict, exec_days: list[str]) -> dict:
    """{exec_day: [final tickers]} — membership effective from the first
    trading day after its quarter-end."""
    qes = sorted(universes)
    snaps = {}
    for d in exec_days:
        eligible = [q for q in qes if q < d]
        if not eligible:
            continue
        u = universes[eligible[-1]]
        snaps[d] = sorted({m["final"] for m in u["members"]})
    return snaps


def _exec_days_after(signal_dates: list[str], all_days: list[str]) -> list[str]:
    idx = {d: i for i, d in enumerate(all_days)}
    out = []
    for sd in signal_dates:
        i = idx.get(sd)
        if i is not None and i + 1 < len(all_days):
            out.append(all_days[i + 1])
    return sorted(set(out))


def phase_cells(scratch: str, out_dir: str) -> None:
    with gzip.open(f"{scratch}/universes.json.gz", "rt") as f:
        udata = json.load(f)
    with gzip.open(f"{scratch}/bars.json.gz", "rt") as f:
        bdata = json.load(f)
    with gzip.open(f"{scratch}/spy.json.gz", "rt") as f:
        spy_rows = json.load(f)
    bars = _to_bar_dicts(bdata["bars"])
    universes = udata["universes"]

    from shared.gauntlet import _trading_days
    all_days = _trading_days(bars, SIM_START, SIM_END)
    weekly_signals = periodic_dates(all_days, "W", "last")
    monthly_signals = periodic_dates(all_days, "M", "last")
    weekly_exec = _exec_days_after(weekly_signals, all_days)
    monthly_exec = _exec_days_after(monthly_signals, all_days)
    snaps_w = _build_snapshots(universes, weekly_exec)
    snaps_m = _build_snapshots(universes, monthly_exec)
    print(f"trading days {len(all_days)}, weekly execs {len(snaps_w)}, "
          f"monthly execs {len(snaps_m)}", flush=True)

    spy_bars = [{"date": r["date"][:10], "close": float(r["close"]),
                 "close_total_return": float(r["closeadj"])}
                for r in spy_rows if r.get("closeadj") is not None]
    spy = benchmark_curve(spy_bars, initial=10_000.0)

    mom = _momentum_select(10, 0.095)
    runs = {}
    cells = {
        "delphi_live": dict(spec=StrategySpec("delphi_live", mom),
                            snaps=snaps_w, cost=COST,
                            exits=ExitRules(ma_period=20, cooldown_days=5)),
        "delphi_no_exit": dict(spec=StrategySpec("delphi_no_exit", mom),
                               snaps=snaps_w, cost=COST, exits=None),
        "delphi_monthly": dict(spec=StrategySpec("delphi_monthly", mom),
                               snaps=snaps_m, cost=COST,
                               exits=ExitRules(ma_period=20, cooldown_days=5)),
        "bench_ew": dict(spec=StrategySpec("bench_ew", _ew_select()),
                         snaps=snaps_w, cost=BENCH_COST, exits=None),
        "delphi_live_2x": dict(spec=StrategySpec("delphi_live_2x", mom),
                               snaps=snaps_w, cost=COST_2X,
                               exits=ExitRules(ma_period=20, cooldown_days=5)),
    }
    for name, cfg in cells.items():
        print(f"running {name} ...", flush=True)
        runs[name] = simulate(cfg["spec"], cfg["snaps"], bars,
                              initial_cash=10_000.0, cost=cfg["cost"],
                              start=SIM_START, end=SIM_END,
                              signal_lag=1, exits=cfg["exits"])
        print(f"  {name}: {runs[name]['stats']['cagr']:.2%} CAGR, "
              f"sharpe {runs[name]['stats']['sharpe']:.2f}, "
              f"maxDD {runs[name]['stats']['max_drawdown']:.1%}", flush=True)

    os.makedirs(out_dir, exist_ok=True)
    report: dict = {"prereg": "docs/lab_prereg_delphi_ruleset_fullwindow.md",
                    "window": [SIM_START, SIM_END], "cells": {}}
    for name, res in runs.items():
        entry = {
            "stats": res["stats"],
            "vs_bench_ew": excess_stats(res["curve"], runs["bench_ew"]["curve"])
            if name != "bench_ew" else None,
            "vs_spy": excess_stats(res["curve"], spy["curve"]),
            "sharpe_ci": sharpe_ci(res["curve"]),
            "regimes": summarize_by_period(res["curve"], REGIME_BOUNDARIES),
            "trades": trade_stats(res["trades"]),
            "turnover": turnover_stats(res["trades"], res["curve"]),
            "drawdown_dist": drawdown_distribution(res["curve"]),
            "price_return_only_symbols": res["price_return_only_symbols"],
            "n_trades": len(res["trades"]),
        }
        if name == "delphi_live":
            entry["capacity"] = capacity_stats(res["trades"], bars)
            entry["bias_checklist_draft"] = draft_bias_checklist(
                res, n_trials=3, cost=COST,
                panel_note=("Sharadar SEP bars (close+closeadj+volume) for the "
                            "union of quarterly PIT top-119 members 1998-12→"
                            "2026-06, delisted included; universes from DAILY "
                            "marketcap quarter-end cross-sections"),
                split_note=("No in-study tuning; parameters are Delphi's live "
                            "frozen values; 3 cells enumerated in the prereg"),
                hypotheses_ever=96, regime_boundaries=REGIME_BOUNDARIES)
        report["cells"][name] = entry
    report["spy"] = {"stats": spy["stats"], "price_field": spy["price_field"]}
    report["universe_excluded"] = udata["excluded"]
    report["bars_missing"] = bdata["missing"]
    with open(f"{out_dir}/results.json", "w") as f:
        json.dump(report, f, indent=1, default=str)
    for name in ("delphi_live", "bench_ew"):
        with gzip.open(f"{out_dir}/curve_{name}.json.gz", "wt") as f:
            json.dump(runs[name]["curve"], f)
    with gzip.open(f"{out_dir}/universes.json.gz", "wt") as f:
        json.dump(udata, f)
    print(f"wrote {out_dir}/results.json")


def phase_faithful(scratch: str, out_dir: str) -> None:
    """docs/lab_prereg_delphi_ruleset_faithful.md — the corrected cells."""
    with gzip.open(f"{scratch}/universes.json.gz", "rt") as f:
        udata = json.load(f)
    with gzip.open(f"{scratch}/bars.json.gz", "rt") as f:
        bdata = json.load(f)
    with gzip.open(f"{scratch}/spy.json.gz", "rt") as f:
        spy_rows = json.load(f)
    bars = _to_bar_dicts(bdata["bars"])
    universes = udata["universes"]

    from shared.gauntlet import _trading_days
    all_days = _trading_days(bars, SIM_START, SIM_END)
    weekly_signals = periodic_dates(all_days, "W", "last")
    weekly_exec = _exec_days_after(weekly_signals, all_days)
    daily_exec = all_days[1:]  # signal_lag=1 needs one prior day
    snaps_w = _build_snapshots(universes, weekly_exec)
    snaps_d = _build_snapshots(universes, daily_exec)
    print(f"trading days {len(all_days)}, daily execs {len(snaps_d)}, "
          f"weekly execs {len(snaps_w)}", flush=True)

    spy_bars = [{"date": r["date"][:10], "close": float(r["close"]),
                 "close_total_return": float(r["closeadj"])}
                for r in spy_rows if r.get("closeadj") is not None]
    spy = benchmark_curve(spy_bars, initial=10_000.0)

    sel = _ma_filtered_momentum_select(10, 0.095)
    cells = {
        "faithful_daily": dict(snaps=snaps_d, cost=COST),
        "faithful_weekly": dict(snaps=snaps_w, cost=COST),
        "faithful_daily_2x": dict(snaps=snaps_d, cost=COST_2X),
        "bench_ew": dict(snaps=snaps_w, cost=BENCH_COST, ew=True),
    }
    runs = {}
    for name, cfg in cells.items():
        print(f"running {name} ...", flush=True)
        runs[name] = simulate(
            StrategySpec(name, _ew_select() if cfg.get("ew") else sel),
            cfg["snaps"], bars, initial_cash=10_000.0, cost=cfg["cost"],
            start=SIM_START, end=SIM_END, signal_lag=1,
            rebalance_band=0.0 if cfg.get("ew") else 0.20,
            sell_cooldown_days=0 if cfg.get("ew") else 5)
        print(f"  {name}: {runs[name]['stats']['cagr']:.2%} CAGR, "
              f"sharpe {runs[name]['stats']['sharpe']:.2f}, "
              f"maxDD {runs[name]['stats']['max_drawdown']:.1%}", flush=True)

    os.makedirs(out_dir, exist_ok=True)
    report = {"prereg": "docs/lab_prereg_delphi_ruleset_faithful.md",
              "window": [SIM_START, SIM_END], "cells": {}}
    for name, res in runs.items():
        report["cells"][name] = {
            "stats": res["stats"],
            "vs_bench_ew": excess_stats(res["curve"], runs["bench_ew"]["curve"])
            if name != "bench_ew" else None,
            "vs_spy": excess_stats(res["curve"], spy["curve"]),
            "sharpe_ci": sharpe_ci(res["curve"]),
            "regimes": summarize_by_period(res["curve"], REGIME_BOUNDARIES),
            "trades": trade_stats(res["trades"]),
            "turnover": turnover_stats(res["trades"], res["curve"]),
            "drawdown_dist": drawdown_distribution(res["curve"]),
            "price_return_only_symbols": res["price_return_only_symbols"],
            "n_trades": len(res["trades"]),
        }
    report["spy"] = {"stats": spy["stats"], "price_field": spy["price_field"]}
    with open(f"{out_dir}/faithful_results.json", "w") as f:
        json.dump(report, f, indent=1, default=str)
    with gzip.open(f"{out_dir}/curve_faithful_daily.json.gz", "wt") as f:
        json.dump(runs["faithful_daily"]["curve"], f)
    print(f"wrote {out_dir}/faithful_results.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["universes", "bars", "cells", "faithful"])
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", default="docs/data/delphi_fullwindow")
    a = ap.parse_args()
    if a.phase == "universes":
        phase_universes(a.scratch)
    elif a.phase == "bars":
        phase_bars(a.scratch)
    elif a.phase == "faithful":
        phase_faithful(a.scratch, a.out)
    else:
        phase_cells(a.scratch, a.out)
