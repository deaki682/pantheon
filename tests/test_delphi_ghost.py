"""Ghost Delphi tests — candidate adapter + signal predictiveness, all offline."""
import pytest

from delphi.ghost import candidates_to_ghost, signal_report
from shared.ghost import grade_entries, numeric_tercile_stats, open_entries, GhostEntry


def test_candidates_to_ghost_skips_blocked_and_unpriceable():
    cands = [
        {"symbol": "AAA", "sector": "tech", "momentum": 0.2, "quality": 0.8, "score": 0.44},
        {"symbol": "BBB", "sector": "energy", "score": 0.0, "blocked": True},  # blocked
        {"symbol": "NOPX", "sector": "tech", "momentum": 0.1, "score": 0.1},   # unpriceable
    ]
    prices = {"AAA": 30.0, "NOPX": None}
    cands_out = candidates_to_ghost(cands, lambda s: prices.get(s))
    assert [c["symbol"] for c in cands_out] == ["AAA"]
    assert cands_out[0]["source"] == "sector"
    assert cands_out[0]["features"]["sector"] == "tech"
    assert cands_out[0]["features"]["momentum"] == 0.2
    assert cands_out[0]["horizon_days"] == 90


def test_signal_report_per_sector_and_momentum_terciles():
    # tech names up, energy down; momentum monotonic with return
    cands = [
        {"symbol": "T1", "sector": "tech", "momentum": 0.30, "score": 0.4},
        {"symbol": "T2", "sector": "tech", "momentum": 0.20, "score": 0.3},
        {"symbol": "E1", "sector": "energy", "momentum": 0.05, "score": 0.1},
        {"symbol": "E2", "sector": "energy", "momentum": -0.05, "score": 0.0},
    ]
    entry = {c["symbol"]: 100.0 for c in cands}
    # higher momentum -> higher forward return
    exit_ = {"T1": 130.0, "T2": 120.0, "E1": 102.0, "E2": 95.0}
    g = candidates_to_ghost(cands, lambda s: entry[s])
    book = open_entries(g, today="2026-01-01")
    grade_entries(book, lambda s: exit_[s], today="2026-06-01")

    rep = signal_report(book)
    assert rep["n"] == 4
    assert rep["sector_return"]["tech"]["mean"] == pytest.approx(0.25)
    assert rep["sector_return"]["energy"]["mean"] == pytest.approx(-0.015)
    # momentum should be monotonic (high tercile beats low tercile)
    mt = rep["momentum_terciles"]
    assert mt["terciles"]["high"]["mean"] >= mt["terciles"]["low"]["mean"]


def test_numeric_tercile_stats_detects_predictive_signal():
    # build entries where the feature perfectly orders returns
    entries = []
    for i in range(9):
        e = GhostEntry(f"S{i}", "2026-01-01", 100.0, 90, "sector",
                       features={"momentum": i / 10.0})
        e.graded_return = i / 100.0  # higher momentum -> higher return
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
    assert signal_report([])["n"] == 0
