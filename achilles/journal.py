"""Event-keyed position journal.

Each open/close action is appended as a JSONL line. Used for the per-class
attribution log (hit rate vs expected) and for performance analysis.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterable


@dataclass
class TradeEntry:
    timestamp: str
    event_id: str
    event_class: str
    symbol: str
    action: str  # 'open' | 'close'
    price: float
    shares: float
    dollars: float
    reason: str = ""
    pnl: float | None = None
    features: dict[str, Any] = field(default_factory=dict)


def append(path: str, entry: TradeEntry) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def read(path: str) -> list[TradeEntry]:
    if not os.path.exists(path):
        return []
    out: list[TradeEntry] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                out.append(TradeEntry(**d))
            except (json.JSONDecodeError, TypeError):
                continue
    return out


def round_trip_pnl(entries: Iterable[TradeEntry]) -> list[dict]:
    """Pair opens with closes by event_id and emit round-trip PnL rows."""
    opens: dict[str, TradeEntry] = {}
    out: list[dict] = []
    for e in entries:
        if e.action == "open":
            opens[e.event_id] = e
        elif e.action == "close":
            o = opens.pop(e.event_id, None)
            if o is None:
                continue
            ret = (e.price - o.price) / o.price if o.price > 0 else 0.0
            out.append({
                "event_id": e.event_id,
                "event_class": e.event_class,
                "symbol": e.symbol,
                "open_date": o.timestamp,
                "close_date": e.timestamp,
                "return_pct": ret,
                "pnl_dollars": e.pnl if e.pnl is not None else (e.dollars - o.dollars),
                "hit": ret > 0,
            })
    return out


def per_class_stats(entries: Iterable[TradeEntry]) -> dict[str, dict]:
    rts = round_trip_pnl(entries)
    by_class: dict[str, list[dict]] = {}
    for rt in rts:
        by_class.setdefault(rt["event_class"], []).append(rt)
    out: dict[str, dict] = {}
    for cls, rows in by_class.items():
        hits = sum(1 for r in rows if r["hit"])
        n = len(rows)
        out[cls] = {
            "n": n,
            "hits": hits,
            "hit_rate": hits / n if n else 0.0,
            "mean_return": sum(r["return_pct"] for r in rows) / n if n else 0.0,
        }
    return out
