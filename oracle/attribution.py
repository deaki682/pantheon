"""Factor attribution — regress Oracle returns against MTUM/QUAL/IWM/VTV.

Measures alpha after factor exposure. Reports the t-statistic of alpha.
No third-party stats deps — we implement OLS by hand.

compute_factor_attribution() is the end-to-end entry point: it takes the
equity curve + broker historicals, aligns dates, computes returns, and
runs the regression. The caller fetches ETF historicals via the broker MCP
and passes them in — this module is pure math, no I/O.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any, Sequence

log = logging.getLogger(__name__)

FACTOR_ETFS = ("MTUM", "QUAL", "IWM", "VTV")
MIN_PERIODS = 6  # need at least 6 return periods for OLS with 5 regressors


def _matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    n, m, p = len(a), len(b), len(b[0])
    out = [[0.0] * p for _ in range(n)]
    for i in range(n):
        for j in range(p):
            s = 0.0
            for k in range(m):
                s += a[i][k] * b[k][j]
            out[i][j] = s
    return out


def _transpose(m: list[list[float]]) -> list[list[float]]:
    return [list(col) for col in zip(*m)]


def _invert(m: list[list[float]]) -> list[list[float]]:
    """Gauss-Jordan inversion. m is square."""
    n = len(m)
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        # Pivot
        pivot = col
        for r in range(col, n):
            if abs(a[r][col]) > abs(a[pivot][col]):
                pivot = r
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("matrix singular")
        a[col], a[pivot] = a[pivot], a[col]
        # Normalize
        scale = a[col][col]
        a[col] = [x / scale for x in a[col]]
        # Eliminate
        for r in range(n):
            if r == col:
                continue
            factor = a[r][col]
            a[r] = [a[r][k] - factor * a[col][k] for k in range(2 * n)]
    return [row[n:] for row in a]


def ols(
    y: Sequence[float], X: Sequence[Sequence[float]]
) -> dict:
    """OLS regression: y on X (n samples, k regressors).

    Returns {coefs: [k], residuals: [n], r2: float, t_stats: [k]}.
    The first column of X should be the intercept (1s) if you want alpha.
    """
    n = len(y)
    if n == 0:
        raise ValueError("y empty")
    k = len(X[0])
    if any(len(row) != k for row in X):
        raise ValueError("X is not rectangular")
    if n != len(X):
        raise ValueError("y/X length mismatch")
    if n <= k:
        raise ValueError("not enough observations")

    Xm = [list(row) for row in X]
    Xt = _transpose(Xm)
    XtX = _matmul(Xt, Xm)
    XtY = _matmul(Xt, [[v] for v in y])
    XtX_inv = _invert(XtX)
    coefs_mat = _matmul(XtX_inv, XtY)
    coefs = [row[0] for row in coefs_mat]
    # residuals
    fitted = [sum(Xm[i][j] * coefs[j] for j in range(k)) for i in range(n)]
    residuals = [y[i] - fitted[i] for i in range(n)]
    rss = sum(r * r for r in residuals)
    ymean = sum(y) / n
    tss = sum((v - ymean) ** 2 for v in y) or 1e-12
    r2 = 1.0 - rss / tss
    sigma2 = rss / (n - k)
    se = [math.sqrt(max(0.0, sigma2 * XtX_inv[i][i])) for i in range(k)]
    t_stats = [
        coefs[i] / se[i] if se[i] > 0 else float("inf") for i in range(k)
    ]
    return {"coefs": coefs, "residuals": residuals, "r2": r2, "t_stats": t_stats, "se": se}


def factor_regression(
    oracle_returns: Sequence[float],
    factor_returns: dict[str, Sequence[float]],
) -> dict:
    """Regress Oracle's returns on the 4 factor ETFs. Returns alpha + t-stat.

    factor_returns: dict mapping ETF symbol -> sequence of returns aligned with oracle_returns.
    """
    factors = list(FACTOR_ETFS)
    n = len(oracle_returns)
    for f in factors:
        if f not in factor_returns:
            raise ValueError(f"missing factor returns for {f}")
        if len(factor_returns[f]) != n:
            raise ValueError(f"factor {f} length mismatch")
    X = []
    for i in range(n):
        row = [1.0] + [factor_returns[f][i] for f in factors]
        X.append(row)
    res = ols(list(oracle_returns), X)
    alpha = res["coefs"][0]
    alpha_t = res["t_stats"][0]
    betas = dict(zip(factors, res["coefs"][1:]))
    beta_t = dict(zip(factors, res["t_stats"][1:]))
    return {
        "alpha": alpha,
        "alpha_t": alpha_t,
        "betas": betas,
        "beta_t": beta_t,
        "r2": res["r2"],
        "n": n,
    }


# ---------------------------------------------------------------------------
# End-to-end attribution from equity curve + broker historicals
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> str:
    """Extract YYYY-MM-DD from any ISO-ish timestamp."""
    return s[:10]


def _curve_to_daily(curve: list[dict[str, Any]]) -> dict[str, float]:
    """Deduplicate the equity curve to one equity value per date (last wins)."""
    daily: dict[str, float] = {}
    for entry in curve:
        ts = entry.get("ts") or entry.get("timestamp") or entry.get("date", "")
        eq = entry.get("equity")
        if not ts or eq is None:
            continue
        date = _parse_date(ts)
        daily[date] = float(eq)
    return daily


def _historicals_to_daily(bars: list[dict[str, Any]]) -> dict[str, float]:
    """Extract {date: close_price} from broker historicals bars."""
    daily: dict[str, float] = {}
    for bar in bars:
        dt = bar.get("begins_at") or bar.get("date", "")
        close = bar.get("close_price")
        if not dt or close is None:
            continue
        date = _parse_date(dt)
        daily[date] = float(close)
    return daily


def _compute_returns(prices: dict[str, float], dates: list[str]) -> list[float]:
    """Compute period returns between consecutive dates."""
    returns = []
    for i in range(1, len(dates)):
        prev = prices.get(dates[i - 1])
        curr = prices.get(dates[i])
        if prev and prev > 0 and curr is not None:
            returns.append((curr - prev) / prev)
        else:
            returns.append(0.0)
    return returns


def compute_factor_attribution(
    equity_curve: list[dict[str, Any]],
    factor_historicals: dict[str, list[dict[str, Any]]],
    *,
    min_periods: int = MIN_PERIODS,
) -> dict[str, Any] | None:
    """End-to-end factor attribution from the equity curve and broker historicals.

    Parameters
    ----------
    equity_curve : list of curve entries (from cache/oracle_curve.json)
    factor_historicals : {ETF_symbol: [broker bar dicts]} for each of FACTOR_ETFS.
        Fetch via get_equity_historicals with interval="day" covering the curve's
        date range.
    min_periods : minimum number of return periods required. With 4 factors + 1
        intercept, OLS needs at least 6 observations.

    Returns
    -------
    dict with {alpha, alpha_t, betas, beta_t, r2, n, skipped_reason} or
    None if attribution was skipped (with reason logged).
    """
    oracle_daily = _curve_to_daily(equity_curve)
    if len(oracle_daily) < 2:
        log.info("Attribution skipped: equity curve has %d date(s), need >= 2", len(oracle_daily))
        return {"skipped": True, "reason": f"equity curve has {len(oracle_daily)} date(s), need >= 2"}

    factor_daily: dict[str, dict[str, float]] = {}
    for etf in FACTOR_ETFS:
        bars = factor_historicals.get(etf)
        if not bars:
            log.info("Attribution skipped: no historicals for %s", etf)
            return {"skipped": True, "reason": f"no historicals for {etf}"}
        factor_daily[etf] = _historicals_to_daily(bars)

    oracle_dates = sorted(oracle_daily.keys())
    factor_dates_sets = [set(factor_daily[etf].keys()) for etf in FACTOR_ETFS]
    common_dates = sorted(
        set(oracle_dates) & factor_dates_sets[0] & factor_dates_sets[1]
        & factor_dates_sets[2] & factor_dates_sets[3]
    )

    if len(common_dates) < min_periods + 1:
        log.info(
            "Attribution skipped: %d common dates, need %d for %d return periods",
            len(common_dates), min_periods + 1, min_periods,
        )
        return {
            "skipped": True,
            "reason": f"{len(common_dates)} common dates, need {min_periods + 1}",
        }

    oracle_returns = _compute_returns(oracle_daily, common_dates)
    factor_returns = {
        etf: _compute_returns(factor_daily[etf], common_dates)
        for etf in FACTOR_ETFS
    }

    n_returns = len(oracle_returns)
    if n_returns < min_periods:
        return {"skipped": True, "reason": f"{n_returns} return periods, need {min_periods}"}

    all_zero = all(abs(r) < 1e-12 for r in oracle_returns)
    if all_zero:
        log.info("Attribution skipped: Oracle returns are all zero (no price movement)")
        return {"skipped": True, "reason": "oracle returns are all zero"}

    try:
        result = factor_regression(oracle_returns, factor_returns)
        result["skipped"] = False
        result["common_dates"] = len(common_dates)
        return result
    except ValueError as e:
        log.warning("Attribution failed: %s", e)
        return {"skipped": True, "reason": str(e)}
