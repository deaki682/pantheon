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
    reaction_pct: Optional[float] = None   # post-report reaction; None = unconfirmed
    score: float = 0.0
    confirming_count: int = 0
    sector: str = ""


def rank_beats(
    candidates: list[BeatCandidate],
    *,
    top_n: int = 12,
    require_reaction: bool = True,
) -> list[BeatCandidate]:
    """Score, gate, and rank beats into a basket of the top N.

    require_reaction (default True): only keep beats the market REWARDED —
    a confirmed positive post-report reaction. This drops 'sold beats'
    (gap up, close red) and beats whose reaction we couldn't verify. Set
    False only for backtests/paper runs where reaction data isn't gathered.
    """
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
        if c.score <= 0:
            continue
        if require_reaction and not (c.reaction_pct is not None and c.reaction_pct > 0):
            continue  # skip sold or unconfirmed beats — trade the reaction, not the headline
        scored.append(c)
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_n]


def pick_best(candidates: list[BeatCandidate], *, require_reaction: bool = True) -> Optional[BeatCandidate]:
    ranked = rank_beats(candidates, require_reaction=require_reaction)
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
