"""Tests for shared.historicals — batching, ingest, coverage, archive."""
import json
import pytest

from shared.historicals import (
    archive_bars,
    bars_for,
    coverage,
    extract_bars,
    ingest_raw,
    load_store,
    plan_batches,
)


# ---- plan_batches ----

def test_plan_batches_chunks_at_nine():
    syms = [f"S{i}" for i in range(20)]
    batches = plan_batches(syms)
    assert [len(b) for b in batches] == [9, 9, 2]


def test_plan_batches_dedupes_and_uppercases():
    assert plan_batches(["aapl", "AAPL", " msft ", ""]) == [["AAPL", "MSFT"]]


def test_plan_batches_rejects_bad_size():
    with pytest.raises(ValueError):
        plan_batches(["A"], batch_size=0)


# ---- extract_bars: the three payload shapes ----

def test_extract_from_symbol_map():
    raw = {"AAPL": [{"date": "2026-07-01", "close": 200.0, "volume": 100}]}
    out = extract_bars(raw)
    assert out["AAPL"][0] == {"date": "2026-07-01", "close": 200.0, "volume": 100}


def test_extract_from_results_list_with_robinhood_fields():
    raw = {"results": [{
        "symbol": "msft",
        "historicals": [{
            "begins_at": "2026-07-01T00:00:00Z",
            "open_price": "99.5", "close_price": "101.25",
            "high_price": "102", "low_price": "99", "volume": "5000",
        }],
    }]}
    out = extract_bars(raw)
    bar = out["MSFT"][0]
    assert bar["date"] == "2026-07-01"
    assert bar["close"] == 101.25
    assert bar["volume"] == 5000


def test_extract_unknown_shape_yields_empty():
    assert extract_bars({"whatever": 42}) == {}
    assert extract_bars([1, 2, 3]) == {}


# ---- ingest + store ----

def _write_raw(tmp_path, payload, name="raw.json"):
    p = tmp_path / name
    p.write_text(json.dumps(payload))
    return str(p)


def test_ingest_merges_and_dedupes_by_date(tmp_path):
    store_path = str(tmp_path / "bars.json")
    raw1 = _write_raw(tmp_path, {"SPY": [
        {"date": "2026-07-01", "close": 740.0},
        {"date": "2026-07-02", "close": 744.8},
    ]}, "r1.json")
    raw2 = _write_raw(tmp_path, {"SPY": [
        {"date": "2026-07-02", "close": 744.8},  # duplicate date
        {"date": "2026-07-06", "close": 748.0},
    ]}, "r2.json")
    assert ingest_raw(raw1, store_path) == {"SPY": 2}
    assert ingest_raw(raw2, store_path) == {"SPY": 1}
    store = load_store(store_path)
    dates = [b["date"] for b in bars_for("spy", store)]
    assert dates == ["2026-07-01", "2026-07-02", "2026-07-06"]


def test_ingest_refuses_silent_empty(tmp_path):
    raw = _write_raw(tmp_path, {"nothing": "here"})
    with pytest.raises(ValueError):
        ingest_raw(raw, str(tmp_path / "bars.json"))


# ---- coverage: the survivorship disclosure ----

def test_coverage_reports_missing_symbols(tmp_path):
    store_path = str(tmp_path / "bars.json")
    raw = _write_raw(tmp_path, {"AAPL": [{"date": "2026-07-01", "close": 200.0}]})
    ingest_raw(raw, store_path)
    rep = coverage(load_store(store_path), ["AAPL", "DELISTEDCO"])
    assert rep["symbols"]["AAPL"]["bars"] == 1
    assert rep["missing"] == ["DELISTEDCO"]


def test_coverage_date_window(tmp_path):
    store_path = str(tmp_path / "bars.json")
    raw = _write_raw(tmp_path, {"AAPL": [
        {"date": "2026-06-01", "close": 190.0},
        {"date": "2026-07-01", "close": 200.0},
    ]})
    ingest_raw(raw, store_path)
    rep = coverage(load_store(store_path), ["AAPL"], start="2026-06-15")
    assert rep["symbols"]["AAPL"] == {
        "bars": 1, "first": "2026-07-01", "last": "2026-07-01",
    }


# ---- archive ----

def test_archive_requires_specific_source(tmp_path):
    with pytest.raises(ValueError):
        archive_bars(
            "GONE", [{"date": "2020-01-02", "close": 5.0}],
            source="web", archive_path=str(tmp_path / "arch.json"),
        )


def test_archive_requires_valid_bars(tmp_path):
    with pytest.raises(ValueError):
        archive_bars(
            "GONE", [{"close": 5.0}],  # no date
            source="https://example.com/gone-history",
            archive_path=str(tmp_path / "arch.json"),
        )


def test_archive_deposits_and_flags_delisted(tmp_path):
    path = str(tmp_path / "arch.json")
    n = archive_bars(
        "GONE", [{"date": "2020-01-02", "close": 5.0}],
        source="https://example.com/gone-history",
        note="delisted 2021-03", delisted=True, archive_path=path,
    )
    assert n == 1
    store = load_store(path)
    assert store["symbols"]["GONE"]["delisted"] is True
    assert bars_for("GONE", store)[0]["close"] == 5.0
