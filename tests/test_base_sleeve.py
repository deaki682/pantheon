from datetime import date, timedelta

import pytest

from shared.base_sleeve import (
    BaseSleeve,
    SleevePosition,
    Settlement,
    next_business_day,
    add_days,
)


def test_next_business_day_skips_weekend():
    # 2024-05-31 is a Friday -> next business day is Monday 2024-06-03
    assert next_business_day("2024-05-31") == "2024-06-03"


def test_next_business_day_midweek():
    # Wednesday -> Thursday
    assert next_business_day("2024-05-29") == "2024-05-30"


def test_add_days_calendar():
    assert add_days("2024-05-29", 7) == "2024-06-05"


def test_initial_state():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    assert s.cash == 1000.0
    assert s.contributed_cash == 1000.0
    assert s.positions == {}
    assert s.pending_settlements == []
    assert s.realized_pnl == 0.0
    assert s.gfv_count == 0
    assert s.trades_count == 0
    assert s.halted is False


def test_inject():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.inject(500.0)
    assert s.cash == 1500.0
    assert s.contributed_cash == 1500.0


def test_inject_rejects_negative():
    s = BaseSleeve("oracle")
    with pytest.raises(ValueError):
        s.inject(-1.0)


def test_withdraw():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.withdraw(300.0)
    assert s.cash == 700.0
    assert s.contributed_cash == 700.0


def test_withdraw_too_much():
    s = BaseSleeve("oracle", initial_cash=100.0)
    with pytest.raises(ValueError):
        s.withdraw(200.0)


def test_buy_basic():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    ok = s.buy("AAPL", shares=2.0, price=100.0, today="2024-05-29")
    assert ok is True
    assert "AAPL" in s.positions
    assert s.positions["AAPL"].shares == 2.0
    assert s.positions["AAPL"].avg_price == 100.0
    # cash -= 200 + 0.10 fee (5bps)
    assert s.cash == pytest.approx(799.90, abs=1e-6)
    assert s.trades_count == 1


def test_buy_halted_blocked_first():
    """Halted check must come BEFORE the price/dollars check."""
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.halted = True
    # Even with valid inputs, halted blocks the buy.
    assert s.buy("AAPL", 1.0, 100.0, "2024-05-29") is False
    assert "AAPL" not in s.positions
    # And with invalid inputs, halted still wins.
    assert s.buy("AAPL", -1.0, -1.0, "2024-05-29") is False


def test_buy_rejects_zero_shares():
    s = BaseSleeve("oracle")
    assert s.buy("AAPL", 0.0, 100.0, "2024-05-29") is False


def test_buy_rejects_zero_price():
    s = BaseSleeve("oracle")
    assert s.buy("AAPL", 1.0, 0.0, "2024-05-29") is False


def test_buy_insufficient_cash():
    s = BaseSleeve("oracle", initial_cash=50.0)
    assert s.buy("AAPL", 1.0, 100.0, "2024-05-29") is False


def test_buy_in_cooldown():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.cooldowns["AAPL"] = "2099-01-01"
    assert s.buy("AAPL", 1.0, 100.0, "2024-05-29") is False


def test_buy_after_cooldown():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.cooldowns["AAPL"] = "2020-01-01"
    assert s.buy("AAPL", 1.0, 100.0, "2024-05-29") is True


def test_buy_adds_to_existing_position():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    s.buy("AAPL", 1.0, 200.0, "2024-05-30")
    pos = s.positions["AAPL"]
    assert pos.shares == 2.0
    assert pos.avg_price == pytest.approx(150.0)


def test_sell_basic():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 2.0, 100.0, "2024-05-29")
    ok = s.sell("AAPL", 1.0, 150.0, "2024-05-30")
    assert ok is True
    assert s.positions["AAPL"].shares == 1.0
    # Settlement is T+1
    assert len(s.pending_settlements) == 1
    assert s.pending_settlements[0].settle_date == "2024-05-31"
    # realized pnl ~ (150-100)*1 - fee
    assert s.realized_pnl == pytest.approx(50.0 - 150.0 * 0.0005, abs=1e-6)


def test_sell_more_than_held():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    assert s.sell("AAPL", 2.0, 150.0, "2024-05-30") is False


def test_sell_nothing_held():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    assert s.sell("AAPL", 1.0, 100.0, "2024-05-30") is False


def test_sell_clears_position_when_flat():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    s.sell("AAPL", 1.0, 150.0, "2024-05-30")
    assert "AAPL" not in s.positions


def test_sell_blocked_when_halted():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    s.halted = True
    assert s.sell("AAPL", 1.0, 100.0, "2024-05-30") is False


def test_settlement_tracking():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    s.sell("AAPL", 1.0, 100.0, "2024-05-30")
    # Unsettled cash exists before T+1 clears
    assert s.unsettled_cash("2024-05-30") > 0
    assert s.settled_cash("2024-05-30") < s.cash
    # After T+1 (2024-05-31), settlement clears
    s.process_settlements("2024-05-31")
    assert s.pending_settlements == []


def test_gfv_count_increments_on_unsettled_buy():
    s = BaseSleeve("oracle", initial_cash=100.0)
    # Buy then sell -> proceeds unsettled
    s.buy("AAPL", 1.0, 50.0, "2024-05-29")
    s.sell("AAPL", 1.0, 60.0, "2024-05-29")
    initial = s.gfv_count
    # Buy again same day using the unsettled proceeds.
    ok = s.buy("MSFT", 1.0, 70.0, "2024-05-29")
    assert ok is True
    # That second buy used unsettled cash -> GFV.
    assert s.gfv_count == initial + 1


def test_equity_includes_positions():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    eq = s.equity({"AAPL": 150.0})
    # cash (~899.95) + 1 * 150 = ~1049.95
    assert eq == pytest.approx(s.cash + 150.0, abs=1e-6)


def test_equity_uses_avg_price_for_missing_marks():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    eq = s.equity({})
    assert eq == pytest.approx(s.cash + 100.0, abs=1e-6)


def test_cooldown_set_on_sell():
    class S(BaseSleeve):
        cooldown_days = 7

    s = S("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    s.sell("AAPL", 1.0, 110.0, "2024-05-30")
    assert "AAPL" in s.cooldowns
    assert s.cooldowns["AAPL"] == "2024-06-06"


def test_liquidate_all_bypasses_halted():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    s.halted = True
    sold = s.liquidate_all({"AAPL": 90.0}, "2024-05-30")
    assert ("AAPL", 1.0, 90.0) == sold[0]
    assert "AAPL" not in s.positions
    assert s.halted is True  # halted state restored


def test_persist_roundtrip(tmp_path):
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 1.0, 100.0, "2024-05-29")
    p = tmp_path / "sleeve.json"
    s.save(str(p))
    s2 = BaseSleeve.load(str(p))
    assert s2.cash == s.cash
    assert s2.positions["AAPL"].shares == 1.0
    assert s2.positions["AAPL"].avg_price == 100.0


def test_to_dict_from_dict_roundtrip():
    s = BaseSleeve("oracle", initial_cash=1000.0)
    s.buy("AAPL", 2.0, 100.0, "2024-05-29")
    s.sell("AAPL", 1.0, 110.0, "2024-05-30")
    d = s.to_dict()
    s2 = BaseSleeve.from_dict(d)
    assert s2.realized_pnl == pytest.approx(s.realized_pnl)
    assert len(s2.pending_settlements) == 1
