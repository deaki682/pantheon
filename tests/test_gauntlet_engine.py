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
