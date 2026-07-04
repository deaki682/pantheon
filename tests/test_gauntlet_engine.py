"""Tests for shared.gauntlet — The Gauntlet backtest engine (backlog #9).

Pure logic, no network: synthetic bars/snapshots exercise the cost
model, no-lookahead universe construction, simulation loop, and the
deflated-Sharpe multiple-testing correction.
"""
import math

import pytest

from shared.gauntlet import (
    CostModel,
    PITEventFeed,
    StrategySpec,
    build_snapshots,
    deflated_sharpe_ratio,
    dollar_volume_pit_universe,
    expected_max_sharpe,
    pit_snapshot,
    probabilistic_sharpe_ratio,
    simulate,
    summarize,
    summarize_by_period,
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
# Total-return marking (dividends must compound, not vanish)
# ---------------------------------------------------------------------------

def _div_payer(days, price=10.0, div_growth=1.01):
    """Flat price, compounding total-return series — a pure dividend payer."""
    return [{"date": d, "close": price,
             "close_total_return": price * div_growth ** i}
            for i, d in enumerate(days)]


def test_simulate_dividends_compound_via_total_return():
    days = [f"2024-01-{i:02d}" for i in range(1, 11)]
    bars = {"DIV": _div_payer(days)}
    snapshots = {days[0]: ["DIV"]}
    spec = StrategySpec("hold-div", lambda day, u, b: {"DIV": 1.0})
    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=1.0)

    result = simulate(spec, snapshots, bars, initial_cash=1000.0, cost=cost)
    # Price-return curve would be dead flat; total return compounds 1.01/day.
    assert result["curve"][-1]["equity"] == pytest.approx(1000.0 * 1.01 ** 9)
    assert result["price_return_only_symbols"] == []


def test_simulate_incomplete_total_return_falls_back_whole_symbol():
    # One bar missing close_total_return -> the WHOLE symbol marks on
    # close (no fake jump from mixing fields), and the fallback is
    # disclosed in price_return_only_symbols.
    days = [f"2024-01-{i:02d}" for i in range(1, 6)]
    bars_list = _div_payer(days)
    del bars_list[2]["close_total_return"]
    bars = {"DIV": bars_list}
    snapshots = {days[0]: ["DIV"]}
    spec = StrategySpec("hold", lambda day, u, b: {"DIV": 1.0})
    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=1.0)

    result = simulate(spec, snapshots, bars, initial_cash=1000.0, cost=cost)
    assert result["curve"][-1]["equity"] == pytest.approx(1000.0)  # flat close
    assert result["price_return_only_symbols"] == ["DIV"]


def test_simulate_mixed_symbols_each_use_own_field():
    days = ["2024-01-01", "2024-01-02"]
    bars = {
        "DIV": _div_payer(days, div_growth=1.10),
        "PLAIN": [{"date": d, "close": 10.0} for d in days],
    }
    snapshots = {days[0]: ["DIV", "PLAIN"]}
    spec = StrategySpec("half-half", lambda day, u, b: {"DIV": 0.5, "PLAIN": 0.5})
    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=1.0)

    result = simulate(spec, snapshots, bars, initial_cash=1000.0, cost=cost)
    # DIV half grows 10%, PLAIN half flat -> book +5%.
    assert result["curve"][-1]["equity"] == pytest.approx(1050.0)
    assert result["price_return_only_symbols"] == ["PLAIN"]


# ---------------------------------------------------------------------------
# Point-in-time event feed
# ---------------------------------------------------------------------------

def _events():
    return [
        {"public_date": "2024-01-05", "symbol": "AAA", "kind": "cluster"},
        {"public_date": "2024-01-10", "symbol": "BBB", "kind": "cluster"},
        {"public_date": "2024-01-10", "symbol": "AAA", "kind": "13d"},
    ]


def test_event_feed_upto_never_returns_future_rows():
    feed = PITEventFeed(_events())
    assert feed.upto("2024-01-01") == []
    assert [r["symbol"] for r in feed.upto("2024-01-05")] == ["AAA"]
    assert len(feed.upto("2024-01-10")) == 3
    assert len(feed.upto("2024-12-31")) == 3


def test_event_feed_on_exact_day_only():
    feed = PITEventFeed(_events())
    assert len(feed.on("2024-01-10")) == 2
    assert feed.on("2024-01-06") == []


def test_event_feed_by_symbol_groups_without_future_leak():
    feed = PITEventFeed(_events())
    grouped = feed.by_symbol("2024-01-09")
    assert set(grouped) == {"AAA"}
    assert len(grouped["AAA"]) == 1  # the 01-10 rows are still in the future


def test_event_feed_rejects_rows_missing_public_date():
    with pytest.raises(ValueError, match="public_date"):
        PITEventFeed([{"symbol": "AAA", "transaction_date": "2024-01-02"}])


def test_event_feed_custom_date_field():
    feed = PITEventFeed([{"filed": "2024-02-01", "symbol": "CCC"}],
                        date_field="filed")
    assert len(feed.upto("2024-02-01")) == 1
    assert feed.upto("2024-01-31") == []


# ---------------------------------------------------------------------------
# Per-regime curve splits
# ---------------------------------------------------------------------------

def test_summarize_by_period_splits_at_boundaries():
    flat = [{"date": f"2024-01-{i:02d}", "equity": 1000.0} for i in range(1, 6)]
    rising = [{"date": f"2024-02-{i:02d}", "equity": 1000.0 * (1.01 ** i)}
              for i in range(1, 6)]
    out = summarize_by_period(flat + rising, ["2024-02-01"])
    assert len(out) == 2
    seg1, seg2 = (out[k] for k in sorted(out))
    assert seg1["total_return"] == pytest.approx(0.0)
    assert seg2["total_return"] > 0.03


def test_summarize_by_period_no_boundaries_is_full_curve():
    curve = [{"date": f"2024-01-{i:02d}", "equity": 1000.0 + i} for i in range(1, 5)]
    out = summarize_by_period(curve, [])
    assert len(out) == 1
    (label,) = out
    assert label == "2024-01-01..2024-01-04"
    assert out[label]["n_obs"] == 3


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


# ---------------------------------------------------------------------------
# ExitRules — daily position-level exits
# ---------------------------------------------------------------------------

from shared.gauntlet import ExitRules, excess_stats, periodic_dates, trade_stats, turnover_stats

_NOCOST = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=1.0)


def _ohlc(rows):
    """[(date, open, high, low, close)] -> bar list."""
    return [{"date": d, "open": o, "high": h, "low": l, "close": c}
            for d, o, h, l, c in rows]


def _hold(sym):
    return StrategySpec("hold", lambda day, u, b: {sym: 1.0})


def test_exit_stop_loss_fills_at_stop_level_intraday():
    bars = {"AAA": _ohlc([
        ("2024-01-01", 10.0, 10.1, 9.9, 10.0),
        ("2024-01-02", 10.0, 10.0, 9.1, 9.8),   # low pierces 9.2 stop
        ("2024-01-03", 9.8, 9.9, 9.7, 9.8),
    ])}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(stop_loss_pct=0.08))
    sell = [t for t in result["trades"] if t["side"] == "sell"][0]
    assert sell["reason"] == "stop_loss"
    assert sell["date"] == "2024-01-02"
    assert sell["price"] == pytest.approx(9.2)   # the level, not the low
    assert result["curve"][-1]["equity"] == pytest.approx(1000.0 * 9.2 / 10.0)


def test_exit_stop_loss_gap_through_fills_at_open():
    bars = {"AAA": _ohlc([
        ("2024-01-01", 10.0, 10.1, 9.9, 10.0),
        ("2024-01-02", 8.5, 8.6, 8.4, 8.5),      # gaps below the 9.2 stop
    ])}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(stop_loss_pct=0.08))
    sell = [t for t in result["trades"] if t["side"] == "sell"][0]
    assert sell["price"] == pytest.approx(8.5)   # the open — no fill at 9.2 exists


def test_exit_trailing_stop_uses_prior_peak():
    bars = {"AAA": _ohlc([
        ("2024-01-01", 10.0, 10.1, 9.9, 10.0),
        ("2024-01-02", 12.0, 12.1, 11.9, 12.0),  # peak close 12
        ("2024-01-03", 11.0, 11.1, 10.7, 11.0),  # low 10.7 <= 12*0.9=10.8 -> exit
    ])}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(trailing_stop_pct=0.10))
    sell = [t for t in result["trades"] if t["side"] == "sell"][0]
    assert sell["reason"] == "trailing_stop"
    assert sell["price"] == pytest.approx(10.8)


def test_exit_profit_target_fills_at_target():
    bars = {"AAA": _ohlc([
        ("2024-01-01", 10.0, 10.1, 9.9, 10.0),
        ("2024-01-02", 10.5, 12.3, 10.4, 11.0),  # high crosses 12.0 target
    ])}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(profit_target_pct=0.20))
    sell = [t for t in result["trades"] if t["side"] == "sell"][0]
    assert sell["reason"] == "profit_target"
    assert sell["price"] == pytest.approx(12.0)


def test_exit_ma_break_exits_at_close():
    rows = [(f"2024-01-{i:02d}", 10.0, 10.0, 10.0, 10.0) for i in range(1, 6)]
    rows.append(("2024-01-06", 9.0, 9.0, 8.9, 9.0))   # close 9 < MA5 (~9.8)
    bars = {"AAA": _ohlc(rows)}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(ma_period=5))
    sell = [t for t in result["trades"] if t["side"] == "sell"][0]
    assert sell["reason"] == "ma_exit"
    assert sell["date"] == "2024-01-06"
    assert sell["price"] == pytest.approx(9.0)


def test_exit_time_stop_after_n_trading_days():
    rows = [(f"2024-01-{i:02d}", 10.0, 10.0, 10.0, 10.0) for i in range(1, 8)]
    bars = {"AAA": _ohlc(rows)}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(time_stop_days=5))
    sell = [t for t in result["trades"] if t["side"] == "sell"][0]
    assert sell["reason"] == "time_stop"
    assert sell["date"] == "2024-01-06"   # entered index 0, exits at index 5


def test_exit_cooldown_blocks_rebuy_then_releases():
    rows = [(f"2024-01-{i:02d}", 10.0, 10.0, 10.0, 10.0) for i in range(1, 3)]
    rows.append(("2024-01-03", 8.0, 8.0, 7.9, 8.0))   # stop fires
    rows += [(f"2024-01-{i:02d}", 8.0, 8.0, 8.0, 8.0) for i in range(4, 9)]
    bars = {"AAA": _ohlc(rows)}
    snapshots = {d: ["AAA"] for d in
                 ["2024-01-01", "2024-01-04", "2024-01-06", "2024-01-08"]}
    result = simulate(_hold("AAA"), snapshots, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(stop_loss_pct=0.10, cooldown_days=3))
    buys = [t["date"] for t in result["trades"] if t["side"] == "buy"]
    # Stop fires 01-03 (index 2); cooldown blocks through index 5 (01-06).
    assert buys == ["2024-01-01", "2024-01-08"]


def test_exit_same_day_rebuy_blocked_even_without_cooldown():
    rows = [("2024-01-01", 10.0, 10.0, 10.0, 10.0),
            ("2024-01-02", 8.0, 8.0, 7.9, 8.0)]
    bars = {"AAA": _ohlc(rows)}
    snapshots = {"2024-01-01": ["AAA"], "2024-01-02": ["AAA"]}
    result = simulate(_hold("AAA"), snapshots, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(stop_loss_pct=0.10))
    trades_0102 = [t for t in result["trades"] if t["date"] == "2024-01-02"]
    assert [t["side"] for t in trades_0102] == ["sell"]   # no same-day rebuy


def test_exit_fill_converts_to_total_return_series():
    # Symbol marks on close_total_return (ratio 1.05 on exit day); the
    # stop triggers on RAW prices but the book is credited in TR units.
    bars = {"AAA": [
        {"date": "2024-01-01", "open": 10.0, "high": 10.0, "low": 10.0,
         "close": 10.0, "close_total_return": 10.0},
        {"date": "2024-01-02", "open": 9.5, "high": 9.5, "low": 9.0,
         "close": 9.1, "close_total_return": 9.555},   # ratio 1.05
    ]}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(stop_loss_pct=0.08))
    sell = [t for t in result["trades"] if t["side"] == "sell"][0]
    assert sell["price"] == pytest.approx(9.2 * 1.05)
    assert result["curve"][-1]["equity"] == pytest.approx(1000.0 * 9.2 * 1.05 / 10.0)


def test_exit_stop_precedes_ma_and_time():
    rows = [(f"2024-01-{i:02d}", 10.0, 10.0, 10.0, 10.0) for i in range(1, 6)]
    rows.append(("2024-01-06", 8.0, 8.0, 7.9, 8.0))
    bars = {"AAA": _ohlc(rows)}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      exits=ExitRules(stop_loss_pct=0.10, ma_period=5,
                                      time_stop_days=5))
    sell = [t for t in result["trades"] if t["side"] == "sell"][0]
    assert sell["reason"] == "stop_loss"


def test_delist_exit_haircut_forces_final_bar_exit():
    bars = {
        "DEAD": _ohlc([("2024-01-01", 10.0, 10.0, 10.0, 10.0),
                        ("2024-01-02", 4.0, 4.0, 4.0, 4.0)]),   # final bar
        "LIVE": _ohlc([(f"2024-01-{i:02d}", 10.0, 10.0, 10.0, 10.0)
                        for i in range(1, 5)]),
    }
    spec = StrategySpec("dead-half", lambda d, u, b: {"DEAD": 0.5, "LIVE": 0.5})
    result = simulate(spec, {"2024-01-01": ["DEAD", "LIVE"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST,
                      delist_exit_haircut=0.5)
    sell = [t for t in result["trades"] if t["symbol"] == "DEAD"
            and t["side"] == "sell"][0]
    assert sell["reason"] == "delisting_exit"
    assert sell["price"] == pytest.approx(2.0)   # 4.0 final close x (1 - 0.5)


def test_exits_none_preserves_legacy_behavior():
    bars = {"AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 5.0})}
    result = simulate(_hold("AAA"), {"2024-01-01": ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST)
    assert [t["side"] for t in result["trades"]] == ["buy"]   # rides it down
    assert result["curve"][-1]["equity"] == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# Analytics: excess_stats / trade_stats / turnover_stats / periodic_dates
# ---------------------------------------------------------------------------

def test_excess_stats_beta_one_alpha_zero_for_identical_curves():
    curve = [{"date": f"2024-01-{i:02d}", "equity": 1000.0 * (1.01 ** i)}
             for i in range(1, 11)]
    out = excess_stats(curve, curve)
    assert out["beta"] == pytest.approx(1.0)
    assert out["alpha_annual"] == pytest.approx(0.0, abs=1e-9)
    assert out["excess_cagr"] == pytest.approx(0.0, abs=1e-9)
    assert out["information_ratio"] == 0.0


def test_excess_stats_flat_strategy_vs_rising_benchmark():
    flat = [{"date": f"2024-01-{i:02d}", "equity": 1000.0} for i in range(1, 11)]
    rising = [{"date": f"2024-01-{i:02d}", "equity": 1000.0 * (1.01 ** i)}
              for i in range(1, 11)]
    out = excess_stats(flat, rising)
    assert out["excess_cagr"] < 0
    assert out["beta"] == pytest.approx(0.0, abs=1e-9)
    assert out["up_capture"] == pytest.approx(0.0, abs=1e-9)


def test_trade_stats_fifo_round_trips_and_reasons():
    trades = [
        {"date": "2024-01-01", "symbol": "A", "side": "buy", "shares": 10,
         "price": 10.0, "cost": 0.0, "reason": "rebalance"},
        {"date": "2024-01-11", "symbol": "A", "side": "sell", "shares": 10,
         "price": 12.0, "cost": 0.0, "reason": "rebalance"},
        {"date": "2024-01-01", "symbol": "B", "side": "buy", "shares": 10,
         "price": 10.0, "cost": 0.0, "reason": "rebalance"},
        {"date": "2024-01-06", "symbol": "B", "side": "sell", "shares": 10,
         "price": 9.0, "cost": 0.0, "reason": "stop_loss"},
    ]
    out = trade_stats(trades)
    assert out["n_round_trips"] == 2
    assert out["win_rate"] == pytest.approx(0.5)
    assert out["avg_win_pct"] == pytest.approx(0.20)
    assert out["avg_loss_pct"] == pytest.approx(-0.10)
    assert out["by_exit_reason"]["stop_loss"]["n"] == 1
    assert out["by_exit_reason"]["stop_loss"]["mean_return"] == pytest.approx(-0.10)
    assert out["median_holding_days"] in (5, 10)


def test_trade_stats_partial_sell_splits_lot():
    trades = [
        {"date": "2024-01-01", "symbol": "A", "side": "buy", "shares": 10,
         "price": 10.0, "cost": 0.0},
        {"date": "2024-01-02", "symbol": "A", "side": "sell", "shares": 4,
         "price": 11.0, "cost": 0.0},
        {"date": "2024-01-03", "symbol": "A", "side": "sell", "shares": 6,
         "price": 12.0, "cost": 0.0},
    ]
    out = trade_stats(trades)
    assert out["n_round_trips"] == 2
    assert out["win_rate"] == 1.0


def test_turnover_stats_hand_calc():
    curve = [{"date": f"2024-01-{i:02d}", "equity": 1000.0}
             for i in range(1, 253 + 1)]  # one year, flat $1000
    trades = [
        {"date": "2024-01-01", "symbol": "A", "side": "buy", "shares": 50,
         "price": 10.0, "cost": 1.0},
        {"date": "2024-06-01", "symbol": "A", "side": "sell", "shares": 50,
         "price": 10.0, "cost": 1.0},
    ]
    out = turnover_stats(trades, curve)
    assert out["annual_turnover"] == pytest.approx(0.5, rel=1e-2)   # $500/$1000/1yr
    assert out["total_costs"] == pytest.approx(2.0)
    assert out["cost_drag_bps_yr"] == pytest.approx(20.0, rel=1e-2)


def test_periodic_dates_month_and_week():
    days = ["2024-01-30", "2024-01-31", "2024-02-01", "2024-02-02",
            "2024-02-05", "2024-02-28"]
    assert periodic_dates(days, "M", "last") == ["2024-01-31", "2024-02-28"]
    assert periodic_dates(days, "M", "first") == ["2024-01-30", "2024-02-01"]
    # ISO weeks: 01-30..02-02 are one week (Tue-Fri), 02-05 the next Mon.
    assert periodic_dates(days, "W", "last") == ["2024-02-02", "2024-02-05", "2024-02-28"]


def test_periodic_dates_rejects_bad_args():
    with pytest.raises(ValueError, match="cadence"):
        periodic_dates(["2024-01-01"], "Q")
    with pytest.raises(ValueError, match="anchor"):
        periodic_dates(["2024-01-01"], "M", "middle")


# ---------------------------------------------------------------------------
# Tier 2: sharpe_ci / walk_forward_windows / parameter_cliff_report / event_car
# ---------------------------------------------------------------------------

from shared.gauntlet import (
    event_car,
    parameter_cliff_report,
    sharpe_ci,
    walk_forward_windows,
)


def test_sharpe_ci_brackets_point_estimate_and_is_deterministic():
    # 300 days of steady drift + wobble -> positive Sharpe, tight-ish CI.
    curve = [{"date": f"2024-{1 + i // 28:02d}-{1 + i % 28:02d}",
              "equity": 1000.0 * (1.001 ** i) * (1 + 0.002 * ((-1) ** i))}
             for i in range(300)]
    a = sharpe_ci(curve, n_boot=200, block=10, seed=42)
    b = sharpe_ci(curve, n_boot=200, block=10, seed=42)
    assert a == b                       # deterministic for a given seed
    assert a["lo"] < a["sharpe"] < a["hi"]


def test_sharpe_ci_refuses_short_series():
    curve = [{"date": f"2024-01-{i:02d}", "equity": 1000.0 + i} for i in range(1, 10)]
    out = sharpe_ci(curve, block=21)
    assert out["lo"] is None and "note" in out


def test_walk_forward_windows_shape_and_no_overlap():
    days = [f"d{i:04d}" for i in range(10)]   # lexicographic == chronological
    ws = walk_forward_windows(days, train_days=4, test_days=2)
    assert ws[0] == {"train": ("d0000", "d0003"), "test": ("d0004", "d0005")}
    assert ws[1] == {"train": ("d0002", "d0005"), "test": ("d0006", "d0007")}
    assert ws[2] == {"train": ("d0004", "d0007"), "test": ("d0008", "d0009")}
    assert len(ws) == 3                  # 4th window wouldn't fit; dropped
    # default step == test_days -> test windows tile without overlap
    tests_seen = [w["test"] for w in ws]
    assert len(set(tests_seen)) == len(tests_seen)


def test_parameter_cliff_report_flags_isolated_peak():
    cells = []
    for lb in (21, 63, 126):
        for n in (10, 25):
            metric = 2.0 if (lb == 63 and n == 10) else 0.1   # lone spike
            cells.append({"params": {"lookback": lb, "n": n}, "metric": metric})
    report = parameter_cliff_report(cells)
    worst = report[0]
    assert worst["params"] == {"lookback": 63, "n": 10}
    assert worst["isolation"] == pytest.approx(2.0 - 0.1)
    assert worst["n_neighbors"] == 3     # lb=21/n10, lb=126/n10, lb=63/n25


def test_parameter_cliff_report_plateau_has_low_isolation():
    cells = [{"params": {"lookback": lb}, "metric": 1.0} for lb in (21, 63, 126)]
    report = parameter_cliff_report(cells)
    assert all(r["isolation"] == pytest.approx(0.0) for r in report)


def _flat_bench(days):
    return [{"date": d, "close": 100.0} for d in days]


def test_event_car_hand_calc_and_entry_day_convention():
    days = [f"2024-01-{i:02d}" for i in range(1, 8)]
    bars = {"AAA": [{"date": d, "close": px} for d, px in
                    zip(days, [10.0, 10.0, 11.0, 12.0, 12.0, 12.0, 12.0])]}
    events = [{"symbol": "AAA", "public_date": "2024-01-02"}]
    out = event_car(events, bars, _flat_bench(days), max_offset=2)
    # Entry at first day strictly AFTER 01-02 -> 01-03 close 11.0.
    assert out["n_events_priced"] == 1
    assert out["mean_car"][0] == pytest.approx(0.0)
    assert out["mean_car"][1] == pytest.approx(12.0 / 11.0 - 1.0)   # flat benchmark
    assert out["unpriceable"] == []


def test_event_car_subtracts_benchmark():
    days = ["2024-01-01", "2024-01-02", "2024-01-03"]
    bars = {"AAA": [{"date": d, "close": px} for d, px in
                    zip(days, [10.0, 10.0, 11.0])]}
    bench = [{"date": d, "close": px} for d, px in
             zip(days, [100.0, 100.0, 110.0])]
    events = [{"symbol": "AAA", "public_date": "2024-01-01"}]
    out = event_car(events, bars, bench, max_offset=1)
    # Stock +10%, benchmark +10% -> CAR 0.
    assert out["mean_car"][1] == pytest.approx(0.0)


def test_event_car_discloses_unpriceable():
    days = ["2024-01-01", "2024-01-02"]
    bars = {"AAA": [{"date": "2024-01-01", "close": 10.0}]}
    events = [
        {"symbol": "AAA", "public_date": "2024-01-01"},   # no bar AFTER pub
        {"symbol": "GONE", "public_date": "2024-01-01"},  # no bars at all
    ]
    out = event_car(events, bars, _flat_bench(days), max_offset=1)
    assert out["n_events_priced"] == 0
    assert len(out["unpriceable"]) == 2
    assert "unpriceable" in out["coverage_note"]


# ---------------------------------------------------------------------------
# Tier 3: benchmark_curve / capacity_stats / combine_curves /
#         drawdown_distribution / draft_bias_checklist
# ---------------------------------------------------------------------------

from shared.gauntlet import (
    benchmark_curve,
    capacity_stats,
    combine_curves,
    draft_bias_checklist,
    drawdown_distribution,
)
from shared.lab import BIAS_CHECKLIST


def test_benchmark_curve_scales_and_prefers_total_return():
    bars = [{"date": "2024-01-01", "close": 100.0, "close_total_return": 200.0},
            {"date": "2024-01-02", "close": 100.0, "close_total_return": 210.0}]
    out = benchmark_curve(bars, initial=1000.0)
    assert out["price_field"] == "close_total_return"
    assert out["curve"][0]["equity"] == pytest.approx(1000.0)
    assert out["curve"][1]["equity"] == pytest.approx(1050.0)  # +5% TR, flat price


def test_benchmark_curve_falls_back_to_close_and_says_so():
    bars = [{"date": "2024-01-01", "close": 100.0},
            {"date": "2024-01-02", "close": 110.0}]
    out = benchmark_curve(bars)
    assert out["price_field"] == "close"
    assert out["curve"][1]["equity"] == pytest.approx(1100.0)


def test_capacity_stats_participation_and_implied_multiple():
    # ADV window (days before the fill): $10k/day dollar volume.
    bars = {"AAA": [{"date": f"2024-01-{i:02d}", "close": 10.0, "volume": 1000}
                    for i in range(1, 11)]}
    trades = [{"date": "2024-01-10", "symbol": "AAA", "side": "buy",
               "shares": 50, "price": 10.0, "cost": 0.0}]   # $500 = 5% of ADV
    out = capacity_stats(trades, bars, adv_window=5)
    assert out["n_fills"] == 1
    assert out["participation_median"] == pytest.approx(0.05)
    assert out["share_above_1pct"] == 1.0
    assert out["share_above_10pct"] == 0.0
    # p90 = 5% -> book can only be 0.2x current size before p90 > 1%.
    assert out["implied_max_equity_multiple"] == pytest.approx(0.2)


def test_capacity_stats_discloses_missing_volume():
    bars = {"AAA": [{"date": "2024-01-01", "close": 10.0}]}   # no volume field
    trades = [{"date": "2024-01-01", "symbol": "AAA", "side": "buy",
               "shares": 1, "price": 10.0, "cost": 0.0}]
    out = capacity_stats(trades, bars)
    assert out["n_fills"] == 0
    assert len(out["no_volume_fills"]) == 1


def test_combine_curves_correlations_and_diversification_gap():
    days = [f"2024-01-{i:02d}" for i in range(1, 12)]
    up = [{"date": d, "equity": 1000.0 * (1.01 ** i)} for i, d in enumerate(days)]
    down_up = [{"date": d, "equity": 1000.0 * (0.99 ** i if i < 5 else
                                                0.99 ** 4 * 1.01 ** (i - 4))}
               for i, d in enumerate(days)]
    out = combine_curves({"a": up, "b": down_up})
    assert out["correlations"]["a"]["a"] == pytest.approx(1.0)
    assert out["correlations"]["a"]["b"] == out["correlations"]["b"]["a"]
    assert out["correlations"]["a"]["b"] < 1.0
    # Sleeve a never draws down; sleeve b does; the combined book's DD is
    # SHALLOWER than the weighted average -> negative gap means diversification
    # helped (gap = combined_dd - wavg_dd, both are <= 0 numbers).
    assert out["stats"]["max_drawdown"] > out["weighted_avg_max_drawdown"]
    assert out["diversification_gap"] > 0


def test_combine_curves_rejects_bad_weights():
    days = ["2024-01-01", "2024-01-02", "2024-01-03"]
    c = [{"date": d, "equity": 1000.0} for d in days]
    with pytest.raises(ValueError, match="weights"):
        combine_curves({"a": c, "b": c}, weights={"a": 0.9, "b": 0.9})


def test_drawdown_distribution_deterministic_and_sane():
    import math as _m
    curve = [{"date": f"d{i:04d}",
              "equity": 1000.0 * _m.exp(0.0005 * i + 0.01 * _m.sin(i))}
             for i in range(300)]
    a = drawdown_distribution(curve, n_sims=200, block=10, seed=1)
    b = drawdown_distribution(curve, n_sims=200, block=10, seed=1)
    assert a == b
    assert a["dd_worst"] <= a["dd_p05"] <= a["dd_p50"] <= 0.0
    assert 0.0 <= a["prob_worse_than"]["40pct"] <= 1.0


def test_draft_bias_checklist_matches_lab_keys_and_floor():
    days = [f"2024-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(120)]
    bars = {"AAA": [{"date": d, "close": 10.0 * (1.001 ** i)}
                    for i, d in enumerate(days)]}
    result = simulate(_hold("AAA"), {days[0]: ["AAA"]}, bars,
                      initial_cash=1000.0, cost=_NOCOST)
    drafts = draft_bias_checklist(
        result, n_trials=90, cost=_NOCOST,
        panel_note="synthetic single-name panel",
        split_note="no split (unit test)", hypotheses_ever=91,
        regime_boundaries=[days[60]])
    assert set(drafts) == set(BIAS_CHECKLIST)          # exact key match
    assert all(len(v) >= 60 for v in drafts.values())  # lab's writing floor
    assert "n_trials=90" in drafts["multiple_testing"]
    assert "hypotheses_ever=91" in drafts["multiple_testing"]
    assert "sharpe" in drafts["regime"]                # per-regime numbers present


def test_lazy_trim_view_matches_eager_trim():
    from shared.gauntlet import _LazyTrim, _trim
    bars = {"AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 11.0,
                           "2024-01-03": 12.0}),
            "BBB": _bars({"2024-01-02": 5.0})}
    dates = {s: [b["date"] for b in bs] for s, bs in bars.items()}
    lazy = _LazyTrim(bars, dates, "2024-01-02")
    eager = _trim(bars, "2024-01-02")
    assert lazy["AAA"] == eager["AAA"]
    assert lazy.get("BBB") == eager["BBB"]
    assert lazy.get("MISSING") is None
    assert set(lazy) == set(eager) and len(lazy) == len(eager)
    assert dict(lazy.items()) == eager
    assert "AAA" in lazy


def test_lazy_trim_tail_matches_full_slice():
    from shared.gauntlet import _LazyTrim
    bars = {"AAA": _bars({f"2024-01-{i:02d}": float(i) for i in range(1, 10)})}
    dates = {"AAA": [b["date"] for b in bars["AAA"]]}
    lazy = _LazyTrim(bars, dates, "2024-01-06")
    assert lazy.tail("AAA", 3) == lazy["AAA"][-3:]
    assert lazy.tail("AAA", 99) == lazy["AAA"]


# ---------------------------------------------------------------------------
# rebalance_band + sell_cooldown_days (faithful-Delphi semantics)
# ---------------------------------------------------------------------------

def test_rebalance_band_suppresses_drift_trades_but_not_full_exits():
    bars = {
        "AAA": _bars({"2024-01-01": 10.0, "2024-01-02": 11.0, "2024-01-03": 11.0}),
        "BBB": _bars({"2024-01-01": 10.0, "2024-01-02": 10.0, "2024-01-03": 10.0}),
    }
    snapshots = {"2024-01-01": ["AAA", "BBB"], "2024-01-02": ["AAA", "BBB"],
                 "2024-01-03": ["AAA", "BBB"]}

    def select(day, universe, trimmed):
        if day == "2024-01-03":
            return {"BBB": 0.5}          # AAA drops out entirely
        return {"AAA": 0.5, "BBB": 0.5}

    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=1.0)
    result = simulate(StrategySpec("band", select), snapshots, bars,
                      initial_cash=1000.0, cost=cost, rebalance_band=0.20)
    t_by_day = {}
    for t in result["trades"]:
        t_by_day.setdefault(t["date"], []).append((t["side"], t["symbol"]))
    # Day 2: AAA drifted +10% (inside the 20% band) -> no trim, no top-up.
    assert "2024-01-02" not in t_by_day
    # Day 3: AAA target 0 -> full exit fires despite the band.
    assert ("sell", "AAA") in t_by_day["2024-01-03"]


def test_sell_cooldown_blocks_rebuy_after_rotation_exit():
    days = [f"2024-01-{i:02d}" for i in range(1, 8)]
    bars = {"AAA": _bars({d: 10.0 for d in days}),
            "BBB": _bars({d: 10.0 for d in days})}
    snapshots = {d: ["AAA", "BBB"] for d in days}

    def select(day, universe, trimmed):
        if day == "2024-01-02":
            return {"BBB": 0.9}          # rotate out of AAA
        return {"AAA": 0.9}              # want AAA every other day

    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=1.0)
    result = simulate(StrategySpec("cd", select), snapshots, bars,
                      initial_cash=1000.0, cost=cost, sell_cooldown_days=3)
    aaa_buys = [t["date"] for t in result["trades"]
                if t["symbol"] == "AAA" and t["side"] == "buy"]
    # Sold 01-02 (idx 1); cooldown blocks idx <= 4 (01-05); rebuy 01-06.
    assert aaa_buys == ["2024-01-01", "2024-01-06"]
