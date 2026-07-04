"""Tests for shared.sharadar pure logic (no network): resolution + bars."""
import pytest

from shared.sharadar import (
    AmbiguousTicker,
    SharadarError,
    fetch_sep_bulk_range,
    resolve_ticker,
    to_shared_bars,
)

# Fixture rows mirroring the real acceptance-QA findings (2026-07-04).
META_ROW = {"ticker": "META", "permaticker": 194817, "name": "META PLATFORMS INC",
            "isdelisted": "N", "firstpricedate": "2012-05-18",
            "lastpricedate": "2026-07-02", "relatedtickers": "FB"}
SIVBQ_ROW = {"ticker": "SIVBQ", "permaticker": 198834, "name": "SVB FINANCIAL GROUP",
             "isdelisted": "Y", "firstpricedate": "1990-03-26",
             "lastpricedate": "2023-03-28",
             "relatedtickers": "SIVBO SIVPQ SIVB SIVBP"}
BBBY_NEW = {"ticker": "BBBY", "permaticker": 195902, "name": "BED BATH & BEYOND INC",
            "isdelisted": "N", "firstpricedate": "2002-05-30",
            "lastpricedate": "2026-07-02", "relatedtickers": "BYON OSTK"}
BBBY_OLD = {"ticker": "BBBYQ", "permaticker": 197799, "name": "BED BATH & BEYOND INC",
            "isdelisted": "Y", "firstpricedate": "1992-06-05",
            "lastpricedate": "2023-05-02", "relatedtickers": "BBBY"}
ALL = [META_ROW, SIVBQ_ROW, BBBY_NEW, BBBY_OLD]


def test_resolve_exact_ticker():
    assert resolve_ticker("META", candidates=ALL)["permaticker"] == 194817


def test_resolve_historical_via_relatedtickers():
    # FB only exists in META's relatedtickers
    assert resolve_ticker("FB", candidates=ALL)["ticker"] == "META"
    # SIVB resolves to the post-bankruptcy final ticker
    assert resolve_ticker("SIVB", candidates=ALL)["ticker"] == "SIVBQ"


def test_recycled_ticker_requires_as_of():
    # "BBBY" matches BOTH the new (Overstock-lineage) row and the old
    # Bed Bath's relatedtickers — the exact trap the QA caught live.
    with pytest.raises(AmbiguousTicker):
        resolve_ticker("BBBY", candidates=ALL)


def test_recycled_ticker_disambiguates_by_date():
    # Meme-era BBBY (2022) must resolve to the ORIGINAL company...
    assert resolve_ticker("BBBY", as_of="2022-08-05",
                          candidates=ALL)["ticker"] == "BBBYQ"
    # ...while 2026 BBBY is the Overstock-lineage entity.
    assert resolve_ticker("BBBY", as_of="2026-06-01",
                          candidates=ALL)["ticker"] == "BBBY"


def test_unresolvable_symbol_raises():
    with pytest.raises(SharadarError):
        resolve_ticker("ZZZZX", candidates=ALL)


def test_to_shared_bars_canonicalizes_and_sorts():
    rows = [
        {"ticker": "AAPL", "date": "2020-09-01", "open": 132.76, "high": 134.8,
         "low": 130.53, "close": 134.18, "volume": 150699000.0,
         "closeadj": 130.163, "closeunadj": 134.18, "lastupdated": "2026-05-11"},
        {"ticker": "AAPL", "date": "2020-08-28", "open": 126.013, "high": 126.442,
         "low": 124.578, "close": 124.808, "volume": 187630000.0,
         "closeadj": 121.071, "closeunadj": 499.23, "lastupdated": "2026-05-11"},
    ]
    bars = to_shared_bars(rows)
    assert [b["date"] for b in bars] == ["2020-08-28", "2020-09-01"]
    assert bars[0]["close"] == 124.808           # split-adjusted, house convention
    assert bars[0]["close_total_return"] == 121.071
    assert bars[0]["volume"] == 187630000
    assert "closeunadj" not in bars[0]


def test_to_shared_bars_skips_dateless_or_closeless():
    assert to_shared_bars([{"ticker": "X", "close": 5.0},
                           {"ticker": "X", "date": "2020-01-02"}]) == []


def test_fetch_sep_bulk_range_omits_ticker_param_by_default(monkeypatch):
    captured = {}

    def fake_datatable(table_name, **params):
        captured["table"] = table_name
        captured["params"] = params
        return [{"ticker": "AAA", "date": "2024-01-02", "close": 1.0}]

    monkeypatch.setattr("shared.sharadar._datatable", fake_datatable)
    rows = fetch_sep_bulk_range("2024-01-01", "2024-01-05")
    assert captured["table"] == "SEP"
    assert "ticker" not in captured["params"]
    assert captured["params"]["date.gte"] == "2024-01-01"
    assert captured["params"]["date.lte"] == "2024-01-05"
    assert rows == [{"ticker": "AAA", "date": "2024-01-02", "close": 1.0}]


def test_fetch_sep_bulk_range_dedupes_and_uppercases_tickers(monkeypatch):
    captured = {}

    def fake_datatable(table_name, **params):
        captured["params"] = params
        return []

    monkeypatch.setattr("shared.sharadar._datatable", fake_datatable)
    fetch_sep_bulk_range("2024-01-01", "2024-01-05", tickers=["aapl", "AAPL", "msft"])
    assert captured["params"]["ticker"] == "AAPL,MSFT"
