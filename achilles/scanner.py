"""PEAD scanner — identifies and ranks earnings beats for Achilles.

Stage 1: Collect recent earnings reporters, compute surprises
Stage 2: Score each beat with confirming signals
Stage 3: Rank and pick the best candidate
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Optional

from .scoring import market_cap_ok, score_beat


@dataclass
class BeatCandidate:
    symbol: str
    surprise_pct: float
    actual_eps: float
    estimate_eps: float
    report_date: str
    revenue_beat: bool = False
    guidance_raised: bool = False
    short_float_pct: Optional[float] = None
    insider_prebuy: bool = False
    market_cap: Optional[float] = None
    current_price: Optional[float] = None
    score: float = 0.0
    confirming_count: int = 0
    sector: str = ""


def rank_beats(candidates: list[BeatCandidate], *, top_n: int = 5) -> list[BeatCandidate]:
    scored = []
    for c in candidates:
        result = score_beat(
            surprise_pct=c.surprise_pct,
            market_cap=c.market_cap,
            revenue_beat=c.revenue_beat,
            guidance_raised=c.guidance_raised,
            short_float_pct=c.short_float_pct,
            insider_prebuy=c.insider_prebuy,
        )
        c.score = result.get("score", 0.0)
        c.confirming_count = result.get("confirming_count", 0)
        if c.score > 0:
            scored.append(c)
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_n]


def pick_best(candidates: list[BeatCandidate]) -> Optional[BeatCandidate]:
    ranked = rank_beats(candidates)
    return ranked[0] if ranked else None


def save_candidates(path: str, candidates: list[BeatCandidate]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {"candidates": [asdict(c) for c in candidates]}
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load_candidates(path: str) -> list[BeatCandidate]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return [BeatCandidate(**c) for c in data.get("candidates", [])]
