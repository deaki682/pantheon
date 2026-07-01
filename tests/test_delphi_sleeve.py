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


# ── circuit breaker ───────────────────────────────────────────────────

from delphi.sleeve import HALT_DRAWDOWN


def test_halt_constant():
    assert HALT_DRAWDOWN == 0.40


def test_peak_initialized():
    s = DelphiSleeve(initial_cash=1000)
    assert s.peak_equity == 1000.0


def test_update_peak_advances():
    s = DelphiSleeve(initial_cash=1000)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    s.update_peak({"AAPL": 200.0})  # equity now well above 1000
    assert s.peak_equity > 1000.0


def test_update_peak_does_not_lower():
    s = DelphiSleeve(initial_cash=1000)
    s.peak_equity = 1500.0
    s.update_peak({})  # equity ~1000 < peak
    assert s.peak_equity == 1500.0


def test_check_halt_trips_at_40pct():
    s = DelphiSleeve(initial_cash=1000)
    s.peak_equity = 1000.0
    s.cash = 600.0  # 40% drawdown
    assert s.check_halt() is True
    assert s.halted is True


def test_check_halt_below_threshold():
    s = DelphiSleeve(initial_cash=1000)
    s.peak_equity = 1000.0
    s.cash = 700.0  # 30% drawdown
    assert s.check_halt() is False
    assert s.halted is False


def test_breaker_blocks_buys():
    s = DelphiSleeve(initial_cash=1000)
    s.peak_equity = 1000.0
    s.cash = 600.0
    s.check_halt()
    assert s.buy("AAPL", 1.0, 100.0, "2024-05-29") is False


def test_peak_persists_roundtrip():
    s = DelphiSleeve(initial_cash=1000)
    s.peak_equity = 1875.0
    s2 = DelphiSleeve.from_dict(s.to_dict())
    assert s2.peak_equity == 1875.0


def test_legacy_null_peak_heals_to_cash():
    # a pre-breaker sleeve on disk (peak_equity None / absent) must not crash
    # or false-trip — it heals to current cash and self-corrects upward.
    legacy = {"name": "delphi", "cash": 358.37, "peak_equity": None}
    s = DelphiSleeve.from_dict(legacy)
    assert s.peak_equity == pytest.approx(358.37)
    assert s.check_halt() is False  # equity == peak -> 0 drawdown
