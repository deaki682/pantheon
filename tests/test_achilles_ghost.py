import pytest

from achilles.ghost import HORIZON_DAYS, SOURCE, beats_to_candidates, pead_report
from achilles.scanner import BeatCandidate
from shared.ghost import GhostEntry, grade_entries


def _beat(sym, reaction=0.05, surprise=15.0, cap=1e9, price=50.0, **kw):
    return BeatCandidate(
        symbol=sym, surprise_pct=surprise, actual_eps=1.15, estimate_eps=1.0,
        report_date="2026-07-14", market_cap=cap, current_price=price,
        reaction_pct=reaction, **kw,
    )


def _px(mapping):
    return lambda s: mapping.get(s.upper())


class TestBeatsToCandidates:
    def test_opens_rewarded_sold_and_unconfirmed(self):
        beats = [_beat("WIN", reaction=0.06), _beat("SOLD", reaction=-0.04),
                 _beat("UNK", reaction=None)]
        out = beats_to_candidates(beats, _px({}))
        feats = {c["symbol"]: c["features"] for c in out}
        assert set(feats) == {"WIN", "SOLD", "UNK"}
        assert feats["WIN"]["rewarded"] is True
        assert feats["SOLD"]["rewarded"] is False          # sold beat = control group
        assert feats["UNK"]["rewarded"] is False
        assert feats["UNK"]["reaction_confirmed"] is False
        assert "reaction_pct" not in feats["UNK"]

    def test_tags_source_and_horizon(self):
        out = beats_to_candidates([_beat("A")], _px({}))
        assert out[0]["source"] == SOURCE
        assert out[0]["horizon_days"] == HORIZON_DAYS

    def test_price_falls_back_to_lookup(self):
        b = _beat("NOPX")
        b.current_price = None
        out = beats_to_candidates([b], _px({"NOPX": 12.5}))
        assert out[0]["price"] == 12.5

    def test_unpriceable_skipped(self):
        b = _beat("GHOST")
        b.current_price = None
        assert beats_to_candidates([b], _px({})) == []

    def test_basket_selected_only_on_rewarded(self):
        beats = [_beat("PICK", reaction=0.05), _beat("PASS", reaction=0.04),
                 _beat("SOLD", reaction=-0.02)]
        out = beats_to_candidates(beats, _px({}), basket_selected=["PICK"])
        feats = {c["symbol"]: c["features"] for c in out}
        assert feats["PICK"]["basket_selected"] is True
        assert feats["PASS"]["basket_selected"] is False
        # a sold beat was never eligible for the basket -> flag omitted
        assert "basket_selected" not in feats["SOLD"]

    def test_no_selection_flag_when_not_provided(self):
        out = beats_to_candidates([_beat("A")], _px({}))
        assert "basket_selected" not in out[0]["features"]

    def test_short_squeeze_derived(self):
        out = beats_to_candidates([_beat("SQ", short_float_pct=25.0)], _px({}))
        assert out[0]["features"]["short_squeeze"] is True


class TestPeadReport:
    def test_empty(self):
        r = pead_report([])
        assert r["n"] == 0

    def test_filters_out_retired_event_entries(self):
        old = GhostEntry("OLD", "2026-05-01", 10.0, 10, "event",
                         features={"event_class": "ma_target"}, graded_return=0.5)
        new = GhostEntry("NEW", "2026-07-14", 10.0, 7, "pead",
                         features={"rewarded": True, "surprise_pct": 12.0},
                         graded_return=0.04)
        r = pead_report([old, new])
        assert r["n"] == 1                      # the event-era entry is excluded
        assert r["mean_return"] == pytest.approx(0.04)

    def test_rewarded_lift_is_measured(self):
        # rewarded beats drift up, sold beats bleed -> gate shows positive lift
        entries = [
            GhostEntry("W1", "2026-07-14", 10.0, 7, "pead",
                       features={"rewarded": True}, graded_return=0.05),
            GhostEntry("W2", "2026-07-14", 10.0, 7, "pead",
                       features={"rewarded": True}, graded_return=0.03),
            GhostEntry("S1", "2026-07-14", 10.0, 7, "pead",
                       features={"rewarded": False}, graded_return=-0.04),
            GhostEntry("S2", "2026-07-14", 10.0, 7, "pead",
                       features={"rewarded": False}, graded_return=-0.02),
        ]
        lift = pead_report(entries)["signal_lift"]["rewarded"]
        assert lift["mean_on"] == pytest.approx(0.04)
        assert lift["mean_off"] == pytest.approx(-0.03)
        assert lift["lift"] == pytest.approx(0.07)

    def test_end_to_end_open_grade_report(self):
        beats = [_beat("UP", reaction=0.05, price=10.0),
                 _beat("DOWN", reaction=-0.03, price=10.0)]
        cands = beats_to_candidates(beats, _px({}))
        entries = [GhostEntry(symbol=c["symbol"], entry_date="2026-07-14",
                              entry_price=c["price"], horizon_days=c["horizon_days"],
                              source=c["source"], features=c["features"])
                   for c in cands]
        n = grade_entries(entries, _px({"UP": 11.0, "DOWN": 9.5}), today="2026-07-30")
        assert n == 2
        r = pead_report(entries)
        assert r["n"] == 2
        assert r["signal_lift"]["rewarded"]["lift"] > 0
