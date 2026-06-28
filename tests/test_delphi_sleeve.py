import pytest

from delphi.sleeve import PICK_BLOCKLIST, COOLDOWN_DAYS, MIN_TICKET, DelphiSleeve, is_blocked


def test_constants():
    assert COOLDOWN_DAYS == 7
    assert MIN_TICKET == 25.0


def test_blocklist_contains_all_sector_etfs():
    for etf in ("XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLRE", "XLB", "XLC"):
        assert etf in PICK_BLOCKLIST


def test_spy_not_in_pick_blocklist():
    assert "SPY" not in PICK_BLOCKLIST


def test_is_blocked_case_insensitive():
    assert is_blocked("xlk")
    assert not is_blocked("SPY")
    assert not is_blocked("AAPL")


def test_init():
    s = DelphiSleeve(initial_cash=1000)
    assert s.name == "delphi"
    assert s.cooldown_days == 7


def test_cannot_buy_sector_etf():
    s = DelphiSleeve(initial_cash=1000)
    assert s.buy("XLK", 1.0, 100, "2024-05-29") is False
    assert "XLK" not in s.positions


def test_can_buy_stock():
    s = DelphiSleeve(initial_cash=1000)
    assert s.buy("AAPL", 1.0, 100, "2024-05-29") is True
    assert "AAPL" in s.positions


def test_can_buy_spy():
    s = DelphiSleeve(initial_cash=1000)
    assert s.buy("SPY", 1.0, 100, "2024-05-29") is True
