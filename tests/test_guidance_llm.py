"""Tests for GuidanceSignals scoring logic and refine_guidance fix."""
from __future__ import annotations

import pytest

from achilles.llm_refine import GuidanceSignals, LONG_DIRECTIONS, _parse_guidance_response


class TestGuidanceStrength:
    def test_raised_high_signal(self):
        """Dramatic, surprising, specific raise → high strength."""
        s = GuidanceSignals(direction="raised", magnitude=1.0, specificity=1.0, surprise=1.0)
        assert s.strength_adjustment == pytest.approx(1.3, abs=0.01)

    def test_raised_low_signal(self):
        """Trivial, expected, vague raise → low but nonzero strength."""
        s = GuidanceSignals(direction="raised", magnitude=0.0, specificity=0.0, surprise=0.0)
        assert s.strength_adjustment == pytest.approx(0.3, abs=0.01)

    def test_raised_moderate(self):
        """Mid-range signals → mid-range strength."""
        s = GuidanceSignals(direction="raised", magnitude=0.5, specificity=0.5, surprise=0.5)
        expected = 0.3 + (0.5 * 0.5 + 0.3 * 0.5 + 0.2 * 0.5) * 1.0
        assert s.strength_adjustment == pytest.approx(expected, abs=0.01)

    def test_initiated_discount(self):
        """Initiated guidance is discounted vs raised."""
        raised = GuidanceSignals(direction="raised", magnitude=0.6, specificity=0.8, surprise=0.5)
        initiated = GuidanceSignals(direction="initiated", magnitude=0.6, specificity=0.8, surprise=0.5)
        assert initiated.strength_adjustment < raised.strength_adjustment
        assert initiated.strength_adjustment == pytest.approx(
            raised.strength_adjustment * 0.85, abs=0.01)

    def test_narrowed_up_tradeable(self):
        s = GuidanceSignals(direction="narrowed_up", magnitude=0.4, specificity=0.7, surprise=0.3)
        assert s.strength_adjustment > 0

    def test_lowered_returns_zero(self):
        s = GuidanceSignals(direction="lowered", magnitude=0.8, specificity=1.0, surprise=1.0)
        assert s.strength_adjustment == 0.0

    def test_withdrawn_returns_zero(self):
        s = GuidanceSignals(direction="withdrawn", magnitude=0.5, specificity=0.5, surprise=0.5)
        assert s.strength_adjustment == 0.0

    def test_narrowed_down_returns_zero(self):
        s = GuidanceSignals(direction="narrowed_down", magnitude=0.5, specificity=0.5, surprise=0.5)
        assert s.strength_adjustment == 0.0

    def test_unknown_returns_zero(self):
        s = GuidanceSignals(direction="unknown")
        assert s.strength_adjustment == 0.0

    def test_clamps_inputs(self):
        """Out-of-range inputs are clamped to [0, 1]."""
        s = GuidanceSignals(direction="raised", magnitude=2.0, specificity=-0.5, surprise=1.5)
        # mag clamped to 1.0, spec clamped to 0.0, surp clamped to 1.0
        # raw = 0.5*1.0 + 0.3*1.0 + 0.2*0.0 = 0.8 → strength = 0.3 + 0.8 = 1.1
        assert s.strength_adjustment == pytest.approx(1.1, abs=0.01)

    def test_to_dict_includes_strength(self):
        s = GuidanceSignals(direction="raised", magnitude=0.5, surprise=0.5)
        d = s.to_dict()
        assert "strength_adjustment" in d
        assert d["direction"] == "raised"
        assert d["magnitude"] == 0.5


class TestParseGuidanceResponse:
    def test_valid_json(self):
        raw = '{"direction": "raised", "metric": "eps", "magnitude": 0.6, "specificity": 0.8, "surprise": 0.4, "prior_range": "$2.10-$2.20", "new_range": "$2.30-$2.40", "one_line_summary": "EPS guidance raised"}'
        s = _parse_guidance_response(raw)
        assert s.direction == "raised"
        assert s.metric == "eps"
        assert s.magnitude == 0.6
        assert s.prior_range == "$2.10-$2.20"
        assert s.new_range == "$2.30-$2.40"

    def test_markdown_wrapped_json(self):
        raw = '```json\n{"direction": "initiated", "metric": "revenue", "magnitude": 0.3, "specificity": 0.9, "surprise": 0.7, "prior_range": "", "new_range": "$100M-$110M", "one_line_summary": "first guidance"}\n```'
        s = _parse_guidance_response(raw)
        assert s.direction == "initiated"
        assert s.metric == "revenue"

    def test_garbage_returns_neutral(self):
        s = _parse_guidance_response("this is not json")
        assert s.direction == "unknown"
        assert s.strength_adjustment == 0.0


class TestRefineGuidanceFix:
    def test_lowered_guidance_no_longer_creates_event(self):
        """The regex fallback should not trade lowered guidance long."""
        from achilles.events import refine_guidance
        from types import SimpleNamespace

        filing = SimpleNamespace(
            symbol="ACME", accession_no="0001-23-456",
            filing_date="2026-06-28",
        )
        # "lowered" body text
        body = "The company lowered its full-year guidance to reflect macro headwinds."
        ev = refine_guidance(filing, body)
        assert ev is None

    def test_raised_guidance_still_works(self):
        from achilles.events import refine_guidance
        from types import SimpleNamespace

        filing = SimpleNamespace(
            symbol="ACME", accession_no="0001-23-789",
            filing_date="2026-06-28",
        )
        body = "Management raised its full-year guidance citing strong demand."
        ev = refine_guidance(filing, body)
        assert ev is not None
        assert ev.event_class == "guidance_revision"
        assert ev.strength == 1.0

    def test_withdrawn_guidance_no_event(self):
        from achilles.events import refine_guidance
        from types import SimpleNamespace

        filing = SimpleNamespace(
            symbol="ACME", accession_no="0001-23-000",
            filing_date="2026-06-28",
        )
        body = "The company has withdrawn its previously issued guidance."
        ev = refine_guidance(filing, body)
        assert ev is None
