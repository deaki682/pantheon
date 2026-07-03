"""Tests for the gated Nemesis live sleeve.

The exit rules here are FROZEN before any dollar moves — these tests pin
the constants and the exit-reason vocabulary so a mid-sample "tune" shows
up as a red test, not a silent rewrite of the experiment.
"""
import json

import pytest

from nemesis.sleeve import (
    CAPITAL_BASE,
    EXIT_REASONS,
    FEE_BPS,
    HALT_DRAWDOWN,
    HARD_STOP_PCT,
    HOLD_DAYS,
    MAX_POSITIONS,
    STOP_COOLDOWN_DAYS,
    THESIS_BREAK_REASONS,
    NemesisPosition,
    NemesisSleeve,
    Settlement,
    TradeResult,
    next_business_day,
)


def test_constants_frozen():
    assert CAPITAL_BASE == 2_000.0  # operator raised from 1k pre-launch, 2026-07-02
    assert MAX_POSITIONS == 5
    assert HOLD_DAYS == 150
    assert HARD_STOP_PCT == -0.40
    assert HALT_DRAWDOWN == 0.40
    assert FEE_BPS == 5
    assert STOP_COOLDOWN_DAYS == 90


def test_thesis_break_reasons_frozen():
    assert THESIS_BREAK_REASONS == frozenset({
        "garbage_materialized", "going_concern", "fraud",
        "delisting_risk", "guidance_collapse",
    })
    assert isinstance(THESIS_BREAK_REASONS, frozenset)


def test_exit_reasons_frozen():
    assert EXIT_REASONS == THESIS_BREAK_REASONS | {
        "time_stop", "hard_stop", "index_inclusion", "liquidation",
    }
    assert isinstance(EXIT_REASONS, frozenset)


def test_standalone_no_base_sleeve_inheritance():
    from shared.base_sleeve import BaseSleeve
    assert not issubclass(NemesisSleeve, BaseSleeve)


def _enter_args(**overrides):
    defaults = dict(
        symbol="SPNC", shares=10.0, price=50.0, today="2026-07-06",
        verdict="own", conviction=0.7, incentive_alignment=0.8,
        entry_window="in_window",
    )
    defaults.update(overrides)
    return defaults


class TestInit:
    def test_defaults(self):
        s = NemesisSleeve()
        assert s.name == "nemesis"
        assert s.cash == 2000.0
        assert s.positions == {}
        assert s.halted is False
        assert s.peak_equity == 2000.0
        assert s.realized_pnl == 0.0
        assert s.trades_count == 0
        assert s.trade_results == []
        assert s.cooldowns == {}
        assert s.gfv_count == 0

    def test_custom_cash(self):
        s = NemesisSleeve(initial_cash=5000.0)
        assert s.cash == 5000.0
        assert s.peak_equity == 5000.0
        assert s.contributed_cash == 5000.0


class TestEnter:
    def test_basic_enter(self):
        s = NemesisSleeve(initial_cash=1000.0)
        assert s.enter(**_enter_args()) is True
        pos = s.positions["SPNC"]
        assert pos.symbol == "SPNC"
        assert pos.shares == 10.0
        assert pos.entry_price == 50.0
        assert pos.entry_date == "2026-07-06"

    def test_dossier_tags_ride_on_position(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(verdict="watch", conviction=0.4,
                              incentive_alignment=0.55, entry_window="late"))
        pos = s.positions["SPNC"]
        assert pos.verdict == "watch"
        assert pos.conviction == 0.4
        assert pos.incentive_alignment == 0.55
        assert pos.entry_window == "late"

    def test_tags_are_keyword_required(self):
        # a TradeResult without its dossier tags is ungradeable, so enter()
        # refuses to open an untagged position at the signature level
        s = NemesisSleeve(initial_cash=1000.0)
        with pytest.raises(TypeError):
            s.enter("SPNC", 10.0, 50.0, "2026-07-06")

    def test_cash_deducted_with_fee(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        assert s.cash == pytest.approx(1000.0 - 500.25)

    def test_stop_price_is_minus_forty_pct(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0))
        assert s.positions["SPNC"].stop_price == pytest.approx(60.0)

    def test_exit_date_is_150_calendar_days(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        assert s.positions["SPNC"].exit_date == "2026-12-03"

    def test_exit_date_counts_calendar_not_trading_days(self):
        # 2026-01-01 + 150 calendar days = 2026-05-31 (a Sunday — calendar
        # holds land wherever they land; the runbook trades the next open)
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-01-01"))
        assert s.positions["SPNC"].exit_date == "2026-05-31"

    def test_cannot_enter_same_symbol_twice(self):
        s = NemesisSleeve(initial_cash=2000.0)
        s.enter(**_enter_args())
        assert s.enter(**_enter_args()) is False
        assert len(s.positions) == 1

    def test_basket_full_blocks_entry(self):
        s = NemesisSleeve(initial_cash=10_000.0)
        for i in range(MAX_POSITIONS):
            assert s.enter(**_enter_args(symbol=f"S{i}", shares=1.0, price=10.0)) is True
        assert len(s.positions) == MAX_POSITIONS
        assert s.enter(**_enter_args(symbol="OVERFLOW", shares=1.0, price=10.0)) is False

    def test_cannot_enter_when_halted(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.halted = True
        assert s.enter(**_enter_args()) is False
        assert s.positions == {}

    def test_cannot_enter_insufficient_cash(self):
        s = NemesisSleeve(initial_cash=100.0)
        assert s.enter(**_enter_args(shares=10.0, price=50.0)) is False
        assert s.positions == {}

    def test_fee_counts_against_cash(self):
        # exactly enough for shares*price but not the fee -> blocked
        s = NemesisSleeve(initial_cash=500.0)
        assert s.enter(**_enter_args(shares=10.0, price=50.0)) is False

    def test_cannot_enter_zero_shares(self):
        s = NemesisSleeve(initial_cash=1000.0)
        assert s.enter(**_enter_args(shares=0)) is False

    def test_cannot_enter_zero_price(self):
        s = NemesisSleeve(initial_cash=1000.0)
        assert s.enter(**_enter_args(price=0)) is False

    def test_trades_count_incremented(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        assert s.trades_count == 1

    def test_gfv_on_unsettled_overspend(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="AAA", shares=10.0, price=99.0))
        s.exit("AAA", 99.0, "2026-07-07", "index_inclusion")  # proceeds settle T+1
        assert s.gfv_count == 0
        assert s.enter(**_enter_args(symbol="BBB", shares=10.0, price=50.0,
                                     today="2026-07-07")) is True
        assert s.gfv_count == 1

    def test_no_gfv_when_settled(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=5.0, price=50.0))
        assert s.gfv_count == 0


class TestExit:
    def test_basic_exit_gain(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        realized = s.exit("SPNC", 60.0, "2026-12-03", "time_stop")
        assert realized is not None and realized > 0
        assert "SPNC" not in s.positions

    def test_exit_loss(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        realized = s.exit("SPNC", 30.0, "2026-08-01", "hard_stop")
        assert realized is not None and realized < 0

    def test_exit_symbol_not_held(self):
        s = NemesisSleeve(initial_cash=1000.0)
        assert s.exit("NOPE", 50.0, "2026-08-01", "time_stop") is None

    def test_exit_zero_price(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        assert s.exit("SPNC", 0, "2026-08-01", "time_stop") is None
        assert "SPNC" in s.positions

    def test_unknown_reason_raises(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        with pytest.raises(ValueError):
            s.exit("SPNC", 55.0, "2026-08-01", "felt_like_it")
        assert "SPNC" in s.positions  # rule violation changed nothing

    def test_unknown_reason_raises_even_when_not_held(self):
        # the vocabulary check is about the rulebook, not the book
        s = NemesisSleeve(initial_cash=1000.0)
        with pytest.raises(ValueError):
            s.exit("NOPE", 55.0, "2026-08-01", "vibes")

    @pytest.mark.parametrize("reason", sorted(EXIT_REASONS))
    def test_every_frozen_reason_is_accepted(self, reason):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        assert s.exit("SPNC", 55.0, "2026-08-01", reason) is not None

    def test_trade_result_carries_dossier_tags(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0, verdict="own",
                              conviction=0.9, incentive_alignment=0.75,
                              entry_window="in_window"))
        s.exit("SPNC", 55.0, "2026-12-03", "time_stop")
        assert len(s.trade_results) == 1
        tr = s.trade_results[0]
        assert tr.symbol == "SPNC"
        assert tr.exit_reason == "time_stop"
        assert tr.return_pct == pytest.approx(0.10)
        assert tr.verdict == "own"
        assert tr.conviction == 0.9
        assert tr.incentive_alignment == 0.75
        assert tr.entry_window == "in_window"

    def test_only_named_position_exits(self):
        s = NemesisSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="AAA"))
        s.enter(**_enter_args(symbol="BBB"))
        s.exit("AAA", 55.0, "2026-12-03", "time_stop")
        assert "AAA" not in s.positions
        assert "BBB" in s.positions


class TestCooldowns:
    def test_hard_stop_sets_90_day_cooldown(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        s.exit("SPNC", 25.0, "2026-07-16", "hard_stop")
        assert s.cooldowns["SPNC"] == "2026-10-14"  # +90 calendar days

    @pytest.mark.parametrize("reason", sorted(THESIS_BREAK_REASONS))
    def test_thesis_break_sets_cooldown(self, reason):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        s.exit("SPNC", 40.0, "2026-07-16", reason)
        assert s.cooldowns["SPNC"] == "2026-10-14"

    def test_time_stop_no_cooldown(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        s.exit("SPNC", 55.0, "2026-12-03", "time_stop")
        assert "SPNC" not in s.cooldowns

    def test_index_inclusion_no_cooldown(self):
        # the one early exit that is thesis COMPLETION, not failure —
        # re-entry stays legal (though inclusion usually ends the story)
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        s.exit("SPNC", 70.0, "2026-09-01", "index_inclusion")
        assert "SPNC" not in s.cooldowns

    def test_liquidation_no_cooldown(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        s.liquidate({"SPNC": 48.0}, "2026-08-01")
        assert "SPNC" not in s.cooldowns

    def test_cooldown_blocks_reentry(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        s.exit("SPNC", 25.0, "2026-07-16", "hard_stop")
        assert s.enter(**_enter_args(today="2026-10-13")) is False

    def test_cooldown_expiry_does_not_readmit_same_spinco(self):
        # The one-shot rule outranks cooldown expiry: a traded spinoff is
        # done forever, because the forced-seller window never recurs. The
        # in_cooldown clock itself expires (pinned below), but the symbol
        # stays blocked through trade_results. (Changed 2026-07-03 with the
        # one-shot rule — the old assertion that expiry readmits the name
        # was the re-buy loophole the review caught.)
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        s.exit("SPNC", 25.0, "2026-07-16", "hard_stop")
        assert s.in_cooldown("SPNC", "2026-10-14") is False
        assert s.enter(**_enter_args(today="2026-10-14")) is False

    def test_cooldown_different_symbol_ok(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(symbol="AAA", today="2026-07-06"))
        s.exit("AAA", 25.0, "2026-07-16", "fraud")
        assert s.enter(**_enter_args(symbol="BBB", today="2026-07-17")) is True

    def test_in_cooldown_case_insensitive(self):
        s = NemesisSleeve()
        s.cooldowns["SPNC"] = "2026-10-14"
        assert s.in_cooldown("spnc", "2026-08-01") is True
        assert s.in_cooldown("SPNC", "2026-10-14") is False


class TestDueExits:
    def test_hard_stop_detected(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0, today="2026-07-06"))
        due = dict(s.due_exits({"SPNC": 59.0}, "2026-08-01"))
        assert due["SPNC"] == "hard_stop"

    def test_time_stop_detected(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))  # exit_date 2026-12-03
        due = dict(s.due_exits({"SPNC": 55.0}, "2026-12-03"))
        assert due["SPNC"] == "time_stop"

    def test_hard_stop_takes_precedence_over_time_stop(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0, today="2026-07-06"))
        due = dict(s.due_exits({"SPNC": 55.0}, "2026-12-03"))
        assert due["SPNC"] == "hard_stop"

    def test_healthy_position_not_due(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0, today="2026-07-06"))
        assert s.due_exits({"SPNC": 80.0}, "2026-08-01") == []

    def test_no_quote_still_time_stops(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        due = dict(s.due_exits({}, "2026-12-03"))
        assert due["SPNC"] == "time_stop"

    def test_thesis_breaks_never_auto_detected(self):
        # even a name trading just above its stop with terrible price
        # action produces nothing — a thesis break requires a written case
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(price=100.0, shares=5.0, today="2026-07-06"))
        for sym, reason in s.due_exits({"SPNC": 60.5}, "2026-08-01"):
            assert reason in ("hard_stop", "time_stop")
        assert s.due_exits({"SPNC": 60.5}, "2026-08-01") == []


class TestHalt:
    def test_check_halt_triggers_at_40pct(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.peak_equity = 1000.0
        s.cash = 600.0
        assert s.check_halt() is True
        assert s.halted is True

    def test_check_halt_below_threshold(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.peak_equity = 1000.0
        s.cash = 700.0
        assert s.check_halt() is False
        assert s.halted is False

    def test_halt_blocks_entries(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.peak_equity = 1000.0
        s.cash = 600.0
        s.check_halt()
        assert s.enter(**_enter_args(shares=1.0, price=10.0)) is False


class TestLiquidate:
    def test_liquidate_closes_all(self):
        s = NemesisSleeve(initial_cash=3000.0)
        s.enter(**_enter_args(symbol="AAA", shares=10.0, price=50.0))
        s.enter(**_enter_args(symbol="BBB", shares=10.0, price=50.0))
        s.liquidate({"AAA": 48.0, "BBB": 52.0}, "2026-08-01")
        assert s.positions == {}

    def test_liquidate_records_reason(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        s.liquidate({"SPNC": 48.0}, "2026-08-01")
        assert s.trade_results[0].exit_reason == "liquidation"

    def test_liquidate_bypasses_halt(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.halted = True
        s.liquidate({"SPNC": 48.0}, "2026-08-01")
        assert s.positions == {}
        assert s.halted is True  # halt flag survives — only new risk stays blocked

    def test_liquidate_empty(self):
        s = NemesisSleeve(initial_cash=1000.0)
        assert s.liquidate({"SPNC": 50.0}, "2026-08-01") == 0.0

    def test_liquidate_uses_mark_price(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        assert s.liquidate({"SPNC": 60.0}, "2026-08-01") > 0


class TestSettlement:
    def test_exit_creates_t_plus_1_settlement(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit("SPNC", 55.0, "2026-12-03", "time_stop")  # Thursday
        assert s.pending_settlements[0].settle_date == "2026-12-04"

    def test_friday_exit_settles_monday(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit("SPNC", 55.0, "2026-12-04", "time_stop")  # Friday
        assert s.pending_settlements[0].settle_date == "2026-12-07"

    def test_settled_vs_unsettled_cash(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit("SPNC", 50.0, "2026-12-03", "time_stop")
        net = 500.0 - 0.25
        assert s.unsettled_cash("2026-12-03") == pytest.approx(net)
        assert s.settled_cash("2026-12-03") == pytest.approx(s.cash - net)
        assert s.unsettled_cash("2026-12-04") == 0.0

    def test_process_settlements_clears(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit("SPNC", 55.0, "2026-12-03", "time_stop")
        s.process_settlements("2026-12-04")
        assert s.pending_settlements == []

    def test_next_business_day_skips_weekend(self):
        assert next_business_day("2026-07-03") == "2026-07-06"  # Fri -> Mon


class TestEquityAndSizing:
    def test_equity_cash_only(self):
        assert NemesisSleeve(initial_cash=1000.0).equity() == 1000.0

    def test_equity_with_marks(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        assert s.equity({"SPNC": 55.0}) == pytest.approx(499.75 + 550.0)

    def test_equity_uses_entry_if_no_mark(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        assert s.equity() == pytest.approx(999.75)

    def test_target_dollars_is_equity_over_max_positions(self):
        s = NemesisSleeve(initial_cash=1000.0)
        assert s.target_dollars() == pytest.approx(200.0)

    def test_open_slots(self):
        s = NemesisSleeve(initial_cash=1000.0)
        assert s.open_slots() == 5
        s.enter(**_enter_args(shares=1.0, price=10.0))
        assert s.open_slots() == 4

    def test_holds(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        assert s.holds("spnc") is True
        assert s.holds("OTHER") is False

    def test_update_peak_and_drawdown(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.cash = 1200.0
        s.update_peak()
        assert s.peak_equity == 1200.0
        s.cash = 900.0
        assert s.absolute_drawdown() == pytest.approx(0.25)


class TestCalibration:
    def _make_sleeve_with_trades(self):
        s = NemesisSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="AAA", shares=5.0, price=50.0,
                              verdict="own", today="2026-07-06"))
        s.exit("AAA", 60.0, "2026-12-03", "time_stop")           # +20%
        s.enter(**_enter_args(symbol="BBB", shares=5.0, price=50.0,
                              verdict="own", today="2026-07-06"))
        s.exit("BBB", 30.0, "2026-08-01", "hard_stop")           # -40%
        s.enter(**_enter_args(symbol="CCC", shares=5.0, price=50.0,
                              verdict="watch", today="2026-07-06"))
        s.exit("CCC", 55.0, "2026-09-01", "index_inclusion")     # +10%
        return s

    def test_graded_count(self):
        assert self._make_sleeve_with_trades().graded_count() == 3

    def test_hit_rate(self):
        assert self._make_sleeve_with_trades().hit_rate() == pytest.approx(2 / 3)

    def test_avg_return(self):
        avg = self._make_sleeve_with_trades().avg_return()
        assert avg == pytest.approx((0.20 - 0.40 + 0.10) / 3)

    def test_empty_calibration(self):
        s = NemesisSleeve()
        assert s.graded_count() == 0
        assert s.hit_rate() is None
        assert s.avg_return() is None
        assert s.verdict_stats() == {}
        assert s.exit_reason_stats() == {}

    def test_verdict_stats(self):
        stats = self._make_sleeve_with_trades().verdict_stats()
        assert stats["own"]["n"] == 2
        assert stats["own"]["mean_return"] == pytest.approx(-0.10)
        assert stats["own"]["hit_rate"] == pytest.approx(0.5)
        assert stats["watch"]["n"] == 1
        assert stats["watch"]["mean_return"] == pytest.approx(0.10)
        assert stats["watch"]["hit_rate"] == pytest.approx(1.0)

    def test_exit_reason_stats(self):
        stats = self._make_sleeve_with_trades().exit_reason_stats()
        assert stats["time_stop"] == {"n": 1, "mean_return": pytest.approx(0.20)}
        assert stats["hard_stop"] == {"n": 1, "mean_return": pytest.approx(-0.40)}
        assert stats["index_inclusion"] == {"n": 1, "mean_return": pytest.approx(0.10)}


class TestInject:
    def test_inject_adds_cash(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.inject(500.0)
        assert s.cash == 1500.0
        assert s.contributed_cash == 1500.0

    def test_inject_negative_raises(self):
        with pytest.raises(ValueError):
            NemesisSleeve(initial_cash=1000.0).inject(-100.0)


class TestPersistence:
    def test_empty_sleeve_roundtrip(self):
        s2 = NemesisSleeve.from_dict(NemesisSleeve(initial_cash=1000.0).to_dict())
        assert s2.cash == 1000.0
        assert s2.positions == {}
        assert s2.name == "nemesis"

    def test_roundtrip_with_positions_and_tags(self):
        s = NemesisSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="AAA", shares=10.0, price=50.0, verdict="own"))
        s.enter(**_enter_args(symbol="BBB", shares=5.0, price=40.0, verdict="watch",
                              conviction=0.3, entry_window="late"))
        s2 = NemesisSleeve.from_dict(s.to_dict())
        assert set(s2.positions) == {"AAA", "BBB"}
        assert s2.positions["AAA"].verdict == "own"
        assert s2.positions["BBB"].conviction == 0.3
        assert s2.positions["BBB"].entry_window == "late"
        assert s2.positions["BBB"].exit_date == s.positions["BBB"].exit_date

    def test_roundtrip_with_trade_results(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        s.exit("SPNC", 55.0, "2026-12-03", "time_stop")
        s2 = NemesisSleeve.from_dict(s.to_dict())
        assert len(s2.trade_results) == 1
        assert s2.trade_results[0].symbol == "SPNC"
        assert s2.trade_results[0].verdict == "own"
        assert s2.trade_results[0].exit_reason == "time_stop"

    def test_roundtrip_preserves_cooldowns(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(today="2026-07-06"))
        s.exit("SPNC", 25.0, "2026-07-16", "hard_stop")
        s2 = NemesisSleeve.from_dict(s.to_dict())
        assert s2.in_cooldown("SPNC", "2026-08-01") is True

    def test_roundtrip_preserves_scalars(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.realized_pnl = 42.5
        s.trades_count = 7
        s.gfv_count = 1
        s.contributed_cash = 2000.0
        s.halted = True
        s2 = NemesisSleeve.from_dict(s.to_dict())
        assert s2.realized_pnl == 42.5
        assert s2.trades_count == 7
        assert s2.gfv_count == 1
        assert s2.contributed_cash == 2000.0
        assert s2.halted is True

    def test_tolerates_missing_optional_fields(self):
        # a position written before a tag existed loads with the tag None
        data = {
            "cash": 500.0,
            "positions": {
                "OLD": {
                    "symbol": "OLD", "shares": 10.0, "entry_price": 50.0,
                    "entry_date": "2026-07-06", "stop_price": 30.0,
                    "exit_date": "2026-12-03",
                },
            },
        }
        s = NemesisSleeve.from_dict(data)
        pos = s.positions["OLD"]
        assert pos.shares == 10.0
        assert pos.verdict is None
        assert pos.conviction is None
        assert pos.incentive_alignment is None
        assert pos.entry_window is None

    def test_save_load_file(self, tmp_path):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args(shares=10.0, price=50.0))
        p = str(tmp_path / "nemesis_sleeve.json")
        s.save(p)
        s2 = NemesisSleeve.load(p)
        assert "SPNC" in s2.positions
        assert s2.positions["SPNC"].verdict == "own"

    def test_save_is_atomic_no_tmp_left_behind(self, tmp_path):
        s = NemesisSleeve(initial_cash=1000.0)
        p = str(tmp_path / "nemesis_sleeve.json")
        s.save(p)
        assert not (tmp_path / "nemesis_sleeve.json.tmp").exists()


class TestGuardsCompat:
    def test_positions_shape_matches_guards_contract(self):
        # shared.guards aggregate_sleeve_shares reads to_dict()["positions"]
        # as a dict keyed by symbol with a "shares" field per entry
        s = NemesisSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="AAA", shares=10.0, price=50.0))
        d = s.to_dict()
        assert isinstance(d["positions"], dict)
        assert "AAA" in d["positions"]
        assert d["positions"]["AAA"]["shares"] == 10.0
        assert d["positions"]["AAA"]["symbol"] == "AAA"

    def test_aggregate_sleeve_shares_reads_saved_sleeve(self, tmp_path):
        from shared.guards import aggregate_sleeve_shares
        s = NemesisSleeve(initial_cash=2000.0)
        s.enter(**_enter_args(symbol="AAA", shares=10.0, price=50.0))
        s.enter(**_enter_args(symbol="BBB", shares=3.0, price=40.0))
        p = str(tmp_path / "nemesis_sleeve.json")
        s.save(p)
        combined = aggregate_sleeve_shares({"nemesis": p})
        assert combined["AAA"]["nemesis"] == 10.0
        assert combined["BBB"]["nemesis"] == 3.0

    def test_saved_file_is_valid_json(self, tmp_path):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter(**_enter_args())
        p = str(tmp_path / "nemesis_sleeve.json")
        s.save(p)
        with open(p) as f:
            data = json.load(f)
        assert data["name"] == "nemesis"


# ------- one-shot rule + cancel_entry (2026-07-03 review fixes) -------

class TestOneShotRule:
    def test_no_reentry_after_time_stop(self):
        # time_stop sets no cooldown, but a completed one-shot is done
        # forever — without this, a stale in_window state re-buys in a loop.
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter("SPIN", 10.0, 20.0, "2026-01-05", verdict="own",
                conviction=0.6, incentive_alignment=0.5, entry_window="in_window")
        s.exit("SPIN", 22.0, "2026-06-04", "time_stop")
        assert s.enter("SPIN", 10.0, 20.0, "2026-06-05", verdict="own",
                       conviction=0.6, incentive_alignment=0.5,
                       entry_window="in_window") is False

    def test_no_reentry_after_index_inclusion(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter("SPIN", 10.0, 20.0, "2026-01-05", verdict="own",
                conviction=0.6, incentive_alignment=0.5, entry_window="in_window")
        s.exit("SPIN", 25.0, "2026-03-01", "index_inclusion")
        assert s.enter("SPIN", 5.0, 25.0, "2026-03-02", verdict="own",
                       conviction=0.6, incentive_alignment=0.5,
                       entry_window="in_window") is False

    def test_one_shot_survives_persistence_roundtrip(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter("SPIN", 10.0, 20.0, "2026-01-05", verdict="own",
                conviction=0.6, incentive_alignment=0.5, entry_window="in_window")
        s.exit("SPIN", 22.0, "2026-06-04", "time_stop")
        s2 = NemesisSleeve.from_dict(s.to_dict())
        assert s2.enter("SPIN", 10.0, 20.0, "2026-06-05", verdict="own",
                        conviction=0.6, incentive_alignment=0.5,
                        entry_window="in_window") is False

    def test_other_symbols_unaffected(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter("SPIN", 10.0, 20.0, "2026-01-05", verdict="own",
                conviction=0.6, incentive_alignment=0.5, entry_window="in_window")
        s.exit("SPIN", 22.0, "2026-06-04", "time_stop")
        assert s.enter("OTHR", 10.0, 20.0, "2026-06-05", verdict="own",
                       conviction=0.6, incentive_alignment=0.5,
                       entry_window="in_window") is True


class TestCancelEntry:
    def test_cancel_restores_cash_exactly(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter("SPIN", 10.0, 20.0, "2026-07-03", verdict="own",
                conviction=0.6, incentive_alignment=0.5, entry_window="in_window")
        assert s.cancel_entry("SPIN", "2026-07-03") is True
        assert s.cash == pytest.approx(1000.0)
        assert "SPIN" not in s.positions
        assert s.trades_count == 0

    def test_cancel_does_not_consume_one_shot(self):
        # A cancelled entry never happened — re-entering must be allowed.
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter("SPIN", 10.0, 20.0, "2026-07-03", verdict="own",
                conviction=0.6, incentive_alignment=0.5, entry_window="in_window")
        s.cancel_entry("SPIN", "2026-07-03")
        assert s.enter("SPIN", 10.0, 20.0, "2026-07-03", verdict="own",
                       conviction=0.6, incentive_alignment=0.5,
                       entry_window="in_window") is True

    def test_cancel_rejected_on_later_day(self):
        # Same-day only: cancel is order-failure repair, not an exit path.
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter("SPIN", 10.0, 20.0, "2026-07-03", verdict="own",
                conviction=0.6, incentive_alignment=0.5, entry_window="in_window")
        assert s.cancel_entry("SPIN", "2026-07-06") is False
        assert "SPIN" in s.positions

    def test_cancel_unknown_symbol(self):
        s = NemesisSleeve(initial_cash=1000.0)
        assert s.cancel_entry("NOPE", "2026-07-03") is False

    def test_cancel_leaves_no_trade_result(self):
        s = NemesisSleeve(initial_cash=1000.0)
        s.enter("SPIN", 10.0, 20.0, "2026-07-03", verdict="own",
                conviction=0.6, incentive_alignment=0.5, entry_window="in_window")
        s.cancel_entry("SPIN", "2026-07-03")
        assert s.trade_results == []
        assert s.cooldowns == {}
