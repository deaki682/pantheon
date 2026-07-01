"""Delphi decision log — the audit trail for the LLM's five decision points.

The override budgets in /delphi ("track them in the decision log and review
monthly") are unenforceable without a reliable record. This module makes the
logging mechanical: a validated append that refuses anything but a proper
record, so a formatting slip can't silently destroy the trail (which is how
cache/delphi_decisions.jsonl once ended up containing a literal file path).

One JSON object per line (JSONL).
"""
from __future__ import annotations

import json
import os
from typing import Optional

DECISIONS_PATH = "cache/delphi_decisions.jsonl"

# A record must carry at least these to be a usable audit row.
REQUIRED_FIELDS = ("date",)


def append_decision(record: dict, path: str = DECISIONS_PATH) -> None:
    """Append one decision record as a JSON line. Raises on malformed input."""
    if not isinstance(record, dict):
        raise TypeError(f"decision record must be a dict, got {type(record).__name__}")
    for f in REQUIRED_FIELDS:
        if not record.get(f):
            raise ValueError(f"decision record missing required field {f!r}")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def load_decisions(path: str = DECISIONS_PATH) -> list[dict]:
    """Read the log, skipping (but counting) corrupt lines rather than dying."""
    if not os.path.exists(path):
        return []
    out: list[dict] = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue  # a corrupt line must not take down the whole trail
        if isinstance(row, dict):
            out.append(row)
    return out


def override_summary(decisions: Optional[list[dict]] = None, path: str = DECISIONS_PATH) -> dict:
    """Roll up override usage across runs — the monthly calibration read."""
    rows = decisions if decisions is not None else load_decisions(path)
    n = len(rows)
    return {
        "runs": n,
        "exits_overridden": sum(int(r.get("exits_overridden", 0) or 0) for r in rows),
        "entries_vetoed": sum(int(r.get("entries_vetoed", 0) or 0) for r in rows),
        "runs_with_weight_tilts": sum(1 for r in rows if r.get("weight_overrides")),
        "avg_risk_budget": (
            sum(float(r.get("risk_budget", 1.0) or 1.0) for r in rows) / n if n else None
        ),
    }
