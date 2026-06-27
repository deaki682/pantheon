import pytest

from delphi.signals import (
    SECTOR_MAP, TIMEFRAMES, composite_score, momentum, rank_sectors, score_sectors,
)


def test_sector_map_has_11():
    assert len(SECTOR_MAP) == 11


def test_timeframes():
    assert TIMEFRAMES == (21, 63, 126)


def test_momentum_simple():
    prices = [100.0] * 127
    prices[-1] = 110.0
    prices[-22] = 100.0
    assert momentum(prices, 21) == pytest.approx(0.10)


def test_momentum_insufficient_data():
    assert momentum([100, 105], 10) == 0.0


def test_momentum_zero_base():
    assert momentum([0] * 22, 21) == 0.0


def test_composite_score_positive():
    sec = [100.0] * 127
    sec[-1] = 120
    spy = [100.0] * 127
    spy[-1] = 105
    out = composite_score(sec, spy)
    # Both have positive momentum; sector outperforms -> positive composite
    assert out > 0


def test_composite_score_negative_when_underperforming():
    sec = [100.0] * 127
    sec[-1] = 95  # -5% over the window
    spy = [100.0] * 127
    spy[-1] = 105  # +5%
    assert composite_score(sec, spy) < 0


def test_score_sectors_keys_canonical():
    sec_prices = {"XLK": [100.0] * 127, "XLF": [100.0] * 127}
    spy = [100.0] * 127
    out = score_sectors(sec_prices, spy)
    assert "technology" in out
    assert "financials" in out


def test_score_sectors_skips_unknown_etf():
    sec_prices = {"ZZZ": [100.0] * 127}
    out = score_sectors(sec_prices, [100.0] * 127)
    assert out == {}


def test_rank_sectors():
    scores = {"tech": 0.1, "finance": 0.3, "energy": -0.1}
    ranked = rank_sectors(scores)
    assert ranked[0] == ("finance", 0.3)
    assert ranked[-1] == ("energy", -0.1)
