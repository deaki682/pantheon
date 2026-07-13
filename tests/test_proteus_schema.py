"""The entry schema (charter v2.1, art. 15) — every duty refused mechanically."""
import pytest

from proteus.registry import empty_registry, register_class, register_tag
from proteus.schema import (AGGREGATE_CAP, EntryContext, SchemaError,
                            SINGLE_CAP, validate_record)


def _registry():
    reg = empty_registry()
    register_class(reg, name="event_convexity",
                   definition="Long options on primary-source dated events where the chain misprices the move.",
                   ledger_family="event_catalyst", hunting_ground="event_convexity",
                   created="2026-07-13")
    register_tag(reg, kind="failure_mode", name="event_no_show",
                 definition="The dated event resolves without the predicted market reaction.",
                 why_no_existing="first tag of its kind in a fresh registry",
                 created="2026-07-13")
    register_tag(reg, kind="judgment_type", name="document_read",
                 definition="A judgment formed by reading the primary document for the name.",
                 why_no_existing="first tag of its kind in a fresh registry",
                 created="2026-07-13")
    return reg


def _ctx(**kw):
    args = dict(sleeve_equity=2500.0, peak_equity=2500.0,
                open_worst_cases_total=0.0, class_open_worst_cases=0.0,
                class_real_grades=0, total_real_grades=0,
                first_in_family=True, registry=_registry())
    args.update(kw)
    return EntryContext(**args)


def _entry(**kw):
    # A probe-sized equity entry that satisfies every duty:
    # $250 notional, worst case $125 (the 50% floor) = 5% of equity.
    rec = {
        "action": "enter", "date": "2026-07-13", "symbol": "TEST",
        "side": "long", "dollars": 250.0, "price": 10.0, "spy_price": 750.0,
        "horizon_days": 30, "confidence": 0.6, "edge_class": "event_catalyst",
        "thesis": "t" * 200, "falsifiable_prediction": "p" * 80,
        "exit_plan": "e" * 40, "kill_condition": "k" * 20,
        "charter": {
            "instrument_kind": "single_name_equity",
            "strategy_class": "event_convexity",
            "worst_case": {"amount": 125.0, "basis": "b" * 60},
            "kelly": {"p": 0.6, "payoff_per_unit_worst_case": 2.0,
                      "fraction": 0.4, "multiplier": 0.25},
            "primary": {"direction": "up", "magnitude_pct": 8.0,
                        "by_date": "2026-08-13", "grading_rule": "g" * 80,
                        "stated_p": 0.6, "judgment_type": "document_read",
                        "cost_hurdle_pct": 0.5},
            "failure_modes": ["event_no_show"],
            "cluster_check": "c" * 40,
            "verified_wake": {"status": "none", "note": "n" * 40},
            "kill_switch_amenability": "a" * 40,
            "tape_verification": "v" * 40,
            "wash_sale_check": "w" * 20,
            "symbol_collision_check": "s" * 20,
            "citations": ["https://www.sec.gov/example-filing"],
            "ledger_check": "l" * 60,
            "spendable": {"sleeve_cash": 2500.0, "account_settled_bp": 2681.63,
                          "other_gods_pending": 0.0, "spendable": 2500.0},
            "staged": {"is_staged": False},
        },
    }
    rec.update(kw)
    return rec


def _charter(rec, **kw):
    rec["charter"].update(kw)
    return rec


def test_valid_entry_passes():
    validate_record(_entry(), _ctx())


def test_enter_requires_charter_and_context():
    rec = _entry()
    del rec["charter"]
    with pytest.raises(SchemaError, match="charter"):
        validate_record(rec, _ctx())
    with pytest.raises(SchemaError, match="EntryContext"):
        validate_record(_entry(), None)


def test_base_journal_floor_still_binds():
    # The schema layers ON TOP of the floor: a thin thesis dies underneath.
    rec = _entry(thesis="it will go up")
    with pytest.raises(Exception):
        validate_record(rec, _ctx())


def test_equity_worst_case_floor():
    rec = _entry()
    rec["charter"]["worst_case"]["amount"] = 50.0   # 20% of notional < 50%
    with pytest.raises(SchemaError, match="50%-of-notional"):
        validate_record(rec, _ctx())
    # a stated senior enforceable bound lifts the floor
    rec["charter"]["senior_bound"] = "s" * 60
    validate_record(rec, _ctx())


def test_index_fund_floor_scales_with_leverage():
    rec = _entry(symbol="SSO", dollars=250.0)
    rec["charter"]["instrument_kind"] = "index_fund"
    rec["charter"]["leverage"] = 2
    rec["charter"]["worst_case"]["amount"] = 80.0    # < 20% x 2 x 250 = 100
    with pytest.raises(SchemaError, match="leverage floor"):
        validate_record(rec, _ctx())
    rec["charter"]["worst_case"]["amount"] = 100.0
    validate_record(rec, _ctx())


def test_merger_target_worst_case_is_deal_break():
    rec = _entry()
    rec["charter"]["instrument_kind"] = "merger_target"
    rec["charter"]["deal_break_price"] = 7.0   # entry 10 -> 30% of notional
    rec["charter"]["worst_case"]["amount"] = 50.0   # < 75
    with pytest.raises(SchemaError, match="deal-break"):
        validate_record(rec, _ctx())
    rec["charter"]["worst_case"]["amount"] = 75.0
    validate_record(rec, _ctx())


def test_single_position_cap():
    # worst case 700 > 25% of 2500 = 625; keep Kelly/probe out of the way
    rec = _entry(dollars=1400.0)
    rec["charter"]["worst_case"]["amount"] = 700.0
    rec["charter"]["spendable"]["spendable"] = 2500.0
    ctx = _ctx(class_real_grades=3, total_real_grades=0)
    with pytest.raises(SchemaError, match="single-position"):
        validate_record(rec, ctx)


def test_aggregate_cap_counts_open_book():
    rec = _entry()  # wc 125
    ctx = _ctx(open_worst_cases_total=0.60 * 2500.0 - 50.0)
    with pytest.raises(SchemaError, match="aggregate"):
        validate_record(rec, ctx)


def test_drawdown_ladder_halves_caps():
    # equity 1800 vs peak 2500 = -28% -> single cap 12.5% = 225
    rec = _entry(dollars=500.0)
    rec["charter"]["worst_case"]["amount"] = 250.0
    ctx = _ctx(sleeve_equity=1800.0, peak_equity=2500.0,
               class_real_grades=3)
    with pytest.raises(SchemaError, match="halved"):
        validate_record(rec, ctx)


def test_probe_size_until_three_class_grades():
    # wc 300 = 12% of equity: inside the 25% cap, past the 10% probe
    rec = _entry(dollars=600.0)
    rec["charter"]["worst_case"]["amount"] = 300.0
    with pytest.raises(SchemaError, match="probe"):
        validate_record(rec, _ctx(class_real_grades=2))
    # kelly cap would also bind at 0.25*0.4*2500=250 — lift it via grades
    rec["charter"]["kelly"]["multiplier"] = 0.5
    validate_record(rec, _ctx(class_real_grades=3, total_real_grades=20,
                              kelly_multiplier=0.5))


def test_kelly_cap_binds_on_worst_case():
    # quarter-Kelly x 0.4 x 2500 = 250; wc 251 must die, 250 passes at 3 grades
    rec = _entry(dollars=502.0)
    rec["charter"]["worst_case"]["amount"] = 251.0
    with pytest.raises(SchemaError, match="Kelly"):
        validate_record(rec, _ctx(class_real_grades=3))


def test_negative_kelly_refused():
    rec = _entry()
    rec["charter"]["kelly"] = {"p": 0.3, "payoff_per_unit_worst_case": 1.0,
                               "fraction": -0.4, "multiplier": 0.25}
    rec["charter"]["primary"]["stated_p"] = 0.3
    with pytest.raises(SchemaError, match="no edge"):
        validate_record(rec, _ctx())


def test_kelly_arithmetic_must_be_shown_correctly():
    rec = _entry()
    rec["charter"]["kelly"]["fraction"] = 0.9
    with pytest.raises(SchemaError, match="does not match"):
        validate_record(rec, _ctx())


def test_stated_p_must_equal_kelly_p():
    rec = _entry()
    rec["charter"]["primary"]["stated_p"] = 0.7
    with pytest.raises(SchemaError, match="SAME"):
        validate_record(rec, _ctx())


def test_primary_below_cost_hurdle_refused():
    rec = _entry()
    rec["charter"]["primary"]["magnitude_pct"] = 0.4
    rec["charter"]["primary"]["cost_hurdle_pct"] = 0.5
    with pytest.raises(SchemaError, match="hurdle"):
        validate_record(rec, _ctx())


def test_unregistered_class_and_tags_refused():
    rec = _entry()
    rec["charter"]["strategy_class"] = "vibes"
    with pytest.raises(SchemaError, match="not registered"):
        validate_record(rec, _ctx())
    rec = _entry()
    rec["charter"]["failure_modes"] = ["unregistered_tag"]
    with pytest.raises(SchemaError, match="unregistered"):
        validate_record(rec, _ctx())


def test_ledger_check_required_first_in_family():
    rec = _entry()
    del rec["charter"]["ledger_check"]
    with pytest.raises(SchemaError, match="ledger_check"):
        validate_record(rec, _ctx(first_in_family=True))
    validate_record(rec, _ctx(first_in_family=False))


def test_spendable_arithmetic_rederived():
    rec = _entry()
    rec["charter"]["spendable"]["spendable"] = 2681.63   # forgot other gods
    with pytest.raises(SchemaError, match="spendable"):
        validate_record(rec, _ctx())


def test_dollars_capped_by_spendable():
    rec = _entry(dollars=300.0)
    rec["charter"]["worst_case"]["amount"] = 150.0
    rec["charter"]["spendable"].update(
        {"sleeve_cash": 200.0, "spendable": 200.0})
    with pytest.raises(SchemaError, match="exceeds spendable"):
        validate_record(rec, _ctx(class_real_grades=3))


def test_handoff_requires_solo_fallback():
    rec = _entry()
    rec["charter"]["handoff"] = {"what": "tender election",
                                 "deadline": "2026-08-01",
                                 "instruction": "elect all 99 shares"}
    with pytest.raises(SchemaError, match="solo_fallback"):
        validate_record(rec, _ctx())


def test_park_whitelist_and_no_primary():
    rec = _entry(symbol="SPY", dollars=2000.0)
    rec["charter"]["park"] = True
    rec["charter"]["park_reason"] = "r" * 40
    rec["charter"]["instrument_kind"] = "index_fund"
    rec["charter"]["leverage"] = 1
    rec["charter"]["worst_case"]["amount"] = 400.0   # 20% crash assumption
    with pytest.raises(SchemaError, match="no thesis prediction"):
        validate_record(rec, _ctx())
    del rec["charter"]["primary"]
    validate_record(rec, _ctx())   # caps exempt: 400 < 625 anyway, but
    rec = _entry(symbol="QQQ", dollars=2000.0)
    rec["charter"]["park"] = True
    rec["charter"]["park_reason"] = "r" * 40
    del rec["charter"]["primary"]
    with pytest.raises(SchemaError, match="not a park instrument"):
        validate_record(rec, _ctx())


def test_park_is_cap_exempt_but_worst_case_honest():
    # 100% of the sleeve into SPY: fine as a park (art. 1), refused as
    # a position (aggregate/single caps).
    rec = _entry(symbol="SPY", dollars=2500.0)
    rec["charter"]["park"] = True
    rec["charter"]["park_reason"] = "r" * 40
    rec["charter"]["instrument_kind"] = "index_fund"
    rec["charter"]["leverage"] = 1
    rec["charter"]["worst_case"]["amount"] = 500.0
    del rec["charter"]["primary"]
    validate_record(rec, _ctx())
    rec["charter"]["worst_case"]["amount"] = 100.0   # below the 20% floor
    with pytest.raises(SchemaError, match="leverage floor"):
        validate_record(rec, _ctx())


def test_staged_entry_mechanics(caplog):
    rec = _entry(dollars=100.0)
    rec["charter"]["worst_case"]["amount"] = 50.0
    rec["charter"]["staged"] = {"is_staged": True,
                                "mechanics_prediction": "m" * 60,
                                "code_change": "c" * 20}
    del rec["charter"]["kelly"]
    del rec["charter"]["primary"]
    del rec["charter"]["ledger_check"]
    validate_record(rec, _ctx())
    # oversize staged order needs the one-increment note
    rec2 = _entry(dollars=200.0)
    rec2["charter"]["worst_case"]["amount"] = 100.0
    rec2["charter"]["staged"] = {"is_staged": True,
                                 "mechanics_prediction": "m" * 60,
                                 "code_change": "c" * 20}
    del rec2["charter"]["kelly"]
    del rec2["charter"]["primary"]
    del rec2["charter"]["ledger_check"]
    with pytest.raises(SchemaError, match="minimum executable size"):
        validate_record(rec2, _ctx())


def test_option_entry_requires_lifecycle():
    rec = _entry(
        instrument="option", symbol="TEST260918C00050000",
        underlying="TEST", option_type="call", strike=50.0,
        expiration="2026-09-18", catalyst_date="2026-08-15", contracts=1,
        dollars=150.0, price=1.50, max_loss=150.0,
        edge_arithmetic="a" * 80)
    rec["charter"]["instrument_kind"] = "long_option"
    rec["charter"]["worst_case"]["amount"] = 150.0
    with pytest.raises(SchemaError, match="lifecycle"):
        validate_record(rec, _ctx())
    rec["charter"]["lifecycle"] = "l" * 60
    validate_record(rec, _ctx())


def test_exit_requires_tax_character():
    rec = {"action": "exit", "date": "2026-08-13", "symbol": "TEST",
           "price": 11.0, "spy_price": 760.0, "exit_reason": "exit_plan"}
    with pytest.raises(SchemaError, match="tax"):
        validate_record(rec)
    rec["tax"] = {"term": "short", "estimated_tax": 12.0,
                  "assumed_rate": 0.24}
    validate_record(rec)


def test_grade_cell_is_derived_not_chosen():
    g = {"action": "grade", "date": "2026-08-13", "symbol": "TEST",
         "entry_date": "2026-07-13", "thesis_verdict": "MISS",
         "pnl_verdict": "PAID", "cell": "SKILL", "stated_p": 0.6,
         "strategy_class": "event_convexity", "judgment_type": "document_read",
         "real_money": True, "shadow": False,
         "worst_case_pct_at_entry": 0.05, "basis": "b" * 60}
    with pytest.raises(SchemaError, match="LUCK"):
        validate_record(g)
    g["cell"] = "LUCK"
    validate_record(g)


def test_disposition_gradable_shadow_needs_divergence():
    d = {"action": "disposition", "date": "2026-07-13", "name": "CRCT",
         "verdict": "declined", "reason": "r" * 20,
         "shadow_primary": {"direction": "up", "magnitude_pct": 10.0,
                            "by_date": "2026-09-13",
                            "hypothetical_dollars": 250.0}}
    with pytest.raises(SchemaError, match="divergence"):
        validate_record(d)
    d["divergence"] = "d" * 40
    validate_record(d)
    # a plain AVOID needs no counterfactual
    validate_record({"action": "disposition", "date": "2026-07-13",
                     "name": "CRCT", "verdict": "avoid", "reason": "r" * 20})


def test_note_passes_through():
    validate_record({"action": "note", "date": "2026-07-13", "text": "t" * 40})


def test_unknown_action_refused():
    with pytest.raises(SchemaError):
        validate_record({"action": "yolo", "date": "2026-07-13"})
