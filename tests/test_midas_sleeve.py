import json

import pytest

from midas.sleeve import (
    CAPITAL_BASE,
    FEE_BPS,
    HALT_DRAWDOWN,
    HARD_STOP_PCT,
    STOP_COOLDOWN_WEEKS,
    MidasPosition,
    MidasSleeve,
    WeeklyResult,
)


def _enter(s, symbol="ACME", price=100.0, shares=9.0, today="2026-07-07",
           score=0.5, convergence_count=2, exit_date="2026-07-11"):
    return s.enter(
        symbol=symbol, shares=shares, price=price, today=today,
        score=score, convergence_count=convergence_count,
        signals={"insider_cluster": 1.0, "earnings_beat": 0.8},
        exit_date=exit_date,
    )


def test_initial_state():
    s = MidasSleeve()
    assert s.name == "midas"
    assert s.cash == CAPITAL_BASE == 1000.0
    assert s.position is None
    assert s.peak_equity == 1000.0
    assert s.halted is False
    assert s.weekly_results == []


def test_enter_basic():
    s = MidasSleeve(initial_cash=1000.0)
    ok = _enter(s, price=100.0, shares=9.0)
    assert ok is True
    assert s.position is not None
    assert s.position.symbol == "ACME"
    assert s.position.shares == 9.0
    assert s.position.entry_price == 100.0
    assert s.position.stop_price == pytest.approx(90.0)
    fee = 900.0 * FEE_BPS / 10_000
    assert s.cash == pytest.approx(1000.0 - 900.0 - fee)


def test_enter_sets_stop_price():
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, price=50.0, shares=10.0)
    assert s.position.stop_price == pytest.approx(50.0 * (1.0 + HARD_STOP_PCT))


def test_enter_blocked_when_halted():
    s = MidasSleeve(initial_cash=1000.0)
    s.halted = True
    ok = _enter(s)
    assert ok is False
    assert s.position is None


def test_enter_blocked_when_position_exists():
    s = MidasSleeve(initial_cash=10000.0)
    _enter(s, symbol="AAPL", price=10.0, shares=1.0)
    ok = _enter(s, symbol="GOOG", price=10.0, shares=1.0)
    assert ok is False


def test_enter_blocked_insufficient_cash():
    s = MidasSleeve(initial_cash=100.0)
    ok = _enter(s, price=200.0, shares=1.0)
    assert ok is False


def test_enter_blocked_cooldown():
    s = MidasSleeve(initial_cash=1000.0)
    s.cooldowns["ACME"] = "2026-08-01"
    ok = _enter(s, symbol="ACME", today="2026-07-07")
    assert ok is False


def test_exit_time_stop():
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, price=100.0, shares=9.0)
    pnl = s.exit(price=110.0, today="2026-07-11", reason="time_stop")
    assert pnl is not None
    assert pnl > 0
    assert s.position is None
    assert len(s.weekly_results) == 1
    assert s.weekly_results[0].exit_reason == "time_stop"
    assert s.weekly_results[0].return_pct == pytest.approx(0.10)


def test_exit_hard_stop_sets_cooldown():
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, price=100.0, shares=9.0)
    s.exit(price=89.0, today="2026-07-09", reason="hard_stop")
    assert "ACME" in s.cooldowns
    assert s.position is None


def test_exit_no_position():
    s = MidasSleeve(initial_cash=1000.0)
    assert s.exit(price=100.0, today="2026-07-11", reason="time_stop") is None


def test_check_stop():
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, price=100.0, shares=9.0)
    assert s.check_stop(95.0) is False
    assert s.check_stop(90.0) is True
    assert s.check_stop(85.0) is True


def test_should_time_stop():
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, exit_date="2026-07-11")
    assert s.should_time_stop("2026-07-10") is False
    assert s.should_time_stop("2026-07-11") is True
    assert s.should_time_stop("2026-07-12") is True


def test_equity_with_position():
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, price=100.0, shares=9.0)
    eq_flat = s.equity({"ACME": 100.0})
    fee = 900.0 * FEE_BPS / 10_000
    assert eq_flat == pytest.approx(1000.0 - fee)
    eq_up = s.equity({"ACME": 110.0})
    assert eq_up > eq_flat


def test_drawdown_and_halt():
    s = MidasSleeve(initial_cash=1000.0)
    s.peak_equity = 1000.0
    _enter(s, price=100.0, shares=9.0)
    assert s.check_halt({"ACME": 30.0}) is True
    assert s.halted is True


def test_liquidate():
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, price=100.0, shares=9.0)
    pnl = s.liquidate({"ACME": 105.0}, "2026-07-09")
    assert pnl is not None
    assert s.position is None


def test_persistence_roundtrip(tmp_path):
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, price=100.0, shares=9.0)
    s.exit(price=110.0, today="2026-07-11", reason="time_stop")
    _enter(s, symbol="GOOG", price=50.0, shares=5.0, today="2026-07-14",
           exit_date="2026-07-18")

    p = tmp_path / "midas.json"
    s.save(str(p))
    loaded = MidasSleeve.from_dict(json.loads(p.read_text()))

    assert isinstance(loaded, MidasSleeve)
    assert loaded.position is not None
    assert loaded.position.symbol == "GOOG"
    assert len(loaded.weekly_results) == 1
    assert loaded.weekly_results[0].symbol == "ACME"
    assert loaded.realized_pnl == s.realized_pnl
    assert loaded.trades_count == s.trades_count


def test_persistence_no_position(tmp_path):
    s = MidasSleeve(initial_cash=1000.0)
    p = tmp_path / "midas.json"
    s.save(str(p))
    loaded = MidasSleeve.load(str(p))
    assert loaded.position is None
    assert loaded.cash == 1000.0


def test_hit_rate():
    s = MidasSleeve(initial_cash=10000.0)
    for i, ret in enumerate([0.05, -0.08, 0.12, 0.03, -0.02]):
        s.weekly_results.append(WeeklyResult(
            symbol=f"SYM{i}", week_id=f"2026-W{i+1:02d}",
            entry_date="2026-01-01", entry_price=100.0,
            exit_date="2026-01-05", exit_price=100.0 * (1 + ret),
            exit_reason="time_stop", return_pct=ret, pnl=ret * 1000,
            score=0.5, convergence_count=2, signals={},
        ))
    assert s.hit_rate() == pytest.approx(3 / 5)


def test_convergence_hit_rates():
    s = MidasSleeve()
    s.weekly_results = [
        WeeklyResult("A", "W01", "", 100, "", 110, "ts", 0.10, 10, 0.5, 1, {}),
        WeeklyResult("B", "W02", "", 100, "", 90, "ts", -0.10, -10, 0.5, 1, {}),
        WeeklyResult("C", "W03", "", 100, "", 120, "ts", 0.20, 20, 0.5, 2, {}),
        WeeklyResult("D", "W04", "", 100, "", 115, "ts", 0.15, 15, 0.5, 2, {}),
        WeeklyResult("E", "W05", "", 100, "", 95, "ts", -0.05, -5, 0.5, 3, {}),
    ]
    rates = s.convergence_hit_rates()
    assert rates[1] == pytest.approx(0.5)
    assert rates[2] == pytest.approx(1.0)
    assert rates[3] == pytest.approx(0.0)


def test_inject_withdraw():
    s = MidasSleeve(initial_cash=1000.0)
    s.inject(500.0)
    assert s.cash == 1500.0
    assert s.contributed_cash == 1500.0
    s.withdraw(200.0)
    assert s.cash == 1300.0
    assert s.contributed_cash == 1300.0


def test_settlements():
    s = MidasSleeve(initial_cash=1000.0)
    _enter(s, price=100.0, shares=9.0)
    s.exit(price=110.0, today="2026-07-11", reason="time_stop")
    assert len(s.pending_settlements) == 1
    assert s.unsettled_cash("2026-07-11") > 0
    s.process_settlements("2026-07-14")
    assert len(s.pending_settlements) == 0


def test_trades_count_increments():
    s = MidasSleeve(initial_cash=1000.0)
    assert s.trades_count == 0
    _enter(s, price=100.0, shares=9.0)
    assert s.trades_count == 1
    s.exit(price=110.0, today="2026-07-11", reason="time_stop")
    assert s.trades_count == 2
