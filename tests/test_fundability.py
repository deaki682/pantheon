"""Fundability prior — pure-logic tests (2026-07-06). Guards the six bugs the
ad-hoc bash ranker shipped: asset-reval discount blindness, net-cash budget
monopoly, and the field-shape mismatches that produce them."""
from oracle import fundability as fb


def test_discount_read_from_floor_usd():
    c = {"ticker": "A", "marketcap_usd": 60e6, "floor_usd": 100e6, "floor_type": "net_cash"}
    assert abs(fb.candidate_discount(c) - 0.40) < 1e-9


def test_asset_reval_discount_read_from_nav_at_cost():
    # THE FPH BUG: a land name carries its floor as nav_at_cost_usd, not floor_usd.
    # The prior must still see a discount, not None.
    fph = {"ticker": "FPH", "marketcap_usd": 775.2e6, "nav_at_cost_usd": 2991.1e6,
           "floor_type": None}
    d = fb.candidate_discount(fph)
    assert d is not None and abs(d - (1 - 775.2 / 2991.1)) < 1e-3
    assert fb.candidate_discount(fph) > 0.70          # deep land-NAV discount, seen


def test_asset_reval_discount_from_coverage_fallback():
    c = {"ticker": "B", "asset_coverage": 4.0}        # only coverage, no nav/floor
    assert abs(fb.candidate_discount(c) - 0.75) < 1e-9


def test_discount_score_sweet_spot_and_trap_decay():
    assert fb.discount_score(0.45) == 1.0             # sweet spot
    assert fb.discount_score(0.10) < 1.0              # below sweet spot ramps down
    assert fb.discount_score(0.74) < 1.0              # caution band decays
    assert fb.discount_score(0.90) < 0.35             # trap zone penalized hard
    assert fb.discount_score(0.99) <= 0.15            # deep trap floored low
    assert fb.discount_score(None) == 0.0


def test_floor_weight_land_from_null_floor_type():
    # a null floor_type + nav_at_cost must still be weighted as land, not defaulted
    assert fb.floor_weight({"nav_at_cost_usd": 1e9}) == fb.FLOOR_W["asset_land"]
    assert fb.floor_weight({"floor_type": "net_cash"}) == 1.0


def test_clean_weight_erodes_on_freshness_flags():
    base = {"marketcap_usd": 100e6}
    assert fb.clean_weight(base) == 1.0
    assert fb.clean_weight({**base, "stale_marketcap": True}) == 0.5
    assert fb.clean_weight({**base, "crypto_treasury": True}) == 0.2
    assert fb.clean_weight({**base, "book_contradicts_floor": True}) == 0.4


def test_per_family_budget_gives_land_its_own_slots():
    # BUG 2: without per-family budgets the net-cash pile buries every land name.
    cands = (
        [{"ticker": f"NC{i}", "marketcap_usd": 60e6, "floor_usd": 100e6,
          "floor_type": "net_cash"} for i in range(12)]
        + [{"ticker": "LAND1", "marketcap_usd": 775e6, "nav_at_cost_usd": 2991e6,
            "floor_type": None}]
    )
    fams = fb.rank_by_family(cands, per_family=8)
    assert "land_nav" in fams and fams["land_nav"][0]["ticker"] == "LAND1"
    q = fb.verification_queue(cands, per_family=8)
    assert "LAND1" in [c["ticker"] for c in q]         # the land name reaches the queue


def test_family_classification_null_floor_is_land_when_nav_present():
    assert fb.candidate_family({"floor_type": None, "nav_at_cost_usd": 1e9}) == "land_nav"
    assert fb.candidate_family({"floor_type": "net_cash"}) == "net_cash"
    assert fb.candidate_family({"floor_type": "tangible_book"}) == "tangible_book"
