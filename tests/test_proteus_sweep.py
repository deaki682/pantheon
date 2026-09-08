"""Tests for proteus.sweep — spec-driven resolved-event sweep."""
import json

import pytest
import requests

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
        # A spec with no forms key falls back to the default list, which must
        # keep 8-K and also carry the tender schedules a capital return
        # commences on (the ABUS SC TO-I the 8-K-only sweep missed).
        assert p["forms"] == sweep.DEFAULT_FORMS
        assert "8-K" in p["forms"]
        assert "SC TO-I" in p["forms"]
        assert p["startdt"] == "2026-08-14"
        assert p["enddt"] == "2026-08-16"


def test_run_sweep_forms_overridable_by_spec():
    seen = []

    def fetch(params):
        seen.append(params)
        return {"hits": {"hits": []}}

    spec = dict(SPEC, forms="8-K")
    sweep.run_sweep("2026-08-14", "2026-08-16", spec=spec, fetch=fetch)
    assert seen and all(p["forms"] == "8-K" for p in seen)


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


def test_default_fetch_retries_intermittent_500(monkeypatch):
    # FTS 500s intermittently; one flaky family query must not kill the run.
    calls = {"n": 0}

    def flaky(url, params=None, timeout=20.0):
        calls["n"] += 1
        if calls["n"] < 3:
            resp = requests.Response()
            resp.status_code = 500
            raise requests.HTTPError("500 Server Error", response=resp)
        return json.dumps({"hits": {"hits": []}})

    monkeypatch.setattr(sweep.edgar, "http_get", flaky)
    monkeypatch.setattr(sweep.time, "sleep", lambda s: None)
    assert sweep._default_fetch({"q": '"x"'}) == {"hits": {"hits": []}}
    assert calls["n"] == 3


def test_default_fetch_gives_up_after_bounded_tries(monkeypatch):
    def always_500(url, params=None, timeout=20.0):
        resp = requests.Response()
        resp.status_code = 500
        raise requests.HTTPError("500 Server Error", response=resp)

    monkeypatch.setattr(sweep.edgar, "http_get", always_500)
    monkeypatch.setattr(sweep.time, "sleep", lambda s: None)
    with pytest.raises(requests.HTTPError):
        sweep._default_fetch({"q": '"x"'})


def test_default_fetch_does_not_retry_4xx(monkeypatch):
    calls = {"n": 0}

    def forbidden(url, params=None, timeout=20.0):
        calls["n"] += 1
        resp = requests.Response()
        resp.status_code = 403
        raise requests.HTTPError("403 Forbidden", response=resp)

    monkeypatch.setattr(sweep.edgar, "http_get", forbidden)
    with pytest.raises(requests.HTTPError):
        sweep._default_fetch({"q": '"x"'})
    assert calls["n"] == 1
