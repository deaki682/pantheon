"""Mention acceleration — the discovery signal.

The edge is the *second derivative* of attention: talk igniting relative to a
stock's own recent baseline, not talk that's already loud (which is arbitraged).
ApeWisdom hands us both sides for free — current `mentions` and `mentions_24h_ago`
per ticker — so acceleration is a direct computation, no scraping or NLP.

Pure stdlib. The /buzz skill fetches the feed and passes rows in.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# A name needs enough *absolute* current chatter to be a real signal, but we do
# NOT want the already-loud names (those are the arbitraged 'level' trap).
MIN_MENTIONS_NOW = 15
# Baseline floor: a jump from 1 -> 20 mentions is noise, not a trend. Require a
# minimum prior base before trusting the ratio; below it, treat as a new entrant.
MIN_BASELINE = 5
# Acceleration must clear this to count as 'igniting'.
MIN_ACCEL_RATIO = 2.0
# Cap the ratio so a tiny base can't produce an absurd score.
MAX_ACCEL_RATIO = 20.0


@dataclass
class BuzzRow:
    ticker: str
    mentions: int
    mentions_prev: int
    rank: Optional[int] = None
    rank_prev: Optional[int] = None
    upvotes: int = 0
    name: str = ""


def parse_apewisdom(payload: dict) -> list[BuzzRow]:
    """Normalize an ApeWisdom /filter response into BuzzRow list."""
    out: list[BuzzRow] = []
    for r in (payload or {}).get("results", []):
        tk = (r.get("ticker") or "").upper()
        if not tk:
            continue
        try:
            mentions = int(r.get("mentions", 0) or 0)
            prev = int(r.get("mentions_24h_ago", 0) or 0)
        except (TypeError, ValueError):
            continue
        out.append(BuzzRow(
            ticker=tk,
            mentions=mentions,
            mentions_prev=prev,
            rank=r.get("rank"),
            rank_prev=r.get("rank_24h_ago"),
            upvotes=int(r.get("upvotes", 0) or 0),
            name=r.get("name", ""),
        ))
    return out


def acceleration_ratio(mentions: int, mentions_prev: int) -> float:
    """mentions / baseline, with a baseline floor and a cap.

    A new entrant (prev below the floor) is measured against MIN_BASELINE so a
    1 -> 40 spike doesn't score infinite. Ratio is capped at MAX_ACCEL_RATIO.
    """
    base = max(mentions_prev, MIN_BASELINE)
    if base <= 0:
        return 0.0
    return min(mentions / base, MAX_ACCEL_RATIO)


def is_new_entrant(mentions_prev: int) -> bool:
    return mentions_prev < MIN_BASELINE


@dataclass
class AccelSignal:
    ticker: str
    mentions: int
    mentions_prev: int
    accel_ratio: float
    rank: Optional[int]
    rank_prev: Optional[int]
    rank_jump: Optional[int]      # positive = climbed toward #1
    new_entrant: bool
    upvotes: int
    name: str


def score_acceleration(row: BuzzRow) -> Optional[AccelSignal]:
    """Return an AccelSignal if the row is genuinely accelerating, else None.

    Gate: enough current chatter (MIN_MENTIONS_NOW) AND acceleration above
    MIN_ACCEL_RATIO. This is a discovery filter, not a ranking of conviction —
    price/volume confirmation (buzz.confirm) decides whether it's tradeable.
    """
    if row.mentions < MIN_MENTIONS_NOW:
        return None
    ratio = acceleration_ratio(row.mentions, row.mentions_prev)
    if ratio < MIN_ACCEL_RATIO:
        return None
    rank_jump = None
    if row.rank is not None and row.rank_prev is not None:
        rank_jump = row.rank_prev - row.rank  # climbing toward #1 -> positive
    return AccelSignal(
        ticker=row.ticker,
        mentions=row.mentions,
        mentions_prev=row.mentions_prev,
        accel_ratio=round(ratio, 2),
        rank=row.rank,
        rank_prev=row.rank_prev,
        rank_jump=rank_jump,
        new_entrant=is_new_entrant(row.mentions_prev),
        upvotes=row.upvotes,
        name=row.name,
    )


def accelerating(rows: list[BuzzRow]) -> list[AccelSignal]:
    """All rows that clear the acceleration gate, hottest first."""
    sigs = [s for s in (score_acceleration(r) for r in rows) if s is not None]
    sigs.sort(key=lambda s: s.accel_ratio, reverse=True)
    return sigs
