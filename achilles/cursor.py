"""EDGAR polling cursor + seen-accessions dedup.

CRITICAL invariants:
  - cursor_date advances ONLY through register_events() based on the maximum
    filing date seen. NEVER assign it today's date directly.
  - The filter is STRICT GREATER-THAN — so if you advance past real filing
    dates you permanently hide same-day filings.
  - seen_accessions is a 5,000-entry FIFO set for fine-grained dedup.
"""
from __future__ import annotations

import json
import os
from collections import deque
from dataclasses import dataclass, field
from typing import Iterable


SEEN_MAX = 5_000


@dataclass
class Cursor:
    cursor_date: str = ""  # last max filing date processed (YYYY-MM-DD)
    seen: deque = field(default_factory=lambda: deque(maxlen=SEEN_MAX))

    @property
    def seen_set(self) -> set[str]:
        return set(self.seen)

    def to_dict(self) -> dict:
        return {"cursor_date": self.cursor_date, "seen": list(self.seen)}

    @classmethod
    def from_dict(cls, d: dict) -> "Cursor":
        c = cls()
        c.cursor_date = d.get("cursor_date", "")
        for acc in d.get("seen", []):
            c.seen.append(acc)
        return c


def register_events(cursor: Cursor, filings: Iterable) -> list:
    """Register a batch of filings, dedup against seen, advance cursor by MAX filing_date.

    Returns the list of NEW filings (those not already in seen_accessions).
    cursor.cursor_date is advanced ONLY by the maximum filing date in the
    batch — never to today's date directly.
    """
    new = []
    max_date = cursor.cursor_date
    seen = cursor.seen_set
    for f in filings:
        acc = getattr(f, "accession_no", "")
        if not acc or acc in seen:
            continue
        new.append(f)
        cursor.seen.append(acc)
        seen.add(acc)
        fd = getattr(f, "filing_date", "")
        if fd and fd > max_date:
            max_date = fd
    # advance ONLY forwards
    if max_date > cursor.cursor_date:
        cursor.cursor_date = max_date
    return new


def filter_new(cursor: Cursor, filings: Iterable) -> list:
    """Return only filings with filing_date > cursor_date. Strict >."""
    out = []
    cutoff = cursor.cursor_date
    for f in filings:
        fd = getattr(f, "filing_date", "")
        if cutoff and fd <= cutoff:
            continue
        out.append(f)
    return out


def save(path: str, cursor: Cursor) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cursor.to_dict(), f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load(path: str) -> Cursor:
    if not os.path.exists(path):
        return Cursor()
    with open(path) as f:
        return Cursor.from_dict(json.load(f))
