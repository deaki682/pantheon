import pytest

from nemesis.detect import Crash, crash_zscore, detect_crashes
from nemesis.ghost import (
    HORIZON_DAYS, SOURCE, crashes_to_ghost, destinations_to_ghost, nemesis_report,
)
from nemesis.rotation import conditional_matrix, predicted_destinations
from shared.ghost import GhostEntry, grade_entries


# ── detect ────────────────────────────────────────────────────────────

def _quiet_then_crash(n=70, base=100.0, crash=-0.08):
    # low, steady daily vol (~±0.3%), then one violent down day
    closes = [base]
    for i in range(1, n):
        closes.append(closes[-1] * (1 + 0.003 * (-1) ** i))
    closes.append(closes[-1] * (1 + crash))
    return closes


class TestDetect:
    def test_flags_violent_no_vol_context(self):
        z = crash_zscore(_quiet_then_crash())
        assert z is not None and z < -2.0

    def test_detect_crashes_thresholds(self):
        uni = {
            "CRSH": _quiet_then_crash(crash=-0.08),
            "MILD": _quiet_then_crash(crash=-0.02),   # under MIN_DROP
            "FLAT": [100.0] * 71,
        }
        out = detect_crashes(uni)
        assert [c.symbol for c in out] == ["CRSH"]
        assert out[0].day_return == pytest.approx(-0.08, abs=1e-3)

    def test_cascade_tagging(self):
        uni = {f"S{i}": _quiet_then_crash(crash=-0.07) for i in range(3)}
        uni["LONER"] = _quiet_then_crash(crash=-0.07)
        sectors = {f"S{i}": "semis" for i in range(3)}
        sectors["LONER"] = "retail"
        out = {c.symbol: c for c in detect_crashes(uni, sectors=sectors)}
        assert out["S0"].sector_cascade is True
        assert out["LONER"].sector_cascade is False

    def test_short_history_skipped(self):
        assert detect_crashes({"NEW": [100.0, 90.0]}) == []


# ── rotation ──────────────────────────────────────────────────────────

def _etf_world(n=260):
    """Trigger ETF crashes periodically; RECV rallies the week after each
    crash; DEAD ignores everything."""
    trig, recv, dead = [100.0], [100.0], [100.0]
    for i in range(1, n):
        if i % 40 == 0:
            trig.append(trig[-1] * 0.97)          # -3% crash day
        elif (i - 1) % 40 < 5 and i > 40:
            trig.append(trig[-1] * 1.001)
        else:
            trig.append(trig[-1] * 1.0005)
        # receiver pops in the 5 sessions after each trigger crash
        recv.append(recv[-1] * (1.004 if 0 < i % 40 <= 5 else 1.0002))
        dead.append(dead[-1] * 1.0001)
    return {"TRIG": trig, "RECV": recv, "DEAD": dead}


class TestRotation:
    def test_matrix_finds_receiver(self):
        m = conditional_matrix(_etf_world(), trigger_sym="TRIG")
        assert m["n_events"] >= 5
        assert m["per_etf"]["RECV"]["excess"] > m["per_etf"]["DEAD"]["excess"]
        assert m["per_etf"]["RECV"]["hit_rate"] > 0.6

    def test_destinations_exclude_trigger_and_floor(self):
        m = conditional_matrix(_etf_world(), trigger_sym="TRIG")
        dests = predicted_destinations(m, min_events=5)
        syms = [d["symbol"] for d in dests]
        assert "TRIG" not in syms
        assert "RECV" in syms

    def test_thin_matrix_refused(self):
        m = conditional_matrix(_etf_world(n=60), trigger_sym="TRIG")
        assert predicted_destinations(m) == []   # < MIN_EVENTS -> anecdote


# ── ghost ─────────────────────────────────────────────────────────────

def _crash(sym, news=False, z=-3.0, cascade=True):
    return Crash(symbol=sym, day_return=-0.08, zscore=z, price=50.0,
                 sector="semis", news_driven=news, sector_cascade=cascade)


class TestGhostAdapter:
    def test_fade_leg_carries_tags(self):
        out = crashes_to_ghost([_crash("AAA", news=False)], lambda s: None)
        f = out[0]["features"]
        assert f["leg"] == "fade"
        assert f["news_driven"] is False and f["news_checked"] is True
        assert out[0]["source"] == SOURCE
        assert out[0]["horizon_days"] == HORIZON_DAYS

    def test_news_crashes_opened_as_control(self):
        out = crashes_to_ghost([_crash("BOMB", news=True)], lambda s: None)
        assert out[0]["features"]["news_driven"] is True   # opened, not dropped

    def test_unchecked_news_tagged(self):
        c = _crash("UNK"); c.news_driven = None
        f = crashes_to_ghost([c], lambda s: None)[0]["features"]
        assert f["news_checked"] is False
        assert "news_driven" not in f

    def test_destination_leg(self):
        dests = [{"symbol": "XLU", "excess": 0.0062, "hit_rate": 0.76}]
        out = destinations_to_ghost(dests, lambda s: 80.0)
        f = out[0]["features"]
        assert f["leg"] == "destination"
        assert f["predicted_excess"] == 0.0062

    def test_unpriceable_skipped(self):
        assert destinations_to_ghost([{"symbol": "XLU"}], lambda s: None) == []


class TestReport:
    def test_head_to_head_and_news_control(self):
        entries = [
            GhostEntry("F1", "2026-07-02", 50.0, 7, "nemesis",
                       features={"leg": "fade", "news_driven": False,
                                 "crash_zscore": -3.0}, graded_return=0.03),
            GhostEntry("F2", "2026-07-02", 50.0, 7, "nemesis",
                       features={"leg": "fade", "news_driven": False,
                                 "crash_zscore": -2.2}, graded_return=0.02),
            GhostEntry("B1", "2026-07-02", 50.0, 7, "nemesis",
                       features={"leg": "fade", "news_driven": True,
                                 "crash_zscore": -3.5}, graded_return=-0.04),
            GhostEntry("D1", "2026-07-02", 80.0, 7, "nemesis",
                       features={"leg": "destination", "predicted_excess": 0.006},
                       graded_return=0.01),
            GhostEntry("X", "2026-07-02", 10.0, 7, "buzz",   # foreign source
                       features={"leg": "fade"}, graded_return=0.9),
        ]
        r = nemesis_report(entries)
        assert r["n"] == 4                                  # buzz entry excluded
        legs = r["leg_returns"]
        assert legs["fade"]["n"] == 3 and legs["destination"]["n"] == 1
        lift = r["signal_lift"]["news_driven"]
        assert lift["lift"] < 0        # news crashes bled -> filter validated

    def test_empty(self):
        assert nemesis_report([])["n"] == 0

    def test_end_to_end_grade(self):
        cands = crashes_to_ghost([_crash("AAA", news=False)], lambda s: None)
        e = GhostEntry(symbol="AAA", entry_date="2026-07-02", entry_price=50.0,
                       horizon_days=7, source="nemesis",
                       features=cands[0]["features"])
        n = grade_entries([e], lambda s: 53.0, today="2026-07-20")
        assert n == 1
        assert nemesis_report([e])["mean_return"] == pytest.approx(0.06)
