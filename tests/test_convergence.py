"""Tests for the convergence scoring module."""
import pytest

from achilles.convergence import (
    neglect_premium,
    conviction_multiplier,
    extract_convergence_signals,
    build_prescreener_lookup,
)


class TestNeglectPremium:
    def test_none_returns_high_neglect(self):
        assert neglect_premium(None) == 0.85

    def test_zero_quality_max_neglect(self):
        assert neglect_premium(0.0) == 1.0

    def test_full_quality_min_neglect(self):
        assert neglect_premium(1.0) == pytest.approx(0.3)

    def test_mid_quality(self):
        assert 0.5 < neglect_premium(0.5) < 0.8

    def test_monotonically_decreasing(self):
        vals = [neglect_premium(q / 10) for q in range(11)]
        for i in range(len(vals) - 1):
            assert vals[i] >= vals[i + 1]


class TestConvictionMultiplier:
    def test_base_is_above_one(self):
        assert conviction_multiplier() >= 1.0

    def test_large_surprise_adds(self):
        base = conviction_multiplier()
        with_surprise = conviction_multiplier(surprise_pct=40.0)
        assert with_surprise > base

    def test_insider_adds(self):
        base = conviction_multiplier()
        with_insider = conviction_multiplier(insider_preactivity=True)
        assert with_insider > base + 0.4

    def test_concurrent_guidance_adds(self):
        base = conviction_multiplier()
        with_guidance = conviction_multiplier(concurrent_guidance=True)
        assert with_guidance > base

    def test_neglect_adds_more_for_low_quality(self):
        low_q = conviction_multiplier(oracle_quality=0.1)
        high_q = conviction_multiplier(oracle_quality=0.9)
        assert low_q > high_q

    def test_heavy_dilution_penalizes(self):
        base = conviction_multiplier()
        diluted = conviction_multiplier(dilution_yoy=0.20)
        assert diluted < base

    def test_full_convergence_high(self):
        full = conviction_multiplier(
            surprise_pct=50.0,
            insider_preactivity=True,
            concurrent_guidance=True,
            oracle_quality=0.0,
        )
        assert full > 2.5

    def test_floor_at_half(self):
        worst = conviction_multiplier(dilution_yoy=0.50, oracle_quality=1.0)
        assert worst >= 0.5

    def test_ignores_unknown_kwargs(self):
        result = conviction_multiplier(revenue_yoy=0.5, fcf=100.0)
        assert result >= 1.0


class TestExtractSignals:
    def test_empty_returns_defaults(self):
        signals = extract_convergence_signals("ACME")
        assert signals["surprise_pct"] is None
        assert signals["insider_preactivity"] is False
        assert signals["concurrent_guidance"] is False

    def test_extracts_from_metadata(self):
        signals = extract_convergence_signals(
            "ACME",
            event_metadata={
                "surprise_pct": 15.0,
                "insider_boost": 1.3,
            },
        )
        assert signals["surprise_pct"] == 15.0
        assert signals["insider_preactivity"] is True

    def test_extracts_dilution_from_prescreener(self):
        signals = extract_convergence_signals(
            "ACME",
            prescreener_rows={"ACME": {"dilution_yoy": 0.05}},
        )
        assert signals["dilution_yoy"] == 0.05

    def test_passes_oracle_quality(self):
        signals = extract_convergence_signals("ACME", oracle_quality=0.6)
        assert signals["oracle_quality"] == 0.6


class TestBuildPrescreenerLookup:
    def test_builds_from_rows(self):
        rows = [
            {"snapshot": {"symbol": "ACME", "revenue_yoy": 0.2}},
            {"snapshot": {"symbol": "BETA", "dilution_yoy": 0.01}},
            {"snapshot": None},
            {"no_snapshot": True},
        ]
        lookup = build_prescreener_lookup(rows)
        assert "ACME" in lookup
        assert "BETA" in lookup
        assert len(lookup) == 2

    def test_uppercases_symbols(self):
        rows = [{"snapshot": {"symbol": "acme"}}]
        lookup = build_prescreener_lookup(rows)
        assert "ACME" in lookup
