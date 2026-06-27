"""Brief — structured note Achilles writes for each candidate event.

A brief has 4 sections:
  - filing: what the filing actually says
  - setup: surrounding context (recent price action, broader news)
  - disqualifiers: red flags that kill the trade
  - play: concrete entry, hard stop, profit target, time stop dates

Briefs are persisted as JSON next to the journal.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from .playbooks import Playbook


@dataclass
class Play:
    entry_dollars: float
    hard_stop_price: float
    profit_target_price: float
    time_stop_date: str
    trail_armed_at: float = 0.0
    trail_pct: float = 0.0


@dataclass
class Brief:
    event_id: str
    event_class: str
    symbol: str
    score: float
    filing: dict[str, Any] = field(default_factory=dict)
    setup: dict[str, Any] = field(default_factory=dict)
    disqualifiers: list[str] = field(default_factory=list)
    play: Optional[Play] = None
    created_at: str = ""


def build_play(
    *,
    playbook: Playbook,
    entry_price: float,
    entry_date: str,
    entry_dollars: float,
) -> Play:
    """Materialize the abstract playbook into absolute dollar levels."""
    if entry_price <= 0:
        raise ValueError("entry_price must be positive")
    hard_stop = entry_price * (1.0 + playbook.hard_stop_pct)
    profit_target = entry_price * (1.0 + playbook.profit_target_pct)
    try:
        dt = datetime.strptime(entry_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"bad entry_date {entry_date!r}") from e
    time_stop = (dt + timedelta(days=playbook.time_stop_days)).strftime("%Y-%m-%d")
    return Play(
        entry_dollars=float(entry_dollars),
        hard_stop_price=hard_stop,
        profit_target_price=profit_target,
        time_stop_date=time_stop,
    )


def make_brief(
    *,
    event_id: str,
    event_class: str,
    symbol: str,
    score: float,
    filing: dict[str, Any],
    setup: dict[str, Any],
    disqualifiers: list[str],
    play: Optional[Play] = None,
) -> Brief:
    return Brief(
        event_id=event_id,
        event_class=event_class,
        symbol=symbol.upper(),
        score=float(score),
        filing=dict(filing or {}),
        setup=dict(setup or {}),
        disqualifiers=list(disqualifiers or ()),
        play=play,
        created_at=datetime.utcnow().isoformat(),
    )


def brief_to_dict(b: Brief) -> dict:
    d = asdict(b)
    return d


def brief_from_dict(d: dict) -> Brief:
    p = d.get("play")
    play = Play(**p) if p else None
    b = Brief(
        event_id=d["event_id"],
        event_class=d["event_class"],
        symbol=d["symbol"],
        score=float(d.get("score", 0.0)),
        filing=dict(d.get("filing", {})),
        setup=dict(d.get("setup", {})),
        disqualifiers=list(d.get("disqualifiers", [])),
        play=play,
        created_at=d.get("created_at", ""),
    )
    return b
