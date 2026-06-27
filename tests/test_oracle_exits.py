from oracle.exits import exit_signal


def _dossier(moat=0.7, quality=0.7, bull=200, bear=50):
    return {
        "ratings": {"moat": moat, "runway": 0.7, "quality": quality, "management": 0.5},
        "scenarios": {
            "bull": {"target": bull, "probability": 0.3},
            "base": {"target": 100, "probability": 0.5},
            "bear": {"target": bear, "probability": 0.2},
        },
    }


def test_hold_thesis_intact():
    d = _dossier()
    out = exit_signal(d, current_price=100)
    assert out["action"] == "hold"


def test_thesis_break_sell_all():
    d = _dossier(moat=0.1, quality=0.1)
    out = exit_signal(d, current_price=100)
    assert out["action"] == "sell"
    assert out["fraction"] == 1.0


def test_thesis_break_requires_both():
    # Only moat broken — NOT a full thesis break
    d = _dossier(moat=0.1, quality=0.8)
    out = exit_signal(d, current_price=100)
    assert out["action"] != "sell"


def test_bull_hit_trim_half():
    d = _dossier()
    out = exit_signal(d, current_price=220)  # past bull target
    assert out["action"] == "trim"
    assert out["fraction"] == 0.5


def test_catalysts_done_review():
    d = _dossier()
    out = exit_signal(d, current_price=100, catalysts_remaining=0)
    assert out["action"] == "review"


def test_bear_hit_review_not_sell():
    d = _dossier()
    out = exit_signal(d, current_price=40)
    # NOT auto-sell; Oracle trusts its own thesis at the bear
    assert out["action"] == "review"
