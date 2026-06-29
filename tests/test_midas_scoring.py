import pytest

from midas.scoring import (
    CONVERGENCE_MAX,
    CONVERGENCE_MULTIPLIERS,
    MIN_MARKET_CAP,
    MAX_MARKET_CAP,
    QUALITY_VALUE_FLOOR,
    convergence_multiplier,
    liquidity_ok,
    neglect_score,
    rank_candidates,
    score_candidate,
)


class TestConvergenceMultiplier:
    def test_zero_signals(self):
        assert convergence_multiplier(0) == 0.0

    def test_one_signal(self):
        assert convergence_multiplier(1) == 1.0

    def test_two_signals(self):
        assert convergence_multiplier(2) == 2.5

    def test_three_signals(self):
        assert convergence_multiplier(3) == 5.0

    def test_four_plus_caps(self):
        assert convergence_multiplier(4) == CONVERGENCE_MAX
        assert convergence_multiplier(5) == CONVERGENCE_MAX


class TestNeglectScore:
    def test_small_cap_high_neglect(self):
        score = neglect_score(100_000_000)
        assert score > 0.8

    def test_large_cap_low_neglect(self):
        score = neglect_score(15_000_000_000)
        assert score < 0.5

    def test_zero_market_cap(self):
        assert neglect_score(0) == 0.0

    def test_none_market_cap(self):
        assert neglect_score(None) == 0.0

    def test_monotonically_decreasing(self):
        caps = [100e6, 500e6, 2e9, 10e9, 20e9]
        scores = [neglect_score(c) for c in caps]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]


class TestLiquidityOk:
    def test_too_small(self):
        assert liquidity_ok(10_000_000) is False

    def test_too_large(self):
        assert liquidity_ok(50_000_000_000) is False

    def test_sweet_spot(self):
        assert liquidity_ok(500_000_000) is True

    def test_boundaries(self):
        assert liquidity_ok(MIN_MARKET_CAP) is True
        assert liquidity_ok(MAX_MARKET_CAP) is True
        assert liquidity_ok(MIN_MARKET_CAP - 1) is False
        assert liquidity_ok(MAX_MARKET_CAP + 1) is False


class TestScoreCandidate:
    def test_no_signals_zero(self):
        result = score_candidate(
            signals={}, quality_value=0.5, market_cap=1e9,
        )
        assert result["score"] == 0.0

    def test_one_signal(self):
        result = score_candidate(
            signals={"insider_cluster": 0.8},
            quality_value=0.5,
            market_cap=1e9,
        )
        assert result["score"] > 0
        assert result["convergence_count"] == 1

    def test_two_signals_higher_than_one(self):
        one = score_candidate(
            signals={"insider_cluster": 0.8},
            quality_value=0.5, market_cap=1e9,
        )
        two = score_candidate(
            signals={"insider_cluster": 0.8, "earnings_beat": 0.7},
            quality_value=0.5, market_cap=1e9,
        )
        assert two["score"] > one["score"]
        assert two["convergence_count"] == 2

    def test_three_signals_much_higher(self):
        two = score_candidate(
            signals={"insider_cluster": 0.8, "earnings_beat": 0.7},
            quality_value=0.5, market_cap=1e9,
        )
        three = score_candidate(
            signals={"insider_cluster": 0.8, "earnings_beat": 0.7, "activist_13d": 1.0},
            quality_value=0.5, market_cap=1e9,
        )
        assert three["score"] > two["score"] * 1.5

    def test_filtered_by_market_cap(self):
        result = score_candidate(
            signals={"insider_cluster": 1.0},
            quality_value=0.5, market_cap=10_000_000,
        )
        assert result["score"] == 0.0
        assert result["reason"] == "liquidity_filter"

    def test_quality_floor_applied(self):
        result = score_candidate(
            signals={"insider_cluster": 1.0},
            quality_value=0.0,
            market_cap=1e9,
        )
        assert result["components"]["quality_value"] == QUALITY_VALUE_FLOOR

    def test_unknown_signal_ignored(self):
        result = score_candidate(
            signals={"insider_cluster": 1.0, "fake_signal": 0.9},
            quality_value=0.5, market_cap=1e9,
        )
        assert result["convergence_count"] == 1

    def test_small_cap_neglect_boost(self):
        small = score_candidate(
            signals={"insider_cluster": 1.0},
            quality_value=0.5, market_cap=100e6,
        )
        large = score_candidate(
            signals={"insider_cluster": 1.0},
            quality_value=0.5, market_cap=15e9,
        )
        assert small["components"]["neglect"] > large["components"]["neglect"]


class TestRankCandidates:
    def test_returns_top_n(self):
        candidates = [
            {"symbol": "A", "score": 0.5},
            {"symbol": "B", "score": 0.9},
            {"symbol": "C", "score": 0.1},
            {"symbol": "D", "score": 0.7},
        ]
        top = rank_candidates(candidates, top_n=2)
        assert len(top) == 2
        assert top[0]["symbol"] == "B"
        assert top[1]["symbol"] == "D"

    def test_filters_zero_scores(self):
        candidates = [
            {"symbol": "A", "score": 0.5},
            {"symbol": "B", "score": 0.0},
        ]
        top = rank_candidates(candidates, top_n=10)
        assert len(top) == 1
        assert top[0]["symbol"] == "A"
