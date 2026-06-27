"""THESIS-ANCHORED exits.

Oracle does NOT use price stop losses. This is opposite of typical traders.

Exit triggers:
  - thesis_break    -> SELL  (moat AND quality both collapsed)
  - bull_hit        -> TRIM HALF
  - catalysts_done  -> REVIEW (look for fresh thesis)
  - bear_hit        -> REVIEW (NOT auto-sell; trust own research)
  - hold otherwise

Returns a structured exit signal that execution layer consumes.
"""
from __future__ import annotations

from typing import Optional


THESIS_BREAK_MOAT = 0.2  # below this -> moat is broken
THESIS_BREAK_QUALITY = 0.2  # below this -> quality has collapsed


def exit_signal(
    dossier: dict,
    current_price: float,
    *,
    catalysts_remaining: int = 1,
) -> dict:
    """Return an exit signal dict: {action, reason, fraction}.

    action: 'sell' | 'trim' | 'review' | 'hold'
    fraction: how much of the position to sell (0..1)
    """
    ratings = dossier.get("ratings", {})
    moat = ratings.get("moat", 0.0)
    quality = ratings.get("quality", 0.0)

    if moat < THESIS_BREAK_MOAT and quality < THESIS_BREAK_QUALITY:
        return {
            "action": "sell",
            "reason": "thesis_break",
            "fraction": 1.0,
        }

    scenarios = dossier.get("scenarios", {})
    bull = scenarios.get("bull", {}).get("target", 0.0)
    bear = scenarios.get("bear", {}).get("target", 0.0)

    if bull > 0 and current_price >= bull:
        return {
            "action": "trim",
            "reason": "bull_hit",
            "fraction": 0.5,
        }

    if catalysts_remaining <= 0:
        return {
            "action": "review",
            "reason": "catalysts_done",
            "fraction": 0.0,
        }

    if bear > 0 and current_price <= bear:
        return {
            "action": "review",
            "reason": "bear_hit",
            "fraction": 0.0,
        }

    return {"action": "hold", "reason": "thesis_intact", "fraction": 0.0}
