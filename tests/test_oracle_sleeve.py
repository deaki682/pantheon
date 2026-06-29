import pytest

from oracle.sleeve import (
    ACHILLES_RESERVE,
    CAPITAL_BASE,
    CAPITAL_CEILING,
    COOLDOWN_DAYS,
    DERISK_DRAWDOWN_VS_MARKET,
    HALT_ABSOLUTE_DRAWDOWN,
    OracleSleeve,
)


def test_initial_state():
    s = OracleSleeve(initial_cash=1000.0)
    assert s.name == "oracle"
    assert s.cash == 1000.0
    assert s.peak_equity == 1000.0
    assert s.cooldown_days == COOLDOWN_DAYS == 31


def test_capital_constants():
    assert CAPITAL_BASE == 1_000.0
    assert CAPITAL_CEILING == 12_000.0
    assert ACHILLES_RESERVE == 1_000.0


def test_update_peak_advances():
    s = OracleSleeve(initial_cash=1000.0)
    s.cash = 1500.0
    s.update_peak()
    assert s.peak_equity == 1500.0


def test_update_peak_doesnt_regress():
    s = OracleSleeve(initial_cash=1000.0)
    s.peak_equity = 1500.0
    s.cash = 800.0
    s.update_peak()
    assert s.peak_equity == 1500.0


def test_absolute_drawdown():
    s = OracleSleeve(initial_cash=1000.0)
    s.peak_equity = 1000.0
    s.cash = 800.0
    assert s.absolute_drawdown() == pytest.approx(0.2)


def test_excess_drawdown_vs_market():
    s = OracleSleeve(initial_cash=1000.0)
    s.peak_equity = 1000.0
    s.cash = 800.0  # 20% absolute drawdown
    # Market down 5%, so our excess is 15%.
    assert s.excess_drawdown_vs_market(None, 0.05) == pytest.approx(0.15)


def test_circuit_breaker_ok():
    s = OracleSleeve(initial_cash=1000.0)
    s.peak_equity = 1000.0
    s.cash = 950.0  # 5% drawdown
    assert s.check_circuit_breakers(None, 0.0) == "ok"


def test_circuit_breaker_derisk():
    s = OracleSleeve(initial_cash=1000.0)
    s.peak_equity = 1000.0
    s.cash = 800.0  # 20% drawdown
    assert s.check_circuit_breakers(None, market_drawdown=0.0) == "derisk"
    assert s.halted is False


def test_circuit_breaker_halt():
    s = OracleSleeve(initial_cash=1000.0)
    s.peak_equity = 1000.0
    s.cash = 600.0  # 40% drawdown -> halt
    out = s.check_circuit_breakers(None, market_drawdown=0.0)
    assert out == "halt"
    assert s.halted is True


def test_halt_threshold_exact():
    s = OracleSleeve(initial_cash=1000.0)
    s.peak_equity = 1000.0
    s.cash = 680.0  # exactly 32% drawdown
    out = s.check_circuit_breakers(None)
    assert out == "halt"


def test_persistence_roundtrip(tmp_path):
    s = OracleSleeve(initial_cash=2000.0)
    s.peak_equity = 2500.0
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    p = tmp_path / "oracle.json"
    s.save(str(p))
    loaded = OracleSleeve.from_dict(__import__("json").loads(p.read_text()))
    assert isinstance(loaded, OracleSleeve)
    assert loaded.peak_equity == 2500.0
    assert "AAPL" in loaded.positions


def test_position_cohort_id_default():
    s = OracleSleeve(initial_cash=1000.0)
    s.buy("ACME", 1.0, 50.0, "2026-06-29")
    assert s.positions["ACME"].cohort_id == ""


def test_position_cohort_id_persists(tmp_path):
    s = OracleSleeve(initial_cash=1000.0)
    s.buy("ACME", 1.0, 50.0, "2026-06-29")
    s.positions["ACME"].cohort_id = "cohort-1"
    p = tmp_path / "oracle.json"
    s.save(str(p))
    loaded = OracleSleeve.from_dict(__import__("json").loads(p.read_text()))
    assert loaded.positions["ACME"].cohort_id == "cohort-1"


def test_position_without_cohort_id_loads():
    """Old sleeve data without cohort_id still loads (backward compat)."""
    from shared.base_sleeve import SleevePosition
    pos = SleevePosition(shares=1.0, avg_price=50.0, entry_date="2026-01-01")
    assert pos.cohort_id == ""


def test_cancel_buy_restores_cash():
    s = OracleSleeve(initial_cash=1000.0)
    s.buy("ACME", 2.0, 50.0, "2026-06-29")
    cash_after_buy = s.cash
    assert "ACME" in s.positions
    s.cancel_buy("ACME", 2.0, 50.0)
    assert "ACME" not in s.positions
    assert s.cash == pytest.approx(1000.0)


def test_cancel_buy_partial():
    s = OracleSleeve(initial_cash=1000.0)
    s.buy("ACME", 4.0, 50.0, "2026-06-29")
    s.cancel_buy("ACME", 2.0, 50.0)
    assert s.positions["ACME"].shares == pytest.approx(2.0)


def test_cancel_buy_unknown_symbol():
    s = OracleSleeve(initial_cash=1000.0)
    assert s.cancel_buy("ZZZZ", 1.0, 50.0) is False


def test_cancel_buy_excess_shares():
    s = OracleSleeve(initial_cash=1000.0)
    s.buy("ACME", 1.0, 50.0, "2026-06-29")
    assert s.cancel_buy("ACME", 5.0, 50.0) is False
