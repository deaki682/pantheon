import pytest

from achilles.scoring import (
    GUIDANCE_RAISED_BOOST,
    INSIDER_PREBUY_BOOST,
    MAX_MARKET_CAP,
    MEGACAP_DECAY_END,
    MEGACAP_DECAY_START,
    MEGACAP_FLOOR,
    MIN_MARKET_CAP,
    REVENUE_BEAT_BOOST,
    SHORT_SQUEEZE_MAX_BOOST,
    confirming_boost,
    liquidity_score,
    market_cap_ok,
    pead_neglect,
    score_beat,
    surprise_strength,
)


# =====================================================================
# surprise_strength
# =====================================================================


class TestSurpriseStrength:
    def test_zero_surprise(self):
        assert surprise_strength(0.0) == 0.0

    def test_ten_pct(self):
        assert surprise_strength(10.0) == pytest.approx(0.95)

    def test_twenty_pct(self):
        assert surprise_strength(20.0) == pytest.approx(1.0)

    def test_fifty_pct(self):
        assert surprise_strength(50.0) == pytest.approx(1.0)

    def test_hundred_pct(self):
        assert surprise_strength(100.0) == pytest.approx(0.95)

    def test_none_returns_neutral(self):
        assert surprise_strength(None) == 1.0

    def test_negative_uses_abs(self):
        assert surprise_strength(-15.0) == surprise_strength(15.0)

    def test_very_large_surprise(self):
        # 500% -> 0.7 (last anchor)
        assert surprise_strength(500.0) == pytest.approx(0.7)

    def test_beyond_max_anchor(self):
        # Beyond 500% -> stays at 0.7
        assert surprise_strength(1000.0) == pytest.approx(0.7)

    def test_small_surprise(self):
        # 3% -> 0.3 (anchor)
        assert surprise_strength(3.0) == pytest.approx(0.3)

    def test_interpolation_between_anchors(self):
        # 15% is between 10% (0.95) and 20% (1.0)
        s = surprise_strength(15.0)
        assert 0.95 <= s <= 1.0


# =====================================================================
# liquidity_score
# =====================================================================


class TestLiquidityScore:
    def test_50m(self):
        assert liquidity_score(50_000_000) == pytest.approx(0.3)

    def test_1b(self):
        assert liquidity_score(1_000_000_000) == pytest.approx(0.8)

    def test_10b(self):
        assert liquidity_score(10_000_000_000) == pytest.approx(1.0)

    def test_below_50b_no_decay(self):
        assert liquidity_score(40_000_000_000) == pytest.approx(1.0)

    def test_above_50b_decays(self):
        s = liquidity_score(100_000_000_000)
        assert s < 1.0
        assert s > MEGACAP_FLOOR

    def test_above_200b_floors(self):
        assert liquidity_score(MEGACAP_DECAY_END) == pytest.approx(MEGACAP_FLOOR)
        assert liquidity_score(1_000_000_000_000) == pytest.approx(MEGACAP_FLOOR)

    def test_zero(self):
        assert liquidity_score(0) == 0.0

    def test_none(self):
        assert liquidity_score(None) == 0.0

    def test_negative(self):
        assert liquidity_score(-1) == 0.0

    def test_tiny_cap(self):
        assert liquidity_score(10_000_000) == 0.1

    def test_300m(self):
        assert liquidity_score(300_000_000) == pytest.approx(0.6)


# =====================================================================
# pead_neglect
# =====================================================================


class TestPeadNeglect:
    def test_50m(self):
        assert pead_neglect(50_000_000) == pytest.approx(1.0)

    def test_2b(self):
        assert pead_neglect(2_000_000_000) == pytest.approx(0.60)

    def test_50b(self):
        assert pead_neglect(50_000_000_000) == pytest.approx(0.25)

    def test_zero(self):
        assert pead_neglect(0) == 0.0

    def test_none(self):
        assert pead_neglect(None) == 0.0

    def test_below_smallest_anchor(self):
        # Below $50M -> returns 0.5
        assert pead_neglect(10_000_000) == pytest.approx(0.5)

    def test_monotonically_decreasing(self):
        caps = [50e6, 200e6, 500e6, 2e9, 10e9, 50e9]
        scores = [pead_neglect(c) for c in caps]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]


# =====================================================================
# market_cap_ok
# =====================================================================


class TestMarketCapOk:
    def test_valid_range(self):
        assert market_cap_ok(50_000_000) is True
        assert market_cap_ok(1_000_000_000) is True
        assert market_cap_ok(50_000_000_000) is True

    def test_below_min(self):
        assert market_cap_ok(49_999_999) is False

    def test_above_max(self):
        assert market_cap_ok(50_000_000_001) is False

    def test_none(self):
        assert market_cap_ok(None) is False

    def test_zero(self):
        assert market_cap_ok(0) is False

    def test_negative(self):
        assert market_cap_ok(-1_000_000) is False

    def test_constants(self):
        assert MIN_MARKET_CAP == 50_000_000
        assert MAX_MARKET_CAP == 50_000_000_000


# =====================================================================
# confirming_boost
# =====================================================================


class TestConfirmingBoost:
    def test_no_signals(self):
        assert confirming_boost() == 1.0

    def test_revenue_beat(self):
        b = confirming_boost(revenue_beat=True)
        assert b == pytest.approx(1.0 + REVENUE_BEAT_BOOST)

    def test_guidance_raised(self):
        b = confirming_boost(guidance_raised=True)
        assert b == pytest.approx(1.0 + GUIDANCE_RAISED_BOOST)

    def test_short_float_above_20(self):
        b = confirming_boost(short_float_pct=25.0)
        assert b == pytest.approx(1.0 + 25.0 / 100.0)

    def test_short_float_capped_at_max(self):
        b = confirming_boost(short_float_pct=50.0)
        # 50/100 = 0.50 > 0.30 max -> capped at 0.30
        assert b == pytest.approx(1.0 + SHORT_SQUEEZE_MAX_BOOST)

    def test_short_float_below_20_no_boost(self):
        b = confirming_boost(short_float_pct=15.0)
        assert b == 1.0

    def test_short_float_none_no_boost(self):
        b = confirming_boost(short_float_pct=None)
        assert b == 1.0

    def test_insider_prebuy(self):
        b = confirming_boost(insider_prebuy=True)
        assert b == pytest.approx(1.0 + INSIDER_PREBUY_BOOST)

    def test_all_signals(self):
        b = confirming_boost(
            revenue_beat=True,
            guidance_raised=True,
            short_float_pct=25.0,
            insider_prebuy=True,
        )
        expected = 1.0 + REVENUE_BEAT_BOOST + GUIDANCE_RAISED_BOOST + 0.25 + INSIDER_PREBUY_BOOST
        assert b == pytest.approx(expected)

    def test_constants(self):
        assert REVENUE_BEAT_BOOST == 0.15
        assert GUIDANCE_RAISED_BOOST == 0.25
        assert SHORT_SQUEEZE_MAX_BOOST == 0.30
        assert INSIDER_PREBUY_BOOST == 0.15


# =====================================================================
# score_beat
# =====================================================================


class TestScoreBeat:
    def test_basic_score(self):
        result = score_beat(surprise_pct=15.0, market_cap=1_000_000_000)
        assert result["score"] > 0
        assert "confirming_count" in result
        assert "components" in result

    def test_market_cap_fails(self):
        result = score_beat(surprise_pct=15.0, market_cap=None)
        assert result["score"] == 0.0
        assert result["reason"] == "market_cap_filter"

    def test_market_cap_too_large(self):
        result = score_beat(surprise_pct=15.0, market_cap=100_000_000_000)
        assert result["score"] == 0.0
        assert result["reason"] == "market_cap_filter"

    def test_zero_surprise(self):
        result = score_beat(surprise_pct=0.0, market_cap=1_000_000_000)
        assert result["score"] == 0.0
        assert result["reason"] == "no_surprise"

    def test_confirming_signals_counted(self):
        result = score_beat(
            surprise_pct=15.0,
            market_cap=1_000_000_000,
            revenue_beat=True,
            guidance_raised=True,
        )
        assert result["confirming_count"] == 2
        assert "revenue_beat" in result["confirming_signals"]
        assert "guidance_raised" in result["confirming_signals"]

    def test_short_squeeze_in_confirming(self):
        result = score_beat(
            surprise_pct=15.0,
            market_cap=1_000_000_000,
            short_float_pct=25.0,
        )
        assert "short_squeeze" in result["confirming_signals"]
        assert result["confirming_signals"]["short_squeeze"] == 25.0

    def test_short_squeeze_below_threshold_not_counted(self):
        result = score_beat(
            surprise_pct=15.0,
            market_cap=1_000_000_000,
            short_float_pct=15.0,
        )
        assert "short_squeeze" not in result.get("confirming_signals", {})

    def test_components_present(self):
        result = score_beat(
            surprise_pct=15.0,
            market_cap=1_000_000_000,
            revenue_beat=True,
        )
        comps = result["components"]
        assert "surprise_strength" in comps
        assert "confirming_boost" in comps
        assert "neglect" in comps
        assert "liquidity" in comps

    def test_score_is_product_of_components(self):
        result = score_beat(surprise_pct=15.0, market_cap=1_000_000_000)
        comps = result["components"]
        expected = (
            comps["surprise_strength"]
            * comps["confirming_boost"]
            * comps["neglect"]
            * comps["liquidity"]
        )
        assert result["score"] == pytest.approx(expected)

    def test_higher_surprise_scores_higher_than_low(self):
        low = score_beat(surprise_pct=5.0, market_cap=1_000_000_000)
        high = score_beat(surprise_pct=15.0, market_cap=1_000_000_000)
        assert high["score"] > low["score"]

    def test_confirming_boosts_increase_score(self):
        base = score_beat(surprise_pct=15.0, market_cap=1_000_000_000)
        boosted = score_beat(
            surprise_pct=15.0,
            market_cap=1_000_000_000,
            revenue_beat=True,
            guidance_raised=True,
        )
        assert boosted["score"] > base["score"]

    def test_no_confirming_count_zero(self):
        result = score_beat(surprise_pct=15.0, market_cap=1_000_000_000)
        assert result["confirming_count"] == 0
