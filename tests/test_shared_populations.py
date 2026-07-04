"""Tests for shared.populations — the reusable population-catalog store."""
import pytest

from shared.populations import (
    list_populations,
    load_population,
    save_population,
)

DEF = ("Every SEC Form 10-12B spinoff registration filed 2021-01-01 to "
       "2026-06-30, from the EDGAR full-text index, all outcomes retained.")
COV = ("Complete against the EDGAR daily index; 3 filings with malformed "
       "accession numbers skipped and listed in the study appendix.")
SRC = "https://www.sec.gov/Archives/edgar/full-index/"


def _save(tmp_path, slug="spinoffs_2021_2026", rows=None, **kw):
    args = dict(definition=DEF, source=SRC, coverage_note=COV,
                built="2026-07-04",
                index_path=str(tmp_path / "shared_populations.json"))
    args.update(kw)
    if rows is None:
        rows = [{"symbol": "VGNT"}]
    return save_population(slug, rows, **args)


def test_roundtrip(tmp_path):
    entry = _save(tmp_path, rows=[{"symbol": "VGNT"}, {"symbol": "OCTV"}])
    assert entry["n"] == 2
    idx = str(tmp_path / "shared_populations.json")
    rows = load_population("spinoffs_2021_2026", index_path=idx)
    assert [r["symbol"] for r in rows] == ["VGNT", "OCTV"]
    assert "spinoffs_2021_2026" in list_populations(index_path=idx)


def test_refuses_empty_rows(tmp_path):
    with pytest.raises(ValueError):
        _save(tmp_path, rows=[])


def test_refuses_stub_definition(tmp_path):
    with pytest.raises(ValueError):
        _save(tmp_path, definition="spinoffs")


def test_refuses_stub_coverage_note(tmp_path):
    with pytest.raises(ValueError):
        _save(tmp_path, coverage_note="complete")


def test_rebuild_keeps_previous_build_record(tmp_path):
    _save(tmp_path)
    entry = _save(tmp_path, rows=[{"symbol": "A"}, {"symbol": "B"}],
                  built="2026-08-01")
    assert entry["n"] == 2
    assert entry["previous_builds"] == [{"built": "2026-07-04", "n": 1}]


def test_unknown_population_raises(tmp_path):
    with pytest.raises(KeyError):
        load_population("nope", index_path=str(tmp_path / "idx.json"))
