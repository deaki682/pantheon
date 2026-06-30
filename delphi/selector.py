"""Select top-N stocks from universe momentum ranking."""
from __future__ import annotations

from .sleeve import MAX_POSITIONS


def select_top(
    ranked: list[dict],
    *,
    top_n: int = MAX_POSITIONS,
) -> list[dict]:
    """Pick the top N from the momentum-ranked list."""
    return ranked[:top_n]
