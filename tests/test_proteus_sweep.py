"""Tests for proteus.sweep — spec-driven resolved-event sweep."""
import json

import pytest

from proteus import sweep


SPEC = {
    "families": [
        '"settlement agreement"',
        '"Dutch auction"',
    ]
}


def _hit(adsh, date, names, file_type):
    return {
        "_source": {
            "adsh": adsh,
            "file_date": date,
            "display_names": names,
            "file_type": file_type,
        }
    }


def test_run_sweep_dedupes_and_merges_families():
    responses = {
        '"settlement agreement"': {
            "hits": {"hits": [
                _hit("0001-26-000001", "2026-08-14", ["Alpha Co (AAA)"], "8-K"),
                _hit("0001-26-000002", "2026-08-14", ["Beta Co (BBB)"], "EX-10.1"),
            ]}
        },
        '"Dutch auction"': {
            "hits": {"hits": [
                _hit("0001-26-000001", "2026-08-14", ["Alpha Co (AAA)"], "EX-99.1"),
            ]}
        },
    }
    hits = sweep.run_sweep(
        "2026-08-14", "2026-08-16", spec=SPEC, fetch=lambda p: responses[p["q"]]
    )
    assert len(hits) == 2
    alpha = next(h for h in hits if h["adsh"] == "0001-26-000001")
    assert alpha["families"] == ["Dutch", "settlement"]
    assert alpha["file_types"] == ["8-K", "EX-99.1"]
    assert alpha["exhibit_only"] is False


def test_exhibit_only_flags_boilerplate_class():
    # All matched docs are EX-4.x/EX-10.x -> batch-kill candidate.
    assert sweep.is_exhibit_only({"EX-4.1", "EX-10.2"}) is True
    # An 8-K body match rescues the hit from the batch-kill class.
    assert sweep.is_exhibit_only({"EX-4.1", "8-K"}) is False
    # EX-99.1 press releases are NOT boilerplate.
    assert sweep.is_exhibit_only({"EX-99.1"}) is False
    # Unknown/empty types alone never flag.
    assert sweep.is_exhibit_only({""}) is False
    assert sweep.is_exhibit_only(set()) is False


def test_run_sweep_passes_forms_and_window():
    seen = []

    def fetch(params):
        seen.append(params)
        return {"hits": {"hits": []}}

    sweep.run_sweep("2026-08-14", "2026-08-16", spec=SPEC, fetch=fetch)
    assert len(seen) == len(SPEC["families"])
    for p in seen:
        assert p["forms"] == "8-K"
        assert p["startdt"] == "2026-08-14"
        assert p["enddt"] == "2026-08-16"


def test_load_spec_from_disk(tmp_path):
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(SPEC))
    assert sweep.load_spec(str(path))["families"] == SPEC["families"]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"families": []}))
    with pytest.raises(ValueError):
        sweep.load_spec(str(bad))


def test_report_counts_reads():
    hits = sweep.run_sweep(
        "2026-08-14",
        "2026-08-16",
        spec=SPEC,
        fetch=lambda p: {
            "hits": {"hits": [
                _hit("0001-26-000001", "2026-08-14", ["Alpha Co (AAA)"], "8-K"),
                _hit("0001-26-000002", "2026-08-14", ["Beta Co (BBB)"], "EX-10.1"),
            ]}
        } if p["q"] == '"settlement agreement"' else {"hits": {"hits": []}},
    )
    text = sweep.report(hits)
    assert "2 unique accessions" in text
    assert "[EX]" in text
    assert "1 need a read (1 exhibit-only batch-kill candidates)" in text


def test_sweep_spec_file_in_cache_is_loadable_when_present():
    # The live spec is state (cache/), not code; only validate when hydrated.
    try:
        spec = sweep.load_spec()
    except FileNotFoundError:
        pytest.skip("cache not hydrated")
    assert len(spec["families"]) == 12
