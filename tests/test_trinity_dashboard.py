import json
import os

import pytest

import trinity_dashboard as td


def test_build_html_empty(tmp_path):
    html = td.build_html(cache_dir=str(tmp_path))
    assert "<!doctype html>" in html
    assert "Trinity" in html
    # All three colors should appear
    assert "#D4AF37" in html
    assert "#9C27B0" in html
    assert "#00BCD4" in html


def test_build_html_with_curves(tmp_path):
    for god in ("oracle", "delphi", "achilles"):
        with open(tmp_path / f"{god}_curve.json", "w") as f:
            json.dump([{"date": "2024-05-29", "equity": 1000.0}], f)
    html = td.build_html(cache_dir=str(tmp_path))
    assert "1000" in html
    assert "Oracle" in html and "Delphi" in html and "Achilles" in html


def test_write_dashboard(tmp_path):
    out = tmp_path / "dash.html"
    td.write_dashboard(str(out), cache_dir=str(tmp_path))
    assert out.exists()
    content = out.read_text()
    assert "<!doctype html>" in content


def test_append_curve_point(tmp_path):
    td.append_curve_point(str(tmp_path), "oracle", equity=1234.5, date="2024-05-29")
    with open(tmp_path / "oracle_curve.json") as f:
        pts = json.load(f)
    assert pts[-1]["equity"] == 1234.5


def test_append_curve_point_overwrites_same_day(tmp_path):
    td.append_curve_point(str(tmp_path), "oracle", equity=1000, date="2024-05-29")
    td.append_curve_point(str(tmp_path), "oracle", equity=1100, date="2024-05-29")
    with open(tmp_path / "oracle_curve.json") as f:
        pts = json.load(f)
    assert len(pts) == 1
    assert pts[0]["equity"] == 1100


def test_load_curve_handles_dict_payload(tmp_path):
    with open(tmp_path / "oracle_curve.json", "w") as f:
        json.dump({"points": [{"date": "2024-05-29", "equity": 1000}]}, f)
    pts = td._load_curve(str(tmp_path / "oracle_curve.json"))
    assert len(pts) == 1


def test_load_curve_missing(tmp_path):
    assert td._load_curve(str(tmp_path / "missing.json")) == []
