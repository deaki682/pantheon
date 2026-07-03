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

# A run that actually reached the decision points must log these numeric
# counters explicitly (even a genuine 0), so override_summary can tell
# "no override happened" apart from "this field was never recorded". A
# record whose run halted before decisions (pre-trade check failure,
# reconcile needed, etc.) is exempt IF it carries `halt_reason` — that is
# itself an honest, self-declaring stub. `weight_overrides` is NOT in this
# list on purpose: it is sparse-by-nature (present only when a tilt
# occurred), so its absence already means "no tilt", not "unrecorded".
DECISION_FIELDS = ("exits_overridden", "entries_vetoed", "risk_budget")


def append_decision(record: dict, path: str = DECISIONS_PATH) -> None:
    """Append one decision record as a JSON line. Raises on malformed input."""
    if not isinstance(record, dict):
        raise TypeError(f"decision record must be a dict, got {type(record).__name__}")
    for f in REQUIRED_FIELDS:
        if not record.get(f):
            raise ValueError(f"decision record missing required field {f!r}")
    # Added 2026-07-04 (LLM integration audit, finding #5): a date-only
    # record used to pass silently and then get counted by override_summary
    # as "0 overrides" — indistinguishable from a run that genuinely had
    # zero overrides. Halted runs self-declare via `halt_reason`; anything
    # else claiming to be a decision row must show its work.
    if not record.get("halt_reason"):
        missing = [f for f in DECISION_FIELDS if f not in record]
        if missing:
            raise ValueError(
                f"decision record missing {missing} — a non-halted run must log its "
                f"decision counters explicitly (use 0, not omission), or set "
                f"halt_reason if the run stopped before deciding"
            )
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
    """Roll up override usage across runs — the monthly calibration read.

    Only rows that explicitly logged all five decision fields count toward
    the override/risk-budget rollup (fixed 2026-07-04 — this used to
    silently treat a missing field as 0 overrides / 1.0 risk budget,
    indistinguishable from a genuine zero). Halted rows are counted
    separately so a month of reconcile failures doesn't read as "zero
    overrides, all clear".
    """
    rows = decisions if decisions is not None else load_decisions(path)
    halted = [r for r in rows if r.get("halt_reason")]
    decided = [r for r in rows if not r.get("halt_reason") and all(f in r for f in DECISION_FIELDS)]
    n = len(decided)
    return {
        "runs": len(rows),
        "halted_runs": len(halted),
        "decided_runs": n,
        "exits_overridden": sum(int(r.get("exits_overridden") or 0) for r in decided),
        "entries_vetoed": sum(int(r.get("entries_vetoed") or 0) for r in decided),
        "runs_with_weight_tilts": sum(1 for r in decided if r.get("weight_overrides")),
        "avg_risk_budget": (
            sum(float(r.get("risk_budget") or 0) for r in decided) / n if n else None
        ),
    }
