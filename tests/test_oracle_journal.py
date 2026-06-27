import pytest

from oracle.journal import JournalEntry, append, grade, read, write


def _entry(decision="buy", conviction=0.8, symbol="ACME", price=100.0):
    return JournalEntry(
        timestamp="2024-05-29T12:00:00",
        symbol=symbol,
        decision=decision,
        conviction=conviction,
        horizon_days=180,
        price=price,
    )


def test_append_and_read(tmp_path):
    p = tmp_path / "journal.jsonl"
    append(str(p), _entry())
    append(str(p), _entry(symbol="MSFT"))
    entries = read(str(p))
    assert len(entries) == 2
    assert entries[0].symbol == "ACME"


def test_invalid_decision_rejected(tmp_path):
    p = tmp_path / "journal.jsonl"
    with pytest.raises(ValueError):
        append(str(p), _entry(decision="hodl"))


def test_grade_buy_win():
    e = _entry(decision="buy", price=100)
    grade(e, final_price=110)  # +10% > 5% threshold
    assert e.graded_return == 0.10
    assert e.graded_outcome == "win"


def test_grade_buy_loss():
    e = _entry(decision="buy", price=100)
    grade(e, final_price=90)
    assert e.graded_outcome == "loss"


def test_grade_buy_neutral():
    e = _entry(decision="buy", price=100)
    grade(e, final_price=102)
    assert e.graded_outcome == "neutral"


def test_grade_sell_win_on_drop():
    e = _entry(decision="sell", price=100)
    grade(e, final_price=85)  # -15%
    assert e.graded_outcome == "win"  # avoided loss


def test_grade_sell_loss_on_rise():
    e = _entry(decision="sell", price=100)
    grade(e, final_price=120)
    assert e.graded_outcome == "loss"


def test_grade_hold_is_neutral():
    e = _entry(decision="hold", price=100)
    grade(e, final_price=200)
    assert e.graded_outcome == "neutral"


def test_read_missing_file(tmp_path):
    assert read(str(tmp_path / "nope.jsonl")) == []


def test_write_overwrites(tmp_path):
    p = tmp_path / "journal.jsonl"
    append(str(p), _entry(symbol="A"))
    write(str(p), [_entry(symbol="B")])
    entries = read(str(p))
    assert len(entries) == 1
    assert entries[0].symbol == "B"
