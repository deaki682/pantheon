import json

import pytest

from delphi.decisions import append_decision, load_decisions, override_summary


def test_append_and_load_roundtrip(tmp_path):
    p = str(tmp_path / "decisions.jsonl")
    append_decision({"date": "2026-07-02", "breadth_pct": 0.55, "risk_budget": 0.85,
                     "exits_overridden": 0, "entries_vetoed": 0}, path=p)
    append_decision({"date": "2026-07-03", "entries_vetoed": 1, "vetoed_symbols": ["XYZ"],
                     "exits_overridden": 0, "risk_budget": 1.0}, path=p)
    rows = load_decisions(p)
    assert [r["date"] for r in rows] == ["2026-07-02", "2026-07-03"]


def test_append_rejects_non_dict(tmp_path):
    p = str(tmp_path / "d.jsonl")
    with pytest.raises(TypeError):
        append_decision("cache/delphi_decisions.jsonl", path=p)  # the exact historical failure


def test_append_rejects_missing_date(tmp_path):
    p = str(tmp_path / "d.jsonl")
    with pytest.raises(ValueError):
        append_decision({"breadth_pct": 0.5}, path=p)


def test_append_rejects_partial_decision_stub(tmp_path):
    """LLM integration audit 2026-07-04, finding #5: a date-only (or
    otherwise partial) record used to pass silently and then get counted
    by override_summary as '0 overrides' — indistinguishable from a run
    that genuinely had zero overrides."""
    p = str(tmp_path / "d.jsonl")
    with pytest.raises(ValueError):
        append_decision({"date": "2026-07-04"}, path=p)
    with pytest.raises(ValueError):
        append_decision({"date": "2026-07-04", "risk_budget": 0.85}, path=p)
    assert load_decisions(p) == []


def test_append_allows_halted_stub(tmp_path):
    """A run that stopped before the decision points is an honest stub as
    long as it self-declares via halt_reason."""
    p = str(tmp_path / "d.jsonl")
    append_decision({"date": "2026-07-04", "halt_reason": "pre_trade_check_failed"}, path=p)
    rows = load_decisions(p)
    assert rows[0]["halt_reason"] == "pre_trade_check_failed"


def test_load_skips_corrupt_lines(tmp_path):
    p = tmp_path / "d.jsonl"
    p.write_text('cache/delphi_decisions.jsonl\n{"date": "2026-07-02"}\nnot json\n')
    rows = load_decisions(str(p))
    assert len(rows) == 1
    assert rows[0]["date"] == "2026-07-02"


def test_load_missing_file(tmp_path):
    assert load_decisions(str(tmp_path / "nope.jsonl")) == []


def test_override_summary():
    rows = [
        {"date": "a", "exits_overridden": 1, "entries_vetoed": 2, "risk_budget": 1.0},
        {"date": "b", "exits_overridden": 0, "entries_vetoed": 1,
         "weight_overrides": {"NVDA": 1.3}, "risk_budget": 0.7},
    ]
    s = override_summary(rows)
    assert s["runs"] == 2
    assert s["decided_runs"] == 2
    assert s["halted_runs"] == 0
    assert s["exits_overridden"] == 1
    assert s["entries_vetoed"] == 3
    assert s["runs_with_weight_tilts"] == 1
    assert s["avg_risk_budget"] == pytest.approx(0.85)


def test_override_summary_excludes_halted_rows():
    """A halted month must not read as '0 overrides, all clear' — fixed
    alongside finding #5. A halted row is counted, but not averaged into
    the risk-budget / override rollup."""
    rows = [
        {"date": "a", "exits_overridden": 1, "entries_vetoed": 2, "risk_budget": 1.0},
        {"date": "b", "halt_reason": "pre_trade_check_failed"},
    ]
    s = override_summary(rows)
    assert s["runs"] == 2
    assert s["decided_runs"] == 1
    assert s["halted_runs"] == 1
    assert s["exits_overridden"] == 1
    assert s["avg_risk_budget"] == pytest.approx(1.0)
