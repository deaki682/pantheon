import json
import os

import pytest

from shared.guards import (
    KILL_SWITCH_FILE,
    OrderRecord,
    already_placed_today,
    append_order,
    filter_orders_by_ledger,
    is_live,
    kill_switch_active,
    liquidate_if_kill,
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
