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

    The ticker annotation, when present, is the paren group EDGAR appends
    immediately before the trailing "(CIK ...)" group. Parens inside the
    legal name itself — "Global Industries (UK) Ltd", "Jerash Holdings
    (US), Inc." — are followed by more name text, never directly by the
    CIK group, so ADJACENCY to the CIK group is what identifies the
    ticker. Taking the first ticker-shaped token in any paren would read
    "(UK)" as a listing, and because update_pipeline never erases a known
    ticker, the false value would permanently shadow the real one once
    EDGAR backfills it.

    Multi-class listings show comma-separated tickers in one paren
    ("(BRK.A, BRK.B)"); we take the first, which EDGAR lists as primary.
    """
    groups = list(_PAREN.finditer(display_name))
    candidate = None
    for i, g in enumerate(groups):
        if g.group(1).strip().upper().startswith("CIK"):
            if i > 0 and not display_name[groups[i - 1].end():g.start()].strip():
                candidate = groups[i - 1]
            break
    else:
        # No CIK group (defensive — EDGAR always appends one): the ticker
        # annotation, if any, is still the trailing paren.
        candidate = groups[-1] if groups else None

    if candidate is None:
        return None
    for token in candidate.group(1).strip().split(","):
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

    EDGAR FTS pages at 10 hits, and one spinoff files 2-5 times (10-12B
    plus amendments), so a single page can hold as few as 2-3 distinct
    companies. Reading only the first page silently drops the rest of the
    window — so we page until the reported total is exhausted (capped at
    500 hits; a window that busy should be narrowed, not trusted).
    """
    hits: list[dict] = []
    offset = 0
    while True:
        try:
            payload = edgar.search_filings(
                "spin-off", forms=["10-12B"],
                date_from=date_from, date_to=date_to, offset=offset,
            )
        except Exception:
            # EDGAR FTS 500s intermittently, sometimes mid-pagination. A
            # partial sweep beats a dead sweep: keep the pages we have —
            # the weekly cadence re-covers the window and heals the gap.
            break
        page = payload.get("hits", {}).get("hits", [])
        hits.extend(page)
        total = payload.get("hits", {}).get("total", {}).get("value", 0)
        offset += len(page)
        if not page or offset >= total or offset >= 500:
            break
    return events_from_search_payload({"hits": {"hits": hits}})


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

        # Like the ticker below, a learned company name is never erased by
        # a degraded event: the parser tolerates hits with no display_names
        # (company == ""), and a narrow re-scan must not blank out a name
        # an earlier sweep already recorded.
        if ev.company:
            entry["company"] = ev.company
        else:
            entry.setdefault("company", "")
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


def backfill_tickers(pipeline: dict, cik_to_symbol: dict) -> list[tuple[str, str]]:
    """Fill missing tickers from the official CIK->symbol registry.

    EDGAR full-text-search display names lie about tickers in three ways
    the 2026-07-03 ocean sweep hit for real: registration shell names
    (Qnity filed as "Novus SpinCo 1"), post-registration renames
    (Cyprium -> Versigent), and recycled symbols (Atrium taking a prior
    issuer's RNA). The company_tickers registry keyed by CIK is
    authoritative for all three — a listing exists there the moment the
    exchange assigns it, whatever the filing prose says.

    Rules match update_pipeline's: a ticker already learned is never
    overwritten, and runbook-owned statuses are never touched. Returns the
    (cik, symbol) pairs actually filled so the runbook can log them.
    """
    filled: list[tuple[str, str]] = []
    for cik, entry in pipeline.items():
        if entry.get("ticker"):
            continue
        sym = cik_to_symbol.get(cik)
        if not sym:
            continue
        entry["ticker"] = sym
        if entry.get("status") not in RUNBOOK_STATUSES:
            entry["status"] = "ticker_assigned"
        filled.append((cik, sym))
    return filled


def tenb_from_daily_indexes(
    date_from: str, date_to: str
):  # pragma: no cover - network
    """Registrant CIKs that filed a 10-12B in the window, from EDGAR's
    daily form indexes — the complete population, no search engine.

    Recall backstop for search_spinoff_registrations: FTS pagination can
    silently drop a page mid-sweep (it cost the scan SOLS — the vintage's
    +79% name — on 2026-07-03 until an independent catalog caught it).
    The weekly runbook diffs this against the FTS result; index-only
    registrants get their filing fetched and keyword-triaged directly.
    Returns {cik10: {"name", "first", "last", "n"}}.
    """
    import re as _re
    from datetime import date as _date, timedelta as _td

    out: dict[str, dict] = {}
    d = _date.fromisoformat(date_from)
    end = _date.fromisoformat(date_to)
    pat = _re.compile(
        r"^(10-12B(?:/A)?)\s+(.+?)\s{2,}(\d+)\s+(\d{4}-?\d{2}-?\d{2})\s+(\S+)\s*$"
    )
    while d <= end:
        if d.weekday() < 5:
            url = (f"https://www.sec.gov/Archives/edgar/daily-index/{d.year}"
                   f"/QTR{(d.month - 1) // 3 + 1}/form.{d.strftime('%Y%m%d')}.idx")
            try:
                body = edgar.http_get(url)
                text = body if isinstance(body, str) else body.decode(
                    "latin-1", errors="replace")
                for line in text.splitlines():
                    m = pat.match(line)
                    if m:
                        cik = edgar.cik10(m.group(3))
                        e = out.setdefault(cik, {"name": m.group(2).strip(),
                                                 "first": d.isoformat(), "n": 0})
                        e["n"] += 1
                        e["last"] = d.isoformat()
            except Exception:
                pass  # holiday or transient; weekly overlap self-heals
        d += _td(days=1)
    return out
