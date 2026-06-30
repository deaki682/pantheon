import pytest

from delphi.signals import (
    UNIVERSE, momentum, moving_average, rank_by_momentum,
    exit_candidates, enrich_with_signals, breadth,
)
from shared.base_sleeve import BaseSleeve


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


# ---- exit_candidates ----

def test_exit_candidates_flags_below_ma():
    s = BaseSleeve("x", initial_cash=10_000)
    s.buy("AAPL", 1.0, 150.0, "2024-05-29")
    prices = {"AAPL": 95.0}
    hist = {"AAPL": [100.0] * 25}
    cands = exit_candidates(s.positions, prices, hist, ma_period=20)
    assert len(cands) == 1
    assert cands[0]["symbol"] == "AAPL"
    assert cands[0]["pct_below_ma"] < 0


def test_exit_candidates_skips_above_ma():
    s = BaseSleeve("x", initial_cash=10_000)
    s.buy("AAPL", 1.0, 150.0, "2024-05-29")
    prices = {"AAPL": 105.0}
    hist = {"AAPL": [100.0] * 25}
    cands = exit_candidates(s.positions, prices, hist, ma_period=20)
    assert len(cands) == 0


def test_exit_candidates_includes_return_since_entry():
    s = BaseSleeve("x", initial_cash=10_000)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    prices = {"AAPL": 90.0}
    hist = {"AAPL": [95.0] * 25}
    cands = exit_candidates(s.positions, prices, hist, ma_period=20)
    assert cands[0]["return_since_entry"] == pytest.approx(-0.10)


# ---- enrich_with_signals ----

def test_enrich_adds_insider_flag():
    cands = [{"symbol": "AAPL", "momentum": 0.3}]
    clusters = {"AAPL": {"n_insiders": 3, "total_value": 500_000}}
    enriched = enrich_with_signals(cands, insider_clusters=clusters)
    assert enriched[0]["insider_buying"] is True
    assert enriched[0]["insider_count"] == 3


def test_enrich_no_signals():
    cands = [{"symbol": "AAPL", "momentum": 0.3}]
    enriched = enrich_with_signals(cands)
    assert enriched[0]["insider_buying"] is False
    assert enriched[0]["smart_money"] is False


def test_enrich_smart_money_list():
    cands = [{"symbol": "MSFT", "momentum": 0.2}]
    sm = {"MSFT": ["Bridgewater", "Renaissance"]}
    enriched = enrich_with_signals(cands, smart_money=sm)
    assert enriched[0]["smart_money"] is True
    assert enriched[0]["smart_money_holders"] == 2


# ---- breadth ----

def test_breadth_all_above():
    prices = {sym: [100.0] * 25 for sym in UNIVERSE[:5]}
    b = breadth(prices, ma_period=20)
    assert b["pct_above_ma"] == 1.0
    assert b["above_ma"] == 5


def test_breadth_none_above():
    prices = {}
    for sym in UNIVERSE[:5]:
        hist = [100.0] * 25
        hist[-1] = 80.0
        prices[sym] = hist
    b = breadth(prices, ma_period=20)
    assert b["pct_above_ma"] == 0.0


def test_breadth_excludes_non_universe():
    prices = {"ZZZZ": [100.0] * 25}
    b = breadth(prices, ma_period=20)
    assert b["total"] == 0
