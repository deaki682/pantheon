"""Tests for proteus.labhost — D6 forward-population logging."""
import json

from proteus import labhost

IDX = """Description:           Daily Index of EDGAR Dissemination Feed by Form Type
Last Data Received:    August 31, 2026

Form Type   Company Name                                                  CIK         Date Filed  File Name
---------------------------------------------------------------------------------------------------------------
8-K         ACME CORP                                                     123456      20260831    edgar/data/123456/0000123456-26-000001.txt
SC 14D9     TARGET CO INC                                                 222333      20260831    edgar/data/222333/0000222333-26-000009.txt
SC 14D9/A   AMENDED TARGET INC                                            444555      20260831    edgar/data/444555/0000444555-26-000010.txt
SC TO-C     SOME CLOSED END FUND                                          666777      20260831    edgar/data/666777/0000666777-26-000011.txt
SC TO-I     ISSUER TENDER CO                                              888999      20260831    edgar/data/888999/0000888999-26-000012.txt
"""


def test_parse_form_idx_initial_forms_only():
    rows = labhost.parse_form_idx(IDX)
    assert [r["form"] for r in rows] == ["SC 14D9", "SC TO-C"]
    r = rows[0]
    assert r["slug"] == "tender_target_14d9"
    assert r["company"] == "TARGET CO INC"
    assert r["cik"] == "222333"
    assert r["date"] == "20260831"
    assert r["accession"] == "0000222333-26-000009"
    assert rows[1]["slug"] == "cef_tender_toc_anchor"


def test_log_days_dedupes_and_skips_unpublished(tmp_path):
    path = str(tmp_path / "book.json")
    fetches = {"count": 0}

    def fake_fetch(url):
        fetches["count"] += 1
        if "20260901" in url:
            return ""
        return IDX

    out = labhost.log_days(["2026-08-31", "2026-09-01"], path=path, fetch=fake_fetch)
    assert len(out["new"]) == 2
    assert out["skipped_days"] == ["2026-09-01"]
    # idempotent second pass
    out2 = labhost.log_days(["2026-08-31"], path=path, fetch=fake_fetch)
    assert out2["new"] == []
    book = json.load(open(path))
    assert len(book["rows"]) == 2
    assert book["rows"][0]["status"] == "logged"
    assert book["rows"][0]["classification"] is None
