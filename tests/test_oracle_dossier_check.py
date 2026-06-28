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


def test_drawdown_from_high():
    from oracle.dossier_check import drawdown_from_high
    assert drawdown_from_high(50.0, 100.0) == 0.5
    assert drawdown_from_high(100.0, 100.0) == 0.0
    assert drawdown_from_high(50.0, 0) == 0.0   # missing high -> no flag
    assert drawdown_from_high(0, 100.0) == 0.0


def test_falling_knife_requires_decline_explanation():
    from oracle.research import make_dossier
    from oracle.dossier_check import DossierError
    kw = dict(
        symbol="FISV", business="payments", thesis="cheap compounder, insiders buying",
        scenarios={"bull": {"target": 78, "probability": 0.25},
                   "base": {"target": 62, "probability": 0.55},
                   "bear": {"target": 36, "probability": 0.20}},
        ratings={"moat": 0.75, "runway": 0.65, "quality": 0.73, "management": 0.72},
        citations=["acc-1"], current_price=49.0, high_52w=176.0,  # down ~72%
    )
    # No decline explanation -> falling-knife gate rejects it.
    try:
        make_dossier(**kw)
        assert False, "expected DossierError for unexplained falling knife"
    except DossierError as e:
        assert "falling-knife" in str(e)
    # With a substantive decline explanation -> valid, and drawdown recorded.
    d = make_dossier(**kw, decline_explanation=(
        "Down 72% after Oct-2025 guidance cut: organic growth slashed 10%->4%, new "
        "CEO admitted prior growth was misleading (Argentina FX), securities-fraud "
        "suit over Clover claims, organic revenue now negative."))
    assert d["drawdown_from_high"] > 0.7


def test_no_high_52w_does_not_flag():
    # Backward compatible: dossiers without 52-wk high data aren't gated.
    from oracle.research import make_dossier
    d = make_dossier(
        symbol="OK", business="b", thesis="t",
        scenarios={"bull": {"target": 150, "probability": 0.3},
                   "base": {"target": 100, "probability": 0.5},
                   "bear": {"target": 60, "probability": 0.2}},
        ratings={"moat": 0.7, "runway": 0.7, "quality": 0.7, "management": 0.7},
        citations=["c"], current_price=100.0,
    )
    assert d["drawdown_from_high"] == 0.0
