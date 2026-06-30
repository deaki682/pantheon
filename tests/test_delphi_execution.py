import pytest

from delphi.execution import build_targets, plan_orders
from delphi.sleeve import DelphiSleeve, MIN_TICKET


def test_build_targets_zero_budget():
    picks = [{"symbol": "AAPL"}]
    out = build_targets(picks, equity=1000.0, risk_budget=0.0)
    assert out == {}


def test_build_targets_equal_weight():
    picks = [{"symbol": "AAPL"}, {"symbol": "MSFT"}]
    out = build_targets(picks, equity=1000.0, risk_budget=1.0)
    assert "AAPL" in out
    assert "MSFT" in out
    assert out["AAPL"] == pytest.approx(out["MSFT"], abs=1.0)


def test_build_targets_per_name_cap():
    picks = [{"symbol": "AAPL"}]
    out = build_targets(picks, equity=10_000.0, risk_budget=1.0)
    assert out["AAPL"] <= 2000.0 + 1e-6


def test_plan_orders_new_position():
    s = DelphiSleeve(initial_cash=1000)
    out = plan_orders(s, targets={"AAPL": 100.0}, prices={"AAPL": 50.0})
    assert any(o["side"] == "buy" and o["symbol"] == "AAPL" for o in out)


def test_plan_orders_rebal_band():
    s = DelphiSleeve(initial_cash=1000)
    s.buy("AAPL", 1.0, 100.0, "2024-01-01")
    out = plan_orders(s, targets={"AAPL": 105.0}, prices={"AAPL": 100.0})
    assert out == []


def test_plan_orders_exits_on_momentum_out():
    s = DelphiSleeve(initial_cash=1000)
    s.buy("AAPL", 1.0, 100.0, "2024-01-01")
    out = plan_orders(s, targets={}, prices={"AAPL": 100.0})
    assert any(o["side"] == "sell" and o["symbol"] == "AAPL" for o in out)
    assert any(o["reason"] == "momentum_exit" for o in out)
