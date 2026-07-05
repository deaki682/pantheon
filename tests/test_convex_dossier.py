import pytest

from oracle.convex_dossier import (make_convex_dossier, asymmetry_score,
                                   rank_by_asymmetry, ConvexDossierError)


def _good(**over):
    kw = dict(
        symbol="abc", business="a neglected regional bank",
        thesis=("Trades at 0.6x tangible book after a forced index deletion dumped the "
                "float; the deposit base is stable and a pending branch sale crystallizes "
                "book value that indexers ignored on the way out."),
        floor_pct=0.20, upside_x=1.8, prob_upside=0.5,
        why_mispriced_type="forced_seller",
        why_mispriced="dropped from the Russell 2000 in June; index funds sold indiscriminately into a coverage-free float",
        catalyst="announced branch-network sale expected to close Q4",
        catalyst_date="2026-12-15",
        falsifiable_prediction="re-rates to >=0.85x TBV within 9 months of the sale close",
        prediction_date="2027-06-30",
        kill_condition="the branch sale is terminated", kill_condition_type="filing_event",
        kill_condition_value="8-K deal-termination", adversarial=(
            "The house knows forced-flow effects are largely arbitraged (Greenwood-Sammon); "
            "the bet rests on this being below arb-fund size, which must be verified."),
        citations=["10-K 2025", "Russell recon list"], current_price=9.5, spy_price=500.0,
        lens_score=0.7,
    )
    kw.update(over)
    return make_convex_dossier(**{k: kw.pop(k) for k in ("symbol",)}, **kw)


def test_asymmetry_score_math():
    # 50% shot at +80%, else -20%: 0.5*0.8 - 0.5*0.2 = 0.30
    assert asymmetry_score(0.20, 1.8, 0.5) == pytest.approx(0.30)


def test_builds_and_scores():
    d = _good()
    assert d["spec"] == "convex" and d["symbol"] == "ABC"
    assert d["asymmetry_score"] == pytest.approx(0.30)
    assert d["convex"] is True


def test_requires_floor():
    with pytest.raises(ConvexDossierError):
        _good(floor_pct=0.0)          # no floor = not an Oracle name
    with pytest.raises(ConvexDossierError):
        _good(floor_pct=1.5)


def test_requires_structural_mispricing_type():
    with pytest.raises(ConvexDossierError):
        _good(why_mispriced_type="the market underappreciates it")


def test_requires_typed_kill():
    with pytest.raises(ConvexDossierError):
        _good(kill_condition_type="vibes")


def test_requires_adversarial():
    with pytest.raises(ConvexDossierError):
        _good(adversarial="looks fine")   # too short


def test_dead_trigger_flag():
    d = _good(thesis=("Insiders bought heavily and the quality lens is strong and it trades cheap; "
                      "a forced index deletion also dumped the float creating a structural discount here."))
    assert d["dead_trigger_risk"] is True   # flagged, not rejected — the reviewer sees it


def test_rank_by_asymmetry_convex_only():
    hi = _good(symbol="HI", upside_x=2.5, prob_upside=0.5, floor_pct=0.2)   # score 0.65
    lo = _good(symbol="LO", upside_x=1.6, prob_upside=0.5, floor_pct=0.2)   # score 0.20
    flat = _good(symbol="FLAT", upside_x=1.2, prob_upside=0.4, floor_pct=0.3)  # score -0.10, not convex
    ranked = rank_by_asymmetry([lo, flat, hi])
    assert [d["symbol"] for d in ranked] == ["HI", "LO"]   # FLAT dropped (non-convex)
