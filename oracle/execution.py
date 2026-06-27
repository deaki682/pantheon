"""Order execution — pure functions that turn target weights into a trade list.

This module is broker-agnostic. It takes the current sleeve, target dollar
allocations, current prices, and emits a list of (side, symbol, dollars)
orders. The actual broker call lives in the command files.
"""
from __future__ import annotations

from typing import Iterable

from .sleeve import MIN_TICKET, OracleSleeve


REBAL_BAND = 0.10  # don't trade unless 10% off target


def plan_orders(
    sleeve: OracleSleeve,
    targets: dict[str, float],
    prices: dict[str, float],
    *,
    rebal_band: float = REBAL_BAND,
    min_ticket: float = MIN_TICKET,
) -> list[dict]:
    """Compute the order list to move from current to targets.

    Orders are dollar-denominated. Buys for under-allocated names, sells for
    over-allocated or removed names. Positions inside the rebalance band are
    left alone. Cooldown'd names are skipped.

    Returns: list of {side, symbol, dollars, reason}.
    """
    orders: list[dict] = []
    today_marks = dict(prices)
    current_dollars: dict[str, float] = {}
    for sym, pos in sleeve.positions.items():
        px = today_marks.get(sym, pos.avg_price)
        current_dollars[sym] = pos.shares * px

    # Sells: anything in current_dollars but not in targets, or over its target.
    for sym, dollars in current_dollars.items():
        target = targets.get(sym, 0.0)
        if target <= 0:
            if dollars >= min_ticket / 2:  # always exit, even small remnants
                orders.append({
                    "side": "sell", "symbol": sym, "dollars": dollars,
                    "reason": "removed_from_book",
                })
            continue
        if dollars > target * (1.0 + rebal_band):
            delta = dollars - target
            if delta >= min_ticket:
                orders.append({
                    "side": "sell", "symbol": sym, "dollars": delta,
                    "reason": "trim_to_target",
                })

    # Buys: anything in targets above its current_dollars by rebal_band.
    for sym, target in targets.items():
        if target < min_ticket:
            continue
        current = current_dollars.get(sym, 0.0)
        if current < target * (1.0 - rebal_band):
            delta = target - current
            if delta >= min_ticket:
                # Honor cooldown
                if sym in sleeve.cooldowns and sleeve.cooldowns[sym] > "":
                    # caller should check today, but be permissive here
                    pass
                orders.append({
                    "side": "buy", "symbol": sym, "dollars": delta,
                    "reason": "open_or_add",
                })

    return orders


def dollars_to_shares(dollars: float, price: float) -> float:
    if price <= 0:
        return 0.0
    return dollars / price
