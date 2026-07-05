"""PEAD gauntlet — the event-driven backtest engine for achilles_pead_gauntlet.

The house gauntlet (shared/gauntlet.py) simulates FACTOR rank-and-hold. PEAD is
EVENT-driven: enter a name the day after its earnings reaction, hold H days with
a -8% stop, measure the drift vs the name's own marketcap-bucket equal-weight.
This module is that engine, plus the survivorship-honest ticker-join layer.

Metric (matching the 2026-07-03 reaction-gate replay and the prereg): the
trade-level distribution of net excess-vs-bucket returns — mean, t, win — at 1x
and 2x cost, in each regime. No compounded equity curve: for an event strategy
the honest measure is "did the average trade beat the bucket over its own
window," not a capacity-dependent curve.

PAPER ONLY. No live path. docs/lab_prereg_achilles_pead_gauntlet.md.
"""
from __future__ import annotations

import math
from typing import Callable, Optional


# ── SUE: Standardized Unexpected Earnings (seasonal random walk, Bernard-Thomas)

def seasonal_sue(eps_series: list[tuple[str, float]], *, min_history: int = 8
                 ) -> dict[str, float]:
    """SUE per quarter from a per-entity EPS series (needs only reported EPS —
    no analyst estimates).

    eps_series: (calendardate, eps) sorted ascending, one row per fiscal quarter.
    SUE_t = (eps_t - eps_{t-4}) / std(the trailing `min_history` seasonal deltas
    eps_q - eps_{q-4}), the classic seasonal-random-walk surprise. Returns
    {calendardate: sue} only for quarters with enough history for a stable std.
    """
    out: dict[str, float] = {}
    n = len(eps_series)
    # seasonal deltas d_q = eps_q - eps_{q-4}
    deltas: list[tuple[str, float]] = []
    for i in range(4, n):
        d = eps_series[i][1] - eps_series[i - 4][1]
        deltas.append((eps_series[i][0], d))
    for k in range(len(deltas)):
        if k < min_history:
            continue
        window = [d for _, d in deltas[k - min_history:k]]
        m = sum(window) / len(window)
        var = sum((x - m) ** 2 for x in window) / (len(window) - 1)
        sd = math.sqrt(var)
        if sd <= 1e-9:
            continue
        date, d_now = deltas[k]
        out[date] = d_now / sd
    return out


# ── Survivorship-honest ticker join (no permaticker column exists in SF1/SEP/DAILY)

def build_entity_map(tickers_rows: list[dict]) -> dict[str, dict]:
    """{TICKER: {permaticker, first, last, category, exchange, isdelisted}} from
    the Sharadar TICKERS table. Each ticker string maps to one permaticker in
    that table (0 collisions verified 2026-07-05), with a price-date window."""
    m: dict[str, dict] = {}
    for r in tickers_rows:
        t = str(r.get("ticker", "")).upper()
        if not t:
            continue
        m[t] = {
            "permaticker": r.get("permaticker"),
            "first": (r.get("firstpricedate") or "")[:10],
            "last": (r.get("lastpricedate") or "")[:10],
            "category": r.get("category") or "",
            "exchange": (r.get("exchange") or "").upper(),
            "isdelisted": r.get("isdelisted"),
        }
    return m


# tradable, exchange-listed common equity — the universe we can actually see AND buy
_MAJOR_EXCH = {"NYSE", "NASDAQ", "NYSEMKT", "NYSEARCA", "BATS"}


def is_tradable_common(ticker: str, emap: dict[str, dict]) -> bool:
    e = emap.get(ticker.upper())
    if not e:
        return False
    cat = e["category"]
    return ("Common Stock" in cat) and (e["exchange"] in _MAJOR_EXCH)


def in_listing_window(ticker: str, date: str, emap: dict[str, dict]) -> bool:
    """The recycled-ticker guard: trust a (ticker, date) row only if date is
    inside that ticker's price-date window. A bar for a ticker on a date OUTSIDE
    its window is a different (recycled/old) entity trading under the same
    string — drop it (disclosed in the coverage_note)."""
    e = emap.get(ticker.upper())
    if not e or not e["first"] or not e["last"]:
        return False
    return e["first"] <= str(date)[:10] <= e["last"]


# ── The trade simulator (one entered event → one trade)

def simulate_trade(path: list[dict], *, hold_days: int, stop_pct: float = 0.08
                   ) -> Optional[dict]:
    """path: daily bars from the entry day forward, each {date, px, low} on an
    adjusted (total-return) basis; path[0] is the entry bar (px = entry close).
    Hold up to hold_days trading days; exit early at the -stop_pct level if a
    day's low breaches it (intraday stop). Returns the trade or None if the path
    is too short to even hold one day."""
    if len(path) < 2:
        return None
    entry = path[0]["px"]
    if entry <= 0:
        return None
    stop = entry * (1.0 - stop_pct)
    last = min(hold_days, len(path) - 1)
    for i in range(1, last + 1):
        bar = path[i]
        if bar.get("low", bar["px"]) <= stop:
            return {"exit_date": bar["date"], "exit_px": stop, "hold_used": i,
                    "reason": "stop", "gross_ret": stop / entry - 1.0}
    exit_bar = path[last]
    return {"exit_date": exit_bar["date"], "exit_px": exit_bar["px"], "hold_used": last,
            "reason": "time", "gross_ret": exit_bar["px"] / entry - 1.0}


def run_cell(events: list[dict], *, price_path: Callable[[str, str, int], list[dict]],
             bucket_bench: Callable[[str, str, str], Optional[float]],
             hold_days: int, reaction_cap: float, sue_threshold: float,
             stop_pct: float = 0.08, cost_oneway: float = 0.0) -> list[dict]:
    """Run one grid cell over the qualifying events.

    events: dicts with {symbol, entry_date, sue, reaction, bucket}. An event
      qualifies if sue >= sue_threshold AND 0 < reaction <= reaction_cap
      (direction + the already-fired magnitude guard).
    price_path(symbol, entry_date, hold_days+1) -> adjusted bars from entry fwd.
    bucket_bench(bucket, entry_date, exit_date) -> the bucket EW return over the
      identical window (the benchmark leg), or None if unavailable.
    cost_oneway: fraction charged per side (round-trip = 2x); pass 2x the base
      for the stress cell. Returns the list of executed trades with net excess.
    """
    trades: list[dict] = []
    for ev in events:
        if ev["sue"] < sue_threshold:
            continue
        r = ev.get("reaction")
        if r is None or r <= 0 or r > reaction_cap:
            continue
        path = price_path(ev["symbol"], ev["entry_date"], hold_days + 1)
        t = simulate_trade(path, hold_days=hold_days, stop_pct=stop_pct)
        if t is None:
            continue
        net = t["gross_ret"] - 2.0 * cost_oneway   # round-trip cost
        bench = bucket_bench(ev["bucket"], ev["entry_date"], t["exit_date"])
        if bench is None:
            continue
        trades.append({**ev, **t, "net_ret": net, "bench_ret": bench,
                       "excess": net - bench})
    return trades


# ── Trade-distribution stats (the verdict inputs)

def summarize(trades: list[dict], *, key: str = "excess") -> dict:
    xs = [t[key] for t in trades]
    n = len(xs)
    if n < 2:
        return {"n": n}
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    t = m / (sd / math.sqrt(n)) if sd > 0 else None
    return {
        "n": n,
        "mean_excess": round(m, 5),
        "t": round(t, 2) if t is not None else None,
        "win": round(sum(1 for x in xs if x > 0) / n, 3),
        "stop_rate": round(sum(1 for tr in trades if tr.get("reason") == "stop") / n, 3),
    }
