"""PRICE-based exits (opposite of Oracle).

Priority:
  1. Hard stop hit               -> EXIT IMMEDIATELY
  2. Profit target hit           -> TAKE PROFIT
  3. Trailing stop tripped       -> EXIT (only if trailing armed)
  4. Time stop date passed       -> EXIT AT MARKET
  5. otherwise                   -> HOLD
"""
from __future__ import annotations

from typing import Optional

from .sleeve import AchillesPosition


def evaluate(
    pos: AchillesPosition, current_price: float, today: str
) -> dict:
    """Return {action, reason}.

    action: 'exit' | 'hold'
    """
    if current_price <= 0:
        return {"action": "hold", "reason": "no_price"}

    # Update high-water for trailing logic
    if current_price > pos.high_water_price:
        pos.high_water_price = current_price

    # 1. Hard stop
    if current_price <= pos.hard_stop_price:
        return {"action": "exit", "reason": "hard_stop"}

    # 2. Profit target
    if current_price >= pos.profit_target_price:
        return {"action": "exit", "reason": "profit_target"}

    # 3. Trailing stop (optional)
    if pos.trail_armed_at > 0 and pos.trail_pct > 0:
        # arm when high-water reaches entry * (1 + trail_armed_at)
        arm_price = pos.entry_price * (1.0 + pos.trail_armed_at)
        if pos.high_water_price >= arm_price:
            trail_level = pos.high_water_price * (1.0 - pos.trail_pct)
            if current_price <= trail_level:
                return {"action": "exit", "reason": "trailing_stop"}

    # 4. Time stop
    if today >= pos.time_stop_date:
        return {"action": "exit", "reason": "time_stop"}

    return {"action": "hold", "reason": "in_window"}
