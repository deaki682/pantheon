"""Minimal backtest harness for Oracle's strategy.

Given a list of dossiers with conviction + horizon and a price history,
simulate buys at the dossier date and compute realized returns over the
horizon. Used to validate calibration before scaling capital.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class BacktestTrade:
    symbol: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float
    conviction: float


def run(
    dossiers: list[dict],
    prices: dict[str, list[tuple[str, float]]],  # symbol -> [(date, close), ...]
    *,
    default_horizon_days: int = 365,
) -> dict:
    """Simulate buy-and-hold for each dossier.

    Returns: {trades: [...], mean_return: float, hit_rate: float, n: int}
    """
    trades: list[BacktestTrade] = []
    for d in dossiers:
        sym = d.get("symbol", "")
        if sym not in prices or not prices[sym]:
            continue
        entry_date = d.get("created_at", "")[:10]
        if not entry_date:
            continue
        horizon_days = int(round(float(d.get("horizon_years", 1.0)) * 365)) or default_horizon_days
        try:
            entry_dt = datetime.strptime(entry_date, "%Y-%m-%d")
        except ValueError:
            continue
        exit_dt = entry_dt + timedelta(days=horizon_days)
        entry_price = _price_on_or_after(prices[sym], entry_dt)
        exit_price = _price_on_or_after(prices[sym], exit_dt)
        if entry_price <= 0 or exit_price <= 0:
            continue
        ret = exit_price / entry_price - 1.0
        trades.append(
            BacktestTrade(
                symbol=sym, entry_date=entry_dt.strftime("%Y-%m-%d"),
                exit_date=exit_dt.strftime("%Y-%m-%d"),
                entry_price=entry_price, exit_price=exit_price,
                return_pct=ret, conviction=float(d.get("conviction", 0.0)),
            )
        )
    if not trades:
        return {"trades": [], "mean_return": 0.0, "hit_rate": 0.0, "n": 0}
    mean = sum(t.return_pct for t in trades) / len(trades)
    hits = sum(1 for t in trades if t.return_pct > 0)
    return {
        "trades": [t.__dict__ for t in trades],
        "mean_return": mean,
        "hit_rate": hits / len(trades),
        "n": len(trades),
    }


def _price_on_or_after(history: list[tuple[str, float]], target: datetime) -> float:
    target_s = target.strftime("%Y-%m-%d")
    for date_s, close in history:
        if date_s >= target_s and close > 0:
            return close
    # fall back to last known
    if history:
        return history[-1][1]
    return 0.0
