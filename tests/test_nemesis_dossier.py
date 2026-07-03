"""Tests for nemesis.dossier — the Form 10 dossier schema and honesty gate.

The validation gates are the product here: a sloppy or over-bullish LLM read
must fail loudly, and a skeptical read with the same numbers must pass. So
each gate gets its own violation test, plus the asymmetry test that defines
the gate's spirit ("own" rejected, "watch" with identical numbers accepted).
"""

import json
import os

import pytest

from nemesis.dossier import (
    SpinDossier,
    load_dossiers,
    make_dossier,
    save_dossiers,
    validate,
)

# A fully articulated, gate-clearing "own" dossier. Tests copy and break it.
VALID = dict(
    symbol="SPNC",
    parent="PRNT",
    cik="0001234567",
    form10_url="https://www.sec.gov/Archives/edgar/data/1234567/form10.htm",
    distribution_date="2026-06-15",
    incentive_alignment=0.7,
    garbage_barge_risk=0.3,
    neglect=0.8,
    forced_seller_map="S&P 500 index funds must sell; parent holders exit small-cap.",
    pro_forma_notes="Pro formas exclude one-time separation costs of $40M.",
    bull_case="Clean balance sheet, CEO holds 5% equity, index selling done by August.",
    bear_case="Single customer is 40% of revenue and the contract reprices in 2027.",
    key_risk="Customer concentration: losing the anchor contract halves revenue.",
    verdict="own",
    conviction=0.6,
    expected_rerating_months=5,
    researched_at="2026-07-02",
)


def _dossier(**overrides) -> SpinDossier:
    return SpinDossier(**{**VALID, **overrides})


# ---------------------------------------------------------------- validity


def test_valid_dossier_passes():
    assert validate(_dossier()) == []


def test_make_dossier_returns_instance():
    d = make_dossier(**VALID)
    assert isinstance(d, SpinDossier)
    assert d.symbol == "SPNC"
    assert d.verdict == "own"


def test_defaults_are_skeptical():
    """Untouched knobs must read as 'assume the worst until the filing says otherwise'."""
    d = SpinDossier(symbol="X", parent="Y")
    assert d.incentive_alignment == 0.0
    assert d.garbage_barge_risk == 1.0
    assert d.verdict == "watch"


# ------------------------------------------------- each gate individually


@pytest.mark.parametrize("field", [
    "incentive_alignment", "garbage_barge_risk", "neglect", "conviction",
])
@pytest.mark.parametrize("bad", [-0.01, 1.01, 5.0])
def test_unit_fields_out_of_range(field, bad):
    problems = validate(_dossier(**{field: bad, "verdict": "watch"}))
    assert any(field in p for p in problems), problems


def test_bad_verdict():
    problems = validate(_dossier(verdict="buy"))
    assert any("verdict" in p for p in problems)


@pytest.mark.parametrize("bad", [0, 13, -1, 6.5])
def test_rerating_months_out_of_range(bad):
    problems = validate(_dossier(expected_rerating_months=bad))
    assert any("expected_rerating_months" in p for p in problems)


@pytest.mark.parametrize("field", ["symbol", "parent", "researched_at"])
def test_required_identity_fields_nonempty(field):
    problems = validate(_dossier(**{field: ""}))
    assert any(field in p for p in problems)
    # Whitespace-only is just as unattributable as empty.
    problems = validate(_dossier(**{field: "   "}))
    assert any(field in p for p in problems)


@pytest.mark.parametrize("field", [
    "bull_case", "bear_case", "key_risk", "forced_seller_map",
])
def test_prose_fields_must_be_articulated(field):
    problems = validate(_dossier(**{field: "n/a"}))
    assert any(field in p for p in problems), problems


def test_all_problems_reported_at_once():
    """One pass must surface every problem, not just the first."""
    problems = validate(_dossier(symbol="", bear_case="no", conviction=2.0))
    assert len(problems) >= 3


# -------------------------------------------- the Greenblatt "own" gates


def test_own_with_low_incentive_alignment_rejected():
    problems = validate(_dossier(incentive_alignment=0.2))
    assert any("incentive_alignment" in p for p in problems)


def test_own_with_high_garbage_barge_rejected():
    problems = validate(_dossier(garbage_barge_risk=0.9))
    assert any("garbage_barge_risk" in p for p in problems)


def test_watch_with_same_failing_numbers_accepted():
    """The gate blocks over-bullish 'own', not skeptical observation."""
    d = _dossier(incentive_alignment=0.2, garbage_barge_risk=0.9, verdict="watch")
    assert validate(d) == []


def test_avoid_with_same_failing_numbers_accepted():
    d = _dossier(incentive_alignment=0.2, garbage_barge_risk=0.9, verdict="avoid")
    assert validate(d) == []


def test_own_at_exact_thresholds_accepted():
    d = _dossier(incentive_alignment=0.5, garbage_barge_risk=0.6)
    assert validate(d) == []


def test_make_dossier_raises_with_joined_problems():
    with pytest.raises(ValueError) as exc:
        make_dossier(**{**VALID, "incentive_alignment": 0.1, "bear_case": ""})
    msg = str(exc.value)
    assert "; " in msg
    assert "incentive_alignment" in msg
    assert "bear_case" in msg


# --------------------------------------------------------- persistence


def test_roundtrip(tmp_path):
    path = str(tmp_path / "nemesis_dossiers.json")
    d1 = make_dossier(**VALID)
    d2 = make_dossier(**{**VALID, "symbol": "OTHR", "verdict": "watch",
                         "incentive_alignment": 0.1})
    save_dossiers(path, [d1, d2])
    loaded = load_dossiers(path)
    assert loaded == [d1, d2]


def test_saved_shape_is_dossiers_key(tmp_path):
    path = str(tmp_path / "nemesis_dossiers.json")
    save_dossiers(path, [make_dossier(**VALID)])
    with open(path) as f:
        raw = json.load(f)
    assert set(raw.keys()) == {"dossiers"}
    assert raw["dossiers"][0]["symbol"] == "SPNC"


def test_save_does_not_leave_tmp_file(tmp_path):
    path = str(tmp_path / "nemesis_dossiers.json")
    save_dossiers(path, [make_dossier(**VALID)])
    assert not os.path.exists(path + ".tmp")


def test_missing_file_returns_empty_list(tmp_path):
    assert load_dossiers(str(tmp_path / "does_not_exist.json")) == []


def test_load_ignores_unknown_keys(tmp_path):
    """Forward compat: files written by a newer schema must still load."""
    path = str(tmp_path / "nemesis_dossiers.json")
    record = {**VALID, "some_future_field": 42, "another": {"nested": True}}
    with open(path, "w") as f:
        json.dump({"dossiers": [record]}, f)
    loaded = load_dossiers(path)
    assert len(loaded) == 1
    assert loaded[0].symbol == "SPNC"
    assert not hasattr(loaded[0], "some_future_field")


def test_save_creates_parent_directory(tmp_path):
    path = str(tmp_path / "deep" / "nested" / "dossiers.json")
    save_dossiers(path, [])
    assert load_dossiers(path) == []
