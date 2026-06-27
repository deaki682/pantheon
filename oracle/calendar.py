"""Cadence helpers.

Oracle runs research every few days, with a heavy quarterly screening pass.
This module tracks last-run timestamps and reports whether it's time.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta


RESEARCH_INTERVAL_DAYS = 3
SCREEN_INTERVAL_DAYS = 90


def _read(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def mark_run(path: str, key: str, *, now: datetime | None = None) -> None:
    now = now or datetime.utcnow()
    d = _read(path)
    d[key] = now.isoformat()
    _write(path, d)


def days_since(path: str, key: str, *, now: datetime | None = None) -> float | None:
    now = now or datetime.utcnow()
    d = _read(path)
    raw = d.get(key)
    if not raw:
        return None
    try:
        ts = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return (now - ts).total_seconds() / 86_400.0


def should_run(
    path: str, key: str, interval_days: float, *, now: datetime | None = None
) -> bool:
    elapsed = days_since(path, key, now=now)
    if elapsed is None:
        return True
    return elapsed >= interval_days
