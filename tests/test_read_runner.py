"""The session-driven CascadeRunner, tested with zero tokens. The load-bearing
test is PARITY: for the same packets/lens/reads, the stepwise runner must return
exactly what the in-process run_cascade returns — same survivors, drops, coverage,
spend, skips. If they ever diverge, the production path is lying about coverage."""
import json

import pytest

from shared.read_cascade import Lens, Tier, build_packet, run_cascade
from shared.read_runner import (
    CascadeRunner,
    dict_reader,
    read_answers,
    write_batch,
)


def _triage():
    return Tier(name="triage", model="sonnet", effort="low",
                prompt=lambda p: f"t {p['symbol']}",
                keep=lambda p, v: bool(v.get("advance")), est_tokens=500)


def _deep():
    return Tier(name="deep", model="opus", effort="high",
                prompt=lambda p: f"d {p['symbol']}",
                parse=lambda raw, p: {**raw, "fundable": bool(raw.get("defended"))},
                keep=lambda p, v: bool(v.get("fundable")), est_tokens=5000)


LENS = Lens(name="test", tiers=[_triage(), _deep()])
TRIAGE = {"A": {"advance": True}, "B": {"advance": True}, "C": {"advance": False}}
DEEP = {"A": {"defended": True}, "B": {"defended": False}}


def _stub(req):
    return (TRIAGE if req["model"] == "sonnet" else DEEP)[req["symbol"]]


def _drive(runner):
    """Drive a runner to completion, answering each batch from the stubs."""
    while not runner.done:
        batch = runner.next_batch()
        if batch is None:
            break
        runner.submit([_stub(r) for r in batch["reqs"]])
    return runner.result()


# ---- PARITY: stepwise == in-process ----------------------------------------
def test_runner_matches_run_cascade():
    packets = [build_packet(symbol=s) for s in "ABC"]
    ref = run_cascade(packets, LENS, lambda reqs: [_stub(r) for r in reqs], budget_tokens=10_000_000)
    got = _drive(CascadeRunner(packets, LENS, budget_tokens=10_000_000))
    assert [s["symbol"] for s in got.survivors] == [s["symbol"] for s in ref.survivors] == ["A"]
    assert {(d.symbol, d.tier) for d in got.dropped} == {(d.symbol, d.tier) for d in ref.dropped}
    assert got.coverage == ref.coverage
    assert got.spent_tokens == ref.spent_tokens
    assert got.skipped_for_budget == ref.skipped_for_budget
    assert got.budget_hit == ref.budget_hit


def test_runner_hands_out_tiers_in_order():
    packets = [build_packet(symbol=s) for s in "AB"]
    runner = CascadeRunner(packets, LENS, budget_tokens=10_000_000)
    b1 = runner.next_batch()
    assert b1["tier"] == "triage" and b1["model"] == "sonnet"
    assert [r["symbol"] for r in b1["reqs"]] == ["A", "B"]
    runner.submit([_stub(r) for r in b1["reqs"]])
    b2 = runner.next_batch()
    assert b2["tier"] == "deep" and b2["model"] == "opus"
    assert [r["symbol"] for r in b2["reqs"]] == ["A", "B"]   # both advanced from triage
    runner.submit([_stub(r) for r in b2["reqs"]])
    assert runner.next_batch() is None and runner.done


def test_runner_budget_binds_on_deep():
    # parity with run_cascade's realistic-budget test, stepwise
    packets = [build_packet(symbol=s) for s in "ABCDEF"]
    fn = lambda req: {"advance": True, "defended": True}
    ref = run_cascade(packets, LENS, lambda reqs: [fn(r) for r in reqs], budget_tokens=18_000)
    runner = CascadeRunner(packets, LENS, budget_tokens=18_000)
    while not runner.done:
        b = runner.next_batch()
        if b is None:
            break
        runner.submit([fn(r) for r in b["reqs"]])
    got = runner.result()
    assert got.coverage == ref.coverage
    assert got.coverage["triage"]["read"] == 6 and got.coverage["deep"]["read"] == 3
    assert len(got.skipped_for_budget) == 3 and got.budget_hit is True


def test_runner_all_dropped_auto_applies_empty_deep():
    packets = [build_packet(symbol=s) for s in "AB"]
    # triage drops everyone -> deep tier has no reqs, runner must auto-apply it
    runner = CascadeRunner(packets, LENS, budget_tokens=10_000_000)
    b = runner.next_batch()
    runner.submit([{"advance": False} for _ in b["reqs"]])
    assert runner.next_batch() is None and runner.done
    r = runner.result()
    assert r.survivors == []
    assert r.coverage["deep"] == {"read": 0, "advanced": 0, "dropped": 0, "skipped_budget": 0}


# ---- protocol guards -------------------------------------------------------
def test_next_batch_twice_without_submit_raises():
    runner = CascadeRunner([build_packet(symbol="A")], LENS, budget_tokens=10_000_000)
    runner.next_batch()
    with pytest.raises(RuntimeError):
        runner.next_batch()


def test_submit_without_batch_raises():
    runner = CascadeRunner([build_packet(symbol="A")], LENS, budget_tokens=10_000_000)
    with pytest.raises(RuntimeError):
        runner.submit([{"advance": True}])


def test_result_before_done_raises():
    runner = CascadeRunner([build_packet(symbol="A")], LENS, budget_tokens=10_000_000)
    runner.next_batch()
    with pytest.raises(RuntimeError):
        runner.result()


def test_submit_wrong_count_raises():
    runner = CascadeRunner([build_packet(symbol=s) for s in "AB"], LENS, budget_tokens=10_000_000)
    runner.next_batch()
    with pytest.raises(ValueError):
        runner.submit([{"advance": True}])          # 1 answer for 2 reqs


# ---- file contract + in-process bridge -------------------------------------
def test_write_and_read_batch_roundtrip(tmp_path):
    runner = CascadeRunner([build_packet(symbol="A")], LENS, budget_tokens=10_000_000)
    batch = runner.next_batch()
    p = str(tmp_path / "batch.json")
    write_batch(p, batch)
    loaded = json.load(open(p))
    assert loaded["reqs"][0]["symbol"] == "A"
    # answers back — both bare-list and {'answers': [...]} forms
    json.dump([{"advance": True}], open(str(tmp_path / "a.json"), "w"))
    assert read_answers(str(tmp_path / "a.json")) == [{"advance": True}]
    json.dump({"answers": [{"advance": False}], "meta": 1}, open(str(tmp_path / "b.json"), "w"))
    assert read_answers(str(tmp_path / "b.json")) == [{"advance": False}]


def test_dict_reader_bridges_and_guards():
    reader = dict_reader({"A": {"advance": True}, "B": {"advance": False}})
    assert reader([{"symbol": "A", "model": "sonnet"}]) == [{"advance": True}]
    with pytest.raises(KeyError):
        reader([{"symbol": "Z", "model": "sonnet"}])


def test_dict_reader_drives_a_whole_cascade():
    # the penny-run shape: the session hands the runner a map of the reads it did
    packets = [build_packet(symbol=s) for s in "AB"]
    reads = {"A": {"advance": True, "defended": True}, "B": {"advance": False}}
    reader = dict_reader(reads)
    runner = CascadeRunner(packets, LENS, budget_tokens=10_000_000)
    while not runner.done:
        b = runner.next_batch()
        if b is None:
            break
        runner.submit(reader(b["reqs"]))
    r = runner.result()
    assert [s["symbol"] for s in r.survivors] == ["A"]
