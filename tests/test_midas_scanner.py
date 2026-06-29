import pytest

from midas.scanner import (
    ScanCandidate,
    WeeklyCatalystDossier,
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


class TestStage2Rank:
    def test_ranks_by_score(self):
        candidates = [
            ScanCandidate("A", market_cap=1e9, signals={"insider_cluster": 1.0}, quality_value=0.5),
            ScanCandidate("B", market_cap=1e9, signals={"insider_cluster": 1.0, "activist_13d": 1.0}, quality_value=0.5),
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
    def test_picks_highest_ev(self):
        dossiers = [
            WeeklyCatalystDossier(
                symbol="A", catalyst="earnings", catalyst_timing="Monday",
                bull_case="", bear_case="", priced_in_judgment="no",
                pop_probability=0.6, expected_magnitude=0.10,
                expected_value=0.06, current_price=50.0,
            ),
            WeeklyCatalystDossier(
                symbol="B", catalyst="13D", catalyst_timing="Tuesday",
                bull_case="", bear_case="", priced_in_judgment="no",
                pop_probability=0.4, expected_magnitude=0.30,
                expected_value=0.12, current_price=30.0,
            ),
        ]
        winner = pick_winner(dossiers)
        assert winner.symbol == "B"

    def test_empty_returns_none(self):
        assert pick_winner([]) is None
