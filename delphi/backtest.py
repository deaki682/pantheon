#!/usr/bin/env python3
"""Full-fidelity Delphi backtest.

Replays historical sector ETF + individual stock prices through the complete
Delphi cycle: sector scoring -> regime classification -> stock selection ->
target allocation -> order execution.  Compares against SPY buy-and-hold.

Data files (pre-fetched via fetch_backtest_data.py or the /delphi skill):
  cache/delphi_bt_sector_prices.json   — {ETF: [{date, close, ...}]}
  cache/delphi_bt_stock_prices.json    — {SYM: [{date, close, ...}]}
  cache/delphi_bt_fundamentals.json    — {SYM: {FundamentalSnapshot fields}}

Usage:
    python -m delphi.backtest
    python -m delphi.backtest --start 2025-01-01 --end 2026-06-28
    python -m delphi.backtest --sweep   # parameter grid search
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from delphi.signals import SECTOR_MAP, TIMEFRAMES, TIMEFRAME_WEIGHTS, momentum, score_sectors
from delphi.rotation import breadth, classify_regime, regime_params, rotation_plan
from delphi.screener import quality_for_delphi
from delphi.selector import score_stock
from delphi.sleeve import (
    BLOCKLIST, CASH_FLOOR, COOLDOWN_DAYS, MAX_NAMES_PER_SECTOR,
    MIN_TICKET, PER_NAME_CAP, PER_SECTOR_CAP, REBAL_BAND, DelphiSleeve,
)
from delphi.execution import build_targets, plan_orders
from shared.fundamentals import FundamentalSnapshot

log = logging.getLogger("delphi.backtest")

SECTOR_PRICES_PATH = "cache/delphi_bt_sector_prices.json"
STOCK_PRICES_PATH = "cache/delphi_bt_stock_prices.json"
FUNDAMENTALS_PATH = "cache/delphi_bt_fundamentals.json"
OUTPUT_PATH = "cache/delphi_bt_results.json"
CURVE_PATH = "cache/delphi_bt_curve.json"
JOURNAL_PATH = "cache/delphi_bt_journal.jsonl"

REBALANCE_INTERVAL_DAYS = 5

# Sector ETF -> top holdings (stable large/mid caps for backtesting).
# These approximate each SPDR sector ETF's top constituents.
SECTOR_CONSTITUENTS: dict[str, list[str]] = {
    "technology":     ["AAPL", "MSFT", "NVDA", "AVGO", "CRM", "AMD", "ADBE", "ORCL", "CSCO", "ACN"],
    "financials":     ["BRK.B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK"],
    "energy":         ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "PXD", "OXY"],
    "healthcare":     ["UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "AMGN"],
    "industrials":    ["GE", "CAT", "RTX", "HON", "UNP", "BA", "DE", "LMT", "UPS", "ADP"],
    "staples":        ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "MDLZ", "CL", "KHC"],
    "discretionary":  ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "CMG"],
    "utilities":      ["NEE", "DUK", "SO", "D", "SRE", "AEP", "EXC", "XEL", "ED", "WEC"],
    "real_estate":    ["PLD", "AMT", "CCI", "EQIX", "PSA", "SPG", "O", "WELL", "DLR", "VICI"],
    "materials":      ["LIN", "APD", "SHW", "ECL", "FCX", "NEM", "NUE", "VMC", "MLM", "DOW"],
    "communication":  ["META", "GOOGL", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "CHTR", "EA"],
}

ALL_STOCK_SYMBOLS = sorted({s for syms in SECTOR_CONSTITUENTS.values() for s in syms})
SECTOR_ETFS = list(SECTOR_MAP.keys())
ALL_ETFS = SECTOR_ETFS + ["SPY"]


# ── data loading ──────────────────────────────────────────────────────

def load_prices(path: str) -> dict[str, dict[str, dict]]:
    """Load as {SYMBOL: {date_str: {close, ...}}}."""
    with open(path) as f:
        raw = json.load(f)
    out: dict[str, dict[str, dict]] = {}
    for sym, bars in raw.items():
        by_date: dict[str, dict] = {}
        for b in bars:
            by_date[b["date"]] = b
        out[sym] = by_date
    return out


def load_fundamentals(path: str) -> dict[str, FundamentalSnapshot]:
    try:
        with open(path) as f:
            raw = json.load(f)
        return {sym: FundamentalSnapshot(**data) for sym, data in raw.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_trading_days(prices: dict[str, dict[str, dict]]) -> list[str]:
    all_dates: set[str] = set()
    for by_date in prices.values():
        all_dates.update(by_date.keys())
    return sorted(all_dates)


def _price_series(by_date: dict[str, dict], days: list[str], end_idx: int, lookback: int) -> list[float]:
    """Extract a close-price series ending at days[end_idx], going back `lookback` trading days."""
    start = max(0, end_idx - lookback)
    return [by_date[days[i]]["close"] for i in range(start, end_idx + 1) if days[i] in by_date]


# ── simulation ────────────────────────────────────────────────────────

@dataclass
class BacktestConfig:
    initial_cash: float = 1000.0
    rebalance_interval: int = REBALANCE_INTERVAL_DAYS
    timeframe_weights: tuple[float, ...] = TIMEFRAME_WEIGHTS
    momentum_weight: float = 0.6
    quality_weight: float = 0.4
    quality_override: Optional[float] = None
    top_n_sectors: Optional[int] = None
    regime_enabled: bool = True
    cash_floor: float = CASH_FLOOR
    per_name_cap: float = PER_NAME_CAP
    per_sector_cap: float = PER_SECTOR_CAP
    max_names_per_sector: int = MAX_NAMES_PER_SECTOR
    rebal_band: float = REBAL_BAND
    cooldown_days: int = COOLDOWN_DAYS
    score_weighted: bool = False
    spy_overlay: bool = False
    spy_overlay_frac: float = 0.0
    momentum_lookback: int = 63


@dataclass
class BacktestTrade:
    symbol: str
    sector: str
    side: str
    date: str
    price: float
    dollars: float
    shares: float
    reason: str = ""


def _custom_score_sectors(
    sector_prices: dict[str, list[float]],
    spy_prices: list[float],
    weights: tuple[float, ...],
) -> dict[str, float]:
    """Score sectors with custom timeframe weights."""
    out: dict[str, float] = {}
    for etf, prices in sector_prices.items():
        sec_name = SECTOR_MAP.get(etf.upper())
        if not sec_name:
            continue
        weighted = sum(w * momentum(prices, tf) for w, tf in zip(weights, TIMEFRAMES))
        rs_sec = momentum(prices, 63)
        rs_spy = momentum(spy_prices, 63)
        relative = rs_sec - rs_spy
        out[sec_name] = weighted + 0.25 * relative
    return out


def run_backtest(
    sector_prices: dict[str, dict[str, dict]],
    stock_prices: dict[str, dict[str, dict]],
    fundamentals: dict[str, FundamentalSnapshot],
    cfg: BacktestConfig,
    *,
    start_date: str = "",
    end_date: str = "",
) -> dict:
    all_prices = {**sector_prices, **stock_prices}
    trading_days = get_trading_days(all_prices)
    if start_date:
        trading_days = [d for d in trading_days if d >= start_date]
    if end_date:
        trading_days = [d for d in trading_days if d <= end_date]
    if not trading_days:
        return {"error": "No trading days in range"}

    log.info("Backtest: %s to %s (%d days)", trading_days[0], trading_days[-1], len(trading_days))

    sleeve = DelphiSleeve(initial_cash=cfg.initial_cash)
    sleeve.cooldown_days = cfg.cooldown_days

    trades: list[BacktestTrade] = []
    equity_curve: list[dict] = []
    regime_log: list[dict] = []
    rotation_log: list[dict] = []
    last_rebalance_idx = -cfg.rebalance_interval

    spy_start = None

    for day_idx, today in enumerate(trading_days):
        sleeve.process_settlements(today)

        today_prices: dict[str, float] = {}
        for sym, by_date in all_prices.items():
            if today in by_date:
                today_prices[sym] = by_date[today]["close"]

        if spy_start is None and "SPY" in today_prices:
            spy_start = today_prices["SPY"]

        # ── Rebalance check ──
        if day_idx - last_rebalance_idx >= cfg.rebalance_interval:
            last_rebalance_idx = day_idx

            # Build sector price series (need 126+ trading days of history)
            etf_series: dict[str, list[float]] = {}
            for etf in SECTOR_ETFS:
                if etf in sector_prices:
                    etf_series[etf] = _price_series(
                        sector_prices[etf], trading_days, day_idx, 150
                    )
            spy_series = _price_series(
                sector_prices.get("SPY", {}), trading_days, day_idx, 150
            ) if "SPY" in sector_prices else []

            if len(spy_series) < 22 or len(etf_series) < 5:
                # Not enough history yet
                pass
            else:
                # 1. Score sectors
                if cfg.timeframe_weights != TIMEFRAME_WEIGHTS:
                    sector_scores = _custom_score_sectors(etf_series, spy_series, cfg.timeframe_weights)
                else:
                    sector_scores = score_sectors(etf_series, spy_series)

                # 2. Regime + rotation
                if cfg.regime_enabled:
                    plan = rotation_plan(spy_series, sector_scores)
                    regime = plan["regime"]
                    risk_budget = plan["risk_budget"]
                    chosen_sectors = plan["sectors"]
                    if cfg.top_n_sectors is not None:
                        chosen_sectors = chosen_sectors[:cfg.top_n_sectors]
                else:
                    regime = "always_in"
                    risk_budget = 1.0
                    ranked = sorted(sector_scores.items(), key=lambda kv: kv[1], reverse=True)
                    n = cfg.top_n_sectors or 3
                    chosen_sectors = [s for s, _ in ranked[:n]]

                regime_log.append({
                    "date": today, "regime": regime,
                    "risk_budget": risk_budget,
                    "spy_1m": momentum(spy_series, 21),
                    "spy_3m": momentum(spy_series, 63),
                    "breadth": breadth(sector_scores),
                })

                # 3. Per-sector stock selection
                picks_by_sector: dict[str, list[dict]] = {}
                for sec in chosen_sectors:
                    candidates: list[dict] = []
                    constituents = SECTOR_CONSTITUENTS.get(sec, [])
                    for sym in constituents:
                        if sym.upper() in BLOCKLIST:
                            continue
                        if sym not in stock_prices:
                            continue
                        sym_series = _price_series(
                            stock_prices[sym], trading_days, day_idx, cfg.momentum_lookback + 5
                        )
                        if len(sym_series) < cfg.momentum_lookback:
                            continue
                        snap = fundamentals.get(sym)
                        if cfg.quality_override is not None:
                            q = cfg.quality_override
                        else:
                            q = quality_for_delphi(snap) if snap is not None else 0.0
                        m = momentum(sym_series, cfg.momentum_lookback)
                        score = cfg.momentum_weight * m + cfg.quality_weight * q
                        candidates.append({
                            "symbol": sym,
                            "sector": sec,
                            "momentum": m,
                            "quality": q,
                            "score": score,
                        })
                    candidates.sort(key=lambda c: c["score"], reverse=True)
                    top = candidates[:cfg.max_names_per_sector]
                    if top:
                        picks_by_sector[sec] = top

                rotation_log.append({
                    "date": today,
                    "regime": regime,
                    "sectors": chosen_sectors,
                    "picks": {s: [p["symbol"] for p in ps] for s, ps in picks_by_sector.items()},
                })

                # 4. Build targets
                eq = sleeve.equity(today_prices)

                if cfg.score_weighted and picks_by_sector:
                    targets = _score_weighted_targets(
                        picks_by_sector, eq, risk_budget,
                        cfg.cash_floor, cfg.per_sector_cap, cfg.per_name_cap,
                    )
                else:
                    targets = build_targets(
                        picks_by_sector, eq, risk_budget=risk_budget,
                    )

                # 5. Plan and execute orders
                orders = plan_orders(
                    sleeve, targets, today_prices,
                    rebal_band=cfg.rebal_band,
                    min_ticket=MIN_TICKET,
                )

                # Execute sells first, then buys
                sells = [o for o in orders if o["side"] == "sell"]
                buys = [o for o in orders if o["side"] == "buy"]

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
                            symbol=sym, sector=pos.sector, side="sell",
                            date=today, price=px, dollars=shares * px,
                            shares=shares, reason=order.get("reason", ""),
                        ))

                for order in buys:
                    sym = order["symbol"]
                    px = today_prices.get(sym)
                    if not px or px <= 0:
                        continue
                    dollars = order["dollars"]
                    shares = dollars / px
                    sec = ""
                    for s, ps in picks_by_sector.items():
                        if any(p["symbol"] == sym for p in ps):
                            sec = s
                            break
                    if shares > 0 and sleeve.buy(sym, shares, px, today, sector=sec):
                        trades.append(BacktestTrade(
                            symbol=sym, sector=sec, side="buy",
                            date=today, price=px, dollars=shares * px,
                            shares=shares, reason=order.get("reason", ""),
                        ))

        # ── Record equity ──
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

    # ── Results ──
    final_eq = sleeve.equity(today_prices) if trading_days else cfg.initial_cash
    total_return = (final_eq / cfg.initial_cash - 1.0)

    # SPY benchmark
    spy_final = today_prices.get("SPY", spy_start or 0) if trading_days else 0
    spy_return = (spy_final / spy_start - 1.0) if spy_start else 0.0
    alpha = total_return - spy_return

    # Sharpe
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

    # Max drawdown
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

    # Regime distribution
    regime_counts: dict[str, int] = defaultdict(int)
    for r in regime_log:
        regime_counts[r["regime"]] += 1

    # Per-sector stats: track which sectors were chosen and their contribution
    sector_exposure: dict[str, int] = defaultdict(int)
    for r in rotation_log:
        for s in r["sectors"]:
            sector_exposure[s] += 1

    # Trade stats
    buy_trades = [t for t in trades if t.side == "buy"]
    sell_trades = [t for t in trades if t.side == "sell"]
    turnover = sum(t.dollars for t in trades)

    results = {
        "period": f"{trading_days[0]} to {trading_days[-1]}" if trading_days else "N/A",
        "trading_days": len(trading_days),
        "config": {
            "initial_cash": cfg.initial_cash,
            "rebalance_interval": cfg.rebalance_interval,
            "timeframe_weights": list(cfg.timeframe_weights),
            "momentum_weight": cfg.momentum_weight,
            "quality_weight": cfg.quality_weight,
            "quality_override": cfg.quality_override,
            "regime_enabled": cfg.regime_enabled,
            "top_n_sectors": cfg.top_n_sectors,
            "score_weighted": cfg.score_weighted,
            "momentum_lookback": cfg.momentum_lookback,
            "max_names_per_sector": cfg.max_names_per_sector,
        },
        "performance": {
            "final_equity": round(final_eq, 2),
            "total_return_pct": round(total_return * 100, 2),
            "spy_return_pct": round(spy_return * 100, 2),
            "alpha_pct": round(alpha * 100, 2),
            "sharpe": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "max_drawdown_date": max_dd_date,
            "annualized_return_pct": round(
                ((final_eq / cfg.initial_cash) ** (252 / max(1, len(trading_days))) - 1) * 100, 2
            ),
        },
        "trades": {
            "total": len(trades),
            "buys": len(buy_trades),
            "sells": len(sell_trades),
            "turnover": round(turnover, 2),
            "avg_trade_dollars": round(turnover / len(trades), 2) if trades else 0,
        },
        "regime_distribution": dict(regime_counts),
        "sector_exposure": dict(sorted(sector_exposure.items(), key=lambda kv: kv[1], reverse=True)),
        "rebalance_count": len(rotation_log),
    }

    return {
        "results": results,
        "equity_curve": equity_curve,
        "trades": [t.__dict__ for t in trades],
        "regime_log": regime_log,
        "rotation_log": rotation_log,
    }


def _score_weighted_targets(
    picks_by_sector: dict[str, list[dict]],
    equity: float,
    risk_budget: float,
    cash_floor: float,
    per_sector_cap: float,
    per_name_cap: float,
) -> dict[str, float]:
    """Allocate proportionally to score magnitude instead of equal-weight."""
    if equity <= 0 or risk_budget <= 0 or not picks_by_sector:
        return {}
    invest = (1.0 - cash_floor) * risk_budget * equity
    n_sectors = len(picks_by_sector)
    per_sector = min(invest / n_sectors, per_sector_cap * equity)
    per_name_cap_dollars = per_name_cap * equity

    targets: dict[str, float] = {}
    for sec, picks in picks_by_sector.items():
        scores = [max(p.get("score", 0.0), 0.01) for p in picks]
        total_score = sum(scores)
        for p, s in zip(picks, scores):
            alloc = per_sector * (s / total_score) if total_score > 0 else per_sector / len(picks)
            alloc = min(alloc, per_name_cap_dollars)
            if alloc >= MIN_TICKET:
                targets[p["symbol"]] = alloc
    return targets


# ── parameter sweep ──────────────────────────────────────────────────

def run_sweep(
    sector_prices: dict[str, dict[str, dict]],
    stock_prices: dict[str, dict[str, dict]],
    fundamentals: dict[str, FundamentalSnapshot],
    *,
    start_date: str = "",
    end_date: str = "",
) -> list[dict]:
    """Grid search over key parameters. Returns sorted by alpha."""
    configs = []

    # Baseline
    configs.append(("baseline", BacktestConfig()))

    # No quality (momentum-only)
    configs.append(("momentum_only", BacktestConfig(momentum_weight=1.0, quality_weight=0.0)))

    # Quality override = 0 (ignore fundamentals)
    configs.append(("quality_zero", BacktestConfig(quality_override=0.0)))

    # Heavy momentum
    configs.append(("heavy_momentum", BacktestConfig(momentum_weight=0.8, quality_weight=0.2)))

    # No regime filter
    configs.append(("no_regime", BacktestConfig(regime_enabled=False)))

    # Score-weighted allocation
    configs.append(("score_weighted", BacktestConfig(score_weighted=True)))

    # Score-weighted + momentum-only
    configs.append(("sw_mom_only", BacktestConfig(score_weighted=True, momentum_weight=1.0, quality_weight=0.0)))

    # Fewer stocks per sector (2 instead of 4)
    configs.append(("concentrated", BacktestConfig(max_names_per_sector=2)))

    # Concentrated + momentum-only
    configs.append(("conc_mom", BacktestConfig(max_names_per_sector=2, momentum_weight=1.0, quality_weight=0.0)))

    # 2 sectors instead of 3
    configs.append(("2_sectors", BacktestConfig(top_n_sectors=2)))

    # Shorter momentum lookback (21 days)
    configs.append(("short_mom", BacktestConfig(momentum_lookback=21)))

    # Longer momentum lookback (126 days)
    configs.append(("long_mom", BacktestConfig(momentum_lookback=126)))

    # Weekly rebalance
    configs.append(("weekly_rebal", BacktestConfig(rebalance_interval=5)))

    # Monthly rebalance
    configs.append(("monthly_rebal", BacktestConfig(rebalance_interval=21)))

    # Faster timeframe weights (more weight on recent)
    configs.append(("fast_weights", BacktestConfig(timeframe_weights=(0.5, 0.3, 0.2))))

    # Slow timeframe weights (more weight on long-term)
    configs.append(("slow_weights", BacktestConfig(timeframe_weights=(0.1, 0.3, 0.6))))

    # Kitchen sink: concentrated + momentum-only + score-weighted + no regime
    configs.append(("kitchen_sink", BacktestConfig(
        max_names_per_sector=2, momentum_weight=1.0, quality_weight=0.0,
        score_weighted=True, regime_enabled=False,
    )))

    results = []
    for name, cfg in configs:
        log.info("Sweep: %s", name)
        out = run_backtest(
            sector_prices, stock_prices, fundamentals, cfg,
            start_date=start_date, end_date=end_date,
        )
        if "error" in out:
            continue
        r = out["results"]
        results.append({
            "name": name,
            "return_pct": r["performance"]["total_return_pct"],
            "spy_return_pct": r["performance"]["spy_return_pct"],
            "alpha_pct": r["performance"]["alpha_pct"],
            "sharpe": r["performance"]["sharpe"],
            "max_dd_pct": r["performance"]["max_drawdown_pct"],
            "trades": r["trades"]["total"],
            "config": r["config"],
        })

    results.sort(key=lambda r: r["alpha_pct"], reverse=True)
    return results


# ── output ────────────────────────────────────────────────────────────

def print_report(output: dict) -> str:
    r = output["results"]
    p = r["performance"]
    t = r["trades"]
    lines = []
    lines.append("=" * 64)
    lines.append("DELPHI BACKTEST REPORT")
    lines.append("=" * 64)
    lines.append(f"Period           : {r['period']}")
    lines.append(f"Trading days     : {r['trading_days']}")
    lines.append("")
    lines.append("── PERFORMANCE ─────────────────────────────────────────")
    lines.append(f"Initial equity   : ${r['config']['initial_cash']:.2f}")
    lines.append(f"Final equity     : ${p['final_equity']:.2f}")
    lines.append(f"Total return     : {p['total_return_pct']:+.2f}%")
    lines.append(f"SPY return       : {p['spy_return_pct']:+.2f}%")
    lines.append(f"Alpha vs SPY     : {p['alpha_pct']:+.2f}%")
    lines.append(f"Annualized return: {p['annualized_return_pct']:+.2f}%")
    lines.append(f"Sharpe ratio     : {p['sharpe']:.2f}")
    lines.append(f"Max drawdown     : {p['max_drawdown_pct']:.2f}%")
    lines.append("")
    lines.append("── CONFIGURATION ───────────────────────────────────────")
    c = r["config"]
    lines.append(f"Rebalance every  : {c['rebalance_interval']} days")
    lines.append(f"Mom/Quality wt   : {c['momentum_weight']:.1f} / {c['quality_weight']:.1f}")
    lines.append(f"Quality override : {c['quality_override']}")
    lines.append(f"Regime filter    : {'ON' if c['regime_enabled'] else 'OFF'}")
    lines.append(f"Score weighted   : {'YES' if c['score_weighted'] else 'NO'}")
    lines.append(f"Mom lookback     : {c['momentum_lookback']}d")
    lines.append(f"Names/sector     : {c['max_names_per_sector']}")
    lines.append("")
    lines.append("── TRADES ──────────────────────────────────────────────")
    lines.append(f"Total trades     : {t['total']}")
    lines.append(f"Buys / Sells     : {t['buys']} / {t['sells']}")
    lines.append(f"Turnover         : ${t['turnover']:.2f}")
    lines.append(f"Avg trade size   : ${t['avg_trade_dollars']:.2f}")
    lines.append("")
    lines.append("── REGIME DISTRIBUTION ─────────────────────────────────")
    for regime, count in sorted(r["regime_distribution"].items()):
        pct = count / r["rebalance_count"] * 100 if r["rebalance_count"] else 0
        lines.append(f"  {regime:12s} : {count:3d} ({pct:.0f}%)")
    lines.append("")
    lines.append("── SECTOR EXPOSURE (rebalance periods) ────────────────")
    for sec, count in r["sector_exposure"].items():
        lines.append(f"  {sec:16s} : {count}")
    lines.append("")
    lines.append("=" * 64)

    text = "\n".join(lines)
    print(text)
    return text


def print_sweep(results: list[dict]) -> str:
    lines = []
    lines.append("=" * 100)
    lines.append("DELPHI PARAMETER SWEEP")
    lines.append("=" * 100)
    lines.append(f"{'Config':20s} {'Return':>8s} {'SPY':>8s} {'Alpha':>8s} {'Sharpe':>7s} {'MaxDD':>7s} {'Trades':>7s}")
    lines.append("-" * 100)
    for r in results:
        lines.append(
            f"{r['name']:20s} {r['return_pct']:+7.2f}% {r['spy_return_pct']:+7.2f}% "
            f"{r['alpha_pct']:+7.2f}% {r['sharpe']:6.2f} {r['max_dd_pct']:6.2f}% {r['trades']:6d}"
        )
    lines.append("=" * 100)
    text = "\n".join(lines)
    print(text)
    return text


# ── main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Delphi full backtest")
    parser.add_argument("--start", default="", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="", help="End date (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float, default=1000.0, help="Initial cash")
    parser.add_argument("--sweep", action="store_true", help="Run parameter grid search")
    parser.add_argument("--momentum-weight", type=float, default=None)
    parser.add_argument("--quality-weight", type=float, default=None)
    parser.add_argument("--quality-override", type=float, default=None)
    parser.add_argument("--no-regime", action="store_true", help="Disable regime filter")
    parser.add_argument("--score-weighted", action="store_true")
    parser.add_argument("--rebalance-interval", type=int, default=None)
    parser.add_argument("--momentum-lookback", type=int, default=None)
    parser.add_argument("--max-names", type=int, default=None)
    parser.add_argument("--top-n-sectors", type=int, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    log.info("Loading sector ETF prices...")
    sector_prices = load_prices(SECTOR_PRICES_PATH)
    log.info("Loaded %d ETFs", len(sector_prices))

    log.info("Loading stock prices...")
    stock_prices = load_prices(STOCK_PRICES_PATH)
    log.info("Loaded %d stocks", len(stock_prices))

    log.info("Loading fundamentals...")
    fundamentals = load_fundamentals(FUNDAMENTALS_PATH)
    log.info("Loaded %d snapshots", len(fundamentals))

    if args.sweep:
        results = run_sweep(
            sector_prices, stock_prices, fundamentals,
            start_date=args.start, end_date=args.end,
        )
        print_sweep(results)
        os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(results, f, indent=2)
        log.info("Sweep results saved to %s", OUTPUT_PATH)
        return

    cfg = BacktestConfig(initial_cash=args.cash)
    if args.momentum_weight is not None:
        cfg.momentum_weight = args.momentum_weight
        cfg.quality_weight = 1.0 - args.momentum_weight
    if args.quality_weight is not None:
        cfg.quality_weight = args.quality_weight
    if args.quality_override is not None:
        cfg.quality_override = args.quality_override
    if args.no_regime:
        cfg.regime_enabled = False
    if args.score_weighted:
        cfg.score_weighted = True
    if args.rebalance_interval is not None:
        cfg.rebalance_interval = args.rebalance_interval
    if args.momentum_lookback is not None:
        cfg.momentum_lookback = args.momentum_lookback
    if args.max_names is not None:
        cfg.max_names_per_sector = args.max_names
    if args.top_n_sectors is not None:
        cfg.top_n_sectors = args.top_n_sectors

    output = run_backtest(
        sector_prices, stock_prices, fundamentals, cfg,
        start_date=args.start, end_date=args.end,
    )

    if "error" in output:
        log.error("Backtest failed: %s", output["error"])
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output["results"], f, indent=2)
    with open(CURVE_PATH, "w") as f:
        json.dump(output["equity_curve"], f, indent=1)
    with open(JOURNAL_PATH, "w") as f:
        for t in output["trades"]:
            f.write(json.dumps(t, sort_keys=True) + "\n")

    print_report(output)
    log.info("Results saved to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
