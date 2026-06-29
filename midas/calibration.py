"""Calibration and capital scaling for Midas.

Tracks weekly results and determines when Midas has proven itself enough
to scale capital. Same gates as Oracle but reached ~6x faster:
  - 30+ graded trades (weekly → ~7 months vs Oracle's ~4 years)
  - alpha > 0 (positive returns after benchmark)
  - alpha_t >= 2.0 (statistically significant)
  - convergence validation (multi-signal picks outperform single-signal)
"""
from __future__ import annotations

import math
from typing import Optional

from .sleeve import CAPITAL_BASE, CAPITAL_CEILING, MidasSleeve, WeeklyResult


MIN_GRADED_FOR_SCALING = 30
MIN_ALPHA_T = 2.0
SCALING_STEPS = [
    (30, 2_000),
    (50, 4_000),
    (75, 8_000),
    (100, CAPITAL_CEILING),
]


def weekly_benchmark_return(spy_start: float, spy_end: float) -> float:
    if spy_start <= 0:
        return 0.0
    return (spy_end - spy_start) / spy_start


def compute_alpha(
    results: list[WeeklyResult],
    benchmark_returns: list[float],
) -> Optional[dict]:
    """Compute alpha (excess return over benchmark) and its t-statistic.

    benchmark_returns: list of SPY weekly returns aligned with results.
    Returns dict with alpha, alpha_t, n, or None if insufficient data.
    """
    if len(results) < 5 or len(benchmark_returns) != len(results):
        return None

    n = len(results)
    excess = [r.return_pct - b for r, b in zip(results, benchmark_returns)]
    mean_excess = sum(excess) / n

    if n < 2:
        return None
    variance = sum((e - mean_excess) ** 2 for e in excess) / (n - 1)
    std = math.sqrt(variance) if variance > 0 else 1e-9
    alpha_t = mean_excess / (std / math.sqrt(n))

    return {
        "alpha": mean_excess,
        "alpha_t": alpha_t,
        "n": n,
        "std": std,
        "hit_rate": sum(1 for e in excess if e > 0) / n,
    }


def convergence_validates(results: list[WeeklyResult]) -> bool:
    """Check that multi-signal picks outperform single-signal picks.

    This is the convergence thesis validation: if 2+ signal picks don't
    beat 1-signal picks, the convergence model isn't adding value.
    """
    single = [r.return_pct for r in results if r.convergence_count == 1]
    multi = [r.return_pct for r in results if r.convergence_count >= 2]

    if len(single) < 5 or len(multi) < 5:
        return True

    avg_single = sum(single) / len(single)
    avg_multi = sum(multi) / len(multi)
    return avg_multi > avg_single


def target_capital(
    sleeve: MidasSleeve,
    benchmark_returns: list[float],
) -> float:
    """Compute target capital level based on calibration gates."""
    results = sleeve.weekly_results
    n = len(results)

    if n < MIN_GRADED_FOR_SCALING:
        return CAPITAL_BASE

    if len(benchmark_returns) != n:
        return CAPITAL_BASE

    stats = compute_alpha(results, benchmark_returns)
    if stats is None:
        return CAPITAL_BASE

    if stats["alpha"] <= 0:
        return CAPITAL_BASE

    if stats["alpha_t"] < MIN_ALPHA_T:
        return CAPITAL_BASE

    if not convergence_validates(results):
        return CAPITAL_BASE

    for threshold, cap in SCALING_STEPS:
        if n < threshold:
            return cap

    return CAPITAL_CEILING


def calibration_summary(
    sleeve: MidasSleeve,
    benchmark_returns: Optional[list[float]] = None,
) -> dict:
    """Human-readable calibration summary."""
    results = sleeve.weekly_results
    n = len(results)

    summary: dict = {
        "graded_trades": n,
        "trades_needed": max(0, MIN_GRADED_FOR_SCALING - n),
        "current_capital": sleeve.contributed_cash,
    }

    if n > 0:
        summary["hit_rate"] = sleeve.hit_rate()
        summary["avg_return"] = sleeve.avg_return()
        summary["convergence_hit_rates"] = sleeve.convergence_hit_rates()
        summary["signal_attribution"] = sleeve.signal_attribution()

    if benchmark_returns and len(benchmark_returns) == n:
        stats = compute_alpha(results, benchmark_returns)
        if stats:
            summary["alpha"] = stats
            summary["convergence_validates"] = convergence_validates(results)
            summary["target_capital"] = target_capital(sleeve, benchmark_returns)

    return summary
