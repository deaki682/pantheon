import pytest

from achilles.earnings import (
    EarningsSurprise,
    compute_surprise,
    is_actionable_beat,
    is_rewarded_beat,
    reaction_return,
    surprise_to_strength,
)


def _beat(is_beat=True):
    return EarningsSurprise(symbol="X", actual_eps=1.1, estimate_eps=1.0,
                            surprise_pct=10.0, is_beat=is_beat)


class TestReactionGate:
    def test_reaction_return_positive(self):
        assert reaction_return(50.0, 53.0) == pytest.approx(0.06)

    def test_reaction_return_negative(self):
        # DAKT case: gap up then close red vs the prior close
        assert reaction_return(20.11, 19.35) == pytest.approx(-0.0378, abs=1e-3)

    def test_reaction_return_guards(self):
        assert reaction_return(0, 10) is None
        assert reaction_return(None, 10) is None
        assert reaction_return("x", 10) is None

    def test_rewarded_beat_true(self):
        assert is_rewarded_beat(_beat(), 0.06) is True

    def test_sold_beat_rejected(self):
        # beat, but the market sold it -> not rewarded
        assert is_rewarded_beat(_beat(), -0.04) is False

    def test_unconfirmed_reaction_rejected(self):
        assert is_rewarded_beat(_beat(), None) is False

    def test_miss_never_rewarded(self):
        assert is_rewarded_beat(_beat(is_beat=False), 0.10) is False


def test_compute_surprise_beat():
    pct, is_beat = compute_surprise(1.50, 1.00)
    assert pct == pytest.approx(50.0)
    assert is_beat is True


def test_compute_surprise_miss():
    pct, is_beat = compute_surprise(0.80, 1.00)
    assert pct == pytest.approx(-20.0)
    assert is_beat is False


def test_compute_surprise_inline():
    pct, is_beat = compute_surprise(1.00, 1.00)
    assert pct == pytest.approx(0.0)
    assert is_beat is False


def test_compute_surprise_near_zero_estimate():
    pct, is_beat = compute_surprise(0.05, 0.001)
    assert is_beat is True
    assert pct == pytest.approx(0.049 * 100.0, abs=0.1)


def test_compute_surprise_negative_eps():
    pct, is_beat = compute_surprise(-0.10, -0.50)
    assert is_beat is True
    assert pct == pytest.approx(80.0)


def test_is_actionable_beat_sweet_spot():
    s = EarningsSurprise("ACME", 1.15, 1.00, 15.0, True)
    assert is_actionable_beat(s) is True


def test_is_actionable_beat_too_small():
    s = EarningsSurprise("ACME", 1.02, 1.00, 2.0, True)
    assert is_actionable_beat(s) is False


def test_is_actionable_beat_very_large_still_valid():
    s = EarningsSurprise("ACME", 3.00, 1.00, 200.0, True)
    assert is_actionable_beat(s) is True


def test_is_actionable_beat_too_large():
    s = EarningsSurprise("ACME", 10.00, 1.00, 900.0, True)
    assert is_actionable_beat(s) is False


def test_is_actionable_beat_miss():
    s = EarningsSurprise("ACME", 0.80, 1.00, -20.0, False)
    assert is_actionable_beat(s) is False


def test_surprise_to_strength_beat():
    s = EarningsSurprise("ACME", 1.15, 1.00, 15.0, True)
    strength = surprise_to_strength(s)
    assert 0.95 <= strength <= 1.0


def test_surprise_to_strength_miss_is_zero():
    s = EarningsSurprise("ACME", 0.80, 1.00, -20.0, False)
    assert surprise_to_strength(s) == 0.0
