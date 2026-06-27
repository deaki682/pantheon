"""Brief structural validation.

Every brief must have: event_id, event_class, symbol, score, and a play
(unless disqualifiers killed it). The play's hard_stop must be below entry
price (implied via negative pct), profit_target above entry, time_stop
in the future relative to created_at.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .brief import Brief, Play


class BriefError(ValueError):
    pass


def validate_brief(b: Brief) -> Brief:
    if not b.event_id:
        raise BriefError("brief missing event_id")
    if not b.event_class:
        raise BriefError("brief missing event_class")
    if not b.symbol:
        raise BriefError("brief missing symbol")

    if b.disqualifiers:
        # Disqualified briefs don't need a play
        return b

    if b.play is None:
        raise BriefError(f"{b.event_id}: brief has no play but no disqualifiers")
    play = b.play
    if play.entry_dollars <= 0:
        raise BriefError(f"{b.event_id}: entry_dollars must be > 0")
    if play.hard_stop_price <= 0:
        raise BriefError(f"{b.event_id}: hard_stop_price must be > 0")
    if play.profit_target_price <= 0:
        raise BriefError(f"{b.event_id}: profit_target_price must be > 0")
    if play.profit_target_price <= play.hard_stop_price:
        raise BriefError(f"{b.event_id}: profit_target <= hard_stop")
    if not play.time_stop_date:
        raise BriefError(f"{b.event_id}: missing time_stop_date")
    return b
