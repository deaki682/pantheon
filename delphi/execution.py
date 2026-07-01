"""Delphi order planning — momentum compounder with LLM judgment.

Equal-weight allocation across top N momentum picks, with optional
conviction tilts from the LLM. Sells positions that fell below their
trailing MA stop (unless the LLM overrides), then buys new top-ranked
names to fill slots.
"""
from __future__ import annotations

from .sleeve import CASH_FLOOR, MIN_TICKET, PER_NAME_CAP, REBAL_BAND, DelphiSleeve


def build_targets(
    picks: list[dict],
    equity: float,
    *,
    risk_budget: float,
    weight_overrides: dict[str, float] | None = None,
) -> dict[str, float]:
    """Return symbol -> $ target.

    Starts equal-weight, then applies optional LLM conviction multipliers.
    A weight_override of 1.5 means 150% of equal-weight; 0.5 means 50%.
    Total allocation is re-normalized after overrides so it doesn't exceed
    the investable amount.
    """
    if equity <= 0 or risk_budget <= 0 or not picks:
        return {}
    invest_dollars = (1.0 - CASH_FLOOR) * risk_budget * equity
    n = len(picks)
    per_name_cap = PER_NAME_CAP * equity

    overrides = weight_overrides or {}
    raw_weights: dict[str, float] = {}
    for p in picks:
        sym = p["symbol"]
        raw_weights[sym] = overrides.get(sym, 1.0)

    total_weight = sum(raw_weights.values())
    if total_weight <= 0:
        return {}

    targets: dict[str, float] = {}
    for sym, w in raw_weights.items():
        alloc = invest_dollars * (w / total_weight)
        alloc = min(alloc, per_name_cap)
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
    hold_overrides: set[str] | None = None,
) -> list[dict]:
    """Compute orders from current sleeve state to targets.

    Sells first (positions not in targets or overweight), then buys.
    hold_overrides: symbols the LLM wants to keep despite MA breach.
    These positions won't generate sell orders even if not in targets.
    """
    holds = hold_overrides or set()
    orders: list[dict] = []
    current: dict[str, float] = {}
    for sym, pos in sleeve.positions.items():
        px = prices.get(sym, pos.avg_price)
        current[sym] = pos.shares * px

    for sym, dollars in current.items():
        if sym in holds:
            continue
        target = targets.get(sym, 0.0)
        if target <= 0:
            if dollars >= min_ticket / 2:
                orders.append({
                    "side": "sell", "symbol": sym, "dollars": dollars,
                    "reason": "momentum_exit",
                    "set_cooldown": True,
                })
            continue
        if dollars > target * (1.0 + rebal_band):
            delta = dollars - target
            if delta >= min_ticket:
                # A trim keeps the name in the book by design — cooling it
                # would block future top-ups and force drift from target.
                # Cooldowns exist to stop exit->re-entry churn, so only full
                # momentum exits set one.
                orders.append({
                    "side": "sell", "symbol": sym, "dollars": delta,
                    "reason": "trim_to_target",
                    "set_cooldown": False,
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
