"""Ghost Achilles tests — event adapter + per-class drift, all offline."""
import pytest

from achilles.ghost import briefs_to_candidates, drift_report
from shared.ghost import GhostEntry, grade_entries, open_entries


def test_briefs_to_candidates_from_dicts():
    briefs = [
        {"symbol": "AAA", "event_class": "earnings_beat", "score": 0.8, "disqualifiers": []},
        {"symbol": "BBB", "event_class": "guidance_raise", "score": 0.6, "disqualifiers": ["illiquid"]},
        {"symbol": "NOPX", "event_class": "spinoff", "score": 0.5, "disqualifiers": []},  # unpriceable
        {"symbol": "", "event_class": "x"},          # no symbol -> skipped
        {"symbol": "CCC", "event_class": ""},          # no class -> skipped
    ]
    prices = {"AAA": 10.0, "BBB": 20.0}
    cands = briefs_to_candidates(briefs, lambda s: prices.get(s))
    assert [c["symbol"] for c in cands] == ["AAA", "BBB"]
    assert cands[0]["source"] == "event"
    assert cands[0]["features"]["event_class"] == "earnings_beat"
    assert cands[0]["features"]["disqualified"] is False
    assert cands[1]["features"]["disqualified"] is True  # had a disqualifier
    assert cands[0]["horizon_days"] == 10  # short event horizon


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
    # earnings_beat names drift +8%, guidance_raise -3% -> measured per class
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
    # disqualified events did worse -> negative lift validates the filter
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
    assert lift["mean_on"] == pytest.approx(-0.05)   # disqualified
    assert lift["mean_off"] == pytest.approx(0.10)    # kept
    assert lift["lift"] == pytest.approx(-0.15)       # filter earns its keep


def test_drift_report_empty():
    assert drift_report([])["n"] == 0
