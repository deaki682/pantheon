"""Select top-N stocks from universe momentum ranking.

Supports LLM vetoes: the mechanical system picks the top N, but the LLM
can veto specific names (e.g., short squeeze, pending bad news). Vetoed
names are skipped and backfilled from further down the ranking.
"""
from __future__ import annotations

from .sleeve import MAX_POSITIONS


def select_top(
    ranked: list[dict],
    *,
    top_n: int = MAX_POSITIONS,
    vetoes: set[str] | None = None,
) -> list[dict]:
    """Pick the top N from the momentum-ranked list, skipping vetoed symbols."""
    skip = vetoes or set()
    selected: list[dict] = []
    for entry in ranked:
        if entry["symbol"] in skip:
            continue
        selected.append(entry)
        if len(selected) >= top_n:
            break
    return selected
