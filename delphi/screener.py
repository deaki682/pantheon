"""Universe momentum screener.

Computes 13-week momentum for all stocks in the Delphi universe and
returns a ranked list filtered to names above their 20-day MA.
"""
from __future__ import annotations

from .signals import UNIVERSE, rank_by_momentum


def score_universe(
    universe_prices: dict[str, list[float]],
) -> list[dict]:
    """Score and rank the full universe by momentum.

    `universe_prices` maps symbol -> list of daily close prices
    (oldest first, most recent last). Only symbols in the Delphi
    UNIVERSE are scored.
    """
    filtered = {sym: prices for sym, prices in universe_prices.items() if sym in UNIVERSE}
    return rank_by_momentum(filtered)
