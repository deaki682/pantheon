"""Factor attribution — regress Oracle returns against MTUM/QUAL/IWM/VTV.

Measures alpha after factor exposure. Reports the t-statistic of alpha.
No third-party stats deps — we implement OLS by hand.
"""
from __future__ import annotations

import math
from typing import Sequence


FACTOR_ETFS = ("MTUM", "QUAL", "IWM", "VTV")


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
