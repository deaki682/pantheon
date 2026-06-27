"""Decision journal — JSONL of every call Oracle makes.

A call records: symbol, decision (buy/add/sell/trim/hold/avoid/watch),
conviction, horizon, price at decision, plus driving features.
After the horizon elapses we grade the call against actual price movement.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterable


VALID_DECISIONS = {"buy", "add", "sell", "trim", "hold", "avoid", "watch"}


@dataclass
class JournalEntry:
    timestamp: str
    symbol: str
    decision: str
    conviction: float
    horizon_days: int
    price: float
    features: dict[str, Any] = field(default_factory=dict)
    graded_at: str = ""
    graded_return: float | None = None
    graded_outcome: str = ""  # 'win' | 'loss' | 'neutral'


def append(path: str, entry: JournalEntry) -> None:
    if entry.decision not in VALID_DECISIONS:
        raise ValueError(f"invalid decision {entry.decision!r}")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(asdict(entry), sort_keys=True) + "\n")


def read(path: str) -> list[JournalEntry]:
    if not os.path.exists(path):
        return []
    out: list[JournalEntry] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                out.append(JournalEntry(**d))
            except (json.JSONDecodeError, TypeError):
                continue
    return out


def grade(
    entry: JournalEntry,
    final_price: float,
    *,
    win_threshold: float = 0.05,
) -> JournalEntry:
    """Grade an entry against the final price.

    For buy/add: positive return is a win.
    For sell/trim: negative return is a win (avoided loss).
    For hold/watch/avoid: neutral.
    """
    if entry.price <= 0:
        return entry
    ret = (final_price - entry.price) / entry.price
    entry.graded_at = datetime.utcnow().isoformat()
    entry.graded_return = ret
    if entry.decision in ("buy", "add"):
        entry.graded_outcome = "win" if ret >= win_threshold else ("loss" if ret <= -win_threshold else "neutral")
    elif entry.decision in ("sell", "trim"):
        entry.graded_outcome = "win" if ret <= -win_threshold else ("loss" if ret >= win_threshold else "neutral")
    else:
        entry.graded_outcome = "neutral"
    return entry


def write(path: str, entries: Iterable[JournalEntry]) -> None:
    """Overwrite the journal with the given entries (e.g. after grading)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        for e in entries:
            f.write(json.dumps(asdict(e), sort_keys=True) + "\n")
    os.replace(tmp, path)
