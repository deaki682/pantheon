import copy

import pytest

from oracle.dossier_check import DossierError, normalize_rating, validate_dossier


def _good_dossier():
    return {
        "symbol": "ACME",
        "scenarios": {
            "bull": {"target": 150.0, "probability": 0.3},
            "base": {"target": 100.0, "probability": 0.5},
            "bear": {"target": 50.0, "probability": 0.2},
        },
        "ratings": {"moat": 0.6, "runway": 0.7, "quality": 0.8, "management": 0.5},
        "citations": ["acc-1"],
    }


def test_normalize_rating_passthrough():
    assert normalize_rating(0.7) == 0.7


def test_normalize_rating_scale_from_ten():
    assert normalize_rating(7.0) == 0.7


def test_normalize_rating_clamp_high():
    assert normalize_rating(15) == 1.0


def test_normalize_rating_clamp_low():
    assert normalize_rating(-1) == 0.0


def test_normalize_rating_none():
    assert normalize_rating(None) == 0.0


def test_validate_good():
    d = _good_dossier()
    validate_dossier(d)
    # probabilities already sum to 1.0
    assert abs(sum(s["probability"] for s in d["scenarios"].values()) - 1.0) < 1e-9


def test_validate_auto_normalizes_probabilities():
    d = _good_dossier()
    d["scenarios"]["bull"]["probability"] = 0.6
    d["scenarios"]["base"]["probability"] = 1.0
    d["scenarios"]["bear"]["probability"] = 0.4  # sums to 2.0
    validate_dossier(d)
    assert sum(s["probability"] for s in d["scenarios"].values()) == pytest.approx(1.0)


def test_validate_scales_ratings():
    d = _good_dossier()
    d["ratings"] = {"moat": 6, "runway": 7, "quality": 8, "management": 5}
    validate_dossier(d)
    assert d["ratings"]["moat"] == 0.6
    assert d["ratings"]["quality"] == 0.8


def test_missing_citations_rejected():
    d = _good_dossier()
    d["citations"] = []
    with pytest.raises(DossierError):
        validate_dossier(d)


def test_missing_scenario_rejected():
    d = _good_dossier()
    del d["scenarios"]["bear"]
    with pytest.raises(DossierError):
        validate_dossier(d)


def test_extra_scenario_rejected():
    d = _good_dossier()
    d["scenarios"]["extreme"] = {"target": 200.0, "probability": 0.1}
    with pytest.raises(DossierError):
        validate_dossier(d)


def test_bull_lt_bear_rejected():
    d = _good_dossier()
    d["scenarios"]["bull"]["target"] = 30.0
    d["scenarios"]["bear"]["target"] = 50.0
    with pytest.raises(DossierError):
        validate_dossier(d)


def test_negative_target_rejected():
    d = _good_dossier()
    d["scenarios"]["bull"]["target"] = -10
    with pytest.raises(DossierError):
        validate_dossier(d)


def test_missing_rating_rejected():
    d = _good_dossier()
    del d["ratings"]["moat"]
    with pytest.raises(DossierError):
        validate_dossier(d)


def test_missing_symbol_rejected():
    d = _good_dossier()
    d["symbol"] = ""
    with pytest.raises(DossierError):
        validate_dossier(d)
