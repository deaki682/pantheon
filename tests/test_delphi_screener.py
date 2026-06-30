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


def test_score_universe_additions():
    prices = [100.0] * 70
    prices[-1] = 120.0
    ranked = score_universe({"NEWCO": prices}, additions={"NEWCO"})
    assert len(ranked) == 1
    assert ranked[0]["symbol"] == "NEWCO"


def test_score_universe_removals():
    prices = [100.0] * 70
    prices[-1] = 120.0
    ranked = score_universe({UNIVERSE[0]: prices}, removals={UNIVERSE[0]})
    assert len(ranked) == 0


def test_score_universe_additions_and_removals():
    prices_new = [100.0] * 70
    prices_new[-1] = 130.0
    prices_old = [100.0] * 70
    prices_old[-1] = 120.0
    ranked = score_universe(
        {UNIVERSE[0]: prices_old, "NEWCO": prices_new},
        additions={"NEWCO"},
        removals={UNIVERSE[0]},
    )
    assert len(ranked) == 1
    assert ranked[0]["symbol"] == "NEWCO"
