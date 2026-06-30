import pytest

from delphi.sleeve import COOLDOWN_DAYS, MIN_TICKET, MAX_POSITIONS, DelphiSleeve


def test_constants():
    assert COOLDOWN_DAYS == 7
    assert MIN_TICKET == 25.0
    assert MAX_POSITIONS == 10


def test_init():
    s = DelphiSleeve(initial_cash=1000)
    assert s.name == "delphi"
    assert s.cooldown_days == 7


def test_can_buy_stock():
    s = DelphiSleeve(initial_cash=1000)
    assert s.buy("AAPL", 1.0, 100, "2024-05-29") is True
    assert "AAPL" in s.positions
