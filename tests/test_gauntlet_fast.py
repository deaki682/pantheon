"""shared.gauntlet_fast — vectorized runner pinned to the reference engine.

The load-bearing tests here are the equivalence ones: on the same
synthetic panel, schedule, and cost model, run_cell must reproduce
shared.gauntlet.simulate's equity curve. If the two engines drift, the
fast one is wrong by definition.
"""
import math

import numpy as np
import pytest

from shared.gauntlet import CostModel, StrategySpec, simulate
from shared.gauntlet_fast import (
    Panel,
    build_panel,
    carry_forward,
    equal_weights,
    median_dollar_volume,
    momentum_scores,
    run_cell,
    volatility_scores,
)


def _bars(prices: dict, volume: float = 1000.0) -> list[dict]:
    return [{"date": d, "close": c, "closeadj": c, "volume": volume}
            for d, c in sorted(prices.items())]


def _panel_three_names() -> dict:
    days = [f"2024-01-{i:02d}" for i in range(1, 11)]
    return {
        "AAA": _bars({d: 10.0 + i for i, d in enumerate(days)}),
        "BBB": _bars({d: 50.0 - 2 * i for i, d in enumerate(days)}),
        "CCC": _bars({d: 20.0 * (1.02 ** i) for i, d in enumerate(days)}),
    }


def test_build_panel_shapes_and_nan_for_missing():
    bars = _panel_three_names()
    del bars["BBB"][3]  # drop one bar
    p = build_panel(bars)
    assert p.closeadj.shape == (10, 3)
    j = p.ticker_index["BBB"]
    i = p.day_index["2024-01-04"]
    assert math.isnan(p.closeadj[i, j])


def test_carry_forward_fills_gaps_not_pre_listing():
    m = np.array([[np.nan, 1.0], [np.nan, np.nan], [3.0, 2.0]])
    f = carry_forward(m)
    assert math.isnan(f[0, 0]) and math.isnan(f[1, 0])  # pre-listing stays NaN
    assert f[1, 1] == 1.0  # gap carried
    assert f[2, 1] == 2.0  # real bar wins


@pytest.mark.parametrize("slippage_bps", [0.0, 25.0])
def test_run_cell_matches_reference_engine_buy_and_hold(slippage_bps):
    bars = _panel_three_names()
    cost = CostModel(commission_bps=0.0, slippage_bps=slippage_bps, min_ticket=0.0)
    snapshots = {"2024-01-02": ["AAA", "CCC"]}

    ref = simulate(StrategySpec("ref", lambda d, u, b: {s: 0.5 for s in u}),
                   snapshots, {s: [{"date": b["date"], "close": b["close"]}
                                    for b in bars[s]] for s in bars},
                   initial_cash=10_000.0, cost=cost)

    p = build_panel(bars)
    schedule = [(p.day_index["2024-01-02"], equal_weights(p, ["AAA", "CCC"]))]
    fast = run_cell(p, schedule, initial_cash=10_000.0, cost=cost,
                    start_idx=0, end_idx=len(p.days) - 1)

    assert len(ref["curve"]) == len(fast["curve"])
    for r, f in zip(ref["curve"], fast["curve"]):
        assert f["equity"] == pytest.approx(r["equity"], rel=1e-9), r["date"]


def test_run_cell_matches_reference_engine_with_rebalances():
    bars = _panel_three_names()
    cost = CostModel(commission_bps=0.0, slippage_bps=10.0, min_ticket=0.0)
    picks = {"2024-01-02": ["AAA", "BBB"],
             "2024-01-05": ["CCC"],
             "2024-01-08": ["AAA", "BBB", "CCC"]}
    snapshots = {d: names for d, names in picks.items()}

    ref = simulate(
        StrategySpec("ref", lambda d, u, b: {s: 1.0 / len(u) for s in u}),
        snapshots, {s: [{"date": b["date"], "close": b["close"]}
                         for b in bars[s]] for s in bars},
        initial_cash=10_000.0, cost=cost)

    p = build_panel(bars)
    schedule = [(p.day_index[d], equal_weights(p, names))
                for d, names in picks.items()]
    fast = run_cell(p, schedule, initial_cash=10_000.0, cost=cost,
                    start_idx=0, end_idx=len(p.days) - 1)

    for r, f in zip(ref["curve"], fast["curve"]):
        assert f["equity"] == pytest.approx(r["equity"], rel=1e-6), r["date"]


def test_run_cell_min_ticket_suppresses_small_trades_like_reference():
    bars = _panel_three_names()
    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=5_000.0)
    snapshots = {"2024-01-02": ["AAA", "CCC"]}
    ref = simulate(StrategySpec("ref", lambda d, u, b: {s: 0.5 for s in u}),
                   snapshots, {s: [{"date": b["date"], "close": b["close"]}
                                    for b in bars[s]] for s in bars},
                   initial_cash=8_000.0, cost=cost)
    p = build_panel(bars)
    schedule = [(p.day_index["2024-01-02"], equal_weights(p, ["AAA", "CCC"]))]
    fast = run_cell(p, schedule, initial_cash=8_000.0, cost=cost,
                    start_idx=0, end_idx=len(p.days) - 1)
    # 0.5 * 8000 = 4000 < min_ticket: both engines refuse to trade at all.
    for r, f in zip(ref["curve"], fast["curve"]):
        assert f["equity"] == pytest.approx(r["equity"], rel=1e-12)
        assert f["equity"] == pytest.approx(8_000.0)


def test_run_cell_dead_name_value_freezes_then_frees_at_rebalance():
    bars = {
        "DEAD": _bars({"2024-01-01": 10.0, "2024-01-02": 10.0}),  # delists
        "LIVE": _bars({f"2024-01-{i:02d}": 100.0 for i in range(1, 7)}),
    }
    cost = CostModel(commission_bps=0.0, slippage_bps=0.0, min_ticket=0.0)
    p = build_panel(bars)
    schedule = [
        (p.day_index["2024-01-02"], equal_weights(p, ["DEAD"])),
        (p.day_index["2024-01-05"], equal_weights(p, ["LIVE"])),
    ]
    fast = run_cell(p, schedule, initial_cash=1_000.0, cost=cost,
                    start_idx=0, end_idx=len(p.days) - 1)
    # DEAD's last close carries; the position is sold at that stale price
    # on 01-05 and equity is preserved (the documented optimistic exit).
    assert fast["curve"][-1]["equity"] == pytest.approx(1_000.0)


def test_run_cell_rejects_overallocated_weights():
    bars = _panel_three_names()
    p = build_panel(bars)
    w = equal_weights(p, ["AAA"]) * 1.5
    with pytest.raises(ValueError, match="> 1.0"):
        run_cell(p, [(1, w)], initial_cash=1000.0, cost=CostModel(),
                 start_idx=0, end_idx=3)


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

def test_momentum_scores_window_and_skip():
    prices = np.array([[100.0], [110.0], [121.0], [133.1], [146.41]])
    # t=4, lookback=2, skip=1: return over rows [1, 3] = 133.1/110 - 1
    s = momentum_scores(prices, 4, 2, 1)
    assert s[0] == pytest.approx(133.1 / 110.0 - 1.0)


def test_momentum_scores_nan_endpoint_is_nan():
    prices = np.array([[np.nan], [110.0], [121.0]])
    assert math.isnan(momentum_scores(prices, 2, 2, 0)[0])


def test_volatility_scores_strict_full_window():
    col_ok = [100.0, 101.0, 99.0, 102.0, 100.0]
    col_gap = [100.0, np.nan, 99.0, 102.0, 100.0]
    prices = np.column_stack([col_ok, col_gap])
    s = volatility_scores(prices, 4, 4)
    rets = np.diff(np.array(col_ok)) / np.array(col_ok)[:-1]
    assert s[0] == pytest.approx(np.std(rets))
    assert math.isnan(s[1])


def test_median_dollar_volume_strict_full_window():
    dv = np.array([[10.0, 10.0], [20.0, np.nan], [30.0, 30.0]])
    s = median_dollar_volume(dv, 2, 3)
    assert s[0] == pytest.approx(20.0)
    assert math.isnan(s[1])
