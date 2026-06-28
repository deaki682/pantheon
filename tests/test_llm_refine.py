"""Tests for the LLM filing analysis module."""
import json
import pytest

from achilles.llm_refine import LLMSignals, _parse_response, analyze_filing


class TestLLMSignals:
    def test_neutral_defaults(self):
        s = LLMSignals()
        assert s.strength_adjustment == 1.0
        assert s.disqualifiers == []

    def test_genuine_beat_confident_tone(self):
        s = LLMSignals(beat_quality="genuine", management_tone="confident")
        assert s.strength_adjustment > 1.0

    def test_one_time_beat_penalized(self):
        s = LLMSignals(beat_quality="one_time")
        assert s.strength_adjustment == pytest.approx(0.4)

    def test_mixed_beat_penalized(self):
        s = LLMSignals(beat_quality="mixed")
        assert s.strength_adjustment == pytest.approx(0.7)

    def test_cautious_tone_penalized(self):
        s = LLMSignals(management_tone="cautious")
        assert s.strength_adjustment < 1.0

    def test_revenue_beat_boosts(self):
        s = LLMSignals(revenue_signal="beat")
        assert s.strength_adjustment > 1.0

    def test_revenue_miss_penalizes(self):
        s = LLMSignals(revenue_signal="miss")
        assert s.strength_adjustment < 1.0

    def test_red_flags_penalize(self):
        s = LLMSignals(red_flags=["restatement", "material weakness"])
        assert s.strength_adjustment < 1.0

    def test_catalysts_boost(self):
        s = LLMSignals(catalysts=["buyback", "guidance raised"])
        assert s.strength_adjustment > 1.0

    def test_hard_disqualifiers_extracted(self):
        s = LLMSignals(red_flags=["restatement", "minor issue", "going concern"])
        assert "restatement" in s.disqualifiers
        assert "going concern" in s.disqualifiers
        assert len(s.disqualifiers) == 2

    def test_worst_case_doesnt_go_negative(self):
        s = LLMSignals(
            beat_quality="one_time",
            management_tone="cautious",
            revenue_signal="miss",
            red_flags=["restatement", "going concern", "auditor change"],
        )
        assert s.strength_adjustment > 0.0

    def test_best_case_capped(self):
        s = LLMSignals(
            beat_quality="genuine",
            management_tone="confident",
            revenue_signal="beat",
            catalysts=["buyback", "guidance raised", "new contract", "dividend"],
        )
        assert s.strength_adjustment <= 2.0

    def test_to_dict(self):
        s = LLMSignals(beat_quality="genuine", summary="strong quarter")
        d = s.to_dict()
        assert d["beat_quality"] == "genuine"
        assert d["summary"] == "strong quarter"
        assert "strength_adjustment" in d


class TestParseResponse:
    def test_valid_json(self):
        raw = json.dumps({
            "beat_quality": "genuine",
            "management_tone": "confident",
            "catalysts": ["buyback"],
            "red_flags": [],
            "revenue_signal": "beat",
            "one_line_summary": "Strong quarter driven by revenue growth",
        })
        s = _parse_response(raw)
        assert s.beat_quality == "genuine"
        assert s.management_tone == "confident"
        assert s.catalysts == ["buyback"]
        assert s.revenue_signal == "beat"

    def test_markdown_wrapped_json(self):
        raw = '```json\n{"beat_quality": "mixed", "management_tone": "neutral", "catalysts": [], "red_flags": [], "revenue_signal": "unknown", "one_line_summary": "ok"}\n```'
        s = _parse_response(raw)
        assert s.beat_quality == "mixed"

    def test_invalid_json_returns_signals_with_raw(self):
        s = _parse_response("this is not json")
        assert s.beat_quality == "unknown"
        assert s.raw_response == "this is not json"

    def test_partial_json_fills_defaults(self):
        raw = json.dumps({"beat_quality": "genuine"})
        s = _parse_response(raw)
        assert s.beat_quality == "genuine"
        assert s.management_tone == "neutral"
        assert s.catalysts == []


class TestAnalyzeFiling:
    def test_no_api_key_returns_neutral(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        s = analyze_filing("some body text " * 50, "ACME", 15.0)
        assert s.strength_adjustment == 1.0

    def test_short_body_returns_neutral(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        s = analyze_filing("too short", "ACME", 15.0)
        assert s.strength_adjustment == 1.0

    def test_empty_body_returns_neutral(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        s = analyze_filing("", "ACME", 15.0)
        assert s.strength_adjustment == 1.0
