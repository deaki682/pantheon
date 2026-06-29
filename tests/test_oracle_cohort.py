from oracle.cohort import (
    DRAWDOWN_EXIT_THRESHOLD,
    Cohort,
    CohortPosition,
    check_thesis_break,
    create_cohort,
    grade_cohort,
    load_cohort,
    record_exit,
    save_cohort,
    should_review,
)


def _dossier(symbol="ACME", thesis="test thesis", price=100.0, sector="Tech"):
    return {
        "symbol": symbol,
        "thesis": thesis,
        "current_price": price,
        "sector": sector,
        "ratings": {"moat": 0.7, "runway": 0.7, "quality": 0.7, "management": 0.5},
        "scenarios": {
            "bull": {"target": 200, "probability": 0.3},
            "base": {"target": 120, "probability": 0.5},
            "bear": {"target": 50, "probability": 0.2},
        },
    }


def _cohort(symbols=("ACME", "BETA"), entry_price=100.0):
    positions = {}
    for sym in symbols:
        positions[sym] = CohortPosition(
            symbol=sym,
            entry_price=entry_price,
            entry_date="2026-06-29",
            thesis_snapshot="test thesis",
            sector="Tech",
        )
    return Cohort(
        cohort_id="cohort-1",
        inception_date="2026-06-29",
        review_date="2027-06-29",
        positions=positions,
    )


def test_create_cohort():
    dossiers = [_dossier("ACME"), _dossier("BETA", price=50.0)]
    prices = {"ACME": 100.0, "BETA": 52.0}
    c = create_cohort("c1", dossiers, prices, inception_date="2026-06-29", review_date="2027-06-29")
    assert c.cohort_id == "c1"
    assert c.status == "active"
    assert set(c.active_symbols()) == {"ACME", "BETA"}
    assert c.positions["BETA"].entry_price == 52.0


def test_active_symbols_excludes_exited():
    c = _cohort()
    record_exit(c, "ACME", exit_price=80.0, exit_date="2026-09-01", exit_reason="drawdown")
    assert c.active_symbols() == ["BETA"]


def test_check_thesis_break_hold_by_default():
    c = _cohort()
    result = check_thesis_break("ACME", c, current_price=95.0)
    assert result is None


def test_check_thesis_break_drawdown():
    c = _cohort(entry_price=100.0)
    result = check_thesis_break("ACME", c, current_price=59.0)
    assert result is not None
    assert result["reason"] == "drawdown"


def test_check_thesis_break_drawdown_threshold():
    c = _cohort(entry_price=100.0)
    assert check_thesis_break("ACME", c, current_price=61.0) is None
    assert check_thesis_break("ACME", c, current_price=60.0) is not None


def test_check_thesis_break_fraud():
    c = _cohort()
    result = check_thesis_break("ACME", c, current_price=100.0, fraud_flag=True)
    assert result["reason"] == "fraud"


def test_check_thesis_break_going_concern():
    c = _cohort()
    result = check_thesis_break("ACME", c, current_price=100.0, going_concern_flag=True)
    assert result["reason"] == "going_concern"


def test_check_thesis_break_insider_reversal():
    c = _cohort()
    result = check_thesis_break("ACME", c, current_price=100.0, insider_reversal=True)
    assert result["reason"] == "insider_reversal"


def test_check_thesis_break_thesis_exhausted():
    c = _cohort()
    result = check_thesis_break("ACME", c, current_price=100.0, thesis_exhausted=True)
    assert result["reason"] == "thesis_exhausted"


def test_check_thesis_break_dossier_moat_quality_collapse():
    c = _cohort()
    bad_dossier = _dossier()
    bad_dossier["ratings"]["moat"] = 0.1
    bad_dossier["ratings"]["quality"] = 0.1
    result = check_thesis_break("ACME", c, current_price=100.0, dossier=bad_dossier)
    assert result["reason"] == "thesis_break"


def test_check_thesis_break_skips_already_exited():
    c = _cohort()
    record_exit(c, "ACME", exit_price=80.0, exit_date="2026-09-01", exit_reason="drawdown")
    result = check_thesis_break("ACME", c, current_price=50.0, fraud_flag=True)
    assert result is None


def test_check_thesis_break_unknown_symbol():
    c = _cohort()
    assert check_thesis_break("ZZZZ", c, current_price=100.0) is None


def test_record_exit():
    c = _cohort(entry_price=100.0)
    record_exit(c, "ACME", exit_price=55.0, exit_date="2026-10-01", exit_reason="drawdown")
    pos = c.positions["ACME"]
    assert pos.exit_date == "2026-10-01"
    assert pos.exit_reason == "drawdown"
    assert pos.graded_return is not None
    assert abs(pos.graded_return - (-0.45)) < 1e-9


def test_grade_cohort():
    c = _cohort(entry_price=100.0)
    record_exit(c, "ACME", exit_price=55.0, exit_date="2026-10-01", exit_reason="drawdown")
    result = grade_cohort(c, {"BETA": 130.0})
    assert c.status == "closed"
    assert result["n_thesis_break"] == 1
    assert result["n_held_to_horizon"] == 1
    assert result["positions"]["ACME"]["held_to_horizon"] is False
    assert result["positions"]["BETA"]["held_to_horizon"] is True
    assert abs(result["positions"]["BETA"]["return"] - 0.30) < 1e-9


def test_should_review():
    c = _cohort()
    assert not should_review(c, "2026-12-01")
    assert should_review(c, "2027-06-29")
    assert should_review(c, "2027-07-01")


def test_save_load_roundtrip(tmp_path):
    c = _cohort()
    record_exit(c, "ACME", exit_price=55.0, exit_date="2026-10-01", exit_reason="drawdown")
    path = str(tmp_path / "cohort.json")
    save_cohort(path, c)
    loaded = load_cohort(path)
    assert loaded is not None
    assert loaded.cohort_id == c.cohort_id
    assert loaded.status == "active"
    assert loaded.positions["ACME"].exit_reason == "drawdown"
    assert loaded.positions["BETA"].exit_date == ""


def test_load_cohort_missing():
    assert load_cohort("/nonexistent/path.json") is None


def test_drawdown_threshold_value():
    assert DRAWDOWN_EXIT_THRESHOLD == 0.40
