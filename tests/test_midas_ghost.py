import pytest

from midas.ghost import (
    HORIZON_DAYS,
    convergence_report,
    finalists_to_candidates,
    GhostEntry,
)


class TestFinalistsToCandidates:
    def _lookup(self, sym):
        return {"ACME": 50.0, "BETA": 30.0, "GAMMA": 100.0}.get(sym)

    def test_basic_conversion(self):
        finalists = [
            {"symbol": "ACME", "score": 0.8, "convergence_count": 3,
             "active_signals": {"insider_cluster": 0.7, "earnings_beat": 0.9},
             "timing_adjusted": {"insider_cluster": 0.35, "earnings_beat": 0.9}},
        ]
        cands = finalists_to_candidates(finalists, self._lookup)
        assert len(cands) == 1
        assert cands[0]["symbol"] == "ACME"
        assert cands[0]["price"] == 50.0
        assert cands[0]["horizon_days"] == HORIZON_DAYS
        assert cands[0]["source"] == "convergence"

    def test_signal_channels_as_booleans(self):
        finalists = [
            {"symbol": "ACME", "score": 0.5, "convergence_count": 2,
             "active_signals": {"short_squeeze": 0.8, "volume_anomaly": 0.6}},
        ]
        cands = finalists_to_candidates(finalists, self._lookup)
        f = cands[0]["features"]
        assert f["short_squeeze"] is True
        assert f["volume_anomaly"] is True
        assert f["insider_cluster"] is False
        assert f["earnings_beat"] is False

    def test_disqualified_included(self):
        finalists = [
            {"symbol": "ACME", "score": 0.9, "disqualified": True,
             "convergence_count": 3, "active_signals": {}},
            {"symbol": "BETA", "score": 0.5, "disqualified": False,
             "convergence_count": 1, "active_signals": {}},
        ]
        cands = finalists_to_candidates(finalists, self._lookup)
        assert len(cands) == 2
        assert cands[0]["features"]["disqualified"] is True
        assert cands[1]["features"]["disqualified"] is False

    def test_uses_current_price_field(self):
        finalists = [
            {"symbol": "ACME", "current_price": 99.0, "score": 0.5,
             "convergence_count": 1, "active_signals": {}},
        ]
        cands = finalists_to_candidates(finalists, self._lookup)
        assert cands[0]["price"] == 99.0

    def test_falls_back_to_lookup(self):
        finalists = [
            {"symbol": "ACME", "score": 0.5,
             "convergence_count": 1, "active_signals": {}},
        ]
        cands = finalists_to_candidates(finalists, self._lookup)
        assert cands[0]["price"] == 50.0

    def test_skips_unpriceable(self):
        finalists = [
            {"symbol": "UNKNOWN", "score": 0.5,
             "convergence_count": 1, "active_signals": {}},
        ]
        cands = finalists_to_candidates(finalists, self._lookup)
        assert len(cands) == 0

    def test_skips_empty_symbol(self):
        finalists = [{"symbol": "", "score": 0.5}]
        cands = finalists_to_candidates(finalists, self._lookup)
        assert len(cands) == 0

    def test_mean_timing_weighted(self):
        finalists = [
            {"symbol": "ACME", "score": 0.5, "convergence_count": 2,
             "active_signals": {"insider_cluster": 0.7},
             "timing_adjusted": {"insider_cluster": 0.35, "earnings_beat": 0.9}},
        ]
        cands = finalists_to_candidates(finalists, self._lookup)
        assert cands[0]["features"]["mean_timing_weighted"] == pytest.approx(0.625)


class TestConvergenceReport:
    def _make_entry(self, symbol, ret, convergence_count=1, score=0.5, **features):
        defaults = {
            "convergence_count": convergence_count,
            "score": score,
            "disqualified": False,
            "insider_cluster": False,
            "earnings_beat": False,
        }
        defaults.update(features)
        e = GhostEntry(
            symbol=symbol, entry_date="2026-06-30", entry_price=100.0,
            horizon_days=5, source="convergence", features=defaults,
        )
        e.exit_date = "2026-07-05"
        e.exit_price = 100.0 * (1 + ret)
        e.graded_return = ret
        return e

    def test_empty_returns_nulls(self):
        r = convergence_report([])
        assert r["n"] == 0
        assert r["mean_return"] is None

    def test_basic_stats(self):
        entries = [
            self._make_entry("A", 0.05),
            self._make_entry("B", -0.03),
            self._make_entry("C", 0.10),
        ]
        r = convergence_report(entries)
        assert r["n"] == 3
        assert r["hit_rate"] == pytest.approx(2 / 3)

    def test_signal_lift_present(self):
        entries = [
            self._make_entry("A", 0.10, insider_cluster=True),
            self._make_entry("B", -0.05, insider_cluster=False),
        ]
        r = convergence_report(entries)
        assert "insider_cluster" in r["signal_lift"]

    def test_ungraded_excluded(self):
        graded = self._make_entry("A", 0.05)
        ungraded = GhostEntry(
            symbol="B", entry_date="2026-06-30", entry_price=100.0,
            horizon_days=5, source="convergence", features={"convergence_count": 1},
        )
        r = convergence_report([graded, ungraded])
        assert r["n"] == 1
