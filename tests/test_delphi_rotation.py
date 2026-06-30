from delphi.rotation import rotation_plan


def test_rotation_plan_always_invested():
    plan = rotation_plan()
    assert plan["regime"] == "momentum"
    assert plan["risk_budget"] == 1.0
