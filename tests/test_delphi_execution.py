import pytest

from delphi.execution import build_targets, plan_orders
from delphi.sleeve import DelphiSleeve, MIN_TICKET


def test_build_targets_risk_off_empty():
    picks = {"tech": [{"symbol": "AAPL", "score": 1.0}]}
    out = build_targets(picks, equity=1000.0, risk_budget=0.0)
    assert out == {}


def test_build_targets_full_budget():
    picks = {
        "tech": [{"symbol": "AAPL", "score": 1.0}, {"symbol": "MSFT", "score": 0.8}],
        "finance": [{"symbol": "JPM", "score": 0.7}],
    }
    out = build_targets(picks, equity=10_000.0, risk_budget=1.0)
    total = sum(out.values())
    # 90% invested
    assert total <= 9000.0 + 1e-6


def test_build_targets_per_name_cap():
    picks = {"tech": [{"symbol": "AAPL", "score": 1.0}]}
    out = build_targets(picks, equity=10_000.0, risk_budget=1.0)
    # 12% cap = $1200
    assert out["AAPL"] <= 1200.0 + 1e-6


def test_build_targets_sector_cap():
    picks = {"tech": [{"symbol": f"S{i}", "score": 1.0} for i in range(4)]}
    out = build_targets(picks, equity=10_000.0, risk_budget=1.0)
    total = sum(out.values())
    # 40% sector cap on a single sector
    assert total <= 4000.0 + 1e-6


def test_build_targets_skips_blocked():
    picks = {"tech": [{"symbol": "XLK", "score": 1.0}, {"symbol": "AAPL", "score": 0.5}]}
    out = build_targets(picks, equity=10_000.0, risk_budget=1.0)
    assert "XLK" not in out
    assert "AAPL" in out


def test_build_targets_max_names_per_sector():
    # 6 picks in tech, should be trimmed to 4
    picks = {"tech": [{"symbol": f"S{i}", "score": 1.0} for i in range(6)]}
    out = build_targets(picks, equity=10_000.0, risk_budget=1.0)
    tech_held = [s for s in out if s.startswith("S")]
    assert len(tech_held) <= 4


def test_plan_orders_new_position():
    s = DelphiSleeve(initial_cash=1000)
    out = plan_orders(s, targets={"AAPL": 100.0}, prices={"AAPL": 50.0})
    assert any(o["side"] == "buy" and o["symbol"] == "AAPL" for o in out)


def test_plan_orders_rebal_band():
    s = DelphiSleeve(initial_cash=1000)
    s.buy("AAPL", 1.0, 100.0, "2024-01-01")
    # Target = 105 (5% over), within 20% band
    out = plan_orders(s, targets={"AAPL": 105.0}, prices={"AAPL": 100.0})
    assert out == []


def test_plan_orders_blocked_filter():
    s = DelphiSleeve(initial_cash=1000)
    out = plan_orders(s, targets={"XLK": 100.0}, prices={"XLK": 100.0})
    # XLK should not be opened
    assert not any(o["symbol"] == "XLK" and o["side"] == "buy" for o in out)


def test_plan_orders_exits_on_rotation_out():
    s = DelphiSleeve(initial_cash=1000)
    s.buy("AAPL", 1.0, 100.0, "2024-01-01")
    out = plan_orders(s, targets={}, prices={"AAPL": 100.0})
    assert any(o["side"] == "sell" and o["symbol"] == "AAPL" for o in out)
