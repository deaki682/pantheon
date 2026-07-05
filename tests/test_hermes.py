import pytest

from hermes.sleeve import (HermesBook, HermesError, PER_DEAL_CAP, MAX_CONCURRENT,
                           BREAK_STOP_PCT, MIN_SPREAD)
from hermes import ab as HAB


def _funded_book(cash=1000.0):
    b = HermesBook()
    b.pending_funding = {"from": "operator"}
    b.fund(amount=cash, source="operator", date="2026-07-06")
    return b


def test_min_spread_gate_rejects_spent_arb():
    b = _funded_book(1000.0)
    # trading AT the offer — no arb edge left
    with pytest.raises(HermesError):
        b.enter(symbol="ATOFFER", shares=10, price=10.0, offer_price=10.0,
                date="2026-07-06", expected_close="2026-10-01", spy_price=500.0, equity=1000.0)
    # trading ABOVE the offer — topping-bid speculation, not arb
    with pytest.raises(HermesError):
        b.enter(symbol="ABOVE", shares=10, price=10.2, offer_price=10.0,
                date="2026-07-06", expected_close="2026-10-01", spy_price=500.0, equity=1000.0)
    # a healthy spread still enters
    p = b.enter(symbol="OK", shares=10, price=9.5, offer_price=10.0,
                date="2026-07-06", expected_close="2026-10-01", spy_price=500.0, equity=1000.0)
    assert p.spread() >= MIN_SPREAD


# ── sleeve: funding + sizing (the ruin guard) ─────────────────────────

def _funded(cash=1000.0):
    b = HermesBook()
    b.pending_funding = {"from": "operator"}
    b.fund(amount=cash, source="operator", date="2026-07-06")
    return b


def test_unfunded_blocks_entry():
    b = HermesBook()
    b.pending_funding = {"from": "operator"}
    assert not b.is_funded()
    ok, why = b.can_enter("ABC", 100, 1000)
    assert not ok and "not funded" in why


def test_per_deal_cap_enforced():
    b = _funded(1000.0)
    # 20% of equity exceeds the 15% per-deal cap
    ok, why = b.can_enter("ABC", 200, 1000)
    assert not ok and "per-deal cap" in why
    ok, why = b.can_enter("ABC", 140, 1000)   # 14% < 15% cap
    assert ok


def test_break_stop_set_on_entry():
    b = _funded(1000.0)
    p = b.enter(symbol="ABC", shares=10, price=9.5, offer_price=10.0,
                date="2026-07-06", expected_close="2026-10-01", spy_price=500.0, equity=1000.0)
    assert p.break_stop == pytest.approx(9.5 * (1 - BREAK_STOP_PCT))
    assert p.spread() == pytest.approx(10.0 / 9.5 - 1)


def test_break_triggered_flags_broken_deal():
    b = _funded(1000.0)
    b.enter(symbol="ABC", shares=10, price=9.5, offer_price=10.0, date="2026-07-06",
            expected_close="2026-10-01", spy_price=500.0, equity=1000.0)
    assert b.break_triggered({"ABC": 9.5}) == []        # holding fine
    assert b.break_triggered({"ABC": 7.0}) == ["ABC"]   # gapped through the stop


def test_max_concurrent():
    b = _funded(100_000.0)
    for i in range(MAX_CONCURRENT):
        b.enter(symbol=f"D{i}", shares=1, price=10.0, offer_price=10.5, date="2026-07-06",
                expected_close="2026-10-01", spy_price=500.0, equity=100_000.0)
    ok, why = b.can_enter("EXTRA", 10, 100_000.0)
    assert not ok and "max concurrent" in why


def test_completion_and_break_returns():
    b = _funded(1000.0)
    b.enter(symbol="WIN", shares=10, price=9.5, offer_price=10.0, date="2026-07-06",
            expected_close="2026-10-01", spy_price=500.0, equity=1000.0)
    t = b.exit(symbol="WIN", price=10.0, date="2026-10-01", spy_price=510.0, outcome="completed")
    assert t.net_return == pytest.approx(10.0 / 9.5 - 1, abs=1e-6)   # ~+5.3% spread captured
    assert t.outcome == "completed"


def test_roundtrip_and_guard_registration():
    b = _funded(1234.5)
    b.enter(symbol="ABC", shares=10, price=9.0, offer_price=9.5, date="2026-07-06",
            expected_close="2026-09-01", spy_price=500.0, equity=1234.5)
    import tempfile, os
    p = os.path.join(tempfile.gettempdir(), "hermes_test_sleeve.json")
    b.save(p)
    b2 = HermesBook.load(p)
    assert b2.is_funded() and "ABC" in b2.positions
    os.unlink(p)
    from shared.guards import _LIVE_ENV, is_live
    assert _LIVE_ENV["hermes"] == "HERMES_LIVE"
    assert is_live("hermes", env={}) is False
    assert is_live("hermes", env={"HERMES_LIVE": "true"}) is True
    from pantheon.persist import owns, GUARD_FILES
    assert owns("hermes", "cache/hermes_sleeve.json")
    assert "cache/hermes_sleeve.json" in GUARD_FILES


# ── A/B tracker: LLM-lift ─────────────────────────────────────────────

def test_ab_records_and_lift():
    ab = {"detected": [], "graded": []}
    # LLM keeps a clean deal, drops a risky one
    HAB.record_detection(ab, symbol="GOOD", detect_date="2026-07-06", entry_price=9.5,
                         offer_price=10.0, spy_entry=500.0, expected_close="2026-10-01",
                         llm_verdict="keep", llm_rationale="clean financing, no antitrust",
                         break_risk="low", arm_a_live=True)
    HAB.record_detection(ab, symbol="RISKY", detect_date="2026-07-06", entry_price=8.0,
                         offer_price=10.0, spy_entry=500.0, expected_close="2026-10-01",
                         llm_verdict="drop", llm_rationale="CFIUS risk, wide spread",
                         break_risk="high", arm_a_live=False)
    # resolve: kept one completes (+5%), dropped one breaks (-25%)
    HAB.record_resolution(ab, symbol="GOOD", exit_price=10.0, exit_date="2026-10-01",
                          spy_exit=505.0, outcome="completed")
    HAB.record_resolution(ab, symbol="RISKY", exit_price=6.0, exit_date="2026-09-01",
                          spy_exit=505.0, outcome="broke")
    lift = HAB.llm_lift(ab)
    assert lift["n_graded"] == 2
    # Arm A (kept only) expectancy should beat Arm B (all deals incl. the break)
    assert lift["arm_A_llm_kept"]["expectancy"] > lift["arm_B_mechanical_all"]["expectancy"]
    assert lift["llm_lift_expectancy"] > 0
    assert lift["verdict"] == "LLM adds value"


def test_ab_dedup():
    ab = {"detected": [], "graded": []}
    for _ in range(2):
        HAB.record_detection(ab, symbol="ABC", detect_date="2026-07-06", entry_price=9.0,
                             offer_price=10.0, spy_entry=500.0, expected_close="2026-10-01",
                             llm_verdict="keep", llm_rationale="x", break_risk="low", arm_a_live=True)
    assert len(ab["detected"]) == 1
