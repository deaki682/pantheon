"""The invariant floor as load-bearing code (charter v2.1 proposal, art. 28b).

OWNERSHIP: this file is OPERATOR-OWNED by definition upon ratification of
the v2.1 charter, regardless of its path matching Proteus's test glob.
Proteus may ADD assertions; he may never weaken, delete, or skip one.
Until ratification it stands as the drafted artifact attached to
docs/proteus_v2_charter_v2.1_PROPOSAL.md (drafted 2026-07-13 by Proteus
per the proposal's own condition-precedent clause).

Each test pins one floor behavior:
  invariant 2 — the kill-switch read (file present => active, no override)
  invariant 4 — journal-before-order refusal (stubs and soft entries refused)
  invariant 1 — bounded loss computed at entry (long option worst case = debit)
  house physics — the ledger contract (append_order round-trips faithfully)
"""
import json

import pytest

from proteus.journal import JournalError, validate_decision
from shared import guards
from shared.guards import OrderRecord, append_order, read_ledger


# ---------- invariant 2: the kill switch ----------

def test_kill_switch_inactive_when_file_absent(tmp_path):
    assert guards.kill_switch_active(cwd=str(tmp_path)) is False


def test_kill_switch_active_when_file_present(tmp_path):
    (tmp_path / guards.KILL_SWITCH_FILE).write_text("halt")
    assert guards.kill_switch_active(cwd=str(tmp_path)) is True


def test_kill_switch_filename_is_the_documented_contract():
    # The operator's control surface: a file literally named KILL_SWITCH.
    assert guards.KILL_SWITCH_FILE == "KILL_SWITCH"


# ---------- invariant 4: journal-before-order refusal ----------

def _valid_equity_enter():
    return {
        "action": "enter", "date": "2026-07-13", "symbol": "TEST",
        "side": "long", "dollars": 100.0, "price": 10.0, "spy_price": 750.0,
        "horizon_days": 30, "confidence": 0.6, "edge_class": "event_catalyst",
        "thesis": "t" * 200, "falsifiable_prediction": "p" * 80,
        "exit_plan": "e" * 40, "kill_condition": "k" * 20,
    }


def test_journal_accepts_a_complete_entry():
    validate_decision(_valid_equity_enter())


def test_journal_refuses_missing_fields():
    rec = _valid_equity_enter()
    del rec["falsifiable_prediction"]
    with pytest.raises(JournalError):
        validate_decision(rec)


def test_journal_refuses_thin_thesis():
    rec = _valid_equity_enter()
    rec["thesis"] = "it will go up"
    with pytest.raises(JournalError):
        validate_decision(rec)


def test_journal_refuses_nonpositive_dollars():
    rec = _valid_equity_enter()
    rec["dollars"] = 0
    with pytest.raises(JournalError):
        validate_decision(rec)


def test_journal_refuses_unknown_action():
    with pytest.raises(JournalError):
        validate_decision({"action": "yolo", "date": "2026-07-13"})


# ---------- invariant 1: bounded loss computed at entry ----------

def _valid_option_enter():
    return {
        "action": "enter", "instrument": "option", "date": "2026-07-13",
        "symbol": "TEST260918C00050000", "underlying": "TEST",
        "option_type": "call", "strike": 50.0, "expiration": "2026-09-18",
        "catalyst_date": "2026-08-15", "contracts": 1, "side": "long",
        "dollars": 150.0, "price": 1.50, "max_loss": 150.0,
        "spy_price": 750.0, "horizon_days": 60, "confidence": 0.55,
        "edge_class": "event_catalyst", "thesis": "t" * 200,
        "falsifiable_prediction": "p" * 80, "exit_plan": "e" * 40,
        "kill_condition": "k" * 20, "edge_arithmetic": "a" * 80,
    }


def test_option_entry_accepts_worst_case_equal_to_debit():
    validate_decision(_valid_option_enter())


def test_option_entry_refuses_max_loss_below_debit():
    # The dishonest-number pathway: claiming a worst case smaller than the
    # premium actually at risk. Refused mechanically.
    rec = _valid_option_enter()
    rec["max_loss"] = 75.0
    with pytest.raises(JournalError):
        validate_decision(rec)


def test_option_entry_refuses_dollars_inconsistent_with_contracts():
    rec = _valid_option_enter()
    rec["dollars"] = 999.0
    with pytest.raises(JournalError):
        validate_decision(rec)


def test_option_entry_refuses_short_side():
    # Forbidden instruments (naked shorts) cannot even be journaled.
    rec = _valid_option_enter()
    rec["side"] = "short"
    with pytest.raises(JournalError):
        validate_decision(rec)


def test_option_entry_refuses_expiry_inside_catalyst_buffer():
    rec = _valid_option_enter()
    rec["expiration"] = "2026-08-16"  # 1 day past catalyst — no buffer
    with pytest.raises(JournalError):
        validate_decision(rec)


# ---------- house physics: the ledger contract ----------

def test_ledger_append_round_trips(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    rec = OrderRecord(order_id="abc-123", symbol="TEST", side="buy",
                      dollars=150.0, date="2026-07-13",
                      shares=10.0, price=15.0, status="filled")
    append_order(path, rec)
    got = read_ledger(path)
    assert len(got) == 1 and got[0] == rec


def test_ledger_is_append_only_json_lines(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    r1 = OrderRecord(order_id="a", symbol="X", side="buy",
                     dollars=1.0, date="2026-07-13")
    r2 = OrderRecord(order_id="b", symbol="Y", side="sell",
                     dollars=2.0, date="2026-07-13")
    append_order(path, r1)
    append_order(path, r2)
    lines = open(path).read().strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["order_id"] == "a"
    assert json.loads(lines[1])["order_id"] == "b"
