"""Ghost Delphi tests — candidate adapter + signal predictiveness, all offline."""
import pytest

from delphi.ghost import candidates_to_ghost, signal_report
from shared.ghost import grade_entries, numeric_tercile_stats, open_entries, GhostEntry


def test_candidates_to_ghost_skips_unpriceable():
    cands = [
        {"symbol": "AAA", "momentum": 0.2, "price": 30.0, "ma": 25.0},
        {"symbol": "NOPX", "momentum": 0.1, "price": 50.0, "ma": 45.0},
    ]
    prices = {"AAA": 30.0, "NOPX": None}
    cands_out = candidates_to_ghost(cands, lambda s: prices.get(s))
    assert [c["symbol"] for c in cands_out] == ["AAA"]
    assert cands_out[0]["source"] == "momentum"
    assert cands_out[0]["features"]["momentum"] == 0.2


def test_candidates_to_ghost_above_ma_feature():
    cands = [
        {"symbol": "AAA", "momentum": 0.3, "price": 110.0, "ma": 100.0},
        {"symbol": "BBB", "momentum": 0.1, "price": 90.0, "ma": 100.0},
    ]
    g = candidates_to_ghost(cands, lambda s: 50.0)
    assert g[0]["features"]["above_ma"] is True
    assert g[1]["features"]["above_ma"] is False


def test_signal_report_momentum_terciles():
    entries = []
    for i in range(9):
        e = GhostEntry(f"S{i}", "2026-01-01", 100.0, 90, "momentum",
                       features={"momentum": i / 10.0})
        e.graded_return = i / 100.0
        entries.append(e)
    rep = signal_report(entries)
    assert rep["n"] == 9
    mt = rep["momentum_terciles"]
    assert mt["terciles"]["high"]["mean"] > mt["terciles"]["low"]["mean"]


def test_signal_report_empty():
    rep = signal_report([])
    assert rep["n"] == 0
    assert rep["momentum_terciles"] == {}
