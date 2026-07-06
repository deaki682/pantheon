import math

import pytest

from oracle.positioning import (
    compute_derived,
    potential_to_conviction,
    rotation_decision,
    size_book,
    topup_targets,
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
    # With only 2 names, each hits the 25% per-name cap. Total = 50%.
    scored = [
        {"symbol": "A", "conviction": 0.8, "sector": "tech"},
        {"symbol": "B", "conviction": 0.5, "sector": "finance"},
    ]
    targets = size_book(scored, equity=1000.0)
    for sym, dollars in targets.items():
        assert dollars <= 250.0 + 1e-6


def test_size_book_per_name_cap():
    scored = [{"symbol": "A", "conviction": 1.0, "sector": "tech"}]
    targets = size_book(scored, equity=1000.0)
    # 25% cap on one name = $250
    assert targets.get("A", 0) <= 250.0 + 1e-6


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


def test_size_book_selects_best_from_large_set():
    # 200 ranked candidates: must pick the top handful and fund them, not
    # dilute the budget below min-ticket and return nothing.
    scored = [
        {"symbol": f"S{i}", "conviction": max(0.05, 0.99 - i * 0.0045), "sector": f"sec{i % 8}"}
        for i in range(200)
    ]
    targets = size_book(scored, equity=1000.0)
    assert 5 <= len(targets) <= 15  # a real book, not empty
    # Every funded name clears the min ticket.
    assert all(v >= 50.0 for v in targets.values())
    # The names chosen are the highest-conviction ones (low indices).
    assert max(int(s[1:]) for s in targets) < 30


def test_size_book_caps_positions_at_max():
    scored = [
        {"symbol": f"S{i}", "conviction": 0.9, "sector": f"sec{i}"} for i in range(40)
    ]
    targets = size_book(scored, equity=100_000.0, max_positions=15)
    assert len(targets) <= 15


def test_size_book_small_equity_holds_fewer_not_empty():
    # A smaller book funds fewer names than a big one — pick the best, don't
    # dilute a large candidate set to zero. ($500 -> ~$450 investable, ~9 @ $50.)
    scored = [
        {"symbol": f"S{i}", "conviction": max(0.1, 0.9 - i * 0.02), "sector": f"s{i}"}
        for i in range(50)
    ]
    targets = size_book(scored, equity=500.0)
    assert 0 < len(targets) <= 9  # fewer than the 15-name cap, but not empty
    assert all(v >= 50.0 for v in targets.values())
    assert max(int(s[1:]) for s in targets) < 12  # the best-conviction names


def test_size_book_filters_megacaps():
    scored = [
        {"symbol": "MEGA", "conviction": 0.95, "sector": "tech", "market_cap": 500_000_000_000},
        {"symbol": "MID", "conviction": 0.80, "sector": "health", "market_cap": 10_000_000_000},
        {"symbol": "SMALL", "conviction": 0.70, "sector": "energy", "market_cap": 2_000_000_000},
    ]
    targets = size_book(scored, equity=10_000.0)
    assert "MEGA" not in targets
    assert "MID" in targets
    assert "SMALL" in targets


def test_size_book_no_mcap_passes_through():
    scored = [
        {"symbol": "OLD", "conviction": 0.80, "sector": "tech"},
        {"symbol": "NEW", "conviction": 0.70, "sector": "health", "market_cap": 5_000_000_000},
    ]
    targets = size_book(scored, equity=10_000.0)
    assert "OLD" in targets
    assert "NEW" in targets


def test_size_book_half_tier_gets_less():
    """Half-tier names get ~50% the weight of full-tier names."""
    scored = [
        {"symbol": "F1", "conviction": 0.8, "sector": "s1", "insider_tier": "full"},
        {"symbol": "F2", "conviction": 0.8, "sector": "s2", "insider_tier": "full"},
        {"symbol": "F3", "conviction": 0.8, "sector": "s3", "insider_tier": "full"},
        {"symbol": "H1", "conviction": 0.8, "sector": "s4", "insider_tier": "half"},
    ]
    targets = size_book(scored, equity=10_000.0)
    assert targets["F1"] > targets["H1"] * 1.5


def test_size_book_none_tier_excluded():
    scored = [
        {"symbol": "OK", "conviction": 0.8, "sector": "tech", "insider_tier": "full"},
        {"symbol": "NO", "conviction": 0.9, "sector": "health", "insider_tier": "none"},
    ]
    targets = size_book(scored, equity=10_000.0)
    assert "OK" in targets
    assert "NO" not in targets


def test_topup_targets_equal_weight():
    targets = topup_targets(["A", "B", "C", "D", "E", "F", "G", "H"], equity=2000.0)
    assert len(targets) == 8
    per_name = 2000.0 * 0.9 / 8  # $225 each, under 25% cap
    assert all(v == pytest.approx(per_name) for v in targets.values())


def test_topup_targets_respects_per_name_cap():
    targets = topup_targets(["A"], equity=2000.0)
    assert targets["A"] <= 500.0 + 1e-6


def test_topup_targets_empty():
    assert topup_targets([], equity=2000.0) == {}


def test_topup_targets_zero_equity():
    assert topup_targets(["A"], equity=0) == {}


def test_rotation_decision_below_margin():
    assert rotation_decision(1.0, 1.1) is False  # only 10% above


def test_rotation_decision_above_margin():
    assert rotation_decision(1.0, 1.3) is True  # 30% above


def test_rotation_decision_no_incumbent():
    assert rotation_decision(0, 0.1) is True
    assert rotation_decision(0, 0) is False


def test_per_name_cap_scales_with_floor_hardness():
    """The largest bet must be the hardest-floored: a hard floor may reach the
    full 25% cap; a soft floor is capped proportionally lower (0.45x), even at
    identical conviction. This is what makes concentration a bounded option."""
    equity = 10000.0
    scored = [
        {"symbol": "HARD", "conviction": 0.9, "sector": "A", "floor_hardness": "hard"},
        {"symbol": "SOFT", "conviction": 0.9, "sector": "B", "floor_hardness": "soft"},
    ]
    t = size_book(scored, equity)
    # hard reaches the full per-name cap (25%); soft is capped at 0.45x (11.25%)
    assert t["HARD"] == pytest.approx(0.25 * equity, rel=1e-3)
    assert t["SOFT"] == pytest.approx(0.45 * 0.25 * equity, rel=1e-3)
    assert t["HARD"] > t["SOFT"]


def test_missing_floor_hardness_keeps_full_cap():
    """Legacy / non-convex names (no floor concept) keep the full 25% cap — only a
    DECLARED softer floor is scaled down, so this change is non-disruptive."""
    equity = 10000.0
    scored = [{"symbol": "X", "conviction": 0.9, "sector": "A"}]  # no floor_hardness
    t = size_book(scored, equity)
    assert t["X"] == pytest.approx(0.25 * equity, rel=1e-3)
