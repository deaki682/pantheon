import math
from shared.gauntlet import convexity_stats


def test_empty():
    assert convexity_stats([]) == {"n": 0}


def test_floor_is_worst_trade():
    s = convexity_stats([0.1, -0.3, 0.05, -0.5, 0.2])
    assert s["floor"] == -0.5          # the survivability number
    assert s["max"] == 0.2


def test_payoff_ratio_and_winrate():
    s = convexity_stats([0.2, 0.2, -0.1])   # 2 wins avg +0.2, 1 loss -0.1
    assert s["win_rate"] == round(2 / 3, 3)
    assert s["avg_win"] == 0.2
    assert s["avg_loss"] == -0.1
    assert s["payoff_ratio"] == 2.0


def test_no_losses_payoff_none():
    s = convexity_stats([0.1, 0.2, 0.3])
    assert s["payoff_ratio"] is None       # infinite / undefined, reported as None
    assert s["win_rate"] == 1.0


def test_right_tail_share_flags_convexity():
    # convex: one huge winner dominates total positive P&L
    convex = [0.02] * 19 + [5.0]
    s = convexity_stats(convex, tail_pct=0.10)
    assert s["right_tail_share"] > 0.9     # the tail IS the return
    # symmetric: gains spread evenly -> low tail share
    flat = [0.05, -0.04, 0.06, -0.05, 0.05, -0.04, 0.05, -0.05, 0.06, -0.04]
    assert convexity_stats(flat, tail_pct=0.10)["right_tail_share"] < 0.35


def test_excess_mode():
    # per-trade excess vs benchmark
    s = convexity_stats([0.10, 0.20], benchmark_returns=[0.08, 0.05])
    assert s["expectancy"] == round((0.02 + 0.15) / 2, 4)


def test_expectancy_is_mean():
    rs = [0.1, -0.2, 0.3, 0.05]
    s = convexity_stats(rs)
    assert s["expectancy"] == round(sum(rs) / len(rs), 4)
