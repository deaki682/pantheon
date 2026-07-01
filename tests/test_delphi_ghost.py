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


# ── universe_to_ghost: full-universe control groups ──────────────────

from delphi.ghost import universe_to_ghost


def _prices(closes):
    return [float(c) for c in closes]


def _universe():
    # UP: rising, well above its 20d MA. DOWN: falling, below its MA.
    up = _prices(range(100, 170))          # 70 sessions, ends 169
    down = _prices(range(170, 100, -1))    # falling, ends 101
    return {"UP": up, "DOWN": down}


def test_universe_opens_below_ma_names_too():
    out = universe_to_ghost(_universe())
    feats = {c["symbol"]: c["features"] for c in out}
    assert set(feats) == {"UP", "DOWN"}          # below-MA name still opened
    assert feats["UP"]["above_ma"] is True
    assert feats["DOWN"]["above_ma"] is False    # the control group exists


def test_universe_momentum_computed():
    out = universe_to_ghost(_universe())
    feats = {c["symbol"]: c["features"] for c in out}
    assert feats["UP"]["momentum"] > 0
    assert feats["DOWN"]["momentum"] < 0


def test_selected_flag_only_on_above_ma():
    out = universe_to_ghost(_universe(), selected=["UP"])
    feats = {c["symbol"]: c["features"] for c in out}
    assert feats["UP"]["selected"] is True
    assert "selected" not in feats["DOWN"]       # never eligible -> no flag


def test_vetoed_flag_only_on_reviewed_set():
    up2 = _prices(range(100, 170))
    uni = {**_universe(), "UP2": up2}
    out = universe_to_ghost(uni, vetoed=["UP2"], reviewed=["UP", "UP2"])
    feats = {c["symbol"]: c["features"] for c in out}
    assert feats["UP2"]["vetoed"] is True
    assert feats["UP"]["vetoed"] is False
    assert "vetoed" not in feats["DOWN"]         # LLM never saw it


def test_no_flags_when_not_provided():
    out = universe_to_ghost(_universe())
    for c in out:
        assert "selected" not in c["features"]
        assert "vetoed" not in c["features"]


def test_report_filters_foreign_sources_and_lifts_above_ma():
    entries = [
        GhostEntry("A", "2026-01-01", 100.0, 90, "momentum",
                   features={"momentum": 0.5, "above_ma": True}, graded_return=0.10),
        GhostEntry("B", "2026-01-01", 100.0, 90, "momentum",
                   features={"momentum": -0.2, "above_ma": False}, graded_return=-0.05),
        GhostEntry("OLD", "2026-01-01", 100.0, 90, "screen",   # retired-strategy entry
                   features={"momentum": 9.9}, graded_return=0.99),
    ]
    rep = signal_report(entries)
    assert rep["n"] == 2                          # 'screen' entry excluded
    lift = rep["signal_lift"]["above_ma"]
    assert lift["lift"] == pytest.approx(0.15)
