"""Tests for proteus.eventfeed — the primary-source dated-event feed.

Fixture snippets mirror real filing language: the LPSN DEFM14A
(accession 0001213900-26-076759, read 2026-07-13) supplied both the
meeting-date and outside-date patterns.
"""
import json

import pytest

from proteus import eventfeed as ef


# ------- date parsing -------

def test_parse_us_date_basic():
    assert ef.parse_us_date("held on August 20, 2026 at 10am") == "2026-08-20"


def test_parse_us_date_first_wins():
    s = "on January 5, 2027 or February 1, 2027"
    assert ef.parse_us_date(s) == "2027-01-05"


def test_parse_us_date_invalid_day_is_none():
    assert ef.parse_us_date("February 30, 2026") is None


def test_parse_us_date_absent():
    assert ef.parse_us_date("no date here, only vibes") is None


# ------- proxy extraction -------

LPSN_MEETING = (
    "The Company will hold a special meeting of its stockholders on "
    "August 20, 2026, at 10:00 a.m. Eastern Time, to consider and vote "
    "upon the proposal to adopt the merger agreement."
)

# Date AFTER the term (LPSN summary-table style).
LPSN_OUTSIDE_AFTER = (
    "Outside Date : By either the Company or Parent if the First "
    "Effective Time shall not have occurred on or before October 21, 2026."
)

# Date BEFORE the term (definition style).
OUTSIDE_BEFORE = (
    "if the merger has not been consummated on or before October 21, "
    "2026 (the “Outside Date”), either party may terminate."
)


def test_extract_meeting_date():
    assert ef.extract_meeting_date(LPSN_MEETING) == "2026-08-20"


def test_extract_meeting_date_none_without_nearby_date():
    assert ef.extract_meeting_date(
        "the special meeting will be held virtually") is None


def test_extract_outside_date_both_orders():
    assert ef.extract_outside_date(LPSN_OUTSIDE_AFTER) == "2026-10-21"
    assert ef.extract_outside_date(OUTSIDE_BEFORE) == "2026-10-21"


def test_extract_outside_date_modal_beats_stray():
    # Two consistent definitional mentions + one stray other-date mention:
    # the modal date wins.
    stray = ("the Outside Date may be extended as described on "
             "March 1, 2019 in the background section.")
    text = " ".join([LPSN_OUTSIDE_AFTER, OUTSIDE_BEFORE, stray])
    assert ef.extract_outside_date(text) == "2026-10-21"


def test_extract_outside_date_absent():
    assert ef.extract_outside_date("no such term appears") is None


# ------- FTS hit parsing -------

FTS_PAYLOAD = {
    "hits": {"total": {"value": 2}, "hits": [
        {
            "_id": "0001213900-26-076759:ea0297465-01.htm",
            "_source": {
                "display_names": ["LIVEPERSON INC  (LPSN)  (CIK 0001102993)"],
                "ciks": ["1102993"],
                "file_type": "DEFM14A",
                "file_date": "2026-07-09",
            },
        },
        {
            "_id": "0000000000-26-000001:proxy.htm",
            "_source": {
                "display_names": [
                    "Equitable Holdings, Inc.  (EQH, EQH-PA, EQH-PC)  (CIK 0001333986)"],
                "ciks": ["1333986"],
                "file_type": "DEFM14A",
                "file_date": "2026-06-23",
            },
        },
    ]},
}


def test_parse_fts_hits_fields():
    recs = ef.parse_fts_hits(FTS_PAYLOAD)
    assert len(recs) == 2
    r = recs[0]
    assert r["accession"] == "0001213900-26-076759"
    assert r["doc"] == "ea0297465-01.htm"
    assert r["cik"] == "1102993"
    assert r["symbol"] == "LPSN"
    assert r["filed"] == "2026-07-09"


def test_ticker_from_display_multiclass_takes_primary():
    recs = ef.parse_fts_hits(FTS_PAYLOAD)
    assert recs[1]["symbol"] == "EQH"


def test_ticker_from_display_no_ticker():
    assert ef.ticker_from_display(
        "Hancock Park Corporate Income, Inc.  (CIK 0001661306)") is None


def test_doc_url():
    recs = ef.parse_fts_hits(FTS_PAYLOAD)
    url = ef.doc_url(recs[0])
    assert url == ("https://www.sec.gov/Archives/edgar/data/1102993/"
                   "000121390026076759/ea0297465-01.htm")


# ------- FR plumbing -------

def test_fr_query_url_encodes_conditions():
    url = ef.fr_query_url('"target date" 337', "2026-07-06")
    assert url.startswith(ef.FR_API + "?")
    assert "conditions%5Bterm%5D=%22target%20date%22%20337" in url
    assert "international-trade-commission" in url
    assert "2026-07-06" in url


def test_parse_fr_results():
    payload = {"results": [{
        "publication_date": "2026-07-10",
        "title": "Certain Crafting Machines...",
        "html_url": "https://example.gov/doc",
        "raw_text_url": "https://example.gov/raw",
        "extra": "dropped",
    }]}
    out = ef.parse_fr_results(payload)
    assert out == [{
        "published": "2026-07-10",
        "title": "Certain Crafting Machines...",
        "html_url": "https://example.gov/doc",
        "raw_text_url": "https://example.gov/raw",
    }]


# ------- event store -------

def _ev(sym="LPSN", etype="merger_vote", d="2026-08-20"):
    return {"symbol": sym, "event_type": etype, "event_date": d,
            "source": "DEFM14A", "source_url": "https://sec.gov/x"}


def test_add_events_dedupes_and_counts():
    store = {"events": []}
    assert ef.add_events(store, [_ev(), _ev()]) == 1
    assert ef.add_events(store, [_ev()]) == 0
    assert ef.add_events(store, [_ev(etype="outside_date", d="2026-10-21")]) == 1
    assert len(store["events"]) == 2


def test_add_events_requires_source_url():
    ev = _ev()
    del ev["source_url"]
    with pytest.raises(ValueError):
        ef.add_events({"events": []}, [ev])


def test_add_events_skips_undated():
    ev = _ev(d=None)
    assert ef.add_events({"events": []}, [ev]) == 0


def test_add_events_drops_event_dated_at_or_before_filing():
    # A vote/outside date on or before the proxy's own filing date is a
    # mis-extraction, never actionable.
    stale = dict(_ev(d="2026-07-06"), filed="2026-07-09")
    same_day = dict(_ev(d="2026-07-09"), filed="2026-07-09")
    good = dict(_ev(d="2026-08-20"), filed="2026-07-09")
    store = {"events": []}
    assert ef.add_events(store, [stale, same_day, good]) == 1
    assert store["events"][0]["event_date"] == "2026-08-20"


def test_add_events_without_filed_is_not_filtered():
    # FR/ITC events carry no filing date; the plausibility rule only
    # applies when 'filed' is present.
    assert ef.add_events({"events": []}, [_ev()]) == 1


def test_upcoming_window_and_order():
    store = {"events": [
        _ev(d="2026-08-20"),
        _ev(etype="outside_date", d="2026-10-21"),
        _ev(sym="OLD", d="2026-07-01"),          # past — excluded
        _ev(sym="FAR", d="2027-09-01"),          # beyond horizon — excluded
    ]}
    got = ef.upcoming(store, "2026-07-13", horizon_days=180)
    assert [e["event_date"] for e in got] == ["2026-08-20", "2026-10-21"]


def test_store_roundtrip(tmp_path):
    p = str(tmp_path / "ef.json")
    store = {"updated": "2026-07-13", "events": [_ev()]}
    ef.save(store, p)
    assert ef.load(p) == store


def test_load_missing_returns_empty(tmp_path):
    assert ef.load(str(tmp_path / "nope.json")) == {"updated": "", "events": []}
