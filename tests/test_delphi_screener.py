import pytest

from delphi.screener import score_universe
from delphi.signals import UNIVERSE


def test_score_universe_ranks():
    prices_up = [100.0] * 70
    prices_up[-1] = 130.0
    prices_flat = [100.0] * 70

    universe_prices = {UNIVERSE[0]: prices_up, UNIVERSE[1]: prices_flat}
    ranked = score_universe(universe_prices)
    assert len(ranked) >= 1
    assert ranked[0]["symbol"] == UNIVERSE[0]


def test_score_universe_filters_non_universe():
    prices = [100.0] * 70
    prices[-1] = 120.0
    universe_prices = {"ZZZZ": prices}
    ranked = score_universe(universe_prices)
    assert len(ranked) == 0
