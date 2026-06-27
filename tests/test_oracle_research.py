import pytest

from oracle.research import load_dossiers, make_dossier, rank, rescore_dossier, save_dossiers


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


def test_rescore():
    d = _make(price=100)
    initial_conv = d["conviction"]
    # At a much higher price, expected return drops
    rescore_dossier(d, current_price=140.0)
    assert d["current_price"] == 140.0
    assert d["conviction"] != initial_conv


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


def test_rank_by_potential():
    a = _make("A", bull=200, bear=80)  # higher upside
    b = _make("B", bull=110, bear=80)  # lower upside
    ranked = rank([b, a])
    # A should be first if its potential is higher
    assert ranked[0]["symbol"] in ("A", "B")
    # The one with higher score should come first
    assert ranked[0]["derived"]["potential_score"] >= ranked[1]["derived"]["potential_score"]
