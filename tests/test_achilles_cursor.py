import pytest

from achilles.cursor import Cursor, SEEN_MAX, filter_new, load, register_events, save
from shared.edgar import Filing


def _filing(acc, date):
    return Filing(
        cik="1", accession_no=acc, form="8-K", filing_date=date,
        primary_document="d.htm", items="2.02", symbol="X",
    )


def test_seen_max_constant():
    assert SEEN_MAX == 5_000


def test_register_advances_by_max_filing_date():
    cur = Cursor()
    register_events(cur, [_filing("a", "2024-05-28"), _filing("b", "2024-05-29")])
    assert cur.cursor_date == "2024-05-29"


def test_register_never_regresses():
    cur = Cursor(cursor_date="2024-05-30")
    register_events(cur, [_filing("a", "2024-05-25")])
    assert cur.cursor_date == "2024-05-30"


def test_register_dedupes_via_accessions():
    cur = Cursor()
    f1 = _filing("a", "2024-05-29")
    new = register_events(cur, [f1, _filing("a", "2024-05-29"), _filing("b", "2024-05-29")])
    assert len(new) == 2
    assert {f.accession_no for f in new} == {"a", "b"}


def test_seen_accessions_capped():
    cur = Cursor()
    for i in range(SEEN_MAX + 100):
        cur.seen.append(f"acc-{i}")
    assert len(cur.seen) <= SEEN_MAX


def test_filter_new_strict_greater_than():
    cur = Cursor(cursor_date="2024-05-29")
    filings = [_filing("a", "2024-05-29"), _filing("b", "2024-05-30")]
    out = filter_new(cur, filings)
    assert len(out) == 1
    assert out[0].accession_no == "b"


def test_filter_new_empty_cursor():
    cur = Cursor()
    filings = [_filing("a", "2024-05-29")]
    out = filter_new(cur, filings)
    assert len(out) == 1


def test_save_and_load(tmp_path):
    p = tmp_path / "cursor.json"
    cur = Cursor(cursor_date="2024-05-29")
    cur.seen.append("a")
    cur.seen.append("b")
    save(str(p), cur)
    loaded = load(str(p))
    assert loaded.cursor_date == "2024-05-29"
    assert "a" in loaded.seen_set


def test_load_missing(tmp_path):
    cur = load(str(tmp_path / "nope.json"))
    assert cur.cursor_date == ""


def test_register_never_uses_today_directly():
    """Critical: cursor_date advance comes only from filing dates, never today."""
    cur = Cursor()
    # Empty batch should not advance cursor
    register_events(cur, [])
    assert cur.cursor_date == ""
    # Single filing dated in the past advances to that date, NOT to today
    register_events(cur, [_filing("a", "2024-05-29")])
    assert cur.cursor_date == "2024-05-29"
