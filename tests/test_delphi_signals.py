import pytest

from delphi.signals import UNIVERSE, momentum, moving_average, rank_by_momentum


def test_universe_has_stocks():
    assert len(UNIVERSE) > 100


def test_momentum_simple():
    prices = [100.0] * 127
    prices[-1] = 110.0
    prices[-22] = 100.0
    assert momentum(prices, 21) == pytest.approx(0.10)


def test_momentum_insufficient_data():
    assert momentum([100, 105], 10) == 0.0


def test_momentum_zero_base():
    assert momentum([0] * 22, 21) == 0.0


def test_moving_average():
    prices = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert moving_average(prices, 3) == pytest.approx(40.0)


def test_moving_average_insufficient():
    assert moving_average([10.0, 20.0], 5) is None


def test_rank_by_momentum_filters_below_ma():
    prices_above = [100.0] * 70
    prices_above[-1] = 130.0

    prices_below = [130.0] * 70
    prices_below[-1] = 100.0

    universe = {"ABOVE": prices_above, "BELOW": prices_below}
    ranked = rank_by_momentum(universe, lookback=65, ma_period=20)
    symbols = [r["symbol"] for r in ranked]
    assert "ABOVE" in symbols
    assert "BELOW" not in symbols


def test_rank_by_momentum_sorted_descending():
    prices_a = [100.0] * 70
    prices_a[-1] = 120.0
    prices_b = [100.0] * 70
    prices_b[-1] = 150.0

    ranked = rank_by_momentum({"A": prices_a, "B": prices_b}, lookback=65, ma_period=20)
    assert ranked[0]["symbol"] == "B"
    assert ranked[1]["symbol"] == "A"
