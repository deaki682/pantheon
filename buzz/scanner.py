"""Assemble the weekly buzz basket.

acceleration (discovery) -> small/mid-cap filter -> price/volume confirmation
-> ranked basket of the strongest confirmed accelerators.

The LLM recommendation layer (in the /buzz skill) runs AFTER this, on the
confirmed set only — it judges authenticity/direction and recommends, it does
not invent candidates.

Pure stdlib.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Optional

from .acceleration import AccelSignal
from .confirm import Confirmation

# Buzz is noise on mega-caps and untradeable on true microcaps. The edge lives
# in the small/mid band with thin coverage.
MICRO_FLOOR = 50_000_000        # $50M — below this, spreads/illiquidity kill it
MEGA_CEILING = 10_000_000_000   # $10B — above this, retail buzz is rounding error


@dataclass
class BuzzCandidate:
    ticker: str
    mentions: int
    mentions_prev: int
    accel_ratio: float
    rank_jump: Optional[int]
    new_entrant: bool
    upvotes: int
    market_cap: Optional[float]
    price_change_pct: Optional[float]
    volume_ratio: Optional[float]
    confirmed: bool
    confirm_reason: str
    sector: str = ""
    name: str = ""


def in_small_mid_band(market_cap: Optional[float]) -> bool:
    """Keep small/mid-caps. Unknown cap is rejected — we won't buy blind."""
    if market_cap is None:
        return False
    return MICRO_FLOOR <= market_cap <= MEGA_CEILING


def build_candidate(sig: AccelSignal, market_cap: Optional[float],
                    conf: Confirmation, *, sector: str = "") -> BuzzCandidate:
    return BuzzCandidate(
        ticker=sig.ticker,
        mentions=sig.mentions,
        mentions_prev=sig.mentions_prev,
        accel_ratio=sig.accel_ratio,
        rank_jump=sig.rank_jump,
        new_entrant=sig.new_entrant,
        upvotes=sig.upvotes,
        market_cap=market_cap,
        price_change_pct=conf.price_change_pct,
        volume_ratio=conf.volume_ratio,
        confirmed=conf.confirmed,
        confirm_reason=conf.reason,
        sector=sector,
        name=sig.name,
    )


def rank_basket(candidates: list[BuzzCandidate], *, top_n: int = 8,
                require_confirmation: bool = True) -> list[BuzzCandidate]:
    """Rank confirmed, small/mid accelerators into a basket of the top N.

    require_confirmation (default True): only names where price/volume backs the
    buzz. Set False for the ghost's control group (it shadows unconfirmed names
    too, to measure whether the confirmation gate actually adds lift).
    """
    pool = [c for c in candidates if in_small_mid_band(c.market_cap)]
    if require_confirmation:
        pool = [c for c in pool if c.confirmed]
    # rank by acceleration, then by how much real volume backs it
    pool.sort(key=lambda c: (c.accel_ratio, c.volume_ratio or 0.0), reverse=True)
    return pool[:top_n]


def save_candidates(path: str, candidates: list[BuzzCandidate], *,
                    scanned_at: Optional[str] = None) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {"scanned_at": scanned_at, "candidates": [asdict(c) for c in candidates]}
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load_candidates(path: str) -> list[BuzzCandidate]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return [BuzzCandidate(**c) for c in data.get("candidates", [])]
