"""Ghost Oracle tests — paper-only learning ledger, all offline."""
import pytest

from oracle.ghost import (
    GhostEntry, calibration_report, dossiers_to_candidates, grade_entries,
    load_ledger, open_entries, save_ledger, screen_rows_to_candidates,
)


def test_open_entries_unconstrained_and_skips_bad_price():
    cands = [
        {"symbol": "AAA", "price": 10.0, "source": "screen", "features": {"smart_money": True}},
        {"symbol": "BBB", "price": 2.5, "source": "screen"},
        {"symbol": "CCC", "price": 0.0},   # bad price -> skipped
        {"symbol": "", "price": 5.0},        # no symbol -> skipped
    ]
    entries = open_entries(cands, today="2026-01-01")
    assert [e.symbol for e in entries] == ["AAA", "BBB"]  # no caps, no min-ticket
    assert entries[0].features["smart_money"] is True


def test_open_entries_dedupes_same_day_same_source():
    cands = [{"symbol": "AAA", "price": 10.0, "source": "screen"}]
    first = open_entries(cands, today="2026-01-01")
    again = open_entries(cands, existing=first, today="2026-01-01")
    assert again == []  # already opened today
    # ...but a later day re-opens (more samples)
    later = open_entries(cands, existing=first, today="2026-02-01")
    assert len(later) == 1


def test_grade_entries_computes_return_at_horizon():
    e = GhostEntry("AAA", "2026-01-01", entry_price=100.0, horizon_days=30, source="screen")
    # before horizon -> not graded
    assert grade_entries([e], lambda s: 120.0, today="2026-01-15") == 0
    assert not e.graded
    # at/after horizon -> graded
    assert grade_entries([e], lambda s: 120.0, today="2026-02-15") == 1
    assert e.graded_return == pytest.approx(0.2)
    assert e.exit_price == 120.0


def test_grade_entries_survivorship_guard():
    e = GhostEntry("ZZZ", "2026-01-01", entry_price=100.0, horizon_days=30, source="screen")
    grade_entries([e], lambda s: None, today="2026-03-01")  # delisted -> can't price
    assert e.graded_return == -1.0  # graded as a loss, not dropped


def test_calibration_report_lens_lift_and_conviction_monotonic():
    entries = []
    # smart_money names did +20%, others -10% -> clear positive lift
    for i in range(5):
        e = GhostEntry(f"S{i}", "2026-01-01", 100.0, 30, "screen",
                       features={"smart_money": True})
        e.graded_return = 0.20
        entries.append(e)
    for i in range(5):
        e = GhostEntry(f"N{i}", "2026-01-01", 100.0, 30, "screen",
                       features={"smart_money": False})
        e.graded_return = -0.10
        entries.append(e)
    # conviction tiers, monotonic high>mid>low
    for conv, ret in [(0.9, 0.30), (0.5, 0.10), (0.2, -0.05)]:
        e = GhostEntry(f"D{conv}", "2026-01-01", 100.0, 365, "dossier",
                       features={"conviction": conv})
        e.graded_return = ret
        entries.append(e)

    rep = calibration_report(entries)
    assert rep["n"] == 13
    lift = rep["lens_lift"]["smart_money"]
    assert lift["mean_on"] == pytest.approx(0.20) and lift["mean_off"] == pytest.approx(-0.10)
    assert lift["lift"] == pytest.approx(0.30)  # smart_money worth +30pts here
    assert rep["conviction_monotonic"] is True
    assert rep["conviction_tiers"]["high"]["mean"] == pytest.approx(0.30)


def test_calibration_report_empty():
    assert calibration_report([])["n"] == 0


def test_screen_rows_to_candidates_attaches_price_and_lenses():
    rows = [
        {"symbol": "AAA", "score": 0.45, "lenses": {"smart_money": True, "quality": 0.9}},
        {"symbol": "NOPX", "score": 0.4, "lenses": {}},  # unpriceable -> dropped
    ]
    prices = {"AAA": 12.0}
    cands = screen_rows_to_candidates(rows, lambda s: prices.get(s))
    assert len(cands) == 1
    assert cands[0]["symbol"] == "AAA" and cands[0]["price"] == 12.0
    assert cands[0]["features"]["smart_money"] is True
    assert cands[0]["source"] == "screen"


def test_dossiers_to_candidates_uses_conviction_and_horizon():
    dossiers = [{"symbol": "AAA", "current_price": 50.0, "conviction": 0.8, "horizon_years": 2.0}]
    cands = dossiers_to_candidates(dossiers)
    assert cands[0]["features"]["conviction"] == 0.8
    assert cands[0]["horizon_days"] == 730
    assert cands[0]["source"] == "dossier"


def test_ledger_save_load_roundtrip(tmp_path):
    p = str(tmp_path / "ghost.json")
    entries = open_entries(
        [{"symbol": "AAA", "price": 10.0, "features": {"smart_money": True}}],
        today="2026-01-01",
    )
    entries[0].graded_return = 0.15
    save_ledger(p, entries)
    back = load_ledger(p)
    assert len(back) == 1
    assert back[0].symbol == "AAA"
    assert back[0].graded_return == 0.15
    assert back[0].features["smart_money"] is True


def test_load_ledger_missing_file():
    assert load_ledger("/nonexistent/ghost.json") == []
