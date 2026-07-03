import pytest

from midas.scoring import (
    CONVERGENCE_MAX,
    CONVERGENCE_MULTIPLIERS,
    CONVERGENCE_TIMING_FLOOR,
    MIN_MARKET_CAP,
    MAX_MARKET_CAP,
    QUALITY_VALUE_FLOOR,
    TIMING_WEIGHTS,
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
        # Live score is max-of-timely-strengths: the earnings beat
        # (0.7 x 1.0 timing) out-scores the insider cluster (0.8 x 0.5),
        # so adding it raises the name's rank. Convergence count still
        # tracks distinct events for the ghost A/B.
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

    def test_convergence_boost_lives_in_legacy_only(self):
        # Operator directive 2026-07-04: the multiplier was refuted under
        # two independent countings, so stacking a WEAKER independent
        # signal no longer moves the LIVE score (max-of-timely carries) —
        # but the legacy ghost formula still boosts, so the A/B race can
        # settle whether the thesis deserves its way back.
        two = score_candidate(
            signals={"short_squeeze": 0.8, "earnings_beat": 0.7},
            quality_value=0.5, market_cap=1e9,
        )
        three = score_candidate(
            signals={"short_squeeze": 0.8, "earnings_beat": 0.7, "insider_cluster": 0.6},
            quality_value=0.5, market_cap=1e9,
        )
        assert three["score"] == pytest.approx(two["score"])  # live: flat
        assert three["score_legacy"] > two["score_legacy"] * 1.5  # ghost: boosted

    def test_weaker_extra_signal_never_lowers_live_score(self):
        # Under the old mean-based formula an extra weak signal could DRAG
        # the average down; max-aggregation makes adding information
        # rank-monotone.
        strong = score_candidate(
            signals={"earnings_beat": 0.9},
            quality_value=0.5, market_cap=1e9,
        )
        with_weak = score_candidate(
            signals={"earnings_beat": 0.9, "guidance_raised": 0.1},
            quality_value=0.5, market_cap=1e9,
        )
        assert with_weak["score"] >= strong["score"]

    def test_same_event_signals_do_not_double_count(self):
        # Fixed 2026-07-04 (LLM integration audit): earnings_beat,
        # guidance_raised, and volume_anomaly can all fire from ONE
        # earnings report. Adding volume_anomaly on top of earnings_beat
        # must NOT bump the convergence tier — they're the same event.
        one = score_candidate(
            signals={"earnings_beat": 0.7},
            quality_value=0.5, market_cap=1e9,
        )
        two = score_candidate(
            signals={"earnings_beat": 0.7, "volume_anomaly": 0.9},
            quality_value=0.5, market_cap=1e9,
        )
        three = score_candidate(
            signals={"earnings_beat": 0.7, "volume_anomaly": 0.9, "guidance_raised": 0.5},
            quality_value=0.5, market_cap=1e9,
        )
        assert one["convergence_count"] == 1
        assert two["convergence_count"] == 1
        assert three["convergence_count"] == 1

    def test_distinct_events_do_count(self):
        # An earnings beat AND a separate insider cluster ARE two distinct
        # informed-money sources and should tier up.
        result = score_candidate(
            signals={"earnings_beat": 0.7, "insider_cluster": 0.6},
            quality_value=0.5, market_cap=1e9,
        )
        assert result["convergence_count"] == 2

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

    def test_timing_weights_applied(self):
        result = score_candidate(
            signals={"insider_cluster": 1.0, "activist_13d": 1.0},
            quality_value=0.5, market_cap=1e9,
        )
        assert "timing_adjusted" in result
        assert result["timing_adjusted"]["activist_13d"] == pytest.approx(0.2)

    def test_slow_signals_alone_score_zero(self):
        """Signals below the timing floor can't carry a name on their own."""
        result = score_candidate(
            signals={"activist_13d": 1.0, "smart_money": 1.0},
            quality_value=0.5, market_cap=1e9,
        )
        assert result["score"] == 0.0
        assert result["convergence_count"] == 0

    def test_slow_signal_does_not_elevate_convergence_tier(self):
        """activist_13d contributes to mean_strength but not convergence count."""
        without_slow = score_candidate(
            signals={"short_squeeze": 0.8, "earnings_beat": 0.7},
            quality_value=0.5, market_cap=1e9,
        )
        with_slow = score_candidate(
            signals={"short_squeeze": 0.8, "earnings_beat": 0.7, "activist_13d": 1.0},
            quality_value=0.5, market_cap=1e9,
        )
        assert without_slow["convergence_count"] == 2
        assert with_slow["convergence_count"] == 2

    def test_slow_signal_moves_legacy_not_live(self):
        """Below-floor signals (13D/13F) affect the legacy mean-strength
        formula but deliberately do NOT move the live max-of-timely score
        (flatten directive 2026-07-04): a months-horizon filing shouldn't
        re-rank a 5-day trade."""
        without_slow = score_candidate(
            signals={"short_squeeze": 0.8, "earnings_beat": 0.7},
            quality_value=0.5, market_cap=1e9,
        )
        with_slow = score_candidate(
            signals={"short_squeeze": 0.8, "earnings_beat": 0.7, "activist_13d": 1.0},
            quality_value=0.5, market_cap=1e9,
        )
        assert with_slow["score"] == pytest.approx(without_slow["score"])
        assert with_slow["score_legacy"] != without_slow["score_legacy"]

    def test_fast_signals_beat_slow_at_same_raw_count(self):
        fast = score_candidate(
            signals={"short_squeeze": 0.8, "earnings_beat": 0.7},
            quality_value=0.5, market_cap=1e9,
        )
        slow = score_candidate(
            signals={"activist_13d": 0.8, "smart_money": 0.7},
            quality_value=0.5, market_cap=1e9,
        )
        assert fast["score"] > 0
        assert slow["score"] == 0.0

    def test_timing_weights_all_channels_defined(self):
        for channel in ("insider_cluster", "earnings_beat", "smart_money",
                        "activist_13d", "guidance_raised", "volume_anomaly",
                        "short_squeeze"):
            assert channel in TIMING_WEIGHTS

    def test_convergence_timing_floor_value(self):
        assert CONVERGENCE_TIMING_FLOOR == 0.4
        assert TIMING_WEIGHTS["activist_13d"] < CONVERGENCE_TIMING_FLOOR
        assert TIMING_WEIGHTS["smart_money"] < CONVERGENCE_TIMING_FLOOR
        assert TIMING_WEIGHTS["insider_cluster"] >= CONVERGENCE_TIMING_FLOOR

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
