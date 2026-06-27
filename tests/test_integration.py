"""End-to-end integration tests across modules."""
import json
import os
import subprocess

import pytest

from achilles.sleeve import AchillesSleeve
from delphi.sleeve import DelphiSleeve
from oracle.sleeve import OracleSleeve
from pantheon import persist
from shared.guards import (
    KILL_SWITCH_FILE, OrderRecord, append_order,
    filter_orders_by_ledger, kill_switch_active, liquidate_if_kill,
)


@pytest.fixture
def repos(tmp_path):
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    remote.mkdir()
    subprocess.run(["git", "init", "--bare", "-b", "main", "."], cwd=remote, check=True, capture_output=True)
    work.mkdir()
    subprocess.run(["git", "init", "-b", "main", "."], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=work, check=True, capture_output=True)
    return work, remote


def test_three_sleeves_independent():
    """Each god runs independently; nothing crosses."""
    o = OracleSleeve(initial_cash=1000)
    d = DelphiSleeve(initial_cash=1000)
    a = AchillesSleeve(initial_cash=1000)
    o.buy("AAPL", 1.0, 100.0, "2024-05-29")
    d.buy("MSFT", 1.0, 100.0, "2024-05-29")
    a.open(
        event_id="e1", symbol="GOOG", event_class="earnings_reaction",
        entry_price=100, score=0.2, hard_stop_price=92, profit_target_price=112,
        time_stop_date="2024-06-15", today="2024-05-29",
    )
    # Each holds only their own
    assert "AAPL" in o.positions and "MSFT" not in o.positions
    assert "MSFT" in d.positions and "AAPL" not in d.positions
    assert "e1" in a.positions
    assert a.positions["e1"].symbol == "GOOG"


def test_kill_switch_liquidates_all_three(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / KILL_SWITCH_FILE).write_text("")

    o = OracleSleeve(initial_cash=10_000)
    o.buy("AAPL", 1.0, 100.0, "2024-05-29")
    d = DelphiSleeve(initial_cash=10_000)
    d.buy("MSFT", 1.0, 100.0, "2024-05-29")
    a = AchillesSleeve(initial_cash=10_000)
    a.open(
        event_id="e1", symbol="GOOG", event_class="earnings_reaction",
        entry_price=100, score=0.2, hard_stop_price=92, profit_target_price=112,
        time_stop_date="2024-06-15", today="2024-05-29",
    )

    marks = {"AAPL": 100.0, "MSFT": 100.0, "GOOG": 100.0}
    liquidate_if_kill(o, marks, "2024-05-30")
    liquidate_if_kill(d, marks, "2024-05-30")
    liquidate_if_kill(a, marks, "2024-05-30")

    assert o.positions == {}
    assert d.positions == {}
    assert a.positions == {}


def test_persist_three_gods_no_clobber(repos):
    """Three persists in sequence, then verify all three sleeve files exist."""
    work, _ = repos
    persist("oracle", {"cache/oracle_sleeve.json": '{"cash": 1000}'},
            repo_dir=str(work), max_retries=2, base_backoff=0)
    persist("delphi", {"cache/delphi_sleeve.json": '{"cash": 1000}'},
            repo_dir=str(work), max_retries=2, base_backoff=0)
    persist("achilles", {"cache/achilles_sleeve.json": '{"cash": 1000}'},
            repo_dir=str(work), max_retries=2, base_backoff=0)
    p = subprocess.run(["git", "ls-tree", "-r", "--name-only", "refs/remotes/origin/claude/live"],
                       cwd=str(work), capture_output=True, text=True)
    files = set(p.stdout.strip().split("\n"))
    assert "cache/oracle_sleeve.json" in files
    assert "cache/delphi_sleeve.json" in files
    assert "cache/achilles_sleeve.json" in files


def test_ledger_per_god_isolation(tmp_path):
    """Two gods' ledgers don't bleed into each other."""
    oracle_path = tmp_path / "oracle_ledger.jsonl"
    delphi_path = tmp_path / "delphi_ledger.jsonl"
    append_order(str(oracle_path), OrderRecord("oracle-1", "AAPL", "buy", 100, "2024-05-29"))
    append_order(str(delphi_path), OrderRecord("delphi-1", "MSFT", "buy", 100, "2024-05-29"))

    broker = [{"order_id": "oracle-1"}, {"order_id": "delphi-1"}, {"order_id": "unknown"}]
    from shared.guards import read_ledger
    o_ledger = read_ledger(str(oracle_path))
    d_ledger = read_ledger(str(delphi_path))
    o_filtered = filter_orders_by_ledger(broker, o_ledger)
    d_filtered = filter_orders_by_ledger(broker, d_ledger)
    assert o_filtered == [{"order_id": "oracle-1"}]
    assert d_filtered == [{"order_id": "delphi-1"}]


def test_oracle_capital_gate_progression():
    """Walk through Oracle's capital allocation gate."""
    from oracle.capital import compute_allocation
    from oracle.sleeve import CAPITAL_BASE, CAPITAL_CEILING, ACHILLES_RESERVE

    # Day 1: no track record -> base
    assert compute_allocation(graded_calls=0, alpha=0, alpha_t=0, monotonic_conviction=False) == CAPITAL_BASE
    # Some calls but not enough -> base
    assert compute_allocation(graded_calls=10, alpha=0.10, alpha_t=3, monotonic_conviction=True) == CAPITAL_BASE
    # 30+ calls, monotonic, but bad alpha -> base
    assert compute_allocation(graded_calls=30, alpha=-0.05, alpha_t=3, monotonic_conviction=True) == CAPITAL_BASE
    # 30+ calls, alpha t=1.5 -> base (need >= 2)
    assert compute_allocation(graded_calls=30, alpha=0.05, alpha_t=1.5, monotonic_conviction=True) == CAPITAL_BASE
    # Proven -> scales up but capped
    out = compute_allocation(graded_calls=100, alpha=0.30, alpha_t=4.0, monotonic_conviction=True)
    assert CAPITAL_BASE < out <= CAPITAL_CEILING - ACHILLES_RESERVE


def test_achilles_event_keyed_two_positions_same_symbol():
    """Two events on the same stock -> two distinct positions, each with own stops."""
    s = AchillesSleeve(initial_cash=10_000, conservative_mode=False)
    s.open(
        event_id="earn1", symbol="ACME", event_class="earnings_reaction",
        entry_price=100, score=0.3, hard_stop_price=92, profit_target_price=112,
        time_stop_date="2024-06-15", today="2024-05-29",
    )
    s.open(
        event_id="cluster1", symbol="ACME", event_class="insider_cluster",
        entry_price=101, score=0.4, hard_stop_price=91, profit_target_price=116,
        time_stop_date="2024-06-29", today="2024-05-29",
    )
    assert len(s.positions) == 2
    assert s.positions["earn1"].event_class == "earnings_reaction"
    assert s.positions["cluster1"].event_class == "insider_cluster"
    # Each has its own stop set
    assert s.positions["earn1"].hard_stop_price == 92
    assert s.positions["cluster1"].hard_stop_price == 91
