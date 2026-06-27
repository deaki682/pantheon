from oracle.journal import JournalEntry
from oracle.learning import bayesian_shrunk_skill, calibration_stats, conviction_tier, hit_rate


def _graded(decision="buy", conviction=0.8, ret=0.1):
    e = JournalEntry(
        timestamp="2024-01-01", symbol="X", decision=decision,
        conviction=conviction, horizon_days=30, price=100.0,
    )
    e.graded_return = ret
    e.graded_outcome = "win" if ret > 0.05 else ("loss" if ret < -0.05 else "neutral")
    return e


def test_conviction_tier():
    assert conviction_tier(0.9) == "high"
    assert conviction_tier(0.5) == "mid"
    assert conviction_tier(0.1) == "low"


def test_calibration_monotonic():
    entries = [
        _graded(conviction=0.9, ret=0.20),
        _graded(conviction=0.85, ret=0.15),
        _graded(conviction=0.5, ret=0.05),
        _graded(conviction=0.45, ret=0.02),
        _graded(conviction=0.1, ret=-0.05),
        _graded(conviction=0.05, ret=-0.10),
    ]
    out = calibration_stats(entries)
    assert out["high"] > out["mid"] > out["low"]
    assert out["monotonic"] is True


def test_calibration_not_monotonic():
    entries = [
        _graded(conviction=0.9, ret=-0.05),  # high conviction loser
        _graded(conviction=0.1, ret=0.20),   # low conviction winner
    ]
    out = calibration_stats(entries)
    assert out["monotonic"] is False


def test_calibration_ignores_ungraded():
    entries = [_graded(ret=0.10)]
    entries[0].graded_return = None
    out = calibration_stats(entries)
    assert out["n"] == 0


def test_hit_rate():
    entries = [_graded(ret=0.10), _graded(ret=-0.10), _graded(ret=0.10)]
    assert hit_rate(entries) == 2 / 3


def test_hit_rate_empty():
    assert hit_rate([]) == 0.0


def test_bayesian_shrinkage_small_sample():
    # Observed mean 0.2, n=5, prior n=20 -> heavy shrinkage toward 0
    out = bayesian_shrunk_skill(0.2, 5, prior_n=20)
    # shrunk = (20*0 + 5*0.2) / 25 = 0.04
    assert 0 < out < 0.2  # smaller than observed; pulled toward prior


def test_bayesian_shrinkage_large_sample():
    out = bayesian_shrunk_skill(0.2, 1000, prior_n=20)
    assert abs(out - 0.2) < 0.01
