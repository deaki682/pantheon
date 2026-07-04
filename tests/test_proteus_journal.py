import pytest

from proteus.journal import (
    CAPITAL_BASE, JournalError, PaperBook, append_decision, checkpoint_stats,
    load_journal, validate_decision,
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
