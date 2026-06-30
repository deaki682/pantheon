import pytest

from achilles.sleeve import (
    CAPITAL_BASE,
    FEE_BPS,
    HALT_DRAWDOWN,
    HARD_STOP_PCT,
    HOLD_DAYS,
    STOP_COOLDOWN_WEEKS,
    AchillesPosition,
    AchillesSleeve,
    Settlement,
    TradeResult,
    trading_days_ahead,
)


# =====================================================================
# Constants
# =====================================================================


def test_constants():
    assert HARD_STOP_PCT == -0.08
    assert HALT_DRAWDOWN == 0.40
    assert HOLD_DAYS == 5
    assert FEE_BPS == 5
    assert CAPITAL_BASE == 1_000.0
    assert STOP_COOLDOWN_WEEKS == 4


# =====================================================================
# trading_days_ahead
# =====================================================================


class TestTradingDaysAhead:
    def test_weekday_to_weekday(self):
        # Wednesday 2026-07-01 + 5 trading days = Wednesday 2026-07-08
        assert trading_days_ahead("2026-07-01", 5) == "2026-07-08"

    def test_friday_skips_weekend(self):
        # Friday 2026-07-03 + 1 = Monday 2026-07-06
        assert trading_days_ahead("2026-07-03", 1) == "2026-07-06"

    def test_friday_plus_five(self):
        # Friday 2026-07-03 + 5 = Friday 2026-07-10
        assert trading_days_ahead("2026-07-03", 5) == "2026-07-10"

    def test_zero_days(self):
        assert trading_days_ahead("2026-07-01", 0) == "2026-07-01"

    def test_monday_plus_one(self):
        # Monday 2026-07-06 + 1 = Tuesday 2026-07-07
        assert trading_days_ahead("2026-07-06", 1) == "2026-07-07"


# =====================================================================
# Standalone check
# =====================================================================


def test_standalone_no_base_sleeve_inheritance():
    """AchillesSleeve must NOT inherit from BaseSleeve."""
    from shared.base_sleeve import BaseSleeve
    assert not issubclass(AchillesSleeve, BaseSleeve)


# =====================================================================
# Constructor
# =====================================================================


class TestInit:
    def test_defaults(self):
        s = AchillesSleeve()
        assert s.cash == 1000.0
        assert s.position is None
        assert s.halted is False
        assert s.peak_equity == 1000.0
        assert s.realized_pnl == 0.0
        assert s.trades_count == 0
        assert s.trade_results == []
        assert s.cooldowns == {}
        assert s.name == "achilles"

    def test_custom_cash(self):
        s = AchillesSleeve(initial_cash=5000.0)
        assert s.cash == 5000.0
        assert s.peak_equity == 5000.0
        assert s.contributed_cash == 5000.0


# =====================================================================
# Helper to enter a position
# =====================================================================


def _enter_args(**overrides):
    defaults = dict(
        symbol="ACME",
        shares=10.0,
        price=50.0,
        today="2026-07-15",
        score=0.85,
        surprise_pct=15.0,
    )
    defaults.update(overrides)
    return defaults


# =====================================================================
# enter / exit flow
# =====================================================================


class TestEnter:
    def test_basic_enter(self):
        s = AchillesSleeve(initial_cash=1000.0)
        ok = s.enter(**_enter_args())
        assert ok is True
        assert s.position is not None
        assert s.position.symbol == "ACME"
        assert s.position.shares == 10.0
        assert s.position.entry_price == 50.0
        assert s.position.entry_date == "2026-07-15"

    def test_cash_deducted_with_fee(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        # cost = 10 * 50 = 500; fee = 500 * 5/10000 = 0.25; total = 500.25
        assert s.cash == pytest.approx(1000.0 - 500.25)

    def test_stop_price_set(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0))
        # stop = 100 * (1 + (-0.08)) = 92.0
        assert s.position.stop_price == pytest.approx(92.0)

    def test_exit_date_five_trading_days(self):
        s = AchillesSleeve(initial_cash=1000.0)
        # 2026-07-15 is a Wednesday; +5 trading days = 2026-07-22 (Wednesday)
        s.enter(**_enter_args(today="2026-07-15"))
        assert s.position.exit_date == "2026-07-22"

    def test_exit_date_skips_weekends(self):
        s = AchillesSleeve(initial_cash=1000.0)
        # 2026-07-17 is Friday; +5 trading days = Friday 2026-07-24
        s.enter(**_enter_args(today="2026-07-17"))
        assert s.position.exit_date == "2026-07-24"

    def test_cannot_enter_when_holding(self):
        s = AchillesSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="ACME"))
        ok = s.enter(**_enter_args(symbol="OTHER"))
        assert ok is False
        assert s.position.symbol == "ACME"

    def test_cannot_enter_when_halted(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.halted = True
        ok = s.enter(**_enter_args())
        assert ok is False
        assert s.position is None

    def test_cannot_enter_insufficient_cash(self):
        s = AchillesSleeve(initial_cash=100.0)
        ok = s.enter(**_enter_args(shares=10.0, price=50.0))
        assert ok is False
        assert s.position is None

    def test_cannot_enter_zero_shares(self):
        s = AchillesSleeve(initial_cash=1000.0)
        ok = s.enter(**_enter_args(shares=0))
        assert ok is False

    def test_cannot_enter_zero_price(self):
        s = AchillesSleeve(initial_cash=1000.0)
        ok = s.enter(**_enter_args(price=0))
        assert ok is False

    def test_trades_count_incremented(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        assert s.trades_count == 1

    def test_optional_confirming_signals(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(
            revenue_beat=True,
            guidance_raised=True,
            short_float_pct=25.0,
        ))
        pos = s.position
        assert pos.revenue_beat is True
        assert pos.guidance_raised is True
        assert pos.short_float_pct == 25.0


class TestExit:
    def test_basic_exit(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        realized = s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        assert realized is not None
        assert realized > 0
        assert s.position is None

    def test_exit_loss(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        realized = s.exit(price=45.0, today="2026-07-22", reason="hard_stop")
        assert realized is not None
        assert realized < 0

    def test_exit_no_position(self):
        s = AchillesSleeve(initial_cash=1000.0)
        result = s.exit(price=50.0, today="2026-07-22", reason="time_stop")
        assert result is None

    def test_exit_zero_price(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        result = s.exit(price=0, today="2026-07-22", reason="time_stop")
        assert result is None
        assert s.position is not None  # position not cleared

    def test_trade_result_recorded(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        assert len(s.trade_results) == 1
        tr = s.trade_results[0]
        assert tr.symbol == "ACME"
        assert tr.entry_price == 50.0
        assert tr.exit_price == 55.0
        assert tr.exit_reason == "time_stop"
        assert tr.return_pct == pytest.approx(0.10)

    def test_cash_restored_on_exit(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        cash_after_entry = s.cash
        s.exit(price=50.0, today="2026-07-22", reason="time_stop")
        # Cash should be higher than after entry (proceeds added, minus exit fee)
        assert s.cash > cash_after_entry

    def test_realized_pnl_accumulated(self):
        s = AchillesSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        pnl1 = s.realized_pnl
        assert pnl1 > 0
        s.enter(**_enter_args(shares=10.0, price=50.0, today="2026-07-23"))
        s.exit(price=52.0, today="2026-07-30", reason="time_stop")
        assert s.realized_pnl > pnl1


# =====================================================================
# check_stop / should_time_stop
# =====================================================================


class TestStopChecks:
    def test_check_stop_triggers(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0))
        # stop at 92.0
        assert s.check_stop(92.0) is True
        assert s.check_stop(91.0) is True

    def test_check_stop_above_stop(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0))
        assert s.check_stop(93.0) is False
        assert s.check_stop(100.0) is False

    def test_check_stop_no_position(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.check_stop(50.0) is False

    def test_should_time_stop_on_exit_date(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-15"))
        # exit_date = 2026-07-22
        assert s.should_time_stop("2026-07-22") is True

    def test_should_time_stop_after_exit_date(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-15"))
        assert s.should_time_stop("2026-07-23") is True

    def test_should_time_stop_before_exit_date(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-15"))
        assert s.should_time_stop("2026-07-21") is False

    def test_should_time_stop_no_position(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.should_time_stop("2026-07-22") is False


# =====================================================================
# Cooldowns
# =====================================================================


class TestCooldowns:
    def test_hard_stop_adds_cooldown(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(price=40.0, today="2026-07-16", reason="hard_stop")
        assert "ACME" in s.cooldowns
        # 4 weeks = 28 days from 2026-07-16 = 2026-08-13
        assert s.cooldowns["ACME"] == "2026-08-13"

    def test_cooldown_blocks_entry(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(price=40.0, today="2026-07-16", reason="hard_stop")
        # Try to re-enter during cooldown
        ok = s.enter(**_enter_args(symbol="ACME", today="2026-07-20"))
        assert ok is False

    def test_cooldown_allows_entry_after_expiry(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(price=40.0, today="2026-07-16", reason="hard_stop")
        # After cooldown (2026-08-13)
        ok = s.enter(**_enter_args(symbol="ACME", today="2026-08-14"))
        assert ok is True

    def test_cooldown_different_symbol_ok(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(price=40.0, today="2026-07-16", reason="hard_stop")
        ok = s.enter(**_enter_args(symbol="OTHER", today="2026-07-17"))
        assert ok is True

    def test_time_stop_no_cooldown(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        assert "ACME" not in s.cooldowns

    def test_in_cooldown_method(self):
        s = AchillesSleeve()
        s.cooldowns["ACME"] = "2026-08-13"
        assert s.in_cooldown("ACME", "2026-07-20") is True
        assert s.in_cooldown("ACME", "2026-08-13") is False  # on expiry day
        assert s.in_cooldown("ACME", "2026-08-14") is False
        assert s.in_cooldown("OTHER", "2026-07-20") is False

    def test_cooldown_case_insensitive(self):
        s = AchillesSleeve()
        s.cooldowns["ACME"] = "2026-08-13"
        assert s.in_cooldown("acme", "2026-07-20") is True


# =====================================================================
# Halt / drawdown
# =====================================================================


class TestHalt:
    def test_check_halt_triggers(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.peak_equity = 1000.0
        s.cash = 600.0  # 40% drawdown
        halted = s.check_halt()
        assert halted is True
        assert s.halted is True

    def test_check_halt_below_threshold(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.peak_equity = 1000.0
        s.cash = 700.0  # 30% drawdown < 40%
        halted = s.check_halt()
        assert halted is False
        assert s.halted is False

    def test_halted_blocks_entry(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.halted = True
        ok = s.enter(**_enter_args())
        assert ok is False


# =====================================================================
# Liquidation
# =====================================================================


class TestLiquidate:
    def test_liquidate_closes_position(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        result = s.liquidate({"ACME": 48.0}, "2026-07-20")
        assert result is not None
        assert s.position is None

    def test_liquidate_no_position(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.liquidate({"ACME": 50.0}, "2026-07-20") is None

    def test_liquidate_bypasses_halt(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.halted = True
        result = s.liquidate({"ACME": 48.0}, "2026-07-20")
        assert result is not None
        assert s.position is None
        # halt state is preserved after liquidation
        assert s.halted is True

    def test_liquidate_uses_mark_price(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        result = s.liquidate({"ACME": 60.0}, "2026-07-20")
        assert result is not None
        assert result > 0  # profit at 60 from entry 50

    def test_liquidate_uses_entry_price_if_no_mark(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        result = s.liquidate({}, "2026-07-20")
        # Falls back to entry price; net ~0 minus fees
        assert result is not None
        assert result < 0  # slight loss from fees


# =====================================================================
# Calibration methods
# =====================================================================


class TestCalibration:
    def _make_sleeve_with_trades(self):
        s = AchillesSleeve(initial_cash=5000.0)
        # Trade 1: win (+10%)
        s.enter(**_enter_args(symbol="AAA", shares=5.0, price=50.0,
                              today="2026-07-15",
                              surprise_pct=8.0, revenue_beat=True))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        # Trade 2: loss (-8%)
        s.enter(**_enter_args(symbol="BBB", shares=5.0, price=50.0,
                              today="2026-07-23",
                              surprise_pct=25.0, guidance_raised=True))
        s.exit(price=46.0, today="2026-07-28", reason="hard_stop")
        # Trade 3: win (+4%)
        s.enter(**_enter_args(symbol="CCC", shares=5.0, price=50.0,
                              today="2026-07-29",
                              surprise_pct=55.0, short_float_pct=25.0))
        s.exit(price=52.0, today="2026-08-05", reason="time_stop")
        return s

    def test_hit_rate(self):
        s = self._make_sleeve_with_trades()
        hr = s.hit_rate()
        assert hr == pytest.approx(2 / 3)

    def test_hit_rate_no_trades(self):
        s = AchillesSleeve()
        assert s.hit_rate() is None

    def test_graded_count(self):
        s = self._make_sleeve_with_trades()
        assert s.graded_count() == 3

    def test_graded_count_empty(self):
        s = AchillesSleeve()
        assert s.graded_count() == 0

    def test_avg_return(self):
        s = self._make_sleeve_with_trades()
        avg = s.avg_return()
        assert avg is not None
        # (10% + (-8%) + 4%) / 3 = 2%
        assert avg == pytest.approx(0.02)

    def test_avg_return_no_trades(self):
        s = AchillesSleeve()
        assert s.avg_return() is None

    def test_hit_rate_by_surprise_bucket(self):
        s = self._make_sleeve_with_trades()
        buckets = s.hit_rate_by_surprise_bucket()
        # 8% -> "3-10%" bucket (win), 25% -> "20-50%" (loss), 55% -> "50%+" (win)
        assert buckets["3-10%"] == pytest.approx(1.0)
        assert buckets["20-50%"] == pytest.approx(0.0)
        assert buckets["50%+"] == pytest.approx(1.0)
        assert buckets["10-20%"] is None  # no trades in this bucket

    def test_confirming_signal_stats(self):
        s = self._make_sleeve_with_trades()
        stats = s.confirming_signal_stats()
        assert "revenue_beat" in stats
        assert "guidance_raised" in stats
        assert "short_squeeze" in stats
        # revenue_beat: trade 1 had it (win), trades 2&3 did not
        assert stats["revenue_beat"]["with_n"] == 1
        assert stats["revenue_beat"]["with_hit_rate"] == pytest.approx(1.0)
        # guidance_raised: trade 2 had it (loss)
        assert stats["guidance_raised"]["with_n"] == 1
        assert stats["guidance_raised"]["with_hit_rate"] == pytest.approx(0.0)


# =====================================================================
# Equity / drawdown
# =====================================================================


class TestEquity:
    def test_equity_cash_only(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.equity() == 1000.0

    def test_equity_with_position(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        # cash ~= 1000 - 500.25 = 499.75; position = 10 * 55 = 550
        eq = s.equity({"ACME": 55.0})
        assert eq == pytest.approx(499.75 + 550.0)

    def test_equity_uses_entry_if_no_mark(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        eq = s.equity()
        # cash ~= 499.75; position = 10 * 50 = 500; total ~= 999.75
        assert eq == pytest.approx(999.75)

    def test_absolute_drawdown(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.peak_equity = 1000.0
        s.cash = 800.0
        assert s.absolute_drawdown() == pytest.approx(0.20)

    def test_update_peak(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.cash = 1200.0
        s.update_peak()
        assert s.peak_equity == 1200.0


# =====================================================================
# Persistence: to_dict / from_dict / save / load
# =====================================================================


class TestPersistence:
    def test_empty_sleeve_roundtrip(self):
        s = AchillesSleeve(initial_cash=1000.0)
        d = s.to_dict()
        s2 = AchillesSleeve.from_dict(d)
        assert s2.cash == 1000.0
        assert s2.position is None
        assert s2.halted is False
        assert s2.trade_results == []

    def test_roundtrip_with_position(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        d = s.to_dict()
        s2 = AchillesSleeve.from_dict(d)
        assert s2.position is not None
        assert s2.position.symbol == "ACME"
        assert s2.position.shares == 10.0
        assert s2.position.entry_price == 50.0
        assert s2.position.stop_price == s.position.stop_price
        assert s2.position.exit_date == s.position.exit_date

    def test_roundtrip_with_trade_results(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        d = s.to_dict()
        s2 = AchillesSleeve.from_dict(d)
        assert len(s2.trade_results) == 1
        assert s2.trade_results[0].symbol == "ACME"
        assert s2.trade_results[0].exit_reason == "time_stop"

    def test_roundtrip_preserves_cooldowns(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(price=40.0, today="2026-07-16", reason="hard_stop")
        d = s.to_dict()
        s2 = AchillesSleeve.from_dict(d)
        assert "ACME" in s2.cooldowns
        assert s2.in_cooldown("ACME", "2026-07-20") is True

    def test_roundtrip_preserves_halted(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.halted = True
        d = s.to_dict()
        s2 = AchillesSleeve.from_dict(d)
        assert s2.halted is True

    def test_roundtrip_preserves_settlements(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        d = s.to_dict()
        s2 = AchillesSleeve.from_dict(d)
        assert len(s2.pending_settlements) == 1

    def test_save_load_file(self, tmp_path):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        p = str(tmp_path / "achilles.json")
        s.save(p)
        s2 = AchillesSleeve.load(p)
        assert s2.cash == s.cash
        assert s2.position is not None
        assert s2.position.symbol == "ACME"

    def test_roundtrip_preserves_fields(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.realized_pnl = 42.5
        s.trades_count = 7
        s.gfv_count = 1
        s.contributed_cash = 2000.0
        d = s.to_dict()
        s2 = AchillesSleeve.from_dict(d)
        assert s2.realized_pnl == 42.5
        assert s2.trades_count == 7
        assert s2.gfv_count == 1
        assert s2.contributed_cash == 2000.0


# =====================================================================
# Settlement
# =====================================================================


class TestSettlement:
    def test_exit_creates_settlement(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        assert len(s.pending_settlements) == 1
        # settle_date is next business day after exit
        assert s.pending_settlements[0].settle_date == "2026-07-23"

    def test_unsettled_cash(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        unsettled = s.unsettled_cash("2026-07-22")
        assert unsettled > 0

    def test_settled_after_settlement_date(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        # After settle date, unsettled = 0
        unsettled = s.unsettled_cash("2026-07-23")
        assert unsettled == 0.0

    def test_process_settlements(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(price=55.0, today="2026-07-22", reason="time_stop")
        assert len(s.pending_settlements) == 1
        s.process_settlements("2026-07-23")
        assert len(s.pending_settlements) == 0


# =====================================================================
# Inject
# =====================================================================


class TestInject:
    def test_inject_adds_cash(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.inject(500.0)
        assert s.cash == 1500.0
        assert s.contributed_cash == 1500.0

    def test_inject_negative_raises(self):
        s = AchillesSleeve(initial_cash=1000.0)
        with pytest.raises(ValueError):
            s.inject(-100.0)
