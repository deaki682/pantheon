"""Ghost Achilles tests — event adapter + per-class drift, all offline."""
import pytest

from achilles.ghost import briefs_to_candidates, drift_report
from shared.ghost import GhostEntry, grade_entries, numeric_tercile_stats, open_entries


def test_briefs_to_candidates_from_dicts():
    briefs = [
        {"symbol": "AAA", "event_class": "earnings_beat", "score": 0.8,
         "disqualifiers": [], "neglect": 0.7, "surprise_pct": 15.0,
         "insider_preactivity": True, "concurrent_guidance": False,
         "conviction": 0.85, "liquidity": 0.6},
        {"symbol": "BBB", "event_class": "guidance_raise", "score": 0.6,
         "disqualifiers": ["illiquid"]},
        {"symbol": "NOPX", "event_class": "spinoff", "score": 0.5,
         "disqualifiers": []},  # unpriceable
        {"symbol": "", "event_class": "x"},          # no symbol -> skipped
        {"symbol": "CCC", "event_class": ""},          # no class -> skipped
    ]
    prices = {"AAA": 10.0, "BBB": 20.0}
    cands = briefs_to_candidates(briefs, lambda s: prices.get(s))
    assert [c["symbol"] for c in cands] == ["AAA", "BBB"]
    assert cands[0]["source"] == "event"
    assert cands[0]["features"]["event_class"] == "earnings_beat"
    assert cands[0]["features"]["disqualified"] is False
    assert cands[1]["features"]["disqualified"] is True
    assert cands[0]["horizon_days"] == 10
    # convergence signals captured
    assert cands[0]["features"]["neglect"] == 0.7
    assert cands[0]["features"]["surprise_pct"] == 15.0
    assert cands[0]["features"]["insider_preactivity"] is True
    assert cands[0]["features"]["concurrent_guidance"] is False
    assert cands[0]["features"]["conviction"] == 0.85
    assert cands[0]["features"]["liquidity"] == 0.6


def test_briefs_to_candidates_missing_convergence_signals():
    briefs = [{"symbol": "AAA", "event_class": "earnings_beat", "score": 0.5,
               "disqualifiers": []}]
    cands = briefs_to_candidates(briefs, lambda s: 10.0)
    f = cands[0]["features"]
    assert f["neglect"] is None
    assert f["surprise_pct"] is None
    assert f["insider_preactivity"] is None
    assert f["concurrent_guidance"] is None
    assert f["conviction"] is None
    assert f["liquidity"] is None


def test_briefs_to_candidates_reads_dataclass_like():
    class Brief:
        def __init__(self, symbol, event_class, score, disqualifiers):
            self.symbol = symbol
            self.event_class = event_class
            self.score = score
            self.disqualifiers = disqualifiers
    cands = briefs_to_candidates([Brief("AAA", "earnings_beat", 0.9, [])], lambda s: 5.0)
    assert cands[0]["features"]["event_class"] == "earnings_beat"


def test_drift_report_measures_per_class_drift():
    briefs = [
        {"symbol": f"E{i}", "event_class": "earnings_beat", "disqualifiers": []} for i in range(3)
    ] + [
        {"symbol": f"G{i}", "event_class": "guidance_raise", "disqualifiers": []} for i in range(3)
    ]
    entry = {s: 100.0 for s in [f"E{i}" for i in range(3)] + [f"G{i}" for i in range(3)]}
    exit_ = {**{f"E{i}": 108.0 for i in range(3)}, **{f"G{i}": 97.0 for i in range(3)}}
    cands = briefs_to_candidates(briefs, lambda s: entry[s], default_horizon_days=10)
    book = open_entries(cands, today="2026-01-01")
    grade_entries(book, lambda s: exit_[s], today="2026-02-01")

    rep = drift_report(book)
    assert rep["n"] == 6
    assert rep["class_drift"]["earnings_beat"]["mean"] == pytest.approx(0.08)
    assert rep["class_drift"]["guidance_raise"]["mean"] == pytest.approx(-0.03)


def test_drift_report_disqualifier_lift():
    entries = []
    for i in range(3):
        e = GhostEntry(f"K{i}", "2026-01-01", 100.0, 10, "event",
                       features={"event_class": "earnings_beat", "disqualified": False})
        e.graded_return = 0.10
        entries.append(e)
    for i in range(3):
        e = GhostEntry(f"D{i}", "2026-01-01", 100.0, 10, "event",
                       features={"event_class": "earnings_beat", "disqualified": True})
        e.graded_return = -0.05
        entries.append(e)
    rep = drift_report(entries)
    lift = rep["lens_lift"]["disqualified"]
    assert lift["mean_on"] == pytest.approx(-0.05)
    assert lift["mean_off"] == pytest.approx(0.10)
    assert lift["lift"] == pytest.approx(-0.15)


def test_drift_report_neglect_terciles():
    entries = []
    for i in range(9):
        e = GhostEntry(f"N{i}", "2026-01-01", 100.0, 10, "event",
                       features={"neglect": i / 10.0, "event_class": "earnings_beat"})
        e.graded_return = i / 100.0  # higher neglect -> higher drift
        entries.append(e)
    rep = drift_report(entries)
    nt = rep["neglect_terciles"]
    assert nt["monotonic"] is True
    assert nt["terciles"]["high"]["mean"] > nt["terciles"]["low"]["mean"]


def test_drift_report_surprise_and_liquidity_terciles():
    entries = []
    for i in range(9):
        e = GhostEntry(f"S{i}", "2026-01-01", 100.0, 10, "event",
                       features={"surprise_pct": i * 5.0, "liquidity": (8 - i) / 10.0,
                                 "event_class": "earnings_beat"})
        e.graded_return = i / 100.0
        entries.append(e)
    rep = drift_report(entries)
    assert rep["surprise_terciles"]["n"] == 9
    assert rep["liquidity_terciles"]["n"] == 9


def test_drift_report_conviction_terciles():
    entries = []
    for i in range(9):
        e = GhostEntry(f"C{i}", "2026-01-01", 100.0, 10, "event",
                       features={"conviction": i / 10.0, "event_class": "earnings_beat"})
        e.graded_return = i / 100.0  # higher conviction -> higher return
        entries.append(e)
    rep = drift_report(entries)
    ct = rep["conviction_terciles"]
    assert ct["monotonic"] is True
    assert ct["terciles"]["high"]["mean"] > ct["terciles"]["low"]["mean"]


def test_drift_report_compound_signal_lift():
    entries = []
    for i in range(3):
        e = GhostEntry(f"I{i}", "2026-01-01", 100.0, 10, "event",
                       features={"insider_preactivity": True, "event_class": "earnings_beat"})
        e.graded_return = 0.15
        entries.append(e)
    for i in range(3):
        e = GhostEntry(f"X{i}", "2026-01-01", 100.0, 10, "event",
                       features={"insider_preactivity": False, "event_class": "earnings_beat"})
        e.graded_return = 0.02
        entries.append(e)
    rep = drift_report(entries)
    lift = rep["lens_lift"]["insider_preactivity"]
    assert lift["mean_on"] == pytest.approx(0.15)
    assert lift["mean_off"] == pytest.approx(0.02)
    assert lift["lift"] == pytest.approx(0.13)


def test_drift_report_empty():
    rep = drift_report([])
    assert rep["n"] == 0
    assert rep["neglect_terciles"] == {}
    assert rep["surprise_terciles"] == {}
    assert rep["conviction_terciles"] == {}
    assert rep["score_terciles"] == {}
    assert rep["liquidity_terciles"] == {}
