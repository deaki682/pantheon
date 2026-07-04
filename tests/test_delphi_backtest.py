"""Tests for the Delphi momentum compounder backtest."""
from __future__ import annotations

import datetime
import pytest

from delphi.backtest import BacktestConfig, _price_series, run_backtest
from delphi.signals import UNIVERSE


def _make_bar(date: str, close: float) -> dict:
    return {"date": date, "close": close, "open": close, "high": close, "low": close, "volume": 1000}


def _linear_bars(start_date: str, n_days: int, start_price: float, daily_return: float) -> dict[str, dict]:
    by_date = {}
    dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    px = start_price
    for i in range(n_days):
        d = (dt + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        by_date[d] = _make_bar(d, round(px, 2))
        px *= (1 + daily_return)
    return by_date


def _build_test_data(n_days: int = 200):
    """Build minimal synthetic data for backtest. Uses UNIVERSE symbols."""
    start = "2025-01-02"
    stock_prices = {}
    stock_prices["SPY"] = _linear_bars(start, n_days, 500, 0.0002)
    for i, sym in enumerate(UNIVERSE[:20]):
        rate = 0.002 - i * 0.0002
        stock_prices[sym] = _linear_bars(start, n_days, 100 + i * 5, rate)
    return stock_prices


class TestPriceSeries:
    def test_basic(self):
        days = ["2025-01-01", "2025-01-02", "2025-01-03"]
        by_date = {d: _make_bar(d, 100 + i) for i, d in enumerate(days)}
        series = _price_series(by_date, days, 2, 2)
        assert len(series) == 3
        assert series[-1] == 102


class TestRunBacktest:
    def test_basic_run(self):
        stock_prices = _build_test_data(200)
        cfg = BacktestConfig(initial_cash=1000.0, rebalance_interval=10)
        out = run_backtest(stock_prices, cfg)
        assert "error" not in out
        r = out["results"]
        assert r["trading_days"] > 150
        assert r["performance"]["final_equity"] > 0
        assert len(out["equity_curve"]) > 150

    def test_date_range(self):
        stock_prices = _build_test_data(200)
        cfg = BacktestConfig(rebalance_interval=10)
        out = run_backtest(
            stock_prices, cfg,
            start_date="2025-03-01", end_date="2025-06-01",
        )
        assert "error" not in out
        assert out["results"]["trading_days"] < 200

    def test_equity_curve_monotonic_dates(self):
        stock_prices = _build_test_data(100)
        cfg = BacktestConfig(rebalance_interval=10)
        out = run_backtest(stock_prices, cfg)
        dates = [p["date"] for p in out["equity_curve"]]
        assert dates == sorted(dates)


class TestDelistedExit:
    def test_no_bar_position_exits_at_last_traded_price_not_avg_price(self):
        """A name whose bars stop (delisting/collapse) must mark and exit
        at its last traded price — exiting at avg_price would erase the
        loss (the pre-2026-07-04 behavior)."""
        start = "2025-01-02"
        n = 150
        stock_prices = {"SPY": _linear_bars(start, n, 500, 0.0)}
        # One strong-momentum name (>= 65 bars so it ranks) that collapses
        # 90% on its final print and then stops trading.
        crash = _linear_bars(start, 100, 100, 0.01)
        days = sorted(crash)
        crash[days[-1]]["close"] = 10.0  # final print: -90%
        stock_prices[UNIVERSE[0]] = crash
        # A flat name so the universe never goes empty.
        stock_prices[UNIVERSE[1]] = _linear_bars(start, n, 100, 0.0)

        cfg = BacktestConfig(initial_cash=10_000.0)
        r = run_backtest(stock_prices, cfg)
        perf = r["results"]["performance"]
        # The collapse must show up as a real loss: final equity clearly
        # below initial. Under the avg_price bug the loss vanished.
        assert perf["final_equity"] < 9_500.0
        sells = [t for t in r["trades"] if t["side"] == "sell"
                 and t["symbol"] == UNIVERSE[0]]
        # Trims while it was still trading are fine; the terminal exit
        # after bars stop must price at the last traded close (10.0).
        assert sells and sells[-1]["price"] == pytest.approx(10.0)
