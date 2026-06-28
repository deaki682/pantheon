"""Delphi order planning.

Translates a rotation plan + selected per-sector candidates into target
dollar allocations, then to buy/sell orders. Applies sector caps,
per-name caps, max names per sector, and the 20% rebalance band.

Score-weighted allocation (default): capital within each sector is
proportional to the candidate's score, not equal-weight. This tilts
more dollars toward higher-conviction picks.

SPY overlay: after sector targets are built, excess cash is deployed
into SPY to maintain market exposure. The overlay is handled by
`overlay_orders`, not `build_targets`, so the sleeve can track
sector picks and the SPY floor separately.
"""
from __future__ import annotations

from .sleeve import (
    CASH_FLOOR, MAX_NAMES_PER_SECTOR, MIN_TICKET, OVERLAY_SYMBOL,
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
    then score-weighted across the picked stocks in each sector. Honors
    per-name, per-sector, max-names caps, and the ETF blocklist.
    """
    if equity <= 0 or risk_budget <= 0 or not picks_by_sector:
        return {}
    invest_dollars = (1.0 - CASH_FLOOR) * risk_budget * equity
    n_sectors = len(picks_by_sector)
    per_sector_dollars = invest_dollars / n_sectors
    per_sector_cap_dollars = PER_SECTOR_CAP * equity
    per_sector_dollars = min(per_sector_dollars, per_sector_cap_dollars)
    per_name_cap_dollars = PER_NAME_CAP * equity

    targets: dict[str, float] = {}
    for sec, picks in picks_by_sector.items():
        valid = [p for p in picks if not is_blocked(p.get("symbol", ""))]
        valid = valid[:MAX_NAMES_PER_SECTOR]
        if not valid:
            continue
        scores = [max(p.get("score", 0.0), 0.01) for p in valid]
        total_score = sum(scores)
        for p, s in zip(valid, scores):
            alloc = per_sector_dollars * (s / total_score) if total_score > 0 else per_sector_dollars / len(valid)
            alloc = min(alloc, per_name_cap_dollars)
            if alloc < MIN_TICKET:
                continue
            targets[p["symbol"]] = alloc
    return targets


def overlay_orders(
    sleeve: DelphiSleeve,
    sector_targets: dict[str, float],
    prices: dict[str, float],
    *,
    min_ticket: float = MIN_TICKET,
) -> list[dict]:
    """Compute SPY overlay buy/sell orders.

    After sector orders execute, remaining cash above CASH_FLOOR buys SPY.
    When cash is needed for sector picks, SPY is sold first.
    """
    orders: list[dict] = []
    spy_px = prices.get(OVERLAY_SYMBOL)
    if not spy_px or spy_px <= 0:
        return orders

    equity = sleeve.equity(prices)
    floor = CASH_FLOOR * equity

    spy_pos = sleeve.positions.get(OVERLAY_SYMBOL)
    spy_current = (spy_pos.shares * spy_px) if spy_pos else 0.0

    sector_invested = sum(
        pos.shares * prices.get(sym, pos.avg_price)
        for sym, pos in sleeve.positions.items()
        if sym != OVERLAY_SYMBOL
    )
    sector_target_total = sum(sector_targets.values())
    sector_delta = sector_target_total - sector_invested

    if sector_delta > 0 and spy_current > 0:
        sell_amount = min(spy_current, sector_delta)
        if sell_amount >= min_ticket:
            orders.append({
                "side": "sell", "symbol": OVERLAY_SYMBOL,
                "dollars": sell_amount, "reason": "free_cash_for_sectors",
            })

    available_for_overlay = max(0.0, sleeve.cash - floor - max(0, sector_delta))
    if available_for_overlay >= min_ticket and sector_delta <= 0:
        orders.append({
            "side": "buy", "symbol": OVERLAY_SYMBOL,
            "dollars": available_for_overlay, "reason": "spy_overlay",
        })

    return orders


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
