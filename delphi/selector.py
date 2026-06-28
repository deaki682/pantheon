"""Within-sector stock selection: pure momentum.

Quality was backtested and showed no predictive value for forward returns
within a sector. Momentum-only selection also eliminates look-ahead bias
from fundamentals data that may not have been available at decision time.
"""
from __future__ import annotations

from .signals import momentum
from .sleeve import MAX_NAMES_PER_SECTOR, is_blocked


def score_stock(
    prices: list[float], quality: float, *, momentum_lookback: int = 63
) -> float:
    """Per-stock score: pure momentum. Quality arg retained for API compat."""
    return momentum(prices, momentum_lookback)


def pick_stocks(
    candidates: list[dict], *, top_n: int = MAX_NAMES_PER_SECTOR
) -> list[dict]:
    """Pick the top-N candidates by `score`, skipping ETF blocklist members."""
    filtered = [c for c in candidates if not is_blocked(c.get("symbol", ""))]
    ranked = sorted(filtered, key=lambda c: c.get("score", 0.0), reverse=True)
    return ranked[:top_n]


def select_for_sectors(
    sector_to_candidates: dict[str, list[dict]],
    *,
    top_n: int = MAX_NAMES_PER_SECTOR,
) -> dict[str, list[dict]]:
    """For each sector -> list of stock candidates -> picked top_n."""
    out: dict[str, list[dict]] = {}
    for sec, candidates in sector_to_candidates.items():
        out[sec] = pick_stocks(candidates, top_n=top_n)
    return out
