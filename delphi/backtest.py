"""Delphi momentum compounder backtest.

Replays historical daily close prices through the momentum compounder
strategy: top 10 by 13-week momentum, exit on 20-day MA break, weekly
rebalance, equal-weight.  Compares against SPY buy-and-hold.
"""
from __future__ import annotations

import json
import logging
import os
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from delphi.signals import UNIVERSE, momentum, moving_average, rank_by_momentum
from delphi.sleeve import (
    CASH_FLOOR, COOLDOWN_DAYS, MA_PERIOD, MAX_POSITIONS,
    MIN_TICKET, MOMENTUM_LOOKBACK, PER_NAME_CAP, REBAL_BAND, DelphiSleeve,
)

log = logging.getLogger("delphi.backtest")

STOCK_PRICES_PATH = "cache/delphi_bt_stock_prices.json"
OUTPUT_PATH = "cache/delphi_bt_results.json"
CURVE_PATH = "cache/delphi_bt_curve.json"
JOURNAL_PATH = "cache/delphi_bt_journal.jsonl"

REBALANCE_INTERVAL_DAYS = 5


def load_prices(path: str) -> dict[str, dict[str, dict]]:
    with open(path) as f:
        raw = json.load(f)
    out: dict[str, dict[str, dict]] = {}
    for sym, bars in raw.items():
        by_date: dict[str, dict] = {}
        for b in bars:
            by_date[b["date"]] = b
        out[sym] = by_date
    return out


def get_trading_days(prices: dict[str, dict[str, dict]]) -> list[str]:
    all_dates: set[str] = set()
    for by_date in prices.values():
        all_dates.update(by_date.keys())
    return sorted(all_dates)


def _price_series(
    by_date: dict[str, dict], days: list[str], end_idx: int, lookback: int,
) -> list[float]:
    start = max(0, end_idx - lookback)
    return [
        by_date[days[i]]["close"]
        for i in range(start, end_idx + 1)
        if days[i] in by_date
    ]


@dataclass
class BacktestConfig:
    initial_cash: float = 1000.0
    rebalance_interval: int = REBALANCE_INTERVAL_DAYS
    max_positions: int = MAX_POSITIONS
    momentum_lookback: int = MOMENTUM_LOOKBACK
    ma_period: int = MA_PERIOD
    cash_floor: float = CASH_FLOOR
    per_name_cap: float = PER_NAME_CAP
    rebal_band: float = REBAL_BAND
    cooldown_days: int = COOLDOWN_DAYS


@dataclass
class BacktestTrade:
    symbol: str
    side: str
    date: str
    price: float
    dollars: float
    shares: float
    reason: str = ""


def run_backtest(
    stock_prices: dict[str, dict[str, dict]],
    cfg: BacktestConfig,
    *,
    start_date: str = "",
    end_date: str = "",
) -> dict:
    trading_days = get_trading_days(stock_prices)
    if start_date:
        trading_days = [d for d in trading_days if d >= start_date]
    if end_date:
        trading_days = [d for d in trading_days if d <= end_date]
    if not trading_days:
        return {"error": "No trading days in range"}

    sleeve = DelphiSleeve(initial_cash=cfg.initial_cash)
    sleeve.cooldown_days = cfg.cooldown_days

    trades: list[BacktestTrade] = []
    equity_curve: list[dict] = []
    holdings_log: list[dict] = []
    last_rebalance_idx = -cfg.rebalance_interval

    spy_start = None

    for day_idx, today in enumerate(trading_days):
        sleeve.process_settlements(today)

        today_prices: dict[str, float] = {}
        for sym, by_date in stock_prices.items():
            if today in by_date:
                today_prices[sym] = by_date[today]["close"]

        if spy_start is None and "SPY" in today_prices:
            spy_start = today_prices["SPY"]

        if day_idx - last_rebalance_idx >= cfg.rebalance_interval:
            last_rebalance_idx = day_idx

            universe_prices: dict[str, list[float]] = {}
            for sym in UNIVERSE:
                if sym in stock_prices:
                    series = _price_series(
                        stock_prices[sym], trading_days, day_idx,
                        cfg.momentum_lookback + 10,
                    )
                    if len(series) >= cfg.momentum_lookback:
                        universe_prices[sym] = series

            if not universe_prices:
                continue

            ranked = rank_by_momentum(
                universe_prices,
                lookback=cfg.momentum_lookback,
                ma_period=cfg.ma_period,
            )
            picks = ranked[:cfg.max_positions]

            targets: dict[str, float] = {}
            eq = sleeve.equity(today_prices)
            if eq > 0 and picks:
                invest = (1.0 - cfg.cash_floor) * eq
                per_name = min(invest / len(picks), cfg.per_name_cap * eq)
                for p in picks:
                    if per_name >= MIN_TICKET:
                        targets[p["symbol"]] = per_name

            current: dict[str, float] = {}
            for sym, pos in sleeve.positions.items():
                px = today_prices.get(sym, pos.avg_price)
                current[sym] = pos.shares * px

            sells = []
            for sym, dollars in current.items():
                target = targets.get(sym, 0.0)
                if target <= 0:
                    if dollars >= MIN_TICKET / 2:
                        sells.append({"side": "sell", "symbol": sym,
                                      "dollars": dollars, "reason": "momentum_exit"})
                elif dollars > target * (1.0 + cfg.rebal_band):
                    delta = dollars - target
                    if delta >= MIN_TICKET:
                        sells.append({"side": "sell", "symbol": sym,
                                      "dollars": delta, "reason": "trim_to_target"})

            buys = []
            for sym, target in targets.items():
                if target < MIN_TICKET:
                    continue
                cur = current.get(sym, 0.0)
                if cur < target * (1.0 - cfg.rebal_band):
                    delta = target - cur
                    if delta >= MIN_TICKET:
                        buys.append({"side": "buy", "symbol": sym,
                                     "dollars": delta, "reason": "momentum_entry"})

            for order in sells:
                sym = order["symbol"]
                if sym not in sleeve.positions:
                    continue
                pos = sleeve.positions[sym]
                px = today_prices.get(sym, pos.avg_price)
                dollars = order["dollars"]
                shares = min(pos.shares, dollars / px) if px > 0 else 0
                if shares > 0 and sleeve.sell(sym, shares, px, today):
                    trades.append(BacktestTrade(
                        symbol=sym, side="sell", date=today,
                        price=px, dollars=shares * px, shares=shares,
                        reason=order.get("reason", ""),
                    ))

            for order in buys:
                sym = order["symbol"]
                px = today_prices.get(sym)
                if not px or px <= 0:
                    continue
                dollars = order["dollars"]
                shares = dollars / px
                if shares > 0 and sleeve.buy(sym, shares, px, today):
                    trades.append(BacktestTrade(
                        symbol=sym, side="buy", date=today,
                        price=px, dollars=shares * px, shares=shares,
                        reason=order.get("reason", ""),
                    ))

            holdings_log.append({
                "date": today,
                "holdings": list(sleeve.positions.keys()),
            })

        eq = sleeve.equity(today_prices)
        spy_px = today_prices.get("SPY", 0)
        spy_ret = (spy_px / spy_start - 1.0) if (spy_start and spy_px) else 0.0
        equity_curve.append({
            "date": today,
            "equity": round(eq, 2),
            "cash": round(sleeve.cash, 2),
            "positions": len(sleeve.positions),
            "spy_price": spy_px,
            "spy_return": round(spy_ret, 4),
            "delphi_return": round((eq / cfg.initial_cash - 1.0), 4),
        })

    final_eq = sleeve.equity(today_prices) if trading_days else cfg.initial_cash
    total_return = (final_eq / cfg.initial_cash - 1.0)

    spy_final = today_prices.get("SPY", spy_start or 0) if trading_days else 0
    spy_return = (spy_final / spy_start - 1.0) if spy_start else 0.0
    alpha = total_return - spy_return

    daily_returns = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]["equity"]
        curr = equity_curve[i]["equity"]
        if prev > 0:
            daily_returns.append((curr - prev) / prev)
    if len(daily_returns) > 1:
        mean_daily = statistics.mean(daily_returns)
        std_daily = statistics.stdev(daily_returns)
        sharpe = (mean_daily / std_daily) * (252 ** 0.5) if std_daily > 0 else 0
    else:
        sharpe = 0

    peak = cfg.initial_cash
    max_dd = 0.0
    max_dd_date = ""
    for pt in equity_curve:
        if pt["equity"] > peak:
            peak = pt["equity"]
        dd = (peak - pt["equity"]) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            max_dd_date = pt["date"]

    buy_trades = [t for t in trades if t.side == "buy"]
    sell_trades = [t for t in trades if t.side == "sell"]
    turnover = sum(t.dollars for t in trades)

    results = {
        "period": f"{trading_days[0]} to {trading_days[-1]}" if trading_days else "N/A",
        "trading_days": len(trading_days),
        "config": {
            "initial_cash": cfg.initial_cash,
            "rebalance_interval": cfg.rebalance_interval,
            "max_positions": cfg.max_positions,
            "momentum_lookback": cfg.momentum_lookback,
            "ma_period": cfg.ma_period,
        },
        "performance": {
            "final_equity": round(final_eq, 2),
            "total_return_pct": round(total_return * 100, 2),
            "spy_return_pct": round(spy_return * 100, 2),
            "alpha_pct": round(alpha * 100, 2),
            "sharpe": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "max_drawdown_date": max_dd_date,
        },
        "trades": {
            "total": len(trades),
            "buys": len(buy_trades),
            "sells": len(sell_trades),
            "turnover": round(turnover, 2),
        },
    }

    return {
        "results": results,
        "equity_curve": equity_curve,
        "trades": [t.__dict__ for t in trades],
        "holdings_log": holdings_log,
    }
