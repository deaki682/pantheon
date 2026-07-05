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

# The "already fired" guard (added 2026-07-05, the Oracle-BOLD lesson applied to
# PEAD). Achilles enters the day AFTER the report, betting on continued drift —
# but a beat whose initial post-report reaction ALREADY ran past this cap has
# been fully repriced by the market, and the academic PEAD edge is a moderate-
# surprise phenomenon: extreme initial reactions revert, they don't drift. So a
# reaction bigger than the cap is "fired" and dropped, exactly like Oracle's
# RUNUP_FIRED_CAP. Direction (rewarded vs sold) was already gated; this gates
# MAGNITUDE. Units: a FRACTION, matching reaction_pct (reaction_return returns
# (post-pre)/pre, so 0.20 = +20%). The exact cap is a hypothesis for the
# Achilles gauntlet to refine.
MAX_REACTION_PCT = 0.20


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
    max_reaction_pct: float = MAX_REACTION_PCT,
) -> list[BeatCandidate]:
    """Score, gate, and rank beats into a basket of the top N.

    require_reaction (default True): only keep beats the market REWARDED —
    a confirmed positive post-report reaction. This drops 'sold beats'
    (gap up, close red) and beats whose reaction we couldn't verify. Set
    False only for backtests/paper runs where reaction data isn't gathered.

    max_reaction_pct (the 'already fired' guard): drop beats whose confirmed
    initial reaction already ran past this cap — the drift is spent (see
    MAX_REACTION_PCT). Applies whenever reaction data is present, independent of
    require_reaction. Direction is gated above; this gates MAGNITUDE.
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
        if c.reaction_pct is not None and c.reaction_pct > max_reaction_pct:
            continue  # already fired — the initial pop spent the drift; don't chase it
        scored.append(c)
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_n]


def pick_best(candidates: list[BeatCandidate], *, require_reaction: bool = True,
              max_reaction_pct: float = MAX_REACTION_PCT) -> Optional[BeatCandidate]:
    ranked = rank_beats(candidates, require_reaction=require_reaction,
                        max_reaction_pct=max_reaction_pct)
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
