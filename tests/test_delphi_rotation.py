import pytest

from delphi.rotation import (
    breadth, choose_sectors, classify_regime, regime_params, rotation_plan,
)


def test_breadth_all_positive():
    assert breadth({"a": 0.1, "b": 0.2}) == 1.0


def test_breadth_half():
    assert breadth({"a": 0.1, "b": -0.1}) == 0.5


def test_breadth_empty():
    assert breadth({}) == 0.0


def test_regime_risk_on():
    assert classify_regime(spy_1m=0.01, spy_3m=0.05, sector_breadth=0.7) == "risk_on"


def test_regime_risk_off_on_spy():
    assert classify_regime(spy_1m=0.0, spy_3m=-0.10, sector_breadth=0.6) == "risk_off"


def test_regime_risk_off_on_breadth():
    assert classify_regime(spy_1m=0.0, spy_3m=0.0, sector_breadth=0.20) == "risk_off"


def test_regime_cautious():
    # SPY 1m < -3%, but 3m not extreme and breadth ok
    assert classify_regime(spy_1m=-0.05, spy_3m=0.0, sector_breadth=0.5) == "cautious"


def test_regime_neutral():
    assert classify_regime(spy_1m=-0.01, spy_3m=0.01, sector_breadth=0.4) == "neutral"


def test_regime_params_risk_on():
    p = regime_params("risk_on")
    assert p["risk_budget"] == 1.00
    assert p["top_n"] == 3


def test_regime_params_risk_off():
    p = regime_params("risk_off")
    assert p["risk_budget"] == 0.0
    assert p["top_n"] == 0


def test_regime_params_cautious():
    p = regime_params("cautious")
    assert p["risk_budget"] == 0.50
    assert p["top_n"] == 2
    assert p["require_positive"] is True


def test_regime_params_neutral():
    p = regime_params("neutral")
    assert p["risk_budget"] == 0.75
    assert p["top_n"] == 3


def test_choose_sectors_risk_on_takes_top3():
    scores = {f"sec{i}": 0.5 - i * 0.05 for i in range(5)}
    out = choose_sectors(scores, "risk_on")
    assert len(out) == 3


def test_choose_sectors_cautious_requires_positive():
    scores = {"a": 0.5, "b": -0.1, "c": -0.2}
    out = choose_sectors(scores, "cautious")
    assert out == ["a"]  # only positive one


def test_choose_sectors_risk_off_empty():
    scores = {"a": 0.5, "b": 0.4}
    assert choose_sectors(scores, "risk_off") == []


def test_rotation_plan_risk_on():
    spy = [100.0] * 127
    spy[-1] = 110.0  # +10% 1m and 3m
    spy[-22] = 100.0
    spy[-64] = 100.0
    scores = {"tech": 0.1, "finance": 0.05, "energy": -0.05, "healthcare": 0.08, "industrials": 0.06}
    plan = rotation_plan(spy, scores)
    assert plan["regime"] in ("risk_on", "neutral")
    assert plan["risk_budget"] > 0


def test_rotation_plan_risk_off_full_cash():
    spy = [100.0] * 127
    spy[-1] = 88.0  # -12% over 3 months
    scores = {"tech": -0.1, "finance": -0.05}
    plan = rotation_plan(spy, scores)
    assert plan["regime"] == "risk_off"
    assert plan["risk_budget"] == 0.0
    assert plan["sectors"] == []
