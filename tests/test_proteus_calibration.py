"""Calibration ledger and grade counters (charter v2.1, arts. 2, 5, 10)."""
import pytest

from proteus import calibration as cal


def _grade(**kw):
    g = {"action": "grade", "date": "2026-08-01", "symbol": "T",
         "entry_date": "2026-07-13", "thesis_verdict": "HIT",
         "pnl_verdict": "PAID", "cell": "SKILL", "stated_p": 0.6,
         "strategy_class": "odd_lot_tender", "judgment_type": "document_read",
         "real_money": True, "shadow": False,
         "worst_case_pct_at_entry": 0.05, "basis": "b" * 60}
    g.update(kw)
    return g


def test_kelly_fraction():
    assert cal.kelly_fraction(0.6, 2.0) == pytest.approx(0.4)
    assert cal.kelly_fraction(0.25, 1.0) == pytest.approx(-0.5)
    with pytest.raises(ValueError):
        cal.kelly_fraction(0.0, 2.0)
    with pytest.raises(ValueError):
        cal.kelly_fraction(0.5, 0.0)


def test_ladder_counter_excludes_shadow_flatmonth_and_dust():
    records = [
        _grade(),
        _grade(shadow=True),
        _grade(flat_month=True),
        _grade(real_money=False),
        _grade(worst_case_pct_at_entry=0.005),   # under the 1% floor
        _grade(strategy_class="other_class"),
    ]
    assert cal.real_money_position_grades(records) == 2
    assert cal.real_money_position_grades(records, "odd_lot_tender") == 1
    assert cal.real_money_position_grades(records, "other_class") == 1


def test_ladder_counter_follows_reclassification():
    from proteus.registry import empty_registry, register_class, reclassify
    reg = empty_registry()
    register_class(reg, name="old_name", definition="d" * 40,
                   ledger_family="f", hunting_ground="g", created="2026-07-13")
    register_class(reg, name="new_name", definition="d" * 40,
                   ledger_family="f", hunting_ground="g", created="2026-07-13")
    reclassify(reg, old="old_name", new="new_name", mapping_note="n" * 40,
               date="2026-07-13")
    records = [_grade(strategy_class="old_name")]
    assert cal.real_money_position_grades(records, "new_name", reg) == 1


def test_kelly_multiplier_quarter_until_twenty():
    records = [_grade() for _ in range(19)]
    assert cal.allowed_kelly_multiplier(records) == cal.KELLY_BASE
    # 20 well-calibrated grades: p=0.6 stated, 60% realized
    records = ([_grade(stated_p=0.6) for _ in range(12)]
               + [_grade(stated_p=0.6, thesis_verdict="MISS",
                         pnl_verdict="UNPAID", cell="ERROR")
                  for _ in range(8)])
    assert cal.allowed_kelly_multiplier(records) == cal.KELLY_MAX


def test_kelly_multiplier_stays_quarter_when_miscalibrated():
    # 20 grades, stated 0.9 but realized 0.5 — gap 0.4 > 0.10
    records = ([_grade(stated_p=0.9) for _ in range(10)]
               + [_grade(stated_p=0.9, thesis_verdict="MISS",
                         pnl_verdict="UNPAID", cell="ERROR")
                  for _ in range(10)])
    assert cal.allowed_kelly_multiplier(records) == cal.KELLY_BASE


def test_calibration_table_partial_and_shadow():
    records = [
        _grade(stated_p=0.6),
        _grade(stated_p=0.6, thesis_verdict="PARTIAL", realized_fraction=0.5),
        _grade(stated_p=0.7, shadow=True, thesis_verdict="MISS",
               pnl_verdict="UNPAID", cell="ERROR"),
    ]
    t = cal.calibration_table(records)
    rm = t["aggregate"]["real_money"]
    assert rm["n"] == 2
    assert rm["realized"] == pytest.approx(0.75)   # (1 + 0.5) / 2
    sh = t["aggregate"]["shadow"]
    assert sh["n"] == 1 and sh["realized"] == 0.0
    assert t["by_judgment_type"]["document_read"]["real_money"]["n"] == 2


def test_partial_without_fraction_raises():
    with pytest.raises(ValueError):
        cal.calibration_table([_grade(thesis_verdict="PARTIAL")])


def test_drawdown_tier():
    assert cal.drawdown_tier(2500, 2500) == 0
    assert cal.drawdown_tier(1900, 2500) == 0     # -24%
    assert cal.drawdown_tier(1850, 2500) == 1     # -26%
    assert cal.drawdown_tier(1450, 2500) == 2     # -42%
    assert cal.drawdown_tier(100, 0) == 0
