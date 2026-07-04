"""Tests for shared.event_calendar — validation, dedupe, upcoming."""
import pytest

from shared.event_calendar import (
    add_events,
    load_calendar,
    upcoming,
    validate_event,
)


def _ev(**kw):
    base = {
        "symbol": "EQPT",
        "type": "lockup_expiry",
        "date": "2026-07-22",
        "source": "https://example.com/eqpt-424b4",
    }
    base.update(kw)
    return base


# ---- validation ----

def test_validate_normalizes():
    out = validate_event(_ev(symbol=" eqpt ", type="LOCKUP_EXPIRY"))
    assert out["symbol"] == "EQPT"
    assert out["type"] == "lockup_expiry"


def test_validate_rejects_unknown_type():
    with pytest.raises(ValueError):
        validate_event(_ev(type="vibes"))


def test_validate_rejects_bad_date():
    with pytest.raises(ValueError):
        validate_event(_ev(date="July 22"))


def test_validate_rejects_vague_source():
    with pytest.raises(ValueError):
        validate_event(_ev(source="web"))


# ---- add_events ----

def test_add_events_all_or_nothing(tmp_path):
    path = str(tmp_path / "cal.json")
    with pytest.raises(ValueError):
        add_events([_ev(), _ev(type="vibes")], path=path)
    assert load_calendar(path) == []


def test_add_events_dedupes_on_identity(tmp_path):
    path = str(tmp_path / "cal.json")
    r1 = add_events([_ev()], path=path, today="2026-07-04")
    r2 = add_events([_ev(note="founders excluded per 13D exhibit")], path=path)
    assert r1["added"] == 1
    assert r2 == {"added": 0, "updated": 1, "total": 1}
    events = load_calendar(path)
    assert len(events) == 1
    assert events[0]["note"] == "founders excluded per 13D exhibit"
    assert events[0]["added_on"] == "2026-07-04"


def test_add_events_distinct_types_coexist(tmp_path):
    path = str(tmp_path / "cal.json")
    add_events([_ev(), _ev(type="ipo", date="2026-01-15")], path=path)
    assert len(load_calendar(path)) == 2


# ---- upcoming ----

def test_upcoming_window_and_sort(tmp_path):
    path = str(tmp_path / "cal.json")
    add_events([
        _ev(),                                             # +18d
        _ev(symbol="OLD", type="spinoff", date="2026-06-01"),   # past
        _ev(symbol="FAR", type="ipo", date="2026-12-01"),       # beyond window
        _ev(symbol="SOON", type="spinoff", date="2026-07-06"),  # +2d
    ], path=path)
    hits = upcoming(load_calendar(path), today="2026-07-04", within_days=45)
    assert [e["symbol"] for e in hits] == ["SOON", "EQPT"]


def test_upcoming_type_filter(tmp_path):
    path = str(tmp_path / "cal.json")
    add_events([_ev(), _ev(symbol="SOON", type="spinoff", date="2026-07-06")], path=path)
    hits = upcoming(
        load_calendar(path), today="2026-07-04", types=["lockup_expiry"]
    )
    assert [e["symbol"] for e in hits] == ["EQPT"]
