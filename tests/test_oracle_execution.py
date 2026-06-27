from oracle.execution import dollars_to_shares, plan_orders
from oracle.sleeve import OracleSleeve


def test_dollars_to_shares():
    assert dollars_to_shares(100, 50) == 2.0
    assert dollars_to_shares(100, 0) == 0.0


def test_plan_orders_new_position():
    s = OracleSleeve(initial_cash=1000)
    orders = plan_orders(s, targets={"AAPL": 200.0}, prices={"AAPL": 100.0})
    assert len(orders) == 1
    assert orders[0]["side"] == "buy"
    assert orders[0]["symbol"] == "AAPL"
    assert orders[0]["dollars"] == 200.0


def test_plan_orders_skips_buy_during_cooldown_when_today_given():
    s = OracleSleeve(initial_cash=1000)
    s.cooldowns["AAPL"] = "2024-06-30"  # cooldown expires end of June
    # today before expiry -> still cooling -> no buy proposed
    assert plan_orders(s, {"AAPL": 200.0}, {"AAPL": 100.0}, today="2024-06-15") == []
    # today after expiry -> buy proposed
    out = plan_orders(s, {"AAPL": 200.0}, {"AAPL": 100.0}, today="2024-07-01")
    assert [o["symbol"] for o in out] == ["AAPL"]
    # today omitted -> permissive (cooldown enforced at the buy layer instead)
    assert len(plan_orders(s, {"AAPL": 200.0}, {"AAPL": 100.0})) == 1


def test_plan_orders_holds_within_band():
    s = OracleSleeve(initial_cash=1000)
    s.buy("AAPL", 1.0, 100.0, "2024-01-01")
    # Current dollar value = 100; target = 105 (5% above) -> within 10% band
    orders = plan_orders(s, targets={"AAPL": 105.0}, prices={"AAPL": 100.0})
    assert orders == []


def test_plan_orders_sells_removed():
    s = OracleSleeve(initial_cash=1000)
    s.buy("AAPL", 1.0, 100.0, "2024-01-01")
    orders = plan_orders(s, targets={}, prices={"AAPL": 100.0})
    assert len(orders) == 1
    assert orders[0]["side"] == "sell"
    assert orders[0]["symbol"] == "AAPL"


def test_plan_orders_trim_overweight():
    s = OracleSleeve(initial_cash=1000)
    s.buy("AAPL", 2.0, 100.0, "2024-01-01")  # current = $200
    # target = $100 -> need to sell $100
    orders = plan_orders(s, targets={"AAPL": 100.0}, prices={"AAPL": 100.0})
    assert len(orders) == 1
    assert orders[0]["side"] == "sell"
    assert orders[0]["dollars"] == 100.0


def test_plan_orders_skips_below_min_ticket():
    s = OracleSleeve(initial_cash=1000)
    orders = plan_orders(s, targets={"AAPL": 30.0}, prices={"AAPL": 100.0})
    assert orders == []
