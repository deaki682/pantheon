"""Classify filings into one of Achilles's 6 event classes.

Pure-classification step. Refinement passes (insider aggregation, guidance
body read, spinoff ex-date) live in events.py.
"""
from __future__ import annotations

from shared.edgar import Filing, classify_8k, parse_items


EVENT_CLASSES = (
    "earnings_reaction",
    "insider_cluster",
    "activist_13d",
    "ma_target",
    "spinoff_window",
    "guidance_revision",
)


def classify_filing(filing: Filing) -> list[str]:
    """Return event class candidates for the filing.

    The result is a list because a single filing (8-K with multiple items)
    can hit multiple classes.
    """
    form = (filing.form or "").upper().strip()

    if form == "4":
        # A single Form 4 is a CANDIDATE — aggregation happens in events.py
        return ["insider_cluster_candidate"]

    if form == "SC 13D":
        return ["activist_13d"]

    if form.startswith("10-12B"):
        return ["spinoff_window_candidate"]

    if form == "8-K":
        labels = classify_8k(filing.items)
        # Drop labels that aren't trading events
        return [l for l in labels if l in EVENT_CLASSES]

    return []


def is_amendment(form: str) -> bool:
    return form.endswith("/A") if form else False
