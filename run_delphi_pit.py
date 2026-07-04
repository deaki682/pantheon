"""Backlog #4 — Delphi point-in-time universe replay.

Executes docs/lab_prereg_delphi_pit_universe.md: two runs of
delphi.backtest.run_backtest (the claim's own code) over the
reconstructed window 2021-06-30..2026-06-30 on Sharadar closeadj —
Run A on the frozen 2026 curated UNIVERSE, Run B on a quarterly
point-in-time top-119-by-marketcap universe (US common stocks,
delisted included). Reads staged Sharadar exports from --scratch;
no network. PAPER ONLY — touches no sleeve, no cache state.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import zipfile

from delphi.backtest import BacktestConfig, run_backtest
from delphi.signals import UNIVERSE

START = "2021-06-30"
END = "2026-06-30"
TOP_N = 119
COMMON = {"Domestic Common Stock", "Domestic Common Stock Primary Class",
          "Domestic Common Stock Secondary Class"}
QE_DATES = ["2021-03-31", "2021-06-30", "2021-09-30", "2021-12-31",
            "2022-03-31", "2022-06-30", "2022-09-30", "2022-12-30",
            "2023-03-31", "2023-06-30", "2023-09-29", "2023-12-29",
            "2024-03-28", "2024-06-28", "2024-09-30", "2024-12-31",
            "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31",
            "2026-03-31"]


def build_pit_lists(S: str) -> dict[str, list[str]]:
    cats = json.load(gzip.open(f"{S}/ticker_categories.json.gz", "rt"))
    mcap = json.load(gzip.open(f"{S}/daily_mcap_delphi_qe.json.gz", "rt"))
    mcap["2021-03-31"] = json.load(gzip.open(f"{S}/daily_mcap_2021q1.json.gz", "rt"))
    lists = {}
    for d in QE_DATES:
        pool = [(m, t) for t, m in mcap[d].items()
                if cats.get(t) in COMMON]
        pool.sort(reverse=True)
        lists[d] = [t for _, t in pool[:TOP_N]]
    return lists


# Renamed tickers: Sharadar SEP keys all history to the FINAL ticker
# (shared.sharadar THE LAW), but DAILY quarter-end rows can carry the
# name as it traded then. Verified via resolve_ticker at run time.
ALIASES = {"SQ": "XYZ"}  # Block Inc, renamed 2025


def load_prices(S: str, needed: set[str]) -> dict[str, dict[str, dict]]:
    """{sym: {date: {"close": closeadj}}} from the staged exports."""
    needed = needed | {ALIASES[t] for t in needed if t in ALIASES}
    out: dict[str, dict[str, dict]] = {t: {} for t in needed}

    with zipfile.ZipFile(f"{S}/sep_ho.zip") as z:
        with z.open(z.namelist()[0]) as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
            header = next(reader)
            ti, di, cai = (header.index("ticker"), header.index("date"),
                           header.index("closeadj"))
            for row in reader:
                t = row[ti]
                if t in out and START <= row[di]:
                    try:
                        out[t][row[di]] = {"close": float(row[cai])}
                    except ValueError:
                        pass

    for r in json.load(gzip.open(f"{S}/sep_2026h1.json.gz", "rt")):
        t = r["ticker"]
        if t in out and r.get("closeadj") is not None:
            out[t][r["date"][:10]] = {"close": float(r["closeadj"])}

    for r in json.load(gzip.open(f"{S}/spy_sfp.json.gz", "rt")):
        if r.get("closeadj") is not None and r["date"][:10] >= START:
            out.setdefault("SPY", {})[r["date"][:10]] = {"close": float(r["closeadj"])}

    for old, final in ALIASES.items():
        if old in out and final in out and not out[old]:
            out[old] = out[final]

    return {t: v for t, v in out.items() if v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    args = ap.parse_args()
    S = args.scratch

    pit = build_pit_lists(S)
    union = set(UNIVERSE) | {t for names in pit.values() for t in names} | {"SPY"}
    print(f"PIT lists: {len(pit)} quarter-ends; ticker union {len(union)}")

    prices = load_prices(S, union)
    missing = sorted(t for t in union if t not in prices)
    print(f"prices loaded for {len(prices)} tickers; missing bars entirely: "
          f"{len(missing)} {missing[:10]}")

    # Universe B: effective from the first trading day AFTER the quarter-end.
    def universe_b(day: str) -> list[str]:
        eff = [d for d in QE_DATES if d < day]
        return pit[eff[-1]] if eff else pit[QE_DATES[0]]

    cfg = BacktestConfig()
    out = {}
    for label, fn in (("A_frozen_2026_list", None), ("B_pit_top119", universe_b)):
        r = run_backtest(prices, cfg, start_date=START, end_date=END,
                         universe_fn=fn)
        perf = r["results"]["performance"]
        out[label] = r["results"]
        out[label]["n_trades"] = r["results"]["trades"]["total"]
        print(f"\n{label}: total={perf['total_return_pct']}% "
              f"spy={perf['spy_return_pct']}% alpha={perf['alpha_pct']}pp "
              f"sharpe={perf['sharpe']} maxDD={perf['max_drawdown_pct']}% "
              f"trades={r['results']['trades']['total']}")
        curve = r["equity_curve"]
        json.dump(curve, open(f"{S}/delphi_pit_curve_{label}.json", "w"))

    json.dump(out, open(f"{S}/delphi_pit_results.json", "w"), indent=1)

    a, b = out["A_frozen_2026_list"], out["B_pit_top119"]
    aa, ba = a["performance"]["alpha_pct"], b["performance"]["alpha_pct"]
    replicates = 60.0 <= a["performance"]["total_return_pct"] <= 110.0
    artifact = (ba < 0.5 * aa) or (ba <= 0)
    print(f"\nreplicates(A in [60,110]%): {replicates}")
    print(f"artifact verdict (B alpha {ba}pp vs A alpha {aa}pp): {artifact}")


if __name__ == "__main__":
    main()
