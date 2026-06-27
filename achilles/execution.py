"""Achilles order planning.

Pure: takes a brief + current price + sleeve state, returns an order plan.
The plan is consumed by the command-file orchestration layer which places
the actual broker order.
"""
from __future__ import annotations

from typing import Optional

from .brief import Brief
from .sleeve import AchillesSleeve, MAX_TRADES_PER_DAY, MIN_SCORE_TO_OPEN


def plan_open(
    sleeve: AchillesSleeve,
    brief: Brief,
    *,
    today: str,
    current_price: float,
) -> Optional[dict]:
    """Return an open-order dict, or None if the trade is blocked."""
    if sleeve.halted:
        return None
    if brief.play is None or brief.disqualifiers:
        return None
    if brief.score < MIN_SCORE_TO_OPEN:
        return None
    if brief.event_id in sleeve.positions:
        return None
    if sleeve.trades_today(today) >= MAX_TRADES_PER_DAY:
        return None
    if current_price <= 0:
        return None
    return {
        "side": "buy",
        "symbol": brief.symbol,
        "event_id": brief.event_id,
        "event_class": brief.event_class,
        "dollars": brief.play.entry_dollars,
        "entry_price": current_price,
        "hard_stop_price": brief.play.hard_stop_price,
        "profit_target_price": brief.play.profit_target_price,
        "time_stop_date": brief.play.time_stop_date,
        "score": brief.score,
    }


def plan_exits(
    sleeve: AchillesSleeve,
    quotes: dict[str, float],
    today: str,
) -> list[dict]:
    """Walk every open position, evaluate exit, emit exit orders for triggers."""
    from . import exits as exit_module
    out: list[dict] = []
    for event_id, pos in list(sleeve.positions.items()):
        price = quotes.get(pos.symbol, pos.entry_price)
        verdict = exit_module.evaluate(pos, price, today)
        if verdict["action"] == "exit":
            out.append({
                "side": "sell",
                "symbol": pos.symbol,
                "event_id": event_id,
                "shares": pos.shares,
                "exit_price": price,
                "reason": verdict["reason"],
            })
    return out
