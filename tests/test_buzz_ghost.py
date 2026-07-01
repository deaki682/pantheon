import pytest

from buzz.ghost import HORIZON_DAYS, buzz_report, candidates_to_ghost
from buzz.scanner import BuzzCandidate
from shared.ghost import GhostEntry, grade_entries


def _cand(ticker, accel=4.0, confirmed=True, vol_ratio=2.0, new_entrant=False):
    return BuzzCandidate(
        ticker=ticker, mentions=100, mentions_prev=20, accel_ratio=accel,
        rank_jump=10, new_entrant=new_entrant, upvotes=500, market_cap=1e9,
        price_change_pct=0.05, volume_ratio=vol_ratio, confirmed=confirmed,
        confirm_reason="confirmed" if confirmed else "no_price_no_volume",
    )


def _px(mapping):
    return lambda s: mapping.get(s.upper())


class TestCandidatesToGhost:
    def test_opens_confirmed_and_unconfirmed(self):
        cands = [_cand("AAA", confirmed=True), _cand("BBB", confirmed=False)]
        out = candidates_to_ghost(cands, _px({"AAA": 10.0, "BBB": 20.0}))
        assert {c["symbol"] for c in out} == {"AAA", "BBB"}
        assert all(c["horizon_days"] == HORIZON_DAYS for c in out)
        conf = {c["symbol"]: c["features"]["confirmed"] for c in out}
        assert conf == {"AAA": True, "BBB": False}

    def test_skips_unpriceable(self):
        out = candidates_to_ghost([_cand("AAA")], _px({}))
        assert out == []

    def test_carries_numeric_features(self):
        out = candidates_to_ghost([_cand("AAA", accel=6.5, vol_ratio=3.1)], _px({"AAA": 10.0}))
        f = out[0]["features"]
        assert f["accel_ratio"] == 6.5
        assert f["volume_ratio"] == 3.1

    def test_llm_flag_only_on_reviewed_confirmed(self):
        cands = [_cand("PICK", confirmed=True), _cand("PASS", confirmed=True),
                 _cand("UNCONF", confirmed=False)]
        out = candidates_to_ghost(
            cands, _px({"PICK": 1.0, "PASS": 1.0, "UNCONF": 1.0}),
            recommended=["PICK"],
        )
        feats = {c["symbol"]: c["features"] for c in out}
        assert feats["PICK"]["llm_recommended"] is True
        assert feats["PASS"]["llm_recommended"] is False
        # unconfirmed name was never reviewed -> flag omitted, not False
        assert "llm_recommended" not in feats["UNCONF"]

    def test_no_llm_flag_when_not_provided(self):
        out = candidates_to_ghost([_cand("AAA")], _px({"AAA": 10.0}))
        assert "llm_recommended" not in out[0]["features"]

    def test_insider_flag_on_reviewed_set(self):
        cands = [_cand("INS", confirmed=True), _cand("NOINS", confirmed=True)]
        out = candidates_to_ghost(
            cands, _px({"INS": 1.0, "NOINS": 1.0}), insider_backed=["INS"],
        )
        feats = {c["symbol"]: c["features"] for c in out}
        assert feats["INS"]["insider_backed"] is True
        assert feats["NOINS"]["insider_backed"] is False


class TestBuzzReport:
    def test_empty(self):
        r = buzz_report([])
        assert r["n"] == 0
        assert r["signal_lift"] == {}

    def test_confirmation_lift(self):
        # confirmed names win (+10%), unconfirmed lose (-5%) -> positive lift
        entries = [
            GhostEntry("A", "2026-06-01", 10.0, 5, "buzz",
                       features={"confirmed": True, "accel_ratio": 5.0},
                       graded_return=0.10),
            GhostEntry("B", "2026-06-01", 10.0, 5, "buzz",
                       features={"confirmed": True, "accel_ratio": 4.0},
                       graded_return=0.08),
            GhostEntry("C", "2026-06-01", 10.0, 5, "buzz",
                       features={"confirmed": False, "accel_ratio": 6.0},
                       graded_return=-0.05),
            GhostEntry("D", "2026-06-01", 10.0, 5, "buzz",
                       features={"confirmed": False, "accel_ratio": 3.0},
                       graded_return=-0.03),
        ]
        r = buzz_report(entries)
        assert r["n"] == 4
        lift = r["signal_lift"]["confirmed"]
        assert lift["mean_on"] == pytest.approx(0.09)
        assert lift["mean_off"] == pytest.approx(-0.04)
        assert lift["lift"] == pytest.approx(0.13)

    def test_grades_then_reports(self):
        cands = [_cand("AAA", confirmed=True), _cand("BBB", confirmed=False)]
        entries = [GhostEntry(**{k: v for k, v in {
            "symbol": c["symbol"], "entry_date": "2026-06-01",
            "entry_price": c["price"], "horizon_days": 5, "source": "buzz",
            "features": c["features"],
        }.items()}) for c in candidates_to_ghost(cands, _px({"AAA": 10.0, "BBB": 10.0}))]
        # price moves: AAA up, BBB down
        n = grade_entries(entries, _px({"AAA": 12.0, "BBB": 9.0}), today="2026-07-01")
        assert n == 2
        r = buzz_report(entries)
        assert r["n"] == 2
        assert r["mean_return"] == pytest.approx((0.20 - 0.10) / 2)
