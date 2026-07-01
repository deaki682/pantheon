import pytest

from achilles.sleeve import (
    CAPITAL_BASE,
    FEE_BPS,
    HALT_DRAWDOWN,
    HARD_STOP_PCT,
    HOLD_DAYS,
    MAX_POSITIONS,
    STOP_COOLDOWN_WEEKS,
    AchillesPosition,
    AchillesSleeve,
    Settlement,
    TradeResult,
    trading_days_ahead,
)


def test_constants():
    assert HARD_STOP_PCT == -0.08
    assert HALT_DRAWDOWN == 0.40
    assert HOLD_DAYS == 5
    assert FEE_BPS == 5
    assert CAPITAL_BASE == 1_000.0
    assert STOP_COOLDOWN_WEEKS == 4
    assert MAX_POSITIONS == 12


class TestTradingDaysAhead:
    def test_weekday_to_weekday(self):
        assert trading_days_ahead("2026-07-01", 5) == "2026-07-08"

    def test_friday_skips_weekend(self):
        assert trading_days_ahead("2026-07-03", 1) == "2026-07-06"

    def test_friday_plus_five(self):
        assert trading_days_ahead("2026-07-03", 5) == "2026-07-10"

    def test_zero_days(self):
        assert trading_days_ahead("2026-07-01", 0) == "2026-07-01"


def test_standalone_no_base_sleeve_inheritance():
    from shared.base_sleeve import BaseSleeve
    assert not issubclass(AchillesSleeve, BaseSleeve)


class TestInit:
    def test_defaults(self):
        s = AchillesSleeve()
        assert s.cash == 1000.0
        assert s.positions == {}
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


def _enter_args(**overrides):
    defaults = dict(
        symbol="ACME", shares=10.0, price=50.0, today="2026-07-15",
        score=0.85, surprise_pct=15.0,
    )
    defaults.update(overrides)
    return defaults


class TestEnter:
    def test_basic_enter(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.enter(**_enter_args()) is True
        pos = s.positions["ACME"]
        assert pos.symbol == "ACME"
        assert pos.shares == 10.0
        assert pos.entry_price == 50.0
        assert pos.entry_date == "2026-07-15"

    def test_cash_deducted_with_fee(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        assert s.cash == pytest.approx(1000.0 - 500.25)

    def test_stop_price_set(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0))
        assert s.positions["ACME"].stop_price == pytest.approx(92.0)

    def test_exit_date_five_trading_days(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-15"))
        assert s.positions["ACME"].exit_date == "2026-07-22"

    def test_can_hold_multiple_names(self):
        s = AchillesSleeve(initial_cash=2000.0)
        assert s.enter(**_enter_args(symbol="ACME")) is True
        assert s.enter(**_enter_args(symbol="OTHER")) is True
        assert set(s.positions) == {"ACME", "OTHER"}

    def test_cannot_enter_same_symbol_twice(self):
        s = AchillesSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="ACME"))
        assert s.enter(**_enter_args(symbol="ACME")) is False
        assert len(s.positions) == 1

    def test_basket_full_blocks_entry(self):
        s = AchillesSleeve(initial_cash=100_000.0)
        for i in range(MAX_POSITIONS):
            assert s.enter(**_enter_args(symbol=f"S{i}", shares=1.0, price=10.0)) is True
        assert len(s.positions) == MAX_POSITIONS
        assert s.enter(**_enter_args(symbol="OVERFLOW", shares=1.0, price=10.0)) is False

    def test_cannot_enter_when_halted(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.halted = True
        assert s.enter(**_enter_args()) is False
        assert s.positions == {}

    def test_cannot_enter_insufficient_cash(self):
        s = AchillesSleeve(initial_cash=100.0)
        assert s.enter(**_enter_args(shares=10.0, price=50.0)) is False
        assert s.positions == {}

    def test_cannot_enter_zero_shares(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.enter(**_enter_args(shares=0)) is False

    def test_cannot_enter_zero_price(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.enter(**_enter_args(price=0)) is False

    def test_trades_count_incremented(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        assert s.trades_count == 1

    def test_optional_confirming_signals(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(revenue_beat=True, guidance_raised=True,
                              short_float_pct=25.0, reaction_pct=0.06))
        pos = s.positions["ACME"]
        assert pos.revenue_beat is True
        assert pos.guidance_raised is True
        assert pos.short_float_pct == 25.0
        assert pos.reaction_pct == 0.06


class TestExit:
    def test_basic_exit(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        realized = s.exit(symbol="ACME", price=55.0, today="2026-07-22", reason="time_stop")
        assert realized is not None and realized > 0
        assert "ACME" not in s.positions

    def test_exit_loss(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        realized = s.exit(symbol="ACME", price=45.0, today="2026-07-22", reason="hard_stop")
        assert realized is not None and realized < 0

    def test_exit_symbol_not_held(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.exit(symbol="NOPE", price=50.0, today="2026-07-22", reason="time_stop") is None

    def test_exit_zero_price(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        assert s.exit(symbol="ACME", price=0, today="2026-07-22", reason="time_stop") is None
        assert "ACME" in s.positions

    def test_trade_result_recorded(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(symbol="ACME", price=55.0, today="2026-07-22", reason="time_stop")
        assert len(s.trade_results) == 1
        tr = s.trade_results[0]
        assert tr.symbol == "ACME"
        assert tr.exit_reason == "time_stop"
        assert tr.return_pct == pytest.approx(0.10)

    def test_only_named_position_exits(self):
        s = AchillesSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="AAA"))
        s.enter(**_enter_args(symbol="BBB"))
        s.exit(symbol="AAA", price=55.0, today="2026-07-22", reason="time_stop")
        assert "AAA" not in s.positions
        assert "BBB" in s.positions


class TestStopChecks:
    def test_check_stop_triggers(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0))
        assert s.check_stop("ACME", 92.0) is True
        assert s.check_stop("ACME", 91.0) is True

    def test_check_stop_above_stop(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0))
        assert s.check_stop("ACME", 93.0) is False

    def test_check_stop_not_held(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.check_stop("ACME", 50.0) is False

    def test_should_time_stop(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-15"))  # exit_date 2026-07-22
        assert s.should_time_stop("ACME", "2026-07-22") is True
        assert s.should_time_stop("ACME", "2026-07-23") is True
        assert s.should_time_stop("ACME", "2026-07-21") is False

    def test_should_time_stop_not_held(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.should_time_stop("ACME", "2026-07-22") is False

    def test_due_exits(self):
        s = AchillesSleeve(initial_cash=3000.0)
        s.enter(**_enter_args(symbol="STOP", price=100.0, shares=5.0, today="2026-07-15"))
        s.enter(**_enter_args(symbol="TIME", price=50.0, shares=5.0, today="2026-07-15"))
        s.enter(**_enter_args(symbol="HOLD", price=20.0, shares=5.0, today="2026-07-15"))
        # STOP below its 92 stop; TIME past exit date; HOLD fine and not yet due
        due = dict(s.due_exits({"STOP": 80.0, "TIME": 55.0, "HOLD": 21.0}, "2026-07-22"))
        assert due["STOP"] == "hard_stop"
        assert due["TIME"] == "time_stop"
        assert "HOLD" in due  # 2026-07-22 is its exit date too -> time_stop
        assert due["HOLD"] == "time_stop"


class TestCooldowns:
    def test_hard_stop_adds_cooldown(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(symbol="ACME", price=40.0, today="2026-07-16", reason="hard_stop")
        assert s.cooldowns["ACME"] == "2026-08-13"

    def test_cooldown_blocks_entry(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(symbol="ACME", price=40.0, today="2026-07-16", reason="hard_stop")
        assert s.enter(**_enter_args(symbol="ACME", today="2026-07-20")) is False

    def test_cooldown_allows_entry_after_expiry(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(symbol="ACME", price=40.0, today="2026-07-16", reason="hard_stop")
        assert s.enter(**_enter_args(symbol="ACME", today="2026-08-14")) is True

    def test_cooldown_different_symbol_ok(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(symbol="ACME", price=40.0, today="2026-07-16", reason="hard_stop")
        assert s.enter(**_enter_args(symbol="OTHER", today="2026-07-17")) is True

    def test_time_stop_no_cooldown(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(symbol="ACME", price=55.0, today="2026-07-22", reason="time_stop")
        assert "ACME" not in s.cooldowns

    def test_in_cooldown_case_insensitive(self):
        s = AchillesSleeve()
        s.cooldowns["ACME"] = "2026-08-13"
        assert s.in_cooldown("acme", "2026-07-20") is True
        assert s.in_cooldown("ACME", "2026-08-13") is False


class TestHalt:
    def test_check_halt_triggers(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.peak_equity = 1000.0
        s.cash = 600.0
        assert s.check_halt() is True
        assert s.halted is True

    def test_check_halt_below_threshold(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.peak_equity = 1000.0
        s.cash = 700.0
        assert s.check_halt() is False


class TestLiquidate:
    def test_liquidate_closes_all(self):
        s = AchillesSleeve(initial_cash=3000.0)
        s.enter(**_enter_args(symbol="AAA", shares=10.0, price=50.0))
        s.enter(**_enter_args(symbol="BBB", shares=10.0, price=50.0))
        total = s.liquidate({"AAA": 48.0, "BBB": 52.0}, "2026-07-20")
        assert s.positions == {}
        assert total is not None

    def test_liquidate_no_position(self):
        s = AchillesSleeve(initial_cash=1000.0)
        assert s.liquidate({"ACME": 50.0}, "2026-07-20") == 0.0

    def test_liquidate_bypasses_halt(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.halted = True
        s.liquidate({"ACME": 48.0}, "2026-07-20")
        assert s.positions == {}
        assert s.halted is True

    def test_liquidate_uses_mark_price(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        assert s.liquidate({"ACME": 60.0}, "2026-07-20") > 0


class TestCalibration:
    def _make_sleeve_with_trades(self):
        s = AchillesSleeve(initial_cash=5000.0)
        s.enter(**_enter_args(symbol="AAA", shares=5.0, price=50.0, today="2026-07-15",
                              surprise_pct=8.0, revenue_beat=True))
        s.exit(symbol="AAA", price=55.0, today="2026-07-22", reason="time_stop")
        s.enter(**_enter_args(symbol="BBB", shares=5.0, price=50.0, today="2026-07-23",
                              surprise_pct=25.0, guidance_raised=True))
        s.exit(symbol="BBB", price=46.0, today="2026-07-28", reason="hard_stop")
        s.enter(**_enter_args(symbol="CCC", shares=5.0, price=50.0, today="2026-07-29",
                              surprise_pct=55.0, short_float_pct=25.0))
        s.exit(symbol="CCC", price=52.0, today="2026-08-05", reason="time_stop")
        return s

    def test_hit_rate(self):
        assert self._make_sleeve_with_trades().hit_rate() == pytest.approx(2 / 3)

    def test_graded_count(self):
        assert self._make_sleeve_with_trades().graded_count() == 3

    def test_avg_return(self):
        assert self._make_sleeve_with_trades().avg_return() == pytest.approx(0.02)

    def test_hit_rate_by_surprise_bucket(self):
        buckets = self._make_sleeve_with_trades().hit_rate_by_surprise_bucket()
        assert buckets["3-10%"] == pytest.approx(1.0)
        assert buckets["20-50%"] == pytest.approx(0.0)
        assert buckets["50%+"] == pytest.approx(1.0)
        assert buckets["10-20%"] is None

    def test_confirming_signal_stats(self):
        stats = self._make_sleeve_with_trades().confirming_signal_stats()
        assert stats["revenue_beat"]["with_n"] == 1
        assert stats["revenue_beat"]["with_hit_rate"] == pytest.approx(1.0)
        assert stats["guidance_raised"]["with_hit_rate"] == pytest.approx(0.0)


class TestEquity:
    def test_equity_cash_only(self):
        assert AchillesSleeve(initial_cash=1000.0).equity() == 1000.0

    def test_equity_with_positions(self):
        s = AchillesSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="AAA", shares=10.0, price=50.0))
        s.enter(**_enter_args(symbol="BBB", shares=10.0, price=50.0))
        # each cost 500.25; cash = 2000 - 1000.50 = 999.50; marks 55 & 60 -> 550 + 600
        eq = s.equity({"AAA": 55.0, "BBB": 60.0})
        assert eq == pytest.approx(999.50 + 550.0 + 600.0)

    def test_equity_uses_entry_if_no_mark(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        assert s.equity() == pytest.approx(999.75)


class TestPersistence:
    def test_empty_sleeve_roundtrip(self):
        s2 = AchillesSleeve.from_dict(AchillesSleeve(initial_cash=1000.0).to_dict())
        assert s2.cash == 1000.0
        assert s2.positions == {}

    def test_roundtrip_with_positions(self):
        s = AchillesSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="AAA", shares=10.0, price=50.0))
        s.enter(**_enter_args(symbol="BBB", shares=5.0, price=40.0))
        s2 = AchillesSleeve.from_dict(s.to_dict())
        assert set(s2.positions) == {"AAA", "BBB"}
        assert s2.positions["AAA"].shares == 10.0
        assert s2.positions["BBB"].entry_price == 40.0

    def test_legacy_single_position_migrates(self):
        # an old single-position sleeve on disk should load into the basket
        legacy = {
            "cash": 500.0,
            "position": {
                "symbol": "OLD", "shares": 10.0, "entry_price": 50.0,
                "entry_date": "2026-07-15", "stop_price": 46.0,
                "exit_date": "2026-07-22", "score": 0.8, "surprise_pct": 12.0,
            },
        }
        s = AchillesSleeve.from_dict(legacy)
        assert "OLD" in s.positions
        assert s.positions["OLD"].shares == 10.0

    def test_roundtrip_with_trade_results(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(symbol="ACME", price=55.0, today="2026-07-22", reason="time_stop")
        s2 = AchillesSleeve.from_dict(s.to_dict())
        assert len(s2.trade_results) == 1
        assert s2.trade_results[0].symbol == "ACME"

    def test_roundtrip_preserves_cooldowns(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="ACME", today="2026-07-15"))
        s.exit(symbol="ACME", price=40.0, today="2026-07-16", reason="hard_stop")
        s2 = AchillesSleeve.from_dict(s.to_dict())
        assert s2.in_cooldown("ACME", "2026-07-20") is True

    def test_save_load_file(self, tmp_path):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        p = str(tmp_path / "achilles.json")
        s.save(p)
        s2 = AchillesSleeve.load(p)
        assert "ACME" in s2.positions

    def test_roundtrip_preserves_fields(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.realized_pnl = 42.5
        s.trades_count = 7
        s.gfv_count = 1
        s.contributed_cash = 2000.0
        s2 = AchillesSleeve.from_dict(s.to_dict())
        assert s2.realized_pnl == 42.5
        assert s2.trades_count == 7
        assert s2.gfv_count == 1
        assert s2.contributed_cash == 2000.0


class TestSettlement:
    def test_exit_creates_settlement(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(symbol="ACME", price=55.0, today="2026-07-22", reason="time_stop")
        assert s.pending_settlements[0].settle_date == "2026-07-23"

    def test_process_settlements(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit(symbol="ACME", price=55.0, today="2026-07-22", reason="time_stop")
        s.process_settlements("2026-07-23")
        assert len(s.pending_settlements) == 0


class TestInject:
    def test_inject_adds_cash(self):
        s = AchillesSleeve(initial_cash=1000.0)
        s.inject(500.0)
        assert s.cash == 1500.0
        assert s.contributed_cash == 1500.0

    def test_inject_negative_raises(self):
        with pytest.raises(ValueError):
            AchillesSleeve(initial_cash=1000.0).inject(-100.0)
