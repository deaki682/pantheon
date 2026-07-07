from oracle.themes import ACTIVE_THEMES, FORMING_THEMES, tag_theme


def test_tight_industry_fires_at_low_strength():
    t = tag_theme("Semiconductors", "Acme Semi Inc")
    assert t["theme"] == "ai_compute" and t["theme_strength"] == 0.6


def test_keyword_fires_at_full_strength():
    t = tag_theme("Aerospace & Defense", "Foo Missile Systems")
    assert t["theme"] == "defense" and t["theme_strength"] == 1.0


def test_keyword_beats_broad_industry():
    # Biotechnology is broad -> only a keyword match fires it
    assert tag_theme("Biotechnology", "Generic Bio") is None
    t = tag_theme("Biotechnology", "Slim Co", "a GLP-1 incretin obesity program")
    assert t["theme"] == "obesity_metabolic" and t["theme_strength"] == 1.0


def test_unrelated_is_none():
    assert tag_theme("Restaurants", "Some Diner") is None


def test_inactive_theme_does_not_fire():
    t = tag_theme("Aerospace & Defense", "Foo Defense", active=set())
    assert t is None


def test_all_forming_themes_have_specs():
    for name in ACTIVE_THEMES:
        spec = FORMING_THEMES[name]
        assert "tight_industries" in spec and "keywords" in spec
