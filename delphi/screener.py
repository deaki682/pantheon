"""Universe momentum screener.

Computes 13-week momentum for all stocks in the Delphi universe and
returns a ranked list filtered to names above their 20-day MA.

Supports LLM universe curation: additions and removals let the LLM
add IPOs/spinoffs or remove delistings without editing source code.
"""
from __future__ import annotations

from .signals import UNIVERSE, rank_by_momentum


def score_universe(
    universe_prices: dict[str, list[float]],
    *,
    additions: set[str] | None = None,
    removals: set[str] | None = None,
) -> list[dict]:
    """Score and rank the universe by momentum.

    additions: symbols to add beyond the base UNIVERSE (e.g., recent IPOs).
    removals: symbols to drop (e.g., delistings, going-concern filings).
    """
    effective = set(UNIVERSE)
    if additions:
        effective |= additions
    if removals:
        effective -= removals
    filtered = {sym: prices for sym, prices in universe_prices.items() if sym in effective}
    return rank_by_momentum(filtered)
