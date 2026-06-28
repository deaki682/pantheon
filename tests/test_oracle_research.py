from datetime import datetime, timedelta

import pytest

from oracle.research import (
    check_staleness,
    load_dossiers,
    make_dossier,
    price_age_hours,
    rank,
    rescore_dossier,
    save_dossiers,
    update_scenarios,
)


def _make(symbol="ACME", price=100, bull=150, bear=50):
    return make_dossier(
        symbol=symbol,
        business="widgets",
        thesis="undervalued widget maker",
        scenarios={
            "bull": {"target": bull, "probability": 0.3},
            "base": {"target": 100, "probability": 0.5},
            "bear": {"target": bear, "probability": 0.2},
        },
        ratings={"moat": 0.7, "runway": 0.7, "quality": 0.7, "management": 0.7},
        citations=["acc-1"],
        horizon_years=2.0,
        current_price=price,
        sector="industrials",
    )


def test_make_dossier_minimal():
    d = _make()
    assert d["symbol"] == "ACME"
    assert "derived" in d
    assert "conviction" in d
    assert 0 <= d["conviction"] <= 1


def test_make_dossier_uppercases_symbol():
    d = _make(symbol="acme")
    assert d["symbol"] == "ACME"


def test_make_dossier_validates():
    with pytest.raises(Exception):
        make_dossier(
            symbol="X",
            business="b",
            thesis="t",
            scenarios={"bull": {"target": 1, "probability": 1}},  # missing base/bear
            ratings={"moat": 0.5, "runway": 0.5, "quality": 0.5, "management": 0.5},
            citations=["c"],
        )


def test_going_concern_gate_blocks_without_explanation():
    from oracle.dossier_check import DossierError
    with pytest.raises(DossierError, match="going_concern"):
        make_dossier(
            symbol="RISKY",
            business="cash burner",
            thesis="speculative",
            scenarios={
                "bull": {"target": 200, "probability": 0.2},
                "base": {"target": 50, "probability": 0.3},
                "bear": {"target": 10, "probability": 0.5},  # 90% loss from $100
            },
            ratings={"moat": 0.3, "runway": 0.2, "quality": 0.3, "management": 0.4},
            citations=["acc-1"],
            current_price=100,
        )


def test_going_concern_gate_passes_with_explanation():
    d = make_dossier(
        symbol="RISKY",
        business="cash burner",
        thesis="speculative but explained",
        scenarios={
            "bull": {"target": 200, "probability": 0.2},
            "base": {"target": 50, "probability": 0.3},
            "bear": {"target": 10, "probability": 0.5},
        },
        ratings={"moat": 0.3, "runway": 0.2, "quality": 0.3, "management": 0.4},
        citations=["acc-1"],
        current_price=100,
        going_concern_explanation=(
            "Company has $200M cash with $50M quarterly burn, giving 4 quarters of runway. "
            "No debt covenants at risk. Refinancing likely given asset base."
        ),
    )
    assert d["symbol"] == "RISKY"


def test_going_concern_gate_skipped_when_runway_ok():
    d = make_dossier(
        symbol="SAFE",
        business="profitable",
        thesis="solid",
        scenarios={
            "bull": {"target": 200, "probability": 0.3},
            "base": {"target": 100, "probability": 0.5},
            "bear": {"target": 15, "probability": 0.2},  # 85% loss but runway is fine
        },
        ratings={"moat": 0.5, "runway": 0.6, "quality": 0.5, "management": 0.5},
        citations=["acc-1"],
        current_price=100,
    )
    assert d["symbol"] == "SAFE"


def test_rescore():
    d = _make(price=100)
    initial_conv = d["conviction"]
    # At a much higher price, expected return drops
    rescore_dossier(d, current_price=140.0)
    assert d["current_price"] == 140.0
    assert d["conviction"] != initial_conv


def test_rescore_rejects_malformed_dossier():
    # A dossier loaded from disk / hand-edited could be malformed; rescore must
    # fail loud with a clear DossierError, not a cryptic KeyError in the math.
    from oracle.dossier_check import DossierError
    d = _make()
    del d["ratings"]["moat"]
    with pytest.raises(DossierError):
        rescore_dossier(d, current_price=120.0)


def test_save_load_dossiers(tmp_path):
    p = tmp_path / "dossiers.json"
    d1 = _make("A")
    d2 = _make("B")
    save_dossiers(str(p), [d1, d2])
    loaded = load_dossiers(str(p))
    assert len(loaded) == 2
    assert {x["symbol"] for x in loaded} == {"A", "B"}


def test_load_dossiers_missing(tmp_path):
    assert load_dossiers(str(tmp_path / "missing.json")) == []


def test_make_dossier_stamps_priced_at():
    d = _make(price=100)
    assert d.get("priced_at"), "make_dossier with a real price must stamp priced_at"
    # priced_at should be ISO-parseable
    datetime.fromisoformat(d["priced_at"])


def test_make_dossier_without_price_has_null_priced_at():
    # If no price was captured, priced_at must be None so no reader mistakes
    # an unset field for a fresh price.
    d = make_dossier(
        symbol="X",
        business="b",
        thesis="t",
        scenarios={
            "bull": {"target": 1, "probability": 0.3},
            "base": {"target": 1, "probability": 0.5},
            "bear": {"target": 1, "probability": 0.2},
        },
        ratings={"moat": 0.5, "runway": 0.5, "quality": 0.5, "management": 0.5},
        citations=["c"],
        current_price=0.0,
    )
    assert d["priced_at"] is None


def test_rescore_refreshes_priced_at():
    d = _make(price=100)
    # Backdate priced_at to simulate a stale dossier.
    d["priced_at"] = "2020-01-01T00:00:00"
    rescore_dossier(d, current_price=110.0)
    assert d["priced_at"] != "2020-01-01T00:00:00"
    # Should be parseable and recent.
    captured = datetime.fromisoformat(d["priced_at"])
    assert (datetime.utcnow() - captured) < timedelta(seconds=60)


def test_update_scenarios_forces_fresh_price():
    # The whole point of update_scenarios: a rebalance pass that rewrites the
    # thesis MUST also refresh the price — otherwise priced_at drifts from
    # the scenarios it's supposed to be paired with.
    d = _make(price=100)
    old_priced_at = d["priced_at"]
    d["priced_at"] = "2020-01-01T00:00:00"  # backdate to simulate staleness

    new_scenarios = {
        "bull": {"target": 200, "probability": 0.4},
        "base": {"target": 120, "probability": 0.4},
        "bear": {"target": 60, "probability": 0.2},
    }
    update_scenarios(d, new_scenarios, current_price=105.0)

    assert d["scenarios"]["bull"]["target"] == 200
    assert d["current_price"] == 105.0
    assert d["priced_at"] != "2020-01-01T00:00:00"
    assert d["priced_at"] != old_priced_at
    # Caller cannot omit current_price — it's keyword-only and required.
    with pytest.raises(TypeError):
        update_scenarios(d, new_scenarios)  # missing current_price


def test_make_dossier_sets_scenario_price():
    d = _make(price=100)
    assert d["scenario_price"] == 100.0


def test_rescore_does_not_change_scenario_price():
    d = _make(price=100)
    rescore_dossier(d, current_price=130.0)
    assert d["current_price"] == 130.0
    assert d["scenario_price"] == 100.0


def test_update_scenarios_resets_scenario_price():
    d = _make(price=100)
    new_scenarios = {
        "bull": {"target": 200, "probability": 0.4},
        "base": {"target": 120, "probability": 0.4},
        "bear": {"target": 60, "probability": 0.2},
    }
    update_scenarios(d, new_scenarios, current_price=150.0)
    assert d["scenario_price"] == 150.0
    assert d["current_price"] == 150.0


def test_price_age_hours_none_when_unstamped():
    d = _make(price=100)
    d.pop("priced_at", None)
    assert price_age_hours(d) is None


def test_price_age_hours_measures_gap():
    d = _make(price=100)
    # Backdate 5 hours.
    backdated = datetime.utcnow() - timedelta(hours=5)
    d["priced_at"] = backdated.isoformat()
    age = price_age_hours(d)
    assert age is not None and 4.5 < age < 5.5


def test_rank_by_potential():
    a = _make("A", bull=200, bear=80)  # higher upside
    b = _make("B", bull=110, bear=80)  # lower upside
    ranked = rank([b, a])
    # A should be first if its potential is higher
    assert ranked[0]["symbol"] in ("A", "B")
    # The one with higher score should come first
    assert ranked[0]["derived"]["potential_score"] >= ranked[1]["derived"]["potential_score"]


# ---------- check_staleness ----------

def test_staleness_fresh_dossier_not_flagged():
    d = _make(price=100)
    assert check_staleness([d]) == []


def test_staleness_old_thesis_flagged():
    d = _make(price=100)
    d["priced_at"] = (datetime.utcnow() - timedelta(days=15)).isoformat()
    flagged = check_staleness([d])
    assert len(flagged) == 1
    assert flagged[0]["symbol"] == "ACME"
    assert any("days old" in r for r in flagged[0]["reasons"])


def test_staleness_price_drift_flagged():
    d = _make(price=100)
    # scenario_price is 100 (set by make_dossier), simulate price moving to 125
    d["current_price"] = 125.0
    flagged = check_staleness([d])
    assert len(flagged) == 1
    assert any("drifted" in r for r in flagged[0]["reasons"])


def test_staleness_no_drift_when_price_near_anchor():
    d = _make(price=100)
    # Price moved 10% from scenario anchor — below 20% threshold
    d["current_price"] = 110.0
    assert check_staleness([d]) == []


def test_staleness_missing_scenario_price_flagged():
    d = _make(price=100)
    d.pop("scenario_price", None)
    flagged = check_staleness([d])
    assert len(flagged) == 1
    assert any("no scenario_price" in r for r in flagged[0]["reasons"])


def test_staleness_no_priced_at_flagged():
    d = _make(price=100)
    d.pop("priced_at", None)
    flagged = check_staleness([d])
    assert len(flagged) == 1
    assert any("no priced_at" in r for r in flagged[0]["reasons"])


def test_staleness_custom_thresholds():
    d = _make(price=100)
    d["priced_at"] = (datetime.utcnow() - timedelta(hours=50)).isoformat()
    # Not stale at default 14-day threshold
    assert check_staleness([d]) == []
    # Stale at 48-hour threshold
    flagged = check_staleness([d], age_hours=48)
    assert len(flagged) == 1
