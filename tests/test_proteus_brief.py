"""Proteus v2 — record brief generator tests (charter v2.1, art. 21)."""
import pytest

from proteus import brief
from proteus.builds import load_register, register_build


def _grade(cell, tv, pv, *, shadow=False, flat=False, real=None, p=0.6,
           cls="neglected_read", jt="doc_read", paid_pos=None, unaud=False):
    g = {"action": "grade", "date": "2026-08-01", "symbol": "TST",
         "entry_date": "2026-07-01", "cell": cell, "thesis_verdict": tv,
         "pnl_verdict": pv, "stated_p": p, "strategy_class": cls,
         "judgment_type": jt, "shadow": shadow,
         "real_money": (not shadow and not flat) if real is None else real,
         "worst_case_pct_at_entry": 0.05,
         "basis": "x" * 80}
    if flat:
        g["flat_month"] = True
    if tv == "PARTIAL":
        g["realized_fraction"] = 0.5
    if unaud:
        g["unauditable"] = True
    return g


def _marks(up=True):
    # two marks; sleeve beats or trails SPY depending on `up`
    eq1 = 1100.0 if up else 900.0
    return [
        {"date": "2026-07-01", "equity": 1000.0, "spy": 100.0,
         "risk_capital": 1000.0, "cash_park": 0.0, "tbill_park": 0.0,
         "index_park": 0.0},
        {"date": "2026-08-01", "equity": eq1, "spy": 100.0,
         "risk_capital": eq1, "cash_park": 0.0, "tbill_park": 0.0,
         "index_park": 0.0},
    ]


def test_grades_as_written_cells_kept_failed_and_arms():
    recs = [
        _grade("SKILL", "HIT", "PAID"),
        _grade("LUCK", "MISS", "PAID"),
        _grade("UNLUCKY", "HIT", "UNPAID"),
        _grade("ERROR", "MISS", "UNPAID"),
        _grade("SKILL", "PARTIAL", "PAID"),          # PARTIAL routes kept
        _grade("SKILL", "HIT", "PAID", shadow=True),  # shadow arm
        _grade(None, "HIT", "PAID", flat=True),       # flat month
        {"action": "note", "date": "2026-08-01", "text": "not a grade"},
    ]
    gw = brief.grades_as_written(recs)
    assert gw["n"] == 7
    assert gw["real_money"]["n"] == 5
    assert gw["real_money"]["cells"]["SKILL"] == 2
    assert gw["shadow"]["n"] == 1
    assert gw["flat_month"]["n"] == 1
    assert gw["kept"] == 5 and gw["failed"] == 2
    assert gw["luck"] == 1
    assert gw["real_money_majority"] is True  # 2 paper < 5 real


def test_unauditable_grade_counts_failed(monkeypatch=None):
    recs = [_grade("SKILL", "HIT", "PAID", unaud=True)]
    gw = brief.grades_as_written(recs)
    assert gw["failed"] == 1 and gw["kept"] == 0
    assert gw["unauditable"] == 1


def test_real_money_majority_fails_when_paper_half_or_more():
    recs = [_grade("SKILL", "HIT", "PAID"),
            _grade("SKILL", "HIT", "PAID", shadow=True)]
    gw = brief.grades_as_written(recs)
    assert gw["real_money_majority"] is False  # 1 paper, n=2: not < n-paper


def _passing_record_set():
    # 21 real-money grades: 12 strict SKILL, 4 LUCK, 5 ERROR
    recs = ([_grade("SKILL", "HIT", "PAID", p=0.6) for _ in range(12)]
            + [_grade("LUCK", "MISS", "PAID", p=0.6) for _ in range(4)]
            + [_grade("ERROR", "MISS", "UNPAID", p=0.6) for _ in range(5)])
    return recs


def test_funding_edge_passes_on_the_bar():
    recs = _passing_record_set()
    # realized freq = kept/(n) = 12/21 = 0.571 vs stated 0.6 -> gap ~3pp
    fe = brief.funding_edge(recs, _marks(up=True))
    assert fe["a_sample"]["pass"] is True
    assert fe["b_excess"]["pass"] is True
    assert fe["c_skill"]["skill_strict"] == 12 and fe["c_skill"]["luck"] == 4
    assert fe["c_skill"]["pass"] is True
    assert fe["pass"] is True


def test_funding_edge_partial_excluded_from_skill_count():
    # 20 grades where every P&L-positive "skill" is a PARTIAL: strict
    # SKILL count is 0, LUCK 1 -> leg (c) fails even though cells look fine
    recs = ([_grade("SKILL", "PARTIAL", "PAID", p=0.55) for _ in range(10)]
            + [_grade("LUCK", "MISS", "PAID", p=0.55)]
            + [_grade("ERROR", "MISS", "UNPAID", p=0.55) for _ in range(9)])
    fe = brief.funding_edge(recs, _marks(up=True))
    assert fe["c_skill"]["skill_strict"] == 0
    assert fe["c_skill"]["pass"] is False
    assert fe["pass"] is False


def test_funding_edge_needs_calibration_within_15pp():
    # stated p 0.95 everywhere but realized ~0.57 -> gap > 15pp on the
    # backing class -> leg (c) fails
    recs = ([_grade("SKILL", "HIT", "PAID", p=0.95) for _ in range(12)]
            + [_grade("LUCK", "MISS", "PAID", p=0.95) for _ in range(4)]
            + [_grade("ERROR", "MISS", "UNPAID", p=0.95) for _ in range(5)])
    fe = brief.funding_edge(recs, _marks(up=True))
    assert fe["c_skill"]["cal_within_15pp"] is False
    assert fe["pass"] is False


def test_funding_edge_fails_below_20_grades():
    recs = _passing_record_set()[:19]
    fe = brief.funding_edge(recs, _marks(up=True))
    assert fe["a_sample"]["pass"] is False
    assert fe["pass"] is False


def test_funding_edge_needs_positive_deployment_excess():
    fe = brief.funding_edge(_passing_record_set(), _marks(up=False))
    assert fe["b_excess"]["pass"] is False
    assert fe["pass"] is False


def test_no_edge_edge_trips_only_on_both_conditions():
    losing = ([_grade("ERROR", "MISS", "UNPAID") for _ in range(3)]
              + [_grade("SKILL", "HIT", "PAID")])
    trip = brief.no_edge_edge(losing, _marks(up=False))
    assert trip["park_default"] is True
    # trailing SPY but kept >= failed -> no trip
    winning = [_grade("SKILL", "HIT", "PAID") for _ in range(3)]
    assert brief.no_edge_edge(winning, _marks(up=False))["park_default"] is False
    # failed > kept but beating SPY -> no trip
    assert brief.no_edge_edge(losing, _marks(up=True))["park_default"] is False


def test_shortcut_summary_flags_recurring_identical_why():
    recs = [
        {"action": "note", "date": "2026-07-01", "shortcut_type": "stale_quote",
         "why": "quote is 2 minutes old and the decision is a screen-kill"},
        {"action": "note", "date": "2026-07-09", "shortcut_type": "stale_quote",
         "why": "quote is 2 minutes old and the decision is a screen-kill"},
    ]
    s = brief.shortcut_summary(recs)
    assert s["n"] == 2 and s["by_type"]["stale_quote"] == 2
    assert len(s["recurring_identical_why"]) == 1


def test_build_register_marks_flags_never_marked_and_dead(tmp_path):
    path = str(tmp_path / "reg.json")
    reg = load_register(path)
    register_build(reg, name="m1", sentence="s" * 40, observable="o" * 40,
                   kill_spec="k" * 40, built="2026-07-25")
    marks = brief.build_register_marks(reg)
    assert marks["machines"]["m1"]["never_marked"] is True
    reg["machines"]["m1"]["mark"] = "DEAD"
    assert brief.build_register_marks(reg)["dead_unpruned"] == ["m1"]


def test_brief_due_grade_time_and_drawdown_triggers():
    recs = [_grade("SKILL", "HIT", "PAID") for _ in range(20)]
    due = brief.brief_due(recs, _marks(), today="2026-08-01",
                          last_brief_grade_count=0)
    assert due["grade_trigger"] is True and due["due"] is True

    due = brief.brief_due([], _marks(), today="2026-10-01",
                          last_brief_date="2026-07-01")
    assert due["time_trigger"] is True and due["days_since_last"] == 92

    dd_marks = [{"date": "2026-07-01", "equity": 1000.0, "spy": 100.0},
                {"date": "2026-07-15", "equity": 740.0, "spy": 100.0}]
    due = brief.brief_due([], dd_marks, today="2026-07-16",
                          last_brief_date="2026-07-15")
    assert due["drawdown_trigger"] is True
    # already briefed for this drawdown -> not re-triggered
    due = brief.brief_due([], dd_marks, today="2026-07-16",
                          last_brief_date="2026-07-15", drawdown_briefed=True)
    assert due["drawdown_trigger"] is False


def test_brief_due_not_due_inside_all_windows():
    due = brief.brief_due([_grade("SKILL", "HIT", "PAID")], _marks(),
                          today="2026-08-15", last_brief_date="2026-08-01")
    assert due["due"] is False


def _attestation():
    return {inv: {"compliant": True, "basis": f"attested with a written basis for {inv}"}
            for inv in brief.INVARIANTS}


def test_record_brief_assembles_all_sections(tmp_path):
    reg = load_register(str(tmp_path / "reg.json"))
    b = brief.record_brief(_passing_record_set(), _marks(up=True), reg,
                           generated="2026-07-25", attestation=_attestation())
    for section in ("grades_as_written", "calibration", "kelly_multiplier",
                    "benchmark", "funding_edge", "no_edge_edge", "shortcuts",
                    "build_register", "attestation", "counting_note"):
        assert section in b
    assert b["benchmark"]["headline"]["excess"] > 0


def test_record_brief_refuses_missing_or_bare_attestation(tmp_path):
    reg = load_register(str(tmp_path / "reg.json"))
    att = _attestation()
    del att["effort_law"]
    with pytest.raises(brief.BriefError):
        brief.record_brief([], _marks(), reg, generated="2026-07-25",
                           attestation=att)
    att = _attestation()
    att["effort_law"]["basis"] = "short"
    with pytest.raises(brief.BriefError):
        brief.record_brief([], _marks(), reg, generated="2026-07-25",
                           attestation=att)
    att = _attestation()
    att["bounded_loss"]["compliant"] = False
    with pytest.raises(brief.BriefError):
        brief.record_brief([], _marks(), reg, generated="2026-07-25",
                           attestation=att)
    att = _attestation()
    att["extra_invariant"] = {"compliant": True, "basis": "x" * 30}
    with pytest.raises(brief.BriefError):
        brief.record_brief([], _marks(), reg, generated="2026-07-25",
                           attestation=att)
