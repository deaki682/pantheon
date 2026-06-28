"""Ghost Delphi tests — candidate adapter + signal predictiveness, all offline."""
import pytest

from delphi.ghost import candidates_to_ghost, signal_report
from shared.ghost import grade_entries, numeric_tercile_stats, open_entries, GhostEntry


def test_candidates_to_ghost_skips_blocked_and_unpriceable():
    cands = [
        {"symbol": "AAA", "sector": "tech", "momentum": 0.2},
        {"symbol": "BBB", "sector": "energy", "blocked": True},  # blocked
        {"symbol": "NOPX", "sector": "tech", "momentum": 0.1},   # unpriceable
    ]
    prices = {"AAA": 30.0, "NOPX": None}
    cands_out = candidates_to_ghost(cands, lambda s: prices.get(s))
    assert [c["symbol"] for c in cands_out] == ["AAA"]
    assert cands_out[0]["source"] == "sector"
    assert cands_out[0]["features"]["sector"] == "tech"
    assert cands_out[0]["features"]["momentum"] == 0.2
    assert cands_out[0]["horizon_days"] == 90


def test_candidates_to_ghost_stamps_regime_and_chosen():
    cands = [
        {"symbol": "AAA", "sector": "tech", "momentum": 0.3},
        {"symbol": "BBB", "sector": "energy", "momentum": 0.1},
    ]
    g = candidates_to_ghost(
        cands, lambda s: 50.0,
        regime="risk_on", chosen_sectors=["tech"],
    )
    assert g[0]["features"]["regime"] == "risk_on"
    assert g[0]["features"]["chosen"] is True   # tech was chosen
    assert g[1]["features"]["chosen"] is False   # energy was not chosen


def test_candidates_to_ghost_chosen_none_when_no_sectors():
    cands = [{"symbol": "AAA", "sector": "tech", "momentum": 0.1}]
    g = candidates_to_ghost(cands, lambda s: 10.0)
    assert g[0]["features"]["chosen"] is None
    assert g[0]["features"]["regime"] is None


def test_signal_report_per_sector_and_momentum_terciles():
    cands = [
        {"symbol": "T1", "sector": "tech", "momentum": 0.30},
        {"symbol": "T2", "sector": "tech", "momentum": 0.20},
        {"symbol": "E1", "sector": "energy", "momentum": 0.05},
        {"symbol": "E2", "sector": "energy", "momentum": -0.05},
    ]
    entry = {c["symbol"]: 100.0 for c in cands}
    exit_ = {"T1": 130.0, "T2": 120.0, "E1": 102.0, "E2": 95.0}
    g = candidates_to_ghost(cands, lambda s: entry[s])
    book = open_entries(g, today="2026-01-01")
    grade_entries(book, lambda s: exit_[s], today="2026-06-01")

    rep = signal_report(book)
    assert rep["n"] == 4
    assert rep["sector_return"]["tech"]["mean"] == pytest.approx(0.25)
    assert rep["sector_return"]["energy"]["mean"] == pytest.approx(-0.015)
    mt = rep["momentum_terciles"]
    assert mt["terciles"]["high"]["mean"] >= mt["terciles"]["low"]["mean"]


def test_signal_report_regime_return():
    entries = []
    for regime, ret in [("risk_on", 0.15), ("risk_on", 0.10),
                        ("cautious", -0.02), ("risk_off", -0.08)]:
        e = GhostEntry(f"R{len(entries)}", "2026-01-01", 100.0, 90, "sector",
                       features={"regime": regime, "momentum": 0.1})
        e.graded_return = ret
        entries.append(e)
    rep = signal_report(entries)
    assert rep["regime_return"]["risk_on"]["mean"] == pytest.approx(0.125)
    assert rep["regime_return"]["risk_off"]["mean"] == pytest.approx(-0.08)


def test_signal_report_rotation_lift():
    entries = []
    for i in range(3):
        e = GhostEntry(f"C{i}", "2026-01-01", 100.0, 90, "sector",
                       features={"chosen": True, "momentum": 0.2})
        e.graded_return = 0.12
        entries.append(e)
    for i in range(3):
        e = GhostEntry(f"U{i}", "2026-01-01", 100.0, 90, "sector",
                       features={"chosen": False, "momentum": 0.05})
        e.graded_return = -0.04
        entries.append(e)
    rep = signal_report(entries)
    lift = rep["rotation_lift"]["chosen"]
    assert lift["mean_on"] == pytest.approx(0.12)
    assert lift["mean_off"] == pytest.approx(-0.04)
    assert lift["lift"] == pytest.approx(0.16)


def test_numeric_tercile_stats_detects_predictive_signal():
    entries = []
    for i in range(9):
        e = GhostEntry(f"S{i}", "2026-01-01", 100.0, 90, "sector",
                       features={"momentum": i / 10.0})
        e.graded_return = i / 100.0
        entries.append(e)
    out = numeric_tercile_stats(entries, "momentum")
    assert out["n"] == 9
    assert out["monotonic"] is True
    assert out["terciles"]["high"]["mean"] > out["terciles"]["low"]["mean"]


def test_numeric_tercile_stats_too_few():
    entries = [GhostEntry("A", "2026-01-01", 100.0, 90, "sector", features={"momentum": 0.1})]
    entries[0].graded_return = 0.05
    assert numeric_tercile_stats(entries, "momentum")["terciles"] == {}


def test_signal_report_empty():
    rep = signal_report([])
    assert rep["n"] == 0
    assert rep["regime_return"] == {}
    assert rep["rotation_lift"] == {}
