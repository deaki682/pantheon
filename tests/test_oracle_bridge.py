import json
import os
import pytest

from achilles.oracle_bridge import (
    QUALITY_DEFAULT,
    company_quality,
    has_insider_preactivity,
    load_dossier_convictions,
    load_insider_activity,
    load_prescreener_quality,
    load_screen_scores,
    _quality_from_snapshot,
)


# ── company_quality ──────────────────────────────────────────────────


def test_quality_dossier_only():
    q = company_quality("ACME", dossier_convictions={"ACME": 0.85}, prescreener_quality={})
    assert q == pytest.approx(0.85)


def test_quality_prescreener_only():
    q = company_quality("ACME", dossier_convictions={}, prescreener_quality={"ACME": 0.6})
    assert q == pytest.approx(0.6)


def test_quality_both_blended():
    q = company_quality(
        "ACME",
        dossier_convictions={"ACME": 0.9},
        prescreener_quality={"ACME": 0.7},
    )
    assert q == pytest.approx(0.6 * 0.9 + 0.4 * 0.7)


def test_quality_screen_fallback():
    q = company_quality(
        "ACME",
        dossier_convictions={},
        prescreener_quality={},
        screen_scores={"ACME": {"score": 0.75}},
    )
    assert q == pytest.approx(0.75)


def test_quality_screen_floor():
    q = company_quality(
        "ACME",
        dossier_convictions={},
        prescreener_quality={},
        screen_scores={"ACME": {"score": 0.3}},
    )
    assert q == pytest.approx(0.5)


def test_quality_unknown_default():
    q = company_quality("UNKNOWN", dossier_convictions={}, prescreener_quality={})
    assert q == QUALITY_DEFAULT


def test_quality_case_insensitive():
    q = company_quality("acme", dossier_convictions={"ACME": 0.8}, prescreener_quality={})
    assert q == pytest.approx(0.8)


# ── has_insider_preactivity ──────────────────────────────────────────


def test_insider_preactivity_present():
    activity = {"ACME": {"latest_date": "2024-05-25", "insider_count": 3}}
    has, boost = has_insider_preactivity(
        "ACME", insider_activity=activity, filing_date="2024-05-29"
    )
    assert has is True
    assert boost > 1.0


def test_insider_preactivity_absent():
    has, boost = has_insider_preactivity(
        "ACME", insider_activity={}, filing_date="2024-05-29"
    )
    assert has is False
    assert boost == 1.0


def test_insider_preactivity_no_date():
    activity = {"ACME": {"insider_count": 2}}
    has, boost = has_insider_preactivity(
        "ACME", insider_activity=activity, filing_date="2024-05-29"
    )
    assert has is True
    assert boost == pytest.approx(1.15)


def test_insider_preactivity_too_old():
    activity = {"ACME": {"latest_date": "2024-04-01", "insider_count": 3}}
    has, boost = has_insider_preactivity(
        "ACME", insider_activity=activity, filing_date="2024-05-29"
    )
    assert has is False
    assert boost == 1.0


def test_insider_boost_scales_with_count():
    activity = {"ACME": {"latest_date": "2024-05-27", "insider_count": 5}}
    _, boost_5 = has_insider_preactivity(
        "ACME", insider_activity=activity, filing_date="2024-05-29"
    )
    activity["ACME"]["insider_count"] = 2
    _, boost_2 = has_insider_preactivity(
        "ACME", insider_activity=activity, filing_date="2024-05-29"
    )
    assert boost_5 > boost_2
    assert boost_5 <= 1.5


# ── _quality_from_snapshot ───────────────────────────────────────────


def test_quality_from_snapshot_full():
    snap = {
        "gross_margin_ttm": 0.4,
        "operating_margin_ttm": 0.15,
        "revenue_ttm": 1e9,
        "free_cash_flow_ttm": 1.5e8,
        "revenue_yoy": 0.2,
        "dilution_yoy": 0.01,
    }
    q = _quality_from_snapshot(snap)
    assert q is not None
    assert 0 <= q <= 1.0


def test_quality_from_snapshot_empty():
    assert _quality_from_snapshot({}) is None


def test_quality_from_snapshot_sparse_penalized():
    snap_one = {"gross_margin_ttm": 0.5}
    snap_full = {
        "gross_margin_ttm": 0.5,
        "operating_margin_ttm": 0.2,
        "revenue_yoy": 0.25,
    }
    q_one = _quality_from_snapshot(snap_one)
    q_full = _quality_from_snapshot(snap_full)
    assert q_one < q_full


# ── load functions with temp files ───────────────────────────────────


def test_load_dossier_convictions_list_format(tmp_path):
    data = [{"symbol": "ACME", "conviction": 0.85}, {"symbol": "XYZ", "conviction": 0.6}]
    p = tmp_path / "dossiers.json"
    p.write_text(json.dumps(data))
    result = load_dossier_convictions(str(p))
    assert result == {"ACME": 0.85, "XYZ": 0.6}


def test_load_dossier_convictions_dict_format(tmp_path):
    data = {"dossiers": [{"symbol": "ACME", "conviction": 0.9}]}
    p = tmp_path / "dossiers.json"
    p.write_text(json.dumps(data))
    result = load_dossier_convictions(str(p))
    assert result == {"ACME": 0.9}


def test_load_dossier_convictions_missing_file():
    result = load_dossier_convictions("/nonexistent/path.json")
    assert result == {}


def test_load_insider_activity(tmp_path):
    data = {"clusters": [{"symbol": "ACME", "insider_count": 3, "latest_date": "2024-05-29"}]}
    p = tmp_path / "insiders.json"
    p.write_text(json.dumps(data))
    result = load_insider_activity(str(p))
    assert "ACME" in result
    assert result["ACME"]["insider_count"] == 3


def test_load_screen_scores(tmp_path):
    data = {"top": [{"symbol": "ACME", "score": 0.8, "lenses": {}}]}
    p = tmp_path / "screen.json"
    p.write_text(json.dumps(data))
    result = load_screen_scores(str(p))
    assert "ACME" in result
    assert result["ACME"]["score"] == 0.8
