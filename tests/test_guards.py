import json
import os

import pytest

from shared.guards import (
    KILL_SWITCH_FILE,
    OrderRecord,
    already_placed_today,
    append_order,
    filter_broker_to_gods,
    filter_orders_by_ledger,
    is_live,
    kill_switch_active,
    liquidate_if_kill,
    pending_shares_from_orders,
    pre_trade_check,
    read_ledger,
)


def test_kill_switch_absent(tmp_path):
    assert kill_switch_active(str(tmp_path)) is False


def test_kill_switch_present(tmp_path):
    (tmp_path / KILL_SWITCH_FILE).write_text("")
    assert kill_switch_active(str(tmp_path)) is True


def test_is_live_default_off():
    assert is_live("oracle", env={}) is False
    assert is_live("delphi", env={}) is False
    assert is_live("achilles", env={}) is False


def test_is_live_requires_exact_string():
    assert is_live("oracle", env={"ORACLE_LIVE": "true"}) is True
    assert is_live("oracle", env={"ORACLE_LIVE": "True"}) is True  # case-insensitive
    assert is_live("oracle", env={"ORACLE_LIVE": "1"}) is False
    assert is_live("oracle", env={"ORACLE_LIVE": "yes"}) is False
    assert is_live("oracle", env={"ORACLE_LIVE": ""}) is False


def test_is_live_unknown_god():
    assert is_live("zeus", env={"ZEUS_LIVE": "true"}) is False


def test_is_live_per_god():
    env = {"ORACLE_LIVE": "true"}
    assert is_live("oracle", env=env) is True
    assert is_live("delphi", env=env) is False
    assert is_live("achilles", env=env) is False


def test_ledger_append_and_read(tmp_path):
    p = tmp_path / "ledger.jsonl"
    append_order(str(p), OrderRecord("o1", "AAPL", "buy", 100.0, "2024-05-29"))
    append_order(str(p), OrderRecord("o2", "MSFT", "buy", 200.0, "2024-05-29"))
    records = read_ledger(str(p))
    assert len(records) == 2
    assert records[0].order_id == "o1"
    assert records[1].symbol == "MSFT"


def test_read_ledger_missing_file(tmp_path):
    p = tmp_path / "nope.jsonl"
    assert read_ledger(str(p)) == []


def test_read_ledger_ignores_bad_lines(tmp_path):
    p = tmp_path / "ledger.jsonl"
    p.write_text("not-json\n" + json.dumps({"order_id": "o1", "symbol": "A", "side": "buy", "dollars": 1.0, "date": "2024-01-01"}) + "\n")
    records = read_ledger(str(p))
    assert len(records) == 1
    assert records[0].order_id == "o1"


def test_filter_orders_empty_ledger_returns_empty():
    """SAFETY: empty ledger must return empty, never all broker orders."""
    broker = [{"order_id": "x"}, {"order_id": "y"}, {"order_id": "z"}]
    out = filter_orders_by_ledger(broker, [])
    assert out == []


def test_filter_orders_intersects():
    broker = [{"order_id": "x"}, {"order_id": "y"}, {"order_id": "z"}]
    ledger = [
        OrderRecord("y", "AAPL", "buy", 100.0, "2024-05-29"),
        OrderRecord("notinbroker", "MSFT", "buy", 50.0, "2024-05-29"),
    ]
    out = filter_orders_by_ledger(broker, ledger)
    assert len(out) == 1
    assert out[0]["order_id"] == "y"


def test_filter_orders_custom_id_field():
    broker = [{"id": "x"}, {"id": "y"}]
    ledger = [OrderRecord("y", "A", "buy", 1.0, "2024-01-01")]
    out = filter_orders_by_ledger(broker, ledger, id_field="id")
    assert len(out) == 1


def test_already_placed_same_day():
    ledger = [OrderRecord("o1", "AAPL", "buy", 100.0, "2024-05-29")]
    assert already_placed_today(ledger, "AAPL", "buy", "2024-05-29") is True
    # Different side -> no
    assert already_placed_today(ledger, "AAPL", "sell", "2024-05-29") is False
    # Different symbol -> no
    assert already_placed_today(ledger, "MSFT", "buy", "2024-05-29") is False
    # Different day -> no
    assert already_placed_today(ledger, "AAPL", "buy", "2024-05-30") is False


def test_liquidate_if_kill_no_op_when_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    class Stub:
        def liquidate_all(self, marks, today):
            raise AssertionError("should not be called")

    assert liquidate_if_kill(Stub(), {}, "2024-05-29") is None


def test_liquidate_if_kill_fires_when_present(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / KILL_SWITCH_FILE).write_text("")

    class Stub:
        def __init__(self):
            self.calls = []
        def liquidate_all(self, marks, today):
            self.calls.append((marks, today))
            return [("AAPL", 1.0, 100.0)]

    s = Stub()
    out = liquidate_if_kill(s, {"AAPL": 100.0}, "2024-05-29")
    assert out == [("AAPL", 1.0, 100.0)]
    assert len(s.calls) == 1


# ------- filter_broker_to_gods -------

def _write_sleeve(path, positions):
    data = {"positions": {sym: {"symbol": sym, "shares": sh} for sym, sh in positions.items()}}
    os.makedirs(os.path.dirname(str(path)) or ".", exist_ok=True)
    with open(str(path), "w") as f:
        json.dump(data, f)


def _write_ledger(path, records):
    os.makedirs(os.path.dirname(str(path)) or ".", exist_ok=True)
    with open(str(path), "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def test_filter_broker_empty_sleeves_returns_empty(tmp_path):
    sleeve_paths = {"oracle": str(tmp_path / "o.json"), "delphi": str(tmp_path / "d.json")}
    ledger_paths = {"oracle": str(tmp_path / "o.jsonl"), "delphi": str(tmp_path / "d.jsonl")}
    broker = {"GOOGL": 50.0, "AAPL": 100.0, "MSFT": 25.0}
    result = filter_broker_to_gods(broker, sleeve_paths=sleeve_paths, ledger_paths=ledger_paths)
    assert result == {}


def test_filter_broker_shows_only_god_symbols(tmp_path):
    _write_sleeve(tmp_path / "o.json", {"MRP": 4.0, "KBR": 3.0})
    _write_sleeve(tmp_path / "d.json", {})
    sleeve_paths = {"oracle": str(tmp_path / "o.json"), "delphi": str(tmp_path / "d.json")}
    ledger_paths = {"oracle": str(tmp_path / "o.jsonl")}
    broker = {"MRP": 4.0, "KBR": 3.0, "GOOGL": 50.0, "AAPL": 100.0}
    result = filter_broker_to_gods(broker, sleeve_paths=sleeve_paths, ledger_paths=ledger_paths)
    assert set(result.keys()) == {"MRP", "KBR"}
    assert "GOOGL" not in result
    assert "AAPL" not in result


def test_filter_broker_includes_ledger_symbols(tmp_path):
    _write_sleeve(tmp_path / "o.json", {})
    _write_ledger(tmp_path / "o.jsonl", [
        {"order_id": "x", "symbol": "SOLD", "side": "sell", "dollars": 100, "date": "2026-01-01"},
    ])
    sleeve_paths = {"oracle": str(tmp_path / "o.json")}
    ledger_paths = {"oracle": str(tmp_path / "o.jsonl")}
    broker = {"SOLD": 0.0, "GOOGL": 50.0}
    result = filter_broker_to_gods(broker, sleeve_paths=sleeve_paths, ledger_paths=ledger_paths)
    assert "SOLD" in result
    assert "GOOGL" not in result


# ------- pending_shares_from_orders -------

def test_pending_shares_buy_queued():
    orders = [
        {"symbol": "VITL", "side": "buy", "state": "queued", "quantity": "10.0", "cumulative_quantity": "0.0"},
        {"symbol": "MRP", "side": "buy", "state": "queued", "quantity": "4.0", "cumulative_quantity": "0.0"},
    ]
    pending = pending_shares_from_orders(orders)
    assert pending["VITL"] == pytest.approx(10.0)
    assert pending["MRP"] == pytest.approx(4.0)


def test_pending_shares_partially_filled():
    orders = [
        {"symbol": "VITL", "side": "buy", "state": "partially_filled", "quantity": "10.0", "cumulative_quantity": "3.0"},
    ]
    pending = pending_shares_from_orders(orders)
    assert pending["VITL"] == pytest.approx(7.0)


def test_pending_shares_sell_subtracts():
    orders = [
        {"symbol": "VITL", "side": "sell", "state": "queued", "quantity": "5.0", "cumulative_quantity": "0.0"},
    ]
    pending = pending_shares_from_orders(orders)
    assert pending["VITL"] == pytest.approx(-5.0)


def test_pending_shares_ignores_filled_and_cancelled():
    orders = [
        {"symbol": "VITL", "side": "buy", "state": "filled", "quantity": "10.0", "cumulative_quantity": "10.0"},
        {"symbol": "MRP", "side": "buy", "state": "cancelled", "quantity": "4.0", "cumulative_quantity": "0.0"},
    ]
    pending = pending_shares_from_orders(orders)
    assert pending == {}


def test_pending_shares_aggregates_same_symbol():
    orders = [
        {"symbol": "VITL", "side": "buy", "state": "queued", "quantity": "5.0", "cumulative_quantity": "0.0"},
        {"symbol": "VITL", "side": "buy", "state": "confirmed", "quantity": "3.0", "cumulative_quantity": "0.0"},
    ]
    pending = pending_shares_from_orders(orders)
    assert pending["VITL"] == pytest.approx(8.0)


# ------- pre_trade_check with pending orders -------

def test_pre_trade_check_passes_with_pending(tmp_path):
    _write_sleeve(tmp_path / "o.json", {"VITL": 10.0, "MRP": 4.0})
    sleeve_paths = {"oracle": str(tmp_path / "o.json")}
    broker = {}  # broker shows 0 shares — orders haven't filled
    pending = {"VITL": 10.0, "MRP": 4.0}  # but queued orders account for it
    result = pre_trade_check(broker, sleeve_paths=sleeve_paths, pending_orders=pending)
    assert result is True


def test_pre_trade_check_fails_without_pending(tmp_path):
    _write_sleeve(tmp_path / "o.json", {"VITL": 10.0, "MRP": 4.0})
    sleeve_paths = {"oracle": str(tmp_path / "o.json")}
    broker = {}  # broker shows 0, no pending info
    result = pre_trade_check(broker, sleeve_paths=sleeve_paths)
    assert result is False


def test_pre_trade_check_partial_pending_still_fails(tmp_path):
    _write_sleeve(tmp_path / "o.json", {"VITL": 10.0})
    sleeve_paths = {"oracle": str(tmp_path / "o.json")}
    broker = {}
    pending = {"VITL": 5.0}  # only half accounted for
    result = pre_trade_check(broker, sleeve_paths=sleeve_paths, pending_orders=pending)
    assert result is False


def test_pre_trade_check_ignores_personal_overlap(tmp_path):
    """Broker has MORE shares than sleeve — personal holdings overlap. Should pass."""
    _write_sleeve(tmp_path / "d.json", {"AMD": 0.384, "CAT": 0.176})
    sleeve_paths = {"delphi": str(tmp_path / "d.json")}
    broker = {"AMD": 1.447, "CAT": 0.605}  # includes personal holdings
    result = pre_trade_check(broker, sleeve_paths=sleeve_paths)
    assert result is True


def test_pre_trade_check_catches_missing_shares(tmp_path):
    """Sleeve claims more than broker holds — real problem. Should fail."""
    _write_sleeve(tmp_path / "o.json", {"VITL": 10.0})
    sleeve_paths = {"oracle": str(tmp_path / "o.json")}
    broker = {"VITL": 3.0}  # broker has fewer than sleeve claims
    result = pre_trade_check(broker, sleeve_paths=sleeve_paths)
    assert result is False
