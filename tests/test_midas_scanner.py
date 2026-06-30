import pytest

from midas.scanner import (
    ScanCandidate,
    WeeklyCatalystDossier,
    _signal_is_stale,
    build_signal_map,
    pick_winner,
    stage1_sieve,
    stage2_rank,
)


class TestBuildSignalMap:
    def test_insider_cluster(self):
        signals = build_signal_map(
            "ACME",
            insider_clusters={"ACME": {"insider_count": 3, "total_dollars": 50000}},
        )
        assert signals["insider_cluster"] == pytest.approx(0.75)

    def test_insider_cluster_capped_at_1(self):
        signals = build_signal_map(
            "ACME",
            insider_clusters={"ACME": {"insider_count": 10}},
        )
        assert signals["insider_cluster"] == 1.0

    def test_smart_money(self):
        signals = build_signal_map(
            "ACME",
            smart_money_holders={"ACME": ["Berkshire", "Baupost"]},
        )
        assert signals["smart_money"] == pytest.approx(2 / 3)

    def test_activist_13d(self):
        signals = build_signal_map(
            "ACME",
            activist_symbols={"ACME", "OTHER"},
        )
        assert signals["activist_13d"] == 1.0

    def test_guidance_raised(self):
        signals = build_signal_map(
            "ACME",
            guidance_raised={"ACME"},
        )
        assert signals["guidance_raised"] == 1.0

    def test_no_signals(self):
        signals = build_signal_map("ACME")
        assert len(signals) == 0

    def test_case_insensitive(self):
        signals = build_signal_map(
            "acme",
            insider_clusters={"ACME": {"insider_count": 2}},
        )
        assert "insider_cluster" in signals

    def test_earnings_miss_excluded(self):
        signals = build_signal_map(
            "ACME",
            earnings_surprise={"ACME": {"is_beat": False, "surprise_pct": -5.0}},
        )
        assert "earnings_beat" not in signals

    def test_volume_anomaly_fires(self):
        signals = build_signal_map(
            "ACME",
            volume_anomalies={"ACME": 3.0},
        )
        assert signals["volume_anomaly"] == pytest.approx(1.0)

    def test_volume_anomaly_scaled(self):
        signals = build_signal_map(
            "ACME",
            volume_anomalies={"ACME": 2.0},
        )
        assert signals["volume_anomaly"] == pytest.approx(2.0 / 3.0)

    def test_volume_anomaly_below_threshold(self):
        signals = build_signal_map(
            "ACME",
            volume_anomalies={"ACME": 1.2},
        )
        assert "volume_anomaly" not in signals

    def test_volume_anomaly_missing_symbol(self):
        signals = build_signal_map(
            "ACME",
            volume_anomalies={"OTHER": 5.0},
        )
        assert "volume_anomaly" not in signals

    def test_short_squeeze_fires(self):
        signals = build_signal_map(
            "ACME",
            short_squeezes={"ACME": 50.0},
        )
        assert signals["short_squeeze"] == pytest.approx(1.0)

    def test_short_squeeze_scaled(self):
        signals = build_signal_map(
            "ACME",
            short_squeezes={"ACME": 30.0},
        )
        assert signals["short_squeeze"] == pytest.approx(0.6)

    def test_short_squeeze_below_threshold(self):
        signals = build_signal_map(
            "ACME",
            short_squeezes={"ACME": 15.0},
        )
        assert "short_squeeze" not in signals

    def test_short_squeeze_missing_symbol(self):
        signals = build_signal_map(
            "ACME",
            short_squeezes={"OTHER": 40.0},
        )
        assert "short_squeeze" not in signals


class TestSignalStaleness:
    def test_stale_when_price_moved_up(self):
        assert _signal_is_stale("ACME", {"ACME": 100.0}, {"ACME": 120.0})

    def test_stale_when_price_moved_down(self):
        assert _signal_is_stale("ACME", {"ACME": 100.0}, {"ACME": 80.0})

    def test_not_stale_small_move(self):
        assert not _signal_is_stale("ACME", {"ACME": 100.0}, {"ACME": 110.0})

    def test_not_stale_missing_signal_price(self):
        assert not _signal_is_stale("ACME", {}, {"ACME": 110.0})

    def test_not_stale_missing_current_price(self):
        assert not _signal_is_stale("ACME", {"ACME": 100.0}, {})


class TestStage1Sieve:
    def test_filters_to_signal_names(self):
        universe = {"ACME": "0001", "BORING": "0002", "COOL": "0003"}
        candidates = stage1_sieve(
            universe,
            insider_clusters={"ACME": {"insider_count": 2}},
            activist_symbols={"COOL"},
        )
        symbols = {c.symbol for c in candidates}
        assert "ACME" in symbols
        assert "COOL" in symbols
        assert "BORING" not in symbols

    def test_filters_by_market_cap(self):
        universe = {"TINY": "0001", "HUGE": "0002", "OK": "0003"}
        candidates = stage1_sieve(
            universe,
            insider_clusters={
                "TINY": {"insider_count": 2},
                "HUGE": {"insider_count": 2},
                "OK": {"insider_count": 2},
            },
            market_caps={"TINY": 1_000_000, "HUGE": 100_000_000_000, "OK": 1_000_000_000},
        )
        symbols = {c.symbol for c in candidates}
        assert "OK" in symbols
        assert "TINY" not in symbols
        assert "HUGE" not in symbols


    def test_filters_recent_ipo(self):
        universe = {"NEW": "0001", "OLD": "0002"}
        candidates = stage1_sieve(
            universe,
            insider_clusters={
                "NEW": {"insider_count": 2},
                "OLD": {"insider_count": 2},
            },
            ipo_dates={"NEW": "2026-06-01", "OLD": "2025-01-01"},
            today="2026-06-30",
        )
        symbols = {c.symbol for c in candidates}
        assert "OLD" in symbols
        assert "NEW" not in symbols

    def test_missing_ipo_date_passes(self):
        universe = {"MYSTERY": "0001"}
        candidates = stage1_sieve(
            universe,
            insider_clusters={"MYSTERY": {"insider_count": 2}},
            ipo_dates={},
            today="2026-06-30",
        )
        assert len(candidates) == 1

    def test_filters_pending_earnings(self):
        universe = {"REPORT": "0001", "SAFE": "0002"}
        candidates = stage1_sieve(
            universe,
            insider_clusters={
                "REPORT": {"insider_count": 3},
                "SAFE": {"insider_count": 3},
            },
            earnings_this_week={"REPORT"},
        )
        symbols = {c.symbol for c in candidates}
        assert "SAFE" in symbols
        assert "REPORT" not in symbols

    def test_earnings_beat_not_filtered(self):
        """A name that already reported and beat is a valid signal, not pending."""
        universe = {"BEAT": "0001"}
        candidates = stage1_sieve(
            universe,
            insider_clusters={"BEAT": {"insider_count": 2}},
            earnings_this_week=set(),
        )
        assert len(candidates) == 1

    def test_filters_stale_signals(self):
        universe = {"STALE": "0001", "FRESH": "0002"}
        candidates = stage1_sieve(
            universe,
            insider_clusters={
                "STALE": {"insider_count": 3},
                "FRESH": {"insider_count": 3},
            },
            signal_prices={"STALE": 100.0, "FRESH": 100.0},
            current_prices={"STALE": 125.0, "FRESH": 105.0},
        )
        symbols = {c.symbol for c in candidates}
        assert "FRESH" in symbols
        assert "STALE" not in symbols

    def test_no_signal_prices_skips_freshness(self):
        universe = {"ACME": "0001"}
        candidates = stage1_sieve(
            universe,
            insider_clusters={"ACME": {"insider_count": 2}},
        )
        assert len(candidates) == 1

    def test_volume_anomaly_passes_through(self):
        universe = {"VOL": "0001"}
        candidates = stage1_sieve(
            universe,
            volume_anomalies={"VOL": 3.0},
        )
        assert len(candidates) == 1
        assert "volume_anomaly" in candidates[0].signals

    def test_short_squeeze_passes_through(self):
        universe = {"SQ": "0001"}
        candidates = stage1_sieve(
            universe,
            short_squeezes={"SQ": 35.0},
        )
        assert len(candidates) == 1
        assert "short_squeeze" in candidates[0].signals


class TestStage2Rank:
    def test_ranks_by_score(self):
        candidates = [
            ScanCandidate("A", market_cap=1e9, signals={"insider_cluster": 1.0}, quality_value=0.5),
            ScanCandidate("B", market_cap=1e9, signals={"insider_cluster": 1.0, "earnings_beat": 1.0}, quality_value=0.5),
        ]
        ranked = stage2_rank(candidates, top_n=10)
        assert ranked[0]["symbol"] == "B"
        assert ranked[0]["convergence_count"] == 2

    def test_top_n_limit(self):
        candidates = [
            ScanCandidate(f"SYM{i}", market_cap=1e9, signals={"insider_cluster": 1.0}, quality_value=0.5)
            for i in range(20)
        ]
        ranked = stage2_rank(candidates, top_n=5)
        assert len(ranked) == 5


class TestPickWinner:
    def _make_dossier(self, symbol, score, **kwargs):
        defaults = dict(
            catalyst="test", catalyst_timing="Monday",
            bull_case="", bear_case="", priced_in_judgment="no",
            current_price=50.0, convergence_count=1,
        )
        defaults.update(kwargs)
        return WeeklyCatalystDossier(symbol=symbol, score=score, **defaults)

    def test_picks_highest_score(self):
        dossiers = [
            self._make_dossier("A", score=0.4, convergence_count=2),
            self._make_dossier("B", score=0.2, convergence_count=1),
        ]
        winner = pick_winner(dossiers)
        assert winner.symbol == "A"

    def test_score_only_ev_ignored(self):
        """EV fields are informational — pick_winner uses score alone."""
        dossiers = [
            self._make_dossier("HIGH_EV", score=0.2,
                               pop_probability=0.9, expected_magnitude=0.50,
                               expected_value=0.45),
            self._make_dossier("HIGH_SCORE", score=0.5,
                               pop_probability=0.1, expected_magnitude=0.05,
                               expected_value=0.005),
        ]
        winner = pick_winner(dossiers)
        assert winner.symbol == "HIGH_SCORE"

    def test_disqualified_skipped(self):
        dossiers = [
            self._make_dossier("BEST", score=0.9, disqualified=True,
                               disqualify_reason="guidance bomb"),
            self._make_dossier("SECOND", score=0.5),
        ]
        winner = pick_winner(dossiers)
        assert winner.symbol == "SECOND"

    def test_all_disqualified_returns_none(self):
        dossiers = [
            self._make_dossier("A", score=0.9, disqualified=True),
            self._make_dossier("B", score=0.5, disqualified=True),
        ]
        assert pick_winner(dossiers) is None

    def test_empty_returns_none(self):
        assert pick_winner([]) is None
