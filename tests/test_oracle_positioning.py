import math

import pytest

from oracle.positioning import (
    compute_derived,
    potential_to_conviction,
    rotation_decision,
    size_book,
)


def _dossier(bull=150, base=100, bear=50, p=(0.3, 0.5, 0.2), ratings=None):
    return {
        "scenarios": {
            "bull": {"target": bull, "probability": p[0]},
            "base": {"target": base, "probability": p[1]},
            "bear": {"target": bear, "probability": p[2]},
        },
        "ratings": ratings or {"moat": 0.7, "runway": 0.7, "quality": 0.7, "management": 0.7},
    }


def test_expected_price():
    d = _dossier()
    out = compute_derived(d, current_price=100.0, horizon_years=2.0)
    expected = 0.3 * 150 + 0.5 * 100 + 0.2 * 50
    assert out["expected_price"] == pytest.approx(expected)


def test_expected_return():
    d = _dossier()
    out = compute_derived(d, current_price=100.0)
    expected = (0.3 * 150 + 0.5 * 100 + 0.2 * 50) / 100 - 1
    assert out["expected_return"] == pytest.approx(expected)


def test_expected_cagr_two_years():
    d = _dossier(bull=200, base=150, bear=100, p=(0.5, 0.3, 0.2))
    out = compute_derived(d, current_price=100.0, horizon_years=2.0)
    # Expected price = 100 + 45 + 20 = 165; return = 0.65 over 2 years
    # CAGR = 1.65^0.5 - 1 = ~0.2845
    assert out["expected_cagr"] == pytest.approx(math.sqrt(1.65) - 1, rel=1e-6)


def test_expected_cagr_zero_horizon():
    d = _dossier()
    out = compute_derived(d, current_price=100.0, horizon_years=0)
    # falls back to expected_return
    assert out["expected_cagr"] == pytest.approx(out["expected_return"])


def test_asymmetry_favorable():
    # bull 200, p_up 0.5 -> upside_ev = 50; bear 80, p_down 0.2 -> down_ev = 4
    d = _dossier(bull=200, base=100, bear=80, p=(0.5, 0.3, 0.2))
    out = compute_derived(d, current_price=100.0)
    # upside = 100 * 0.5 = 50; downside = 20 * 0.2 = 4; asym = 12.5
    assert out["asymmetry"] == pytest.approx(50 / 4)


def test_asymmetry_no_downside():
    # bear target = current -> downside = 0
    d = _dossier(bull=200, base=100, bear=100, p=(0.3, 0.5, 0.2))
    out = compute_derived(d, current_price=100.0)
    assert out["asymmetry"] == 10.0  # capped sentinel


def test_quality_mult_range():
    d = _dossier(ratings={"moat": 1.0, "runway": 1.0, "quality": 1.0, "management": 1.0})
    out = compute_derived(d, current_price=100.0)
    assert out["quality_mult"] == 1.5
    d = _dossier(ratings={"moat": 0.0, "runway": 0.0, "quality": 0.0, "management": 0.0})
    out = compute_derived(d, current_price=100.0)
    assert out["quality_mult"] == 0.5


def test_asymmetry_mult_capped():
    d = _dossier(bull=1000, base=200, bear=99, p=(0.5, 0.3, 0.2))
    out = compute_derived(d, current_price=100.0)
    assert out["asymmetry_mult"] <= 2.0


def test_potential_score_combined():
    d = _dossier(bull=200, base=120, bear=90, p=(0.4, 0.4, 0.2))
    out = compute_derived(d, current_price=100.0, horizon_years=1.0)
    # Just sanity that it's positive when expected_return is positive
    assert out["expected_return"] > 0
    assert out["potential_score"] > 0


def test_zero_current_price():
    d = _dossier()
    out = compute_derived(d, current_price=0)
    assert out["potential_score"] == 0


def test_conviction_zero():
    assert potential_to_conviction(0) == 0.0
    assert potential_to_conviction(-1) == 0.0


def test_conviction_bounded():
    assert 0 < potential_to_conviction(0.1) < 1
    # large input asymptotes to 1.0
    assert potential_to_conviction(100) <= 1.0
    assert potential_to_conviction(100) > 0.99


def test_size_book_basic():
    # With 7 names spread across sectors, we can fully use the 90% invested target.
    scored = [
        {"symbol": f"S{i}", "conviction": 0.7, "sector": f"sec{i}"} for i in range(7)
    ]
    targets = size_book(scored, equity=10_000.0)
    total = sum(targets.values())
    assert total <= 9_000.0 + 1e-6  # 90% cap
    assert total > 8_500.0  # close to 90% utilization


def test_size_book_two_names_capped_to_per_name():
    # With only 2 names, each hits the 15% per-name cap. Total = 30%.
    scored = [
        {"symbol": "A", "conviction": 0.8, "sector": "tech"},
        {"symbol": "B", "conviction": 0.5, "sector": "finance"},
    ]
    targets = size_book(scored, equity=1000.0)
    for sym, dollars in targets.items():
        assert dollars <= 150.0 + 1e-6


def test_size_book_per_name_cap():
    scored = [{"symbol": "A", "conviction": 1.0, "sector": "tech"}]
    targets = size_book(scored, equity=1000.0)
    # 15% cap on one name = $150
    assert targets.get("A", 0) <= 150.0 + 1e-6


def test_size_book_sector_cap():
    scored = [
        {"symbol": "A", "conviction": 0.9, "sector": "tech"},
        {"symbol": "B", "conviction": 0.9, "sector": "tech"},
        {"symbol": "C", "conviction": 0.9, "sector": "tech"},
        {"symbol": "D", "conviction": 0.9, "sector": "tech"},
    ]
    targets = size_book(scored, equity=10_000.0)
    tech_total = sum(v for k, v in targets.items())
    # Sector cap 35% of $10k = $3500
    assert tech_total <= 3500.0 + 1e-6


def test_size_book_drops_below_min_ticket():
    scored = [{"symbol": "A", "conviction": 0.0001, "sector": "tech"}]
    targets = size_book(scored, equity=1000.0)
    assert "A" not in targets or targets["A"] >= 50.0


def test_size_book_empty():
    assert size_book([], equity=1000.0) == {}


def test_rotation_decision_below_margin():
    assert rotation_decision(1.0, 1.1) is False  # only 10% above


def test_rotation_decision_above_margin():
    assert rotation_decision(1.0, 1.3) is True  # 30% above


def test_rotation_decision_no_incumbent():
    assert rotation_decision(0, 0.1) is True
    assert rotation_decision(0, 0) is False
