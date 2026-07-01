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


def test_build_targets_weight_overrides():
    picks = [{"symbol": "AAPL"}, {"symbol": "MSFT"}, {"symbol": "GOOG"},
             {"symbol": "AMZN"}, {"symbol": "META"}]
    out = build_targets(
        picks, equity=10_000.0, risk_budget=1.0,
        weight_overrides={"AAPL": 2.0},
    )
    assert out["AAPL"] > out["MSFT"]


def test_build_targets_weight_overrides_normalize():
    picks = [{"symbol": "A"}, {"symbol": "B"}, {"symbol": "C"}]
    no_override = build_targets(picks, equity=10_000.0, risk_budget=1.0)
    with_override = build_targets(
        picks, equity=10_000.0, risk_budget=1.0,
        weight_overrides={"A": 1.0, "B": 1.0, "C": 1.0},
    )
    assert sum(no_override.values()) == pytest.approx(sum(with_override.values()), abs=1.0)


def test_build_targets_weight_override_default_one():
    picks = [{"symbol": "AAPL"}, {"symbol": "MSFT"}]
    out_default = build_targets(picks, equity=10_000.0, risk_budget=1.0)
    out_explicit = build_targets(
        picks, equity=10_000.0, risk_budget=1.0,
        weight_overrides={"AAPL": 1.0, "MSFT": 1.0},
    )
    assert out_default["AAPL"] == pytest.approx(out_explicit["AAPL"], abs=0.01)


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


def test_plan_orders_hold_override_skips_sell():
    s = DelphiSleeve(initial_cash=1000)
    s.buy("AAPL", 1.0, 100.0, "2024-01-01")
    out = plan_orders(s, targets={}, prices={"AAPL": 100.0}, hold_overrides={"AAPL"})
    assert not any(o["symbol"] == "AAPL" for o in out)


def test_plan_orders_hold_override_doesnt_affect_others():
    s = DelphiSleeve(initial_cash=2000)
    s.buy("AAPL", 1.0, 100.0, "2024-01-01")
    s.buy("MSFT", 1.0, 100.0, "2024-01-01")
    out = plan_orders(
        s, targets={}, prices={"AAPL": 100.0, "MSFT": 100.0},
        hold_overrides={"AAPL"},
    )
    assert not any(o["symbol"] == "AAPL" for o in out)
    assert any(o["symbol"] == "MSFT" and o["side"] == "sell" for o in out)


# ── cooldown intent on sells (trim vs exit) ──────────────────────────

def test_full_exit_sets_cooldown_flag():
    s = DelphiSleeve(initial_cash=0)
    s.positions["AAPL"] = __import__("shared.base_sleeve", fromlist=["SleevePosition"]).SleevePosition(
        shares=2.0, avg_price=100.0, entry_date="2026-06-01")
    out = plan_orders(s, targets={}, prices={"AAPL": 100.0})
    assert out[0]["reason"] == "momentum_exit"
    assert out[0]["set_cooldown"] is True


def test_trim_does_not_set_cooldown():
    s = DelphiSleeve(initial_cash=0)
    s.positions["AAPL"] = __import__("shared.base_sleeve", fromlist=["SleevePosition"]).SleevePosition(
        shares=4.0, avg_price=100.0, entry_date="2026-06-01")
    # held $400 vs target $200 -> trim $200 (> min ticket, > band)
    out = plan_orders(s, targets={"AAPL": 200.0}, prices={"AAPL": 100.0})
    trims = [o for o in out if o["reason"] == "trim_to_target"]
    assert len(trims) == 1
    assert trims[0]["set_cooldown"] is False
