"""Vectorized runner for The Gauntlet's factory screen (backlog #9 phase c).

`shared.gauntlet.simulate` is the reference implementation — readable,
tested, and O(days x names x bars), which is fine for a handful of
names and unusable for 90 cells x ~6,000 names x 4,000 days. This
module implements the SAME frozen execution model (prereg
docs/lab_prereg_gauntlet_v1.md section 4) on numpy matrices:

- signals through close of signal day t, execution at close of the
  execution day (the caller passes explicit signal/execution index
  pairs — the one-day-plus lag is data, not a hidden default);
- equal weight 1/N, long only, remainder implicitly zero (weights sum
  to 1 across selected names);
- linear slippage on turnover notional; trades under `min_ticket` are
  suppressed;
- a name with no bar on a day carries its last price (zero return)
  until the next rebalance — Sharadar bars end at the true final
  trading day, so a dead name's stale value is sold at the next
  rebalance, optimistic by the recovery gap (disclosed in the prereg).

Equivalence with the reference engine is pinned by
tests/test_gauntlet_fast.py on synthetic panels.

The Panel matrices are dates x tickers, float64, NaN where no bar.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from shared.gauntlet import CostModel, summarize


@dataclass
class Panel:
    """Aligned price panel: `days` (sorted ISO dates), `tickers` (sorted),
    and dates-x-tickers matrices. NaN marks no-bar."""
    days: list[str]
    tickers: list[str]
    closeadj: np.ndarray
    close: np.ndarray      # unadjusted, for price floors
    volume: np.ndarray

    def __post_init__(self):
        n_d, n_t = len(self.days), len(self.tickers)
        for name in ("closeadj", "close", "volume"):
            m = getattr(self, name)
            if m.shape != (n_d, n_t):
                raise ValueError(
                    f"{name} shape {m.shape} != (days={n_d}, tickers={n_t})")
        self.day_index = {d: i for i, d in enumerate(self.days)}
        self.ticker_index = {t: j for j, t in enumerate(self.tickers)}

    def dollar_volume(self) -> np.ndarray:
        return self.close * self.volume


def build_panel(bars_by_symbol: dict[str, list[dict]]) -> Panel:
    """Assemble a Panel from per-symbol bar lists ({date, close,
    closeadj, volume}). Symbols with zero bars are dropped."""
    days = sorted({b["date"] for bars in bars_by_symbol.values() for b in bars})
    tickers = sorted(s for s, bars in bars_by_symbol.items() if bars)
    day_idx = {d: i for i, d in enumerate(days)}
    shape = (len(days), len(tickers))
    closeadj = np.full(shape, np.nan)
    close = np.full(shape, np.nan)
    volume = np.full(shape, np.nan)
    for j, t in enumerate(tickers):
        for b in bars_by_symbol[t]:
            i = day_idx[b["date"]]
            closeadj[i, j] = b.get("closeadj", b.get("close"))
            close[i, j] = b.get("close")
            volume[i, j] = b.get("volume", np.nan)
    return Panel(days, tickers, closeadj, close, volume)


def carry_forward(closeadj: np.ndarray) -> np.ndarray:
    """Last-known-price fill (NaN before a name's first bar stays NaN).
    Mirrors the reference engine's `last_price` carry."""
    filled = closeadj.copy()
    n_d = filled.shape[0]
    for i in range(1, n_d):
        row = filled[i]
        prev = filled[i - 1]
        mask = np.isnan(row) & ~np.isnan(prev)
        row[mask] = prev[mask]
    return filled


def run_cell(
    panel: Panel,
    schedule: list[tuple[int, np.ndarray]],
    *,
    initial_cash: float,
    cost: CostModel,
    start_idx: int,
    end_idx: int,
    prices: np.ndarray | None = None,
) -> dict:
    """Simulate one grid cell.

    `schedule` is [(execution_day_index, weight_vector)] — weight_vector
    is a len(tickers) float array summing to <= 1.0 (equal weights over
    the selected names; selection itself happened upstream from
    signal-day data only). Returns {"curve", "stats"} like the
    reference engine (trades are not itemized — the screen needs
    curves, and turnover costs are applied inside).

    `prices` lets a multi-cell screen pass `carry_forward(panel.closeadj)`
    once instead of recomputing it per cell.
    """
    if prices is None:
        prices = carry_forward(panel.closeadj)
    exec_by_idx = {i: w for i, w in schedule}
    n_t = len(panel.tickers)

    cash = initial_cash
    shares = np.zeros(n_t)
    curve = []
    for i in range(start_idx, end_idx + 1):
        px = prices[i]
        pos_value = np.nansum(shares * px)
        equity = cash + pos_value
        if i in exec_by_idx:
            w = exec_by_idx[i]
            total_w = w.sum()
            if total_w > 1.0 + 1e-9:
                raise ValueError(f"weights sum to {total_w:.6f} > 1.0 at day {i}")
            cur_value = np.where(np.isnan(px), 0.0, shares * np.nan_to_num(px))
            target_value = w * equity
            # A target on a name with no price ever seen is unfillable.
            target_value = np.where(np.isnan(px), 0.0, target_value)
            delta = target_value - cur_value
            delta[np.abs(delta) < cost.min_ticket] = 0.0
            sells = np.minimum(delta, 0.0)
            buys = np.maximum(delta, 0.0)
            rate = (cost.commission_bps + cost.slippage_bps) / 10_000.0
            cash += -sells.sum() * (1 - rate)
            # Buys bounded by cash actually on hand, incl. their own cost.
            buy_total = buys.sum()
            if buy_total > 0:
                afford = cash / (1 + rate)
                scale = min(1.0, afford / buy_total)
                buys = buys * scale
                # Mirror the reference engine: a buy scaled below the
                # min ticket is skipped, its cash left idle.
                buys[(buys > 0) & (buys < cost.min_ticket)] = 0.0
                cash -= buys.sum() * (1 + rate)
            trade = buys + sells
            with np.errstate(invalid="ignore", divide="ignore"):
                d_shares = np.where(trade != 0, trade / px, 0.0)
            d_shares = np.nan_to_num(d_shares)
            shares = shares + d_shares
            shares[np.abs(shares) < 1e-12] = 0.0
            pos_value = np.nansum(shares * px)
            equity = cash + pos_value
        curve.append({"date": panel.days[i], "equity": float(equity)})
    return {"curve": curve, "stats": summarize(curve)}


def equal_weights(panel: Panel, names: list[str]) -> np.ndarray:
    """1/N weight vector over `names` (positions in panel.tickers)."""
    w = np.zeros(len(panel.tickers))
    if not names:
        return w
    for t in names:
        w[panel.ticker_index[t]] = 1.0 / len(names)
    return w


# ---------------------------------------------------------------------------
# Signal computations (prereg section 5) — all evaluated at a signal-day
# row index, using only rows <= that index.
# ---------------------------------------------------------------------------

def momentum_scores(prices: np.ndarray, t: int, lookback: int, skip: int) -> np.ndarray:
    """Return over [t-skip-lookback, t-skip] from closeadj. NaN unless
    both endpoint bars exist (prereg: full-window eligibility for
    momentum = both endpoints; halts between endpoints do not change a
    two-point return)."""
    a = prices[t - skip - lookback]
    b = prices[t - skip]
    return b / a - 1.0


def window_matrix(prices: np.ndarray, t: int, window: int) -> np.ndarray:
    """Rows [t-window+1 .. t], for full-window signals."""
    return prices[t - window + 1: t + 1]


def volatility_scores(prices: np.ndarray, t: int, window: int) -> np.ndarray:
    """Stdev of daily returns over the trailing `window` bars ending t.
    NaN unless every bar in the window is present (strict full-window
    rule, prereg section 3)."""
    w = prices[t - window: t + 1]
    rets = w[1:] / w[:-1] - 1.0
    out = np.std(rets, axis=0)
    out[np.isnan(rets).any(axis=0)] = np.nan
    return out


def median_dollar_volume(dv: np.ndarray, t: int, window: int = 21) -> np.ndarray:
    """Median close*volume over the trailing `window` bars ending t.
    NaN unless every bar is present (strict full-window rule)."""
    w = dv[t - window + 1: t + 1]
    out = np.median(w, axis=0)
    out[np.isnan(w).any(axis=0)] = np.nan
    return out
