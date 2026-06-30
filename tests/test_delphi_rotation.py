from delphi.rotation import rotation_plan


def test_rotation_plan_default():
    plan = rotation_plan()
    assert plan["regime"] == "momentum"
    assert plan["risk_budget"] == 1.0


def test_rotation_plan_custom_risk_budget():
    plan = rotation_plan(risk_budget=0.7)
    assert plan["risk_budget"] == 0.7


def test_rotation_plan_clamps_low():
    plan = rotation_plan(risk_budget=0.2)
    assert plan["risk_budget"] == 0.5


def test_rotation_plan_clamps_high():
    plan = rotation_plan(risk_budget=1.5)
    assert plan["risk_budget"] == 1.0
