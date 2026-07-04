"""Tests for shared.gauntlet — The Gauntlet backtest engine (backlog #9).

Pure logic, no network: synthetic bars/snapshots exercise the cost
model, no-lookahead universe construction, simulation loop, and the
deflated-Sharpe multiple-testing correction.
"""
import math

import pytest

from shared.gauntlet import (
    CostModel,
    StrategySpec,
    build_snapshots,
    deflated_sharpe_ratio,
    dollar_volume_pit_universe,
    expected_max_sharpe,
    pit_snapshot,
    probabilistic_sharpe_ratio,
    simulate,
    summarize,
)


def _bars(prices: dict) -> dict:
    """{date: close} -> canonical bar list."""
    return [{"date": d, "close": c} for d, c in sorted(prices.items())]


# ---------------------------------------------------------------------------
# Cost model
# ---------------------------------------------------------------------------

def test_cost_model_scales_with_notional():
    cost = CostModel(commission_bps=0.0, slippage_bps=10.0)
    assert cost.total_cost(10_000.0) == pytest.approx(10.0)
    assert cost.total_cost(0.0) == 0.0
    assert cost.total_cost(-5.0) == 0.0


# ---------------------------------------------------------------------------
# Point-in-time universe
# ---------------------------------------------------------------------------

def test_pit_snapshot_uses_only_the_exact_date():
    rows = [
        {"date": "2024-01-01", "ticker": "AAA", "marketcap": 100},
        {"date": "2024-04-01", "ticker": "AAA", "marketcap": 999999},  # future
        {"date": "2024-01-01", "ticker": "BBB", "marketcap": 50},
    ]
    names = pit_snapshot(rows, "2024-01-01", floor=60)
    assert names == ["AAA"]  # BBB excluded by floor, future AAA row never touched


def test_pit_snapshot_ceiling_and_floor():
    rows = [
        {"date": "2024-01-01", "ticker": "SMALL", "marketcap": 50},
        {"date": "2024-01-01", "ticker": "MID", "marketcap": 500},
        {"date": "2024-01-01", "ticker": "BIG", "marketcap": 5000},
    ]
    assert pit_snapshot(rows, "2024-01-01", floor=100, ceiling=1000) == ["MID"]


def test_build_snapshots_raises_on_empty_date():
    rows = [{"date": "2024-01-01", "ticker": "AAA", "marketcap": 100}]
    with pytest.raises(ValueError, match="zero eligible names"):
        build_snapshots(rows, ["2024-01-01", "2024-06-01"], floor=1)


def test_dollar_volume_proxy_ranks_by_price_times_volume():
    sep_rows = [
        {"date": "2024-01-01", "ticker": "THIN", "close": 100.0, "volume": 10},
        {"date": "2024-01-01", "ticker": "LIQUID", "close": 10.0, "volume": 100_000},
    ]
    snaps = dollar_volume_pit_universe(sep_rows, ["2024-01-01"], floor=50_000)
    assert snaps["2024-01-01"] == ["LIQUID"]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def test_simulate_buy_and_hold_matches_hand_calc_net_of_cost():
    bars = {"AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 11.0, "2024-01-03": 12.0})}
    snapshots = {"2024-01-01": ["AAA"]}
    spec = StrategySpec("all-in", lambda day, universe, b: {"AAA": 1.0})
    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=1.0)

    result = simulate(spec, snapshots, bars, initial_cash=1000.0, cost=cost)
    curve = {c["date"]: c["equity"] for c in result["curve"]}

    assert curve["2024-01-01"] == pytest.approx(1000.0)
    assert curve["2024-01-02"] == pytest.approx(1100.0)
    assert curve["2024-01-03"] == pytest.approx(1200.0)
    assert len(result["trades"]) == 1
    assert result["trades"][0]["side"] == "buy"


def test_simulate_deducts_slippage_on_entry():
    bars = {"AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 10.0})}
    snapshots = {"2024-01-01": ["AAA"]}
    spec = StrategySpec("all-in", lambda day, universe, b: {"AAA": 1.0})
    cost = CostModel(commission_bps=0.0, slippage_bps=100.0, min_ticket=1.0)  # 1%

    result = simulate(spec, snapshots, bars, initial_cash=1000.0, cost=cost)
    # Spend solves spend*(1+0.01) <= 1000 -> spend ~= 990.10, cost ~= 9.90
    assert result["curve"][0]["equity"] == pytest.approx(1000.0 - 9.9010, rel=1e-3)


def test_simulate_rejects_overallocated_weights():
    bars = {"AAA": _bars({"2024-01-01": 10.0})}
    snapshots = {"2024-01-01": ["AAA"]}
    spec = StrategySpec("bad", lambda day, universe, b: {"AAA": 1.5})
    with pytest.raises(ValueError, match="weights sum"):
        simulate(spec, snapshots, bars)


def test_simulate_rebalances_out_of_a_position():
    bars = {
        "AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 10.0, "2024-01-03": 10.0}),
        "BBB": _bars({"2024-01-01": 10.0, "2024-01-02": 10.0, "2024-01-03": 10.0}),
    }
    snapshots = {"2024-01-01": ["AAA", "BBB"], "2024-01-03": ["AAA", "BBB"]}

    def select(day, universe, b):
        return {"AAA": 1.0} if day == "2024-01-01" else {"BBB": 1.0}

    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=1.0)
    result = simulate(StrategySpec("switch", select), snapshots, bars, cost=cost)
    sides = [(t["date"], t["symbol"], t["side"]) for t in result["trades"]]
    assert ("2024-01-01", "AAA", "buy") in sides
    assert ("2024-01-03", "AAA", "sell") in sides
    assert ("2024-01-03", "BBB", "buy") in sides


def test_simulate_no_lookahead_strategy_sees_only_past_bars():
    bars = {"AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 20.0, "2024-01-03": 30.0})}
    snapshots = {"2024-01-01": ["AAA"], "2024-01-02": ["AAA"]}
    seen_last_dates = []

    def select(day, universe, trimmed):
        seen_last_dates.append(trimmed["AAA"][-1]["date"])
        return {"AAA": 1.0}

    simulate(StrategySpec("probe", select), snapshots, bars)
    assert seen_last_dates == ["2024-01-01", "2024-01-02"]  # never 01-03


def test_simulate_signal_lag_hides_execution_day_bar():
    bars = {"AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 20.0, "2024-01-03": 30.0})}
    snapshots = {"2024-01-02": ["AAA"], "2024-01-03": ["AAA"]}
    seen_last_dates = []

    def select(day, universe, trimmed):
        seen_last_dates.append(trimmed["AAA"][-1]["date"])
        return {"AAA": 1.0}

    simulate(StrategySpec("probe", select), snapshots, bars, signal_lag=1)
    # Executions on 01-02 and 01-03 see signals through 01-01 and 01-02.
    assert seen_last_dates == ["2024-01-01", "2024-01-02"]


def test_simulate_signal_lag_fills_at_execution_day_price():
    bars = {"AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 20.0, "2024-01-03": 20.0})}
    snapshots = {"2024-01-02": ["AAA"]}
    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=0.0)
    result = simulate(StrategySpec("s", lambda d, u, b: {"AAA": 1.0}),
                      snapshots, bars, initial_cash=1000.0, cost=cost,
                      signal_lag=1)
    trade = result["trades"][0]
    assert trade["date"] == "2024-01-02"
    assert trade["price"] == 20.0  # execution-day close, not the signal day's 10.0


def test_simulate_signal_lag_rejects_rebalance_at_window_start():
    bars = {"AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 20.0})}
    snapshots = {"2024-01-01": ["AAA"]}
    with pytest.raises(ValueError, match="no lagged signal date"):
        simulate(StrategySpec("s", lambda d, u, b: {"AAA": 1.0}),
                 snapshots, bars, signal_lag=1)


def test_simulate_negative_signal_lag_rejected():
    bars = {"AAA": _bars({"2024-01-01": 10.0})}
    with pytest.raises(ValueError, match="signal_lag"):
        simulate(StrategySpec("s", lambda d, u, b: {}), {}, bars, signal_lag=-1)


# ---------------------------------------------------------------------------
# Summary stats
# ---------------------------------------------------------------------------

def test_summarize_flat_curve_is_zero_everywhere():
    curve = [{"date": f"2024-01-0{i}", "equity": 1000.0} for i in range(1, 4)]
    stats = summarize(curve)
    assert stats["total_return"] == pytest.approx(0.0)
    assert stats["sharpe"] == 0.0
    assert stats["max_drawdown"] == 0.0


def test_summarize_drawdown_and_total_return():
    curve = [{"date": "d1", "equity": 100.0}, {"date": "d2", "equity": 150.0},
             {"date": "d3", "equity": 75.0}, {"date": "d4", "equity": 90.0}]
    stats = summarize(curve)
    assert stats["total_return"] == pytest.approx(-0.10)
    assert stats["max_drawdown"] == pytest.approx(75.0 / 150.0 - 1.0)


# ---------------------------------------------------------------------------
# Deflated Sharpe ratio
# ---------------------------------------------------------------------------

def test_expected_max_sharpe_grows_with_trials():
    assert expected_max_sharpe(2) < expected_max_sharpe(10) < expected_max_sharpe(1000)
    assert expected_max_sharpe(1) == 0.0


def test_probabilistic_sharpe_ratio_at_benchmark_is_half():
    assert probabilistic_sharpe_ratio(1.0, 1.0, n_obs=252) == pytest.approx(0.5)


def test_deflated_sharpe_penalizes_more_trials():
    # A fixed observed Sharpe becomes LESS convincing as the grid (and
    # hence the multiple-testing benchmark) grows — the whole point.
    dsr_small_grid = deflated_sharpe_ratio(1.0, n_trials=5, n_obs=252)
    dsr_big_grid = deflated_sharpe_ratio(1.0, n_trials=500, n_obs=252)
    assert dsr_big_grid < dsr_small_grid


def test_deflated_sharpe_single_trial_equals_plain_psr_at_zero_benchmark():
    # n_trials=1 -> expected_max_sharpe=0 -> DSR reduces to PSR vs 0.
    dsr = deflated_sharpe_ratio(0.5, n_trials=1, n_obs=100)
    psr = probabilistic_sharpe_ratio(0.5, 0.0, n_obs=100)
    assert dsr == pytest.approx(psr)
