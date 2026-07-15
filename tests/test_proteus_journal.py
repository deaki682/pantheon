import pytest

from proteus.journal import (
    CAPITAL_BASE, JournalError, PaperBook, append_decision, checkpoint_stats,
    load_journal, validate_decision, trade_drought_stats,
    DROUGHT_SESSIONS, DROUGHT_MIN_DAYS,
)

THESIS = ("A genuine, articulated thesis about why this position has edge, "
          "grounded in specific documents, base rates, and a mechanism that "
          "explains who is on the other side of the trade and why they are "
          "constrained or wrong at this moment in time.")
PRED = ("The stock closes above $25 within 30 days as the Q2 filing confirms "
        "the segment margin inflection.")


def _enter(**over):
    rec = {
        "date": "2026-07-06", "action": "enter", "symbol": "TEST",
        "side": "long", "dollars": 1000.0, "price": 20.0, "spy_price": 745.0,
        "horizon_days": 30, "confidence": 0.6, "edge_class": "special_situation",
        "thesis": THESIS, "falsifiable_prediction": PRED,
        "exit_plan": "Exit at $25 target or after the Q2 filing lands.",
        "kill_condition": "Exit immediately on going-concern language.",
    }
    rec.update(over)
    return rec


def test_valid_enter_passes():
    validate_decision(_enter())


def test_stub_thesis_rejected():
    with pytest.raises(JournalError):
        validate_decision(_enter(thesis="short stub"))


def test_bad_edge_class_rejected():
    with pytest.raises(JournalError):
        validate_decision(_enter(edge_class="vibes"))


def test_bad_action_rejected():
    with pytest.raises(JournalError):
        validate_decision({"action": "amend", "date": "2026-07-06"})


def test_exit_requires_reason():
    with pytest.raises(JournalError):
        validate_decision({"date": "2026-07-07", "action": "exit", "symbol": "TEST",
                           "price": 22.0, "spy_price": 750.0, "exit_reason": "felt like it"})


def test_journal_roundtrip(tmp_path):
    p = str(tmp_path / "j.jsonl")
    append_decision(_enter(), path=p)
    rows = load_journal(p)
    assert len(rows) == 1 and rows[0]["symbol"] == "TEST"


def test_long_lifecycle_and_fees():
    b = PaperBook()
    b.enter(symbol="ABC", side="long", dollars=1000, price=10.0, date="2026-07-06",
            spy_price=700.0, horizon_days=30, confidence=0.7, edge_class="value")
    assert b.cash < CAPITAL_BASE - 1000  # entry fee taken
    t = b.exit(symbol="ABC", price=12.0, date="2026-07-20", spy_price=707.0,
               exit_reason="exit_plan")
    assert t.net_return == pytest.approx(0.20, abs=0.005)  # ~+20% less fees
    assert t.spy_return == pytest.approx(0.01)
    assert t.excess == pytest.approx(t.net_return - 0.01)
    assert b.positions == {}


def test_short_lifecycle_borrow_and_mirror():
    b = PaperBook()
    b.enter(symbol="XYZ", side="short", dollars=1000, price=50.0, date="2026-07-06",
            spy_price=700.0, horizon_days=30, confidence=0.5, edge_class="short_thesis")
    t = b.exit(symbol="XYZ", price=40.0, date="2026-08-05", spy_price=714.0,
               exit_reason="exit_plan")
    assert t.net_return == pytest.approx(0.20, abs=0.01)  # +20% less fees+borrow
    # short mirror is -SPY: SPY +2% => mirror -2% => excess ~ +22%
    assert t.excess == pytest.approx(t.net_return + 0.02, abs=0.001)


def test_no_leverage():
    b = PaperBook()
    with pytest.raises(JournalError):
        b.enter(symbol="BIG", side="long", dollars=CAPITAL_BASE + 1, price=10.0,
                date="2026-07-06", spy_price=700.0, horizon_days=10,
                confidence=0.5, edge_class="value")


def test_short_gross_cap():
    b = PaperBook()
    with pytest.raises(JournalError):
        b.enter(symbol="SH", side="short", dollars=0.51 * CAPITAL_BASE, price=10.0,
                date="2026-07-06", spy_price=700.0, horizon_days=10,
                confidence=0.5, edge_class="short_thesis")


def test_one_position_per_symbol():
    b = PaperBook()
    b.enter(symbol="DUP", side="long", dollars=500, price=10.0, date="2026-07-06",
            spy_price=700.0, horizon_days=10, confidence=0.5, edge_class="value")
    with pytest.raises(JournalError):
        b.enter(symbol="DUP", side="long", dollars=500, price=10.0, date="2026-07-06",
                spy_price=700.0, horizon_days=10, confidence=0.5, edge_class="value")


def test_horizon_expiry_flagged():
    b = PaperBook()
    b.enter(symbol="OLD", side="long", dollars=500, price=10.0, date="2026-07-06",
            spy_price=700.0, horizon_days=5, confidence=0.5, edge_class="value")
    assert b.horizon_expired("2026-07-11") == ["OLD"]
    assert b.horizon_expired("2026-07-08") == []


def test_book_save_load_roundtrip(tmp_path):
    p = str(tmp_path / "book.json")
    b = PaperBook()
    b.enter(symbol="RT", side="long", dollars=500, price=10.0, date="2026-07-06",
            spy_price=700.0, horizon_days=10, confidence=0.5, edge_class="value")
    b.save(p)
    b2 = PaperBook.load(p)
    assert "RT" in b2.positions and b2.cash == pytest.approx(b.cash)


def test_checkpoint_stats_calibration():
    class T:
        def __init__(self, excess, conf):
            self.excess, self.confidence = excess, conf
    closed = [T(0.05, 0.9), T(0.04, 0.8), T(0.01, 0.5), T(-0.02, 0.3),
              T(-0.03, 0.2), T(0.02, 0.7)]
    s = checkpoint_stats(closed)
    assert s["n"] == 6
    assert s["calibration_ok"] is True


def test_green_day_stats():
    from proteus.journal import green_day_stats
    curve = [
        {"date": "d1", "equity": 10000, "spy": 700},
        {"date": "d2", "equity": 10050, "spy": 705},  # green, spy green
        {"date": "d3", "equity": 10040, "spy": 710},  # red, spy green
        {"date": "d4", "equity": 10100, "spy": 708},  # green, spy red
        {"date": "d5", "equity": 10150, "spy": 712},  # green, spy green
    ]
    s = green_day_stats(curve)
    assert s["days"] == 4
    assert s["green_rate"] == 0.75
    assert s["spy_green_rate"] == 0.75
    assert s["current_streak"] == 2
    assert s["best_streak"] == 2


def test_green_day_stats_empty():
    from proteus.journal import green_day_stats
    assert green_day_stats([])["green_rate"] is None


# ---- typed kill conditions (2026-07-04, self-review finding #1) ----

def test_kill_condition_type_optional_but_validated():
    validate_decision(_enter())  # untyped still passes (schema-optional)
    with pytest.raises(JournalError):
        validate_decision(_enter(kill_condition_type="vibes"))


def test_kill_condition_numeric_types_require_value():
    validate_decision(_enter(kill_condition_type="drawdown_pct",
                             kill_condition_value=-0.15))
    validate_decision(_enter(kill_condition_type="price_level",
                             kill_condition_value=17.5))
    for kc in ("drawdown_pct", "price_level"):
        with pytest.raises(JournalError):
            validate_decision(_enter(kill_condition_type=kc))
        with pytest.raises(JournalError):
            validate_decision(_enter(kill_condition_type=kc,
                                     kill_condition_value="soon"))
        with pytest.raises(JournalError):
            validate_decision(_enter(kill_condition_type=kc,
                                     kill_condition_value=True))


def test_kill_condition_thesis_date_requires_iso_date():
    validate_decision(_enter(kill_condition_type="thesis_date",
                             kill_condition_value="2026-08-15"))
    with pytest.raises(JournalError):
        validate_decision(_enter(kill_condition_type="thesis_date",
                                 kill_condition_value="mid-August"))
    with pytest.raises(JournalError):
        validate_decision(_enter(kill_condition_type="thesis_date"))


def test_kill_condition_filing_event_needs_no_value():
    validate_decision(_enter(kill_condition_type="filing_event"))


def test_kill_condition_other_requires_written_reason():
    with pytest.raises(JournalError):
        validate_decision(_enter(kill_condition_type="other"))
    validate_decision(_enter(
        kill_condition_type="other",
        kill_condition_untyped_reason=(
            "The trigger is a counterparty action with no numeric or "
            "filing form: the founder publicly withdrawing the voting "
            "agreement in any venue.")))


# ---- shrunk small-sample stat (finding #3, reported-not-gating) ----

def test_checkpoint_stats_reports_shrunk_mean():
    closed = [{"excess": 0.10, "confidence": 0.5},
              {"excess": 0.06, "confidence": 0.7}]
    stats = checkpoint_stats(closed)
    assert stats["mean_excess"] == pytest.approx(0.08)
    # prior_n=20 toward 0: (2 * 0.08) / 22
    assert stats["mean_excess_shrunk"] == pytest.approx(round(2 * 0.08 / 22, 4))
    # frozen raw fields still present and unchanged
    assert "t" in stats and "calibration_ok" in stats


# ---- secondary price guard (finding #6) ----

def test_secondary_price_suspect():
    from shared.guards import secondary_price_suspect
    assert secondary_price_suspect(32.0, 19.0)          # the EQPT case
    assert not secondary_price_suspect(19.5, 19.0)      # normal drift
    assert secondary_price_suspect(0.0, 19.0)           # unusable input
    assert secondary_price_suspect(None, 19.0)
    assert secondary_price_suspect(19.0, 0.0)
    assert not secondary_price_suspect(114.9, 100.0)    # just inside 15%
    assert secondary_price_suspect(115.1, 100.0)        # just outside


# ---- trade-drought diagnostic (paralysis guard, reported-not-gating) ----

def _notes(dates):
    return [{"action": "note", "date": d, "text": "sweep, no trade"} for d in dates]


def test_drought_unfunded_never_flags():
    # $0, market shut: the weekend research sessions must NEVER count as a drought
    recs = _notes(["2026-06-30", "2026-07-01", "2026-07-04", "2026-07-05"])
    s = trade_drought_stats(recs, today="2026-07-05", funded=False, cash=0.0,
                            equity=0.0, funded_since=None)
    assert s["drought_flag"] is False
    assert "clock not started" in s["status"]


def test_drought_funded_deployed_is_not_a_drought():
    recs = _notes(["2026-07-07"])
    s = trade_drought_stats(recs, today="2026-08-01", funded=True, cash=100.0,
                            equity=1000.0, funded_since="2026-07-07")
    assert s["drought_flag"] is False
    assert s["deployed_pct"] == pytest.approx(0.9)
    assert "deployed" in s["status"]


def test_drought_within_calendar_floor_does_not_flag():
    # 8 all-cash sessions but only 9 days since funding -> floor blocks the flag
    dates = ["2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10",
             "2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16"]
    s = trade_drought_stats(_notes(dates), today="2026-07-16", funded=True,
                            cash=1000.0, equity=1000.0, funded_since="2026-07-07")
    assert s["sessions_all_cash"] >= DROUGHT_SESSIONS
    assert s["days_since"] < DROUGHT_MIN_DAYS
    assert s["drought_flag"] is False


def test_drought_flags_when_sustained_and_all_cash():
    dates = ["2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10",
             "2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16"]
    s = trade_drought_stats(_notes(dates), today="2026-08-05", funded=True,
                            cash=1000.0, equity=1000.0, funded_since="2026-07-07")
    assert s["drought_flag"] is True
    assert s["days_since"] == 29
    assert s["deployed_pct"] == pytest.approx(0.0)
    assert "DROUGHT" in s["status"]


def test_drought_ignores_pre_funding_sessions():
    # 4 unfunded weekend notes + only 2 funded sessions -> window starts at funding
    recs = _notes(["2026-06-30", "2026-07-01", "2026-07-04", "2026-07-05",
                   "2026-07-07", "2026-07-08"])
    s = trade_drought_stats(recs, today="2026-08-01", funded=True, cash=1000.0,
                            equity=1000.0, funded_since="2026-07-07")
    assert s["sessions_all_cash"] == 2          # only the two post-funding dates
    assert s["drought_flag"] is False


def test_drought_resets_after_a_trade():
    recs = _notes(["2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10",
                   "2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16"])
    recs.append({"action": "enter", "date": "2026-07-20", "symbol": "MFP"})
    recs += _notes(["2026-07-21", "2026-07-22"])
    s = trade_drought_stats(recs, today="2026-08-15", funded=True, cash=1000.0,
                            equity=1000.0, funded_since="2026-07-07")
    assert s["last_entry_date"] == "2026-07-20"
    assert s["sessions_all_cash"] == 2          # only sessions AFTER the entry
    assert s["drought_flag"] is False


def test_journal_default_path_is_the_live_v2_journal():
    """Regression: until 2026-07-15 journal.JOURNAL_PATH pointed at the v1
    ghost path, so append_decision's DEFAULT silently routed live session
    notes into an unpersisted stray file (two sessions lost narrative
    entries — journal INTEGRITY EVENT, 2026-07-15). The writer default and
    the sleeve's journal constant must name the same live file, forever."""
    from proteus import journal, sleeve
    assert journal.JOURNAL_PATH == "cache/proteus_journal.jsonl"
    assert journal.JOURNAL_PATH == sleeve.JOURNAL_PATH
    assert "ghost" not in journal.JOURNAL_PATH
