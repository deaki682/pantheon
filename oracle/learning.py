"""Calibration stats — does conviction predict returns?

The real test of skill: are high-conviction calls actually outperforming
low-conviction calls? We bucket by conviction tier and check monotonicity.
"""
from __future__ import annotations

from typing import Iterable

from .journal import JournalEntry


def conviction_tier(conviction: float) -> str:
    if conviction >= 0.66:
        return "high"
    if conviction >= 0.33:
        return "mid"
    return "low"


def calibration_stats(entries: Iterable[JournalEntry]) -> dict:
    """Compute per-tier mean returns from graded buy/add calls.

    Returns: {high: mean, mid: mean, low: mean, n: total, monotonic: bool}
    monotonic = high >= mid >= low (the conviction edge test).
    """
    buckets: dict[str, list[float]] = {"high": [], "mid": [], "low": []}
    n_graded = 0
    for e in entries:
        if e.graded_return is None:
            continue
        if e.decision not in ("buy", "add"):
            continue
        tier = conviction_tier(e.conviction)
        buckets[tier].append(e.graded_return)
        n_graded += 1

    means: dict[str, float | None] = {}
    for tier in ("high", "mid", "low"):
        if buckets[tier]:
            means[tier] = sum(buckets[tier]) / len(buckets[tier])
        else:
            means[tier] = None

    counts = {t: len(buckets[t]) for t in buckets}
    valid = [t for t in ("high", "mid", "low") if means[t] is not None]
    if len(valid) >= 2:
        # Check h >= m >= l where each is present.
        ordered = [means[t] for t in valid]
        monotonic = all(ordered[i] >= ordered[i + 1] for i in range(len(ordered) - 1))
    else:
        monotonic = False

    return {
        "high": means["high"],
        "mid": means["mid"],
        "low": means["low"],
        "counts": counts,
        "n": n_graded,
        "monotonic": monotonic,
    }


def hit_rate(entries: Iterable[JournalEntry]) -> float:
    """Fraction of graded buy/add calls that ended 'win'."""
    n = 0
    wins = 0
    for e in entries:
        if e.graded_outcome and e.decision in ("buy", "add"):
            n += 1
            if e.graded_outcome == "win":
                wins += 1
    return wins / n if n else 0.0


def bayesian_shrunk_skill(
    observed_mean: float, n: int, prior_n: int = 20, prior_mean: float = 0.0
) -> float:
    """Shrink the observed mean toward the prior when n is small."""
    return (prior_n * prior_mean + n * observed_mean) / (prior_n + n)
