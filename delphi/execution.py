"""Delphi order planning — momentum compounder.

Equal-weight allocation across top N momentum picks. No sector caps,
no SPY overlay. Sells positions that fell below their trailing MA stop,
then buys new top-ranked names to fill slots.
"""
from __future__ import annotations

from .sleeve import CASH_FLOOR, MIN_TICKET, PER_NAME_CAP, REBAL_BAND, DelphiSleeve


def build_targets(
    picks: list[dict],
    equity: float,
    *,
    risk_budget: float,
) -> dict[str, float]:
    """Return symbol -> $ target. Equal-weight across picks."""
    if equity <= 0 or risk_budget <= 0 or not picks:
        return {}
    invest_dollars = (1.0 - CASH_FLOOR) * risk_budget * equity
    n = len(picks)
    per_name = invest_dollars / n
    per_name_cap = PER_NAME_CAP * equity
    per_name = min(per_name, per_name_cap)

    targets: dict[str, float] = {}
    for p in picks:
        sym = p["symbol"]
        alloc = per_name
        if alloc < MIN_TICKET:
            continue
        targets[sym] = alloc
    return targets


def plan_orders(
    sleeve: DelphiSleeve,
    targets: dict[str, float],
    prices: dict[str, float],
    *,
    rebal_band: float = REBAL_BAND,
    min_ticket: float = MIN_TICKET,
) -> list[dict]:
    """Compute orders from current sleeve state to targets.

    Sells first (positions not in targets or overweight), then buys.
    """
    orders: list[dict] = []
    current: dict[str, float] = {}
    for sym, pos in sleeve.positions.items():
        px = prices.get(sym, pos.avg_price)
        current[sym] = pos.shares * px

    for sym, dollars in current.items():
        target = targets.get(sym, 0.0)
        if target <= 0:
            if dollars >= min_ticket / 2:
                orders.append({
                    "side": "sell", "symbol": sym, "dollars": dollars,
                    "reason": "momentum_exit",
                })
            continue
        if dollars > target * (1.0 + rebal_band):
            delta = dollars - target
            if delta >= min_ticket:
                orders.append({
                    "side": "sell", "symbol": sym, "dollars": delta,
                    "reason": "trim_to_target",
                })

    for sym, target in targets.items():
        if target < min_ticket:
            continue
        cur = current.get(sym, 0.0)
        if cur < target * (1.0 - rebal_band):
            delta = target - cur
            if delta >= min_ticket:
                orders.append({
                    "side": "buy", "symbol": sym, "dollars": delta,
                    "reason": "momentum_entry",
                })
    return orders
