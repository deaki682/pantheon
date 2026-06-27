"""Delphi order planning.

Translates a rotation plan + selected per-sector candidates into target
dollar allocations, then to buy/sell orders. Applies sector caps,
per-name caps, max names per sector, and the 20% rebalance band.
"""
from __future__ import annotations

from .sleeve import (
    CASH_FLOOR, MAX_NAMES_PER_SECTOR, MIN_TICKET,
    PER_NAME_CAP, PER_SECTOR_CAP, REBAL_BAND, DelphiSleeve, is_blocked,
)


def build_targets(
    picks_by_sector: dict[str, list[dict]],
    equity: float,
    *,
    risk_budget: float,
) -> dict[str, float]:
    """Return symbol -> $ target.

    Allocates (1 - CASH_FLOOR) * risk_budget * equity across sectors equally,
    then evenly across the picked stocks in each sector. Honors per-name,
    per-sector, max-names caps, and the ETF blocklist.
    """
    if equity <= 0 or risk_budget <= 0 or not picks_by_sector:
        return {}
    invest_dollars = (1.0 - CASH_FLOOR) * risk_budget * equity
    n_sectors = len(picks_by_sector)
    per_sector_dollars = invest_dollars / n_sectors
    # Cap per sector by the absolute sector cap (40%).
    per_sector_cap_dollars = PER_SECTOR_CAP * equity
    per_sector_dollars = min(per_sector_dollars, per_sector_cap_dollars)
    per_name_cap_dollars = PER_NAME_CAP * equity

    targets: dict[str, float] = {}
    for sec, picks in picks_by_sector.items():
        valid = [p for p in picks if not is_blocked(p.get("symbol", ""))]
        valid = valid[:MAX_NAMES_PER_SECTOR]
        if not valid:
            continue
        per_name = per_sector_dollars / len(valid)
        per_name = min(per_name, per_name_cap_dollars)
        if per_name < MIN_TICKET:
            continue
        for p in valid:
            targets[p["symbol"]] = per_name
    return targets


def plan_orders(
    sleeve: DelphiSleeve,
    targets: dict[str, float],
    prices: dict[str, float],
    *,
    rebal_band: float = REBAL_BAND,
    min_ticket: float = MIN_TICKET,
) -> list[dict]:
    """Compute orders from current sleeve state to targets."""
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
                    "reason": "sector_rotated_out",
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
        if is_blocked(sym):
            continue
        if target < min_ticket:
            continue
        cur = current.get(sym, 0.0)
        if cur < target * (1.0 - rebal_band):
            delta = target - cur
            if delta >= min_ticket:
                orders.append({
                    "side": "buy", "symbol": sym, "dollars": delta,
                    "reason": "open_or_add",
                })
    return orders
