import json
import os

import pytest

from achilles.scanner import (
    BeatCandidate,
    load_candidates,
    pick_best,
    rank_beats,
    save_candidates,
)


# --- BeatCandidate construction ---


class TestBeatCandidate:
    def test_required_fields(self):
        c = BeatCandidate(
            symbol="ACME",
            surprise_pct=15.0,
            actual_eps=1.15,
            estimate_eps=1.00,
            report_date="2026-07-15",
        )
        assert c.symbol == "ACME"
        assert c.surprise_pct == 15.0
        assert c.actual_eps == 1.15
        assert c.estimate_eps == 1.00
        assert c.report_date == "2026-07-15"

    def test_defaults(self):
        c = BeatCandidate(
            symbol="ACME",
            surprise_pct=10.0,
            actual_eps=1.10,
            estimate_eps=1.00,
            report_date="2026-07-15",
        )
        assert c.revenue_beat is False
        assert c.guidance_raised is False
        assert c.short_float_pct is None
        assert c.insider_prebuy is False
        assert c.market_cap is None
        assert c.current_price is None
        assert c.score == 0.0
        assert c.confirming_count == 0
        assert c.sector == ""
        assert c.reaction_pct is None

    def test_optional_fields(self):
        c = BeatCandidate(
            symbol="XYZ",
            surprise_pct=20.0,
            actual_eps=1.20,
            estimate_eps=1.00,
            report_date="2026-07-20",
            revenue_beat=True,
            guidance_raised=True,
            short_float_pct=25.0,
            insider_prebuy=True,
            market_cap=1_000_000_000,
            current_price=50.0,
            sector="Technology",
        )
        assert c.revenue_beat is True
        assert c.guidance_raised is True
        assert c.short_float_pct == 25.0
        assert c.insider_prebuy is True
        assert c.market_cap == 1_000_000_000
        assert c.current_price == 50.0
        assert c.sector == "Technology"


def _make_candidate(
    symbol="ACME",
    surprise_pct=15.0,
    market_cap=1_000_000_000,
    reaction_pct=0.05,   # rewarded beat by default so it clears the gate
    **kwargs,
):
    return BeatCandidate(
        symbol=symbol,
        surprise_pct=surprise_pct,
        actual_eps=1.15,
        estimate_eps=1.00,
        report_date="2026-07-15",
        market_cap=market_cap,
        reaction_pct=reaction_pct,
        **kwargs,
    )


# --- rank_beats ---


class TestRankBeats:
    def test_scores_and_sorts(self):
        c1 = _make_candidate(symbol="LOW", surprise_pct=5.0)
        c2 = _make_candidate(symbol="HIGH", surprise_pct=20.0, revenue_beat=True)
        ranked = rank_beats([c1, c2])
        assert len(ranked) > 0
        assert ranked[0].symbol == "HIGH"
        assert ranked[0].score > 0

    def test_respects_top_n(self):
        candidates = [
            _make_candidate(symbol=f"S{i}", surprise_pct=10.0 + i)
            for i in range(10)
        ]
        ranked = rank_beats(candidates, top_n=3)
        assert len(ranked) == 3

    def test_filters_zero_score(self):
        # market_cap=None fails market_cap_ok -> score=0
        c_bad = _make_candidate(symbol="BAD", market_cap=None)
        c_good = _make_candidate(symbol="GOOD", surprise_pct=15.0)
        ranked = rank_beats([c_bad, c_good])
        symbols = [c.symbol for c in ranked]
        assert "BAD" not in symbols
        assert "GOOD" in symbols

    def test_filters_below_min_market_cap(self):
        c = _make_candidate(symbol="TINY", market_cap=1_000_000)
        ranked = rank_beats([c])
        assert len(ranked) == 0

    def test_filters_above_max_market_cap(self):
        c = _make_candidate(symbol="MEGA", market_cap=100_000_000_000)
        ranked = rank_beats([c])
        assert len(ranked) == 0

    def test_empty_input(self):
        assert rank_beats([]) == []

    def test_all_filtered_returns_empty(self):
        candidates = [_make_candidate(symbol="X", market_cap=None)]
        assert rank_beats(candidates) == []

    def test_updates_score_on_candidates(self):
        c = _make_candidate(surprise_pct=15.0)
        rank_beats([c])
        # score was updated in-place (even if filtered, it's set)
        # If it passed, score > 0
        assert c.score > 0


class TestReactionGate:
    def test_drops_sold_beat(self):
        # strong beat but the market SOLD it (negative reaction) -> dropped
        sold = _make_candidate(symbol="SOLD", surprise_pct=20.0, reaction_pct=-0.04)
        rewarded = _make_candidate(symbol="REWARD", surprise_pct=20.0, reaction_pct=0.06)
        ranked = rank_beats([sold, rewarded])
        syms = [c.symbol for c in ranked]
        assert "SOLD" not in syms
        assert "REWARD" in syms

    def test_drops_unconfirmed_reaction(self):
        unknown = _make_candidate(symbol="UNK", reaction_pct=None)
        assert rank_beats([unknown]) == []

    def test_require_reaction_false_keeps_all(self):
        sold = _make_candidate(symbol="SOLD", surprise_pct=20.0, reaction_pct=-0.04)
        unknown = _make_candidate(symbol="UNK", reaction_pct=None)
        ranked = rank_beats([sold, unknown], require_reaction=False)
        assert {c.symbol for c in ranked} == {"SOLD", "UNK"}


class TestReactionMagnitudeGuard:
    """The 'already fired' guard: a beat that already popped too far has spent
    its drift (the Oracle-BOLD lesson applied to PEAD)."""

    def test_drops_already_fired_beat(self):
        moderate = _make_candidate(symbol="MOD", surprise_pct=20.0, reaction_pct=0.08)
        fired = _make_candidate(symbol="FIRED", surprise_pct=20.0, reaction_pct=0.35)  # +35% pop
        ranked = rank_beats([moderate, fired])
        syms = [c.symbol for c in ranked]
        assert "FIRED" not in syms      # already fired -> dropped
        assert "MOD" in syms

    def test_fired_guard_applies_even_without_require_reaction(self):
        fired = _make_candidate(symbol="FIRED", surprise_pct=20.0, reaction_pct=0.40)
        assert rank_beats([fired], require_reaction=False) == []

    def test_cap_is_configurable(self):
        c = _make_candidate(symbol="C", surprise_pct=20.0, reaction_pct=0.15)
        assert rank_beats([c], max_reaction_pct=0.10) == []     # tighter cap drops it
        assert [x.symbol for x in rank_beats([c], max_reaction_pct=0.25)] == ["C"]


# --- pick_best ---


class TestPickBest:
    def test_returns_highest(self):
        c1 = _make_candidate(symbol="LOW", surprise_pct=5.0)
        c2 = _make_candidate(symbol="HIGH", surprise_pct=20.0, guidance_raised=True)
        best = pick_best([c1, c2])
        assert best is not None
        assert best.symbol == "HIGH"

    def test_empty_returns_none(self):
        assert pick_best([]) is None

    def test_all_filtered_returns_none(self):
        c = _make_candidate(market_cap=None)
        assert pick_best([c]) is None

    def test_single_valid_candidate(self):
        c = _make_candidate(symbol="ONLY")
        best = pick_best([c])
        assert best is not None
        assert best.symbol == "ONLY"


# --- save / load round-trip ---


class TestPersistence:
    def test_save_load_roundtrip(self, tmp_path):
        candidates = [
            _make_candidate(
                symbol="AAA",
                surprise_pct=15.0,
                revenue_beat=True,
                short_float_pct=25.0,
            ),
            _make_candidate(symbol="BBB", surprise_pct=10.0),
        ]
        path = str(tmp_path / "candidates.json")
        save_candidates(path, candidates)
        loaded = load_candidates(path)
        assert len(loaded) == 2
        assert loaded[0].symbol == "AAA"
        assert loaded[0].revenue_beat is True
        assert loaded[0].short_float_pct == 25.0
        assert loaded[1].symbol == "BBB"

    def test_load_missing_file_returns_empty(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        assert load_candidates(path) == []

    def test_save_creates_directories(self, tmp_path):
        path = str(tmp_path / "deep" / "nested" / "candidates.json")
        save_candidates(path, [_make_candidate()])
        assert os.path.exists(path)

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        c = _make_candidate(
            symbol="FULL",
            surprise_pct=22.0,
            revenue_beat=True,
            guidance_raised=True,
            short_float_pct=30.0,
            insider_prebuy=True,
            market_cap=500_000_000,
        )
        c.score = 0.75
        c.confirming_count = 3
        c.sector = "Healthcare"
        c.current_price = 42.0

        path = str(tmp_path / "full.json")
        save_candidates(path, [c])
        loaded = load_candidates(path)
        assert len(loaded) == 1
        r = loaded[0]
        assert r.symbol == "FULL"
        assert r.surprise_pct == 22.0
        assert r.revenue_beat is True
        assert r.guidance_raised is True
        assert r.short_float_pct == 30.0
        assert r.insider_prebuy is True
        assert r.market_cap == 500_000_000
        assert r.score == 0.75
        assert r.confirming_count == 3
        assert r.sector == "Healthcare"
        assert r.current_price == 42.0

    def test_save_is_valid_json(self, tmp_path):
        path = str(tmp_path / "valid.json")
        save_candidates(path, [_make_candidate()])
        with open(path) as f:
            data = json.load(f)
        assert "candidates" in data
        assert len(data["candidates"]) == 1
