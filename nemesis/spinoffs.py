"""Spinoff discovery pipeline — EDGAR Form 10-12B → tracked candidates.

Every spinoff announces itself months in advance: the parent registers the
new company on SEC Form 10-12B (the "Form 10"), often amending it several
times before distribution. This module finds those registrations via EDGAR
full-text search and keeps a persistent pipeline of candidates, keyed by CIK,
so the god can watch each one march from paper filing to tradeable stock.

Why this matters to the strategy: after distribution, index funds that held
the parent receive spinco shares they are not allowed to keep (wrong index,
wrong size bucket) and must sell regardless of price. Nemesis does NOT buy
at distribution — it buys AFTER the forced-seller dump, on a window trigger,
and holds ~5 months. This module is only the eyes: it discovers and tracks.
The judgment call — reading the Form 10 for management incentives, dumped
liabilities, and the size of the forced-seller flow — belongs to the LLM
runbook, which reads documents and never predicts prices.

Division of labor over the pipeline dict:
  - This module (auto) owns: company, ticker, filing dates, n_filings,
    first_seen / last_updated, and the two early statuses ("registered",
    "ticker_assigned").
  - The runbook owns the lifecycle from distribution onward: statuses
    "distributed" / "entered" / "skipped" / "expired" and the fields
    distribution_date, first_trade_date, window_state, dossier_verdict.
    update_pipeline never overwrites or erases what the runbook set —
    a fresh EDGAR sweep must not un-distribute a spinoff.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

from shared import edgar


# Statuses the runbook assigns as a spinoff progresses past registration.
# They are strictly "richer" than the auto statuses: once the runbook has
# spoken, a re-run of the EDGAR sweep must never downgrade the entry back
# to "registered"/"ticker_assigned".
RUNBOOK_STATUSES = frozenset({"distributed", "entered", "skipped", "expired"})

# Fields only the runbook writes. Listed here for documentation; the code
# preserves them by construction (update_pipeline only ever sets its own
# keys and never deletes anything).
RUNBOOK_FIELDS = (
    "distribution_date",
    "first_trade_date",
    "window_state",
    "dossier_verdict",
)


@dataclass
class SpinEvent:
    """One registering spinco, merged from all its 10-12B hits in a search.

    A single spinoff typically produces several hits (the initial 10-12B
    plus /A amendments), so the event carries the first/last filing dates
    and the hit count — a long amendment trail is itself a signal that the
    distribution is being actively worked toward.
    """

    company: str
    cik: str  # 10-digit zero-padded, the stable key across the pipeline
    ticker: Optional[str]  # None until the exchange listing is in the filing
    first_filed: str  # YYYY-MM-DD of the earliest hit
    last_filed: str  # YYYY-MM-DD of the latest hit
    n_filings: int


# EDGAR full-text-search display names look like:
#   "Versant Media Group, Inc.  (VSNT)  (CIK 0002067876)"
#   "Cyprium Holdings Ltd  (CIK 0002078008)"
# i.e. an optional ticker paren, then always a CIK paren.
_PAREN = re.compile(r"\(([^)]*)\)")
_CIK_IN_NAME = re.compile(r"\(\s*CIK\s+(\d{1,10})\s*\)", re.IGNORECASE)
# A ticker token: 1-6 chars, uppercase letters plus the class separators
# EDGAR uses (BRK.B, MOG-A). Must start with a letter so stray punctuation
# in a paren never reads as a ticker.
_TICKER_TOKEN = re.compile(r"[A-Z][A-Z.\-]{0,5}")


def extract_ticker(display_name: str) -> Optional[str]:
    """Pull the ticker out of an EDGAR display name, or None if unlisted.

    A missing ticker is meaningful, not an error: freshly registered spincos
    have no exchange listing yet, and the ticker appearing in a later
    amendment is exactly the pipeline progression we want to observe.

    Multi-class listings show comma-separated tickers in one paren
    ("(BRK.A, BRK.B)"); we take the first, which EDGAR lists as primary.
    """
    for group in _PAREN.finditer(display_name):
        content = group.group(1).strip()
        if content.upper().startswith("CIK"):
            continue  # the "(CIK 0001234567)" group, never a ticker
        for token in content.split(","):
            token = token.strip()
            if _TICKER_TOKEN.fullmatch(token):
                return token
    return None


def _cik_from_display_name(display_name: str) -> Optional[str]:
    """Parse the "(CIK 0001234567)" group out of a display name."""
    m = _CIK_IN_NAME.search(display_name)
    if not m:
        return None
    return edgar.cik10(m.group(1))


def _company_from_display_name(display_name: str) -> str:
    """Strip the ticker/CIK paren annotations, leaving the plain name."""
    name = _PAREN.sub(" ", display_name)
    return re.sub(r"\s+", " ", name).strip()


def events_from_search_payload(payload: dict) -> list[SpinEvent]:
    """Pure parser: EDGAR full-text-search response → one SpinEvent per CIK.

    Kept free of network so tests can feed it captured payloads. Each hit's
    _source carries display_names (list of str), file_date (YYYY-MM-DD),
    and usually cik; when cik is absent we fall back to parsing it out of
    the display name, since the CIK is the only stable join key — tickers
    arrive late and company names get restyled between amendments.

    Hits are grouped by CIK because one spinoff files repeatedly (initial
    10-12B plus amendments). Within a group we prefer whichever display
    name carries a ticker: EDGAR backfills the ticker onto display names
    once the listing exists, and the ticker is what the trading half of
    the pipeline ultimately needs.
    """
    groups: dict[str, dict] = {}  # cik10 -> accumulator

    for hit in payload.get("hits", {}).get("hits", []):
        source = hit.get("_source", {}) or {}
        names = source.get("display_names") or []
        display = names[0] if names else ""

        raw_cik = source.get("cik")
        if raw_cik not in (None, ""):
            cik = edgar.cik10(raw_cik)
        else:
            cik = _cik_from_display_name(display)
        if not cik:
            continue  # no join key — nothing we can track

        g = groups.setdefault(
            cik, {"display": display, "dates": [], "n": 0}
        )
        g["n"] += 1
        date = source.get("file_date") or ""
        if date:
            g["dates"].append(date)
        # Upgrade to a ticker-bearing display name the moment we see one.
        if display and (
            not g["display"]
            or (extract_ticker(display) and not extract_ticker(g["display"]))
        ):
            g["display"] = display

    events: list[SpinEvent] = []
    for cik, g in groups.items():
        dates = sorted(g["dates"])
        events.append(
            SpinEvent(
                company=_company_from_display_name(g["display"]),
                cik=cik,
                ticker=extract_ticker(g["display"]),
                first_filed=dates[0] if dates else "",
                last_filed=dates[-1] if dates else "",
                n_filings=g["n"],
            )
        )
    # Oldest registration first: those are closest to distribution, i.e.
    # closest to becoming actionable.
    events.sort(key=lambda e: (e.first_filed, e.cik))
    return events


def search_spinoff_registrations(
    date_from: str, date_to: str
) -> list[SpinEvent]:  # pragma: no cover - network
    """Find spinoff registrations filed in [date_from, date_to].

    Form 10-12B is the registration statement for securities distributed
    to existing holders — the canonical spinoff paper trail. Full-text
    searching it for "spin-off" filters out the rare non-spinoff 10-12B
    (direct listings, emergences) at the cost of missing filers who never
    use the word; in practice the Form 10 of a genuine spinoff says it
    on page one.
    """
    payload = edgar.search_filings(
        "spin-off", forms=["10-12B"], date_from=date_from, date_to=date_to
    )
    return events_from_search_payload(payload)


# ------- Pipeline persistence -------
#
# The pipeline is the god's memory between weekly sweeps: {cik10: entry}.
# It has two writers — this module (discovery) and the runbook (lifecycle) —
# so the merge rules below are the contract that keeps them from clobbering
# each other.


def load_pipeline(path: str) -> dict:
    """Load the tracked pipeline; {} when missing or corrupt.

    Corrupt-tolerant on purpose: a torn or garbage file should degrade to
    "start tracking fresh" (spinoffs re-appear on the next sweep, runbook
    state is rebuilt from filings), never crash the weekly run.
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_pipeline(path: str, pipeline: dict) -> None:
    """Atomic write (tmp + os.replace) so a crash never tears the file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(pipeline, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def update_pipeline(pipeline: dict, events: list[SpinEvent], *, today: str) -> dict:
    """Merge a sweep's SpinEvents into the pipeline. Mutates and returns it.

    Merge rules, each protecting a different truth:
      - first_seen is set once, on creation — it dates our discovery, not
        the filing (the gap between first_filed and first_seen measures
        how stale our sweep cadence is).
      - first_filed/last_filed merge by min/max and n_filings by max,
        because each sweep only sees its own date window; a narrow re-scan
        must not shrink history we already learned.
      - a known ticker is never erased by a ticker-less event: display
        names in older filings lack the ticker, and forgetting a listing
        we already saw would move the entry backward in its lifecycle.
      - auto-status ("registered" → "ticker_assigned") only ever fills in
        or upgrades; any runbook-set status (RUNBOOK_STATUSES) is final
        from this module's point of view, and runbook-owned fields
        (RUNBOOK_FIELDS) are never written or deleted here.
    """
    for ev in events:
        entry = pipeline.get(ev.cik)
        if entry is None:
            entry = {"first_seen": today}
            pipeline[ev.cik] = entry

        entry["company"] = ev.company
        if ev.ticker:
            entry["ticker"] = ev.ticker
        else:
            entry.setdefault("ticker", None)

        prev_first = entry.get("first_filed") or ev.first_filed
        prev_last = entry.get("last_filed") or ev.last_filed
        entry["first_filed"] = min(prev_first, ev.first_filed or prev_first)
        entry["last_filed"] = max(prev_last, ev.last_filed or prev_last)
        entry["n_filings"] = max(int(entry.get("n_filings") or 0), ev.n_filings)
        entry["last_updated"] = today

        if entry.get("status") not in RUNBOOK_STATUSES:
            entry["status"] = (
                "ticker_assigned" if entry.get("ticker") else "registered"
            )

    return pipeline
