"""Tests for the Delphi backtest harness."""
from __future__ import annotations

import pytest

from delphi.backtest import (
    BacktestConfig, _price_series, _score_weighted_targets,
    run_backtest, run_sweep,
)
from delphi.sleeve import MIN_TICKET
from shared.fundamentals import FundamentalSnapshot


# ── helpers ──────────────────────────────────────────────────────────

def _make_bar(date: str, close: float) -> dict:
    return {"date": date, "close": close, "open": close, "high": close, "low": close, "volume": 1000}


def _linear_bars(start_date: str, n_days: int, start_price: float, daily_return: float) -> dict[str, dict]:
    """Generate n_days of bars with a fixed daily return."""
    import datetime
    by_date = {}
    dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    px = start_price
    for i in range(n_days):
        d = (dt + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        by_date[d] = _make_bar(d, round(px, 2))
        px *= (1 + daily_return)
    return by_date


def _build_test_data(n_days: int = 200):
    """Build minimal synthetic data for backtest tests.

    Creates diverging sector performance so the rotation signal is clear:
    - Technology goes up steadily (+0.2%/day)
    - Energy goes down (-0.1%/day)
    - SPY is flat (+0.02%/day)
    - All other sectors are slightly positive
    """
    start = "2025-01-02"

    sector_prices = {
        "SPY": _linear_bars(start, n_days, 500, 0.0002),
        "XLK": _linear_bars(start, n_days, 200, 0.002),   # strong up
        "XLF": _linear_bars(start, n_days, 40, 0.0005),
        "XLE": _linear_bars(start, n_days, 80, -0.001),   # weak
        "XLV": _linear_bars(start, n_days, 140, 0.0003),
        "XLI": _linear_bars(start, n_days, 110, 0.0004),
        "XLP": _linear_bars(start, n_days, 75, 0.0001),
        "XLY": _linear_bars(start, n_days, 180, 0.0006),
        "XLU": _linear_bars(start, n_days, 70, 0.0002),
        "XLRE": _linear_bars(start, n_days, 45, 0.0001),
        "XLB": _linear_bars(start, n_days, 85, 0.0003),
        "XLC": _linear_bars(start, n_days, 80, 0.0005),
    }

    stock_prices = {}
    # Tech stocks go up
    for i, sym in enumerate(["AAPL", "MSFT", "NVDA", "AVGO", "CRM", "AMD", "ADBE", "ORCL", "CSCO", "ACN"]):
        stock_prices[sym] = _linear_bars(start, n_days, 150 + i * 10, 0.002 + i * 0.0001)
    # Financial stocks moderate
    for i, sym in enumerate(["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK"]):
        stock_prices[sym] = _linear_bars(start, n_days, 100 + i * 5, 0.0005)
    # Energy stocks weak
    for i, sym in enumerate(["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "OXY"]):
        stock_prices[sym] = _linear_bars(start, n_days, 80 + i * 5, -0.001 + i * 0.0001)

    fundamentals = {
        "AAPL": FundamentalSnapshot(symbol="AAPL", operating_margin_ttm=0.30, revenue_yoy=0.08),
        "MSFT": FundamentalSnapshot(symbol="MSFT", operating_margin_ttm=0.45, revenue_yoy=0.12),
        "NVDA": FundamentalSnapshot(symbol="NVDA", operating_margin_ttm=0.55, revenue_yoy=0.80),
    }

    return sector_prices, stock_prices, fundamentals


# ── unit tests ───────────────────────────────────────────────────────

class TestPriceSeries:
    def test_basic(self):
        days = ["2025-01-01", "2025-01-02", "2025-01-03"]
        by_date = {d: _make_bar(d, 100 + i) for i, d in enumerate(days)}
        series = _price_series(by_date, days, 2, 2)
        assert len(series) == 3
        assert series[-1] == 102

    def test_short_history(self):
        days = ["2025-01-01", "2025-01-02"]
        by_date = {d: _make_bar(d, 100 + i) for i, d in enumerate(days)}
        series = _price_series(by_date, days, 1, 10)
        assert len(series) == 2


class TestScoreWeightedTargets:
    def test_higher_score_gets_more(self):
        picks = {
            "technology": [
                {"symbol": "AAPL", "score": 0.3},
                {"symbol": "MSFT", "score": 0.1},
            ]
        }
        targets = _score_weighted_targets(picks, 1000, 1.0, 0.1, 0.4, 0.12)
        assert targets["AAPL"] > targets["MSFT"]

    def test_zero_equity(self):
        picks = {"tech": [{"symbol": "AAPL", "score": 0.5}]}
        assert _score_weighted_targets(picks, 0, 1.0, 0.1, 0.4, 0.12) == {}

    def test_zero_risk_budget(self):
        picks = {"tech": [{"symbol": "AAPL", "score": 0.5}]}
        assert _score_weighted_targets(picks, 1000, 0.0, 0.1, 0.4, 0.12) == {}


# ── integration tests ────────────────────────────────────────────────

class TestRunBacktest:
    def test_basic_run(self):
        sector_prices, stock_prices, fundamentals = _build_test_data(200)
        cfg = BacktestConfig(initial_cash=1000.0, rebalance_interval=10)
        out = run_backtest(sector_prices, stock_prices, fundamentals, cfg)
        assert "error" not in out
        r = out["results"]
        assert r["trading_days"] == 200
        assert r["performance"]["final_equity"] > 0
        assert len(out["equity_curve"]) == 200
        assert len(out["regime_log"]) > 0

    def test_regime_disabled(self):
        sector_prices, stock_prices, fundamentals = _build_test_data(200)
        cfg = BacktestConfig(regime_enabled=False, rebalance_interval=10)
        out = run_backtest(sector_prices, stock_prices, fundamentals, cfg)
        assert "error" not in out
        for r in out["regime_log"]:
            assert r["regime"] == "always_in"

    def test_momentum_only(self):
        sector_prices, stock_prices, fundamentals = _build_test_data(200)
        cfg = BacktestConfig(momentum_weight=1.0, quality_weight=0.0, rebalance_interval=10)
        out = run_backtest(sector_prices, stock_prices, fundamentals, cfg)
        assert "error" not in out
        assert out["results"]["performance"]["final_equity"] > 0

    def test_score_weighted(self):
        sector_prices, stock_prices, fundamentals = _build_test_data(200)
        cfg = BacktestConfig(score_weighted=True, rebalance_interval=10)
        out = run_backtest(sector_prices, stock_prices, fundamentals, cfg)
        assert "error" not in out

    def test_date_range(self):
        sector_prices, stock_prices, fundamentals = _build_test_data(200)
        cfg = BacktestConfig(rebalance_interval=10)
        out = run_backtest(
            sector_prices, stock_prices, fundamentals, cfg,
            start_date="2025-03-01", end_date="2025-06-01",
        )
        assert "error" not in out
        assert out["results"]["trading_days"] < 200

    def test_tech_sector_chosen(self):
        """With tech strongly outperforming, it should be in the rotation."""
        sector_prices, stock_prices, fundamentals = _build_test_data(200)
        cfg = BacktestConfig(rebalance_interval=10)
        out = run_backtest(sector_prices, stock_prices, fundamentals, cfg)
        tech_exposure = out["results"]["sector_exposure"].get("technology", 0)
        assert tech_exposure > 0, "Technology should appear in rotation when outperforming"

    def test_concentrated_fewer_trades(self):
        sector_prices, stock_prices, fundamentals = _build_test_data(200)
        baseline = run_backtest(
            sector_prices, stock_prices, fundamentals,
            BacktestConfig(max_names_per_sector=4, rebalance_interval=10),
        )
        concentrated = run_backtest(
            sector_prices, stock_prices, fundamentals,
            BacktestConfig(max_names_per_sector=2, rebalance_interval=10),
        )
        assert concentrated["results"]["trades"]["total"] <= baseline["results"]["trades"]["total"]

    def test_equity_curve_monotonic_dates(self):
        sector_prices, stock_prices, fundamentals = _build_test_data(100)
        cfg = BacktestConfig(rebalance_interval=10)
        out = run_backtest(sector_prices, stock_prices, fundamentals, cfg)
        dates = [p["date"] for p in out["equity_curve"]]
        assert dates == sorted(dates)


class TestSweep:
    def test_sweep_returns_sorted_results(self):
        sector_prices, stock_prices, fundamentals = _build_test_data(150)
        results = run_sweep(
            sector_prices, stock_prices, fundamentals,
        )
        assert len(results) > 5
        alphas = [r["alpha_pct"] for r in results]
        assert alphas == sorted(alphas, reverse=True)
