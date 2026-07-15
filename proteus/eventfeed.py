"""Proteus v2 — primary-source dated-event feed (options sourcing, step 1).

Doctrine context (cache/proteus_playbook.md, "Options sourcing doctrine"):
the retail catalyst calendar IS the crowd — any event listed there is
presumptively priced (measured 2026-07-12: REPL/SVRA chains showed
269-300% IV or zero bids). The inverted doctrine sources dated events
from PRIMARY feeds retail calendars don't carry, verifies the date in
the source document, then runs the mechanical chain-kink test before
any expensive read.

This module is the feed layer. Two feeds, both shaken down before being
written here (the 2026-07-11 Gmail lesson — never write a capability
into the machine before proving it):

1. **EDGAR DEFM14A merger proxies** — special-meeting (vote) dates and
   outside dates. Shakedown 2026-07-13: 13 filings in 30d carried
   "outside date"; LPSN proxy yielded meeting 2026-08-20 and outside
   date 2026-10-21 on the first extraction. Honest caveat: announced
   deals are specialist-covered; the kink screen is the gate, and the
   neglected residue (extensions, financing deadlines, small deals) is
   the target, not the headline vote.
2. **Federal Register / ITC section 337** — target dates and final
   determinations. Shakedown 2026-07-12 (267 docs on test query) and
   2026-07-13 (crafting-machines GEO surfaced, read, correctly killed).
   Slow drip; parties skew mega-cap/foreign.

THE FEED ONLY AIMS THE READ. Extraction is heuristic (regex over
cleaned filing text); the document is the authority. Nothing here is a
signal — an event graduates to a trade only through the chain-kink
screen, the document read, and the seven option gates.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import date, timedelta
from typing import Optional
from urllib.parse import quote, urlencode

from shared import edgar

EVENTFEED_PATH = "cache/proteus_eventfeed.json"

PROXY_FORMS = ("DEFM14A",)

# ------- date parsing (pure, tested) -------

_MONTHS = {m: i + 1 for i, m in enumerate(
    ("january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"))}

_US_DATE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),\s+(20\d{2})\b")


def parse_us_date(text: str) -> Optional[str]:
    """First 'Month D, YYYY' in text -> ISO date string, else None."""
    m = _US_DATE.search(text)
    if not m:
        return None
    month = _MONTHS[m.group(1).lower()]
    try:
        return date(int(m.group(3)), month, int(m.group(2))).isoformat()
    except ValueError:
        return None


# ------- proxy extraction (pure, tested) -------

_MEETING = re.compile(r"special\s+meeting", re.IGNORECASE)
_OUTSIDE = re.compile(r"outside\s+date", re.IGNORECASE)

_WINDOW = 400  # chars searched around a term for its date


def _dates_near(term: re.Pattern, text: str) -> list[str]:
    found: list[str] = []
    for m in term.finditer(text):
        lo = max(0, m.start() - _WINDOW)
        hi = min(len(text), m.end() + _WINDOW)
        d = parse_us_date(text[lo:hi])
        if d:
            found.append(d)
    return found


def extract_meeting_date(text: str) -> Optional[str]:
    """Special-meeting date. Proxies lead with it on the cover page, so
    the first dated mention wins."""
    hits = _dates_near(_MEETING, text)
    return hits[0] if hits else None


def extract_outside_date(text: str) -> Optional[str]:
    """Merger-agreement outside date. Definitions appear dozens of times
    in both orders ("on or before <date> (the 'Outside Date')" and
    "Outside Date: ... <date>"); the modal extracted date is far more
    robust than any single mention."""
    hits = _dates_near(_OUTSIDE, text)
    if not hits:
        return None
    return Counter(hits).most_common(1)[0][0]


# ------- EDGAR FTS plumbing (pure parse, network scan) -------

_TICKER = re.compile(r"\(([A-Z][A-Z0-9.\-]{0,9}(?:,\s*[A-Z][A-Z0-9.\-]{0,9})*)\)\s*\(CIK")


def ticker_from_display(display: str) -> Optional[str]:
    """'LiveRamp Holdings, Inc.  (RAMP)  (CIK ...)' -> 'RAMP'. Multi-class
    listings keep the first (primary) ticker."""
    m = _TICKER.search(display)
    if not m:
        return None
    return m.group(1).split(",")[0].strip()


def parse_fts_hits(payload: dict) -> list[dict]:
    """EDGAR FTS payload -> candidate records (unenriched)."""
    out = []
    for h in payload.get("hits", {}).get("hits", []):
        src = h.get("_source", {})
        _id = h.get("_id", "")
        acc, _, doc = _id.partition(":")
        display = (src.get("display_names") or [""])[0]
        ciks = src.get("ciks") or []
        out.append({
            "accession": acc,
            "doc": doc,
            "cik": ciks[0] if ciks else "",
            "name": display,
            "symbol": ticker_from_display(display),
            "form": src.get("file_type") or src.get("root_forms", [""])[0],
            "filed": src.get("file_date"),
        })
    return out


def doc_url(rec: dict) -> str:
    if not (rec.get("cik") and rec.get("accession") and rec.get("doc")):
        return ""
    return edgar.ARCHIVE_URL.format(
        cik=int(rec["cik"]),
        acc_no_clean=edgar.acc_no_clean(rec["accession"]),
        file=rec["doc"],
    )


def scan_proxies(date_from: str, date_to: str) -> list[dict]:  # pragma: no cover - network
    """Sweep EDGAR FTS for merger proxies carrying outside-date language."""
    page = edgar.search_filings(
        '"outside date"', forms=list(PROXY_FORMS),
        date_from=date_from, date_to=date_to)
    return parse_fts_hits(page)


def enrich_proxy(rec: dict) -> dict:  # pragma: no cover - network
    """Fetch the proxy and attach extracted dates. The document remains
    the authority; these aim the read."""
    out = dict(rec)
    url = doc_url(rec)
    text = edgar.clean_html(edgar.http_get(url)) if url else ""
    out["doc_url"] = url
    out["meeting_date"] = extract_meeting_date(text)
    out["outside_date"] = extract_outside_date(text)
    return out


# ------- 8-K financing-deadline feed (pure parse, network scan) -------
#
# Feed #3 (build register: feed3_8k_financing_deadlines, 2026-07-14).
# Small companies announce debt-maturity extensions, forbearance
# agreements, and waiver windows in 8-Ks (often the EX-10 exhibit). The
# new deadline is a dated, non-merger catalyst no retail calendar
# carries — exactly the supply the chain-kink screen needs. THE FEED
# ONLY AIMS THE READ; the filing is the authority.

DEADLINE_FORMS = ("8-K",)

DEADLINE_QUERIES = (
    '"maturity date has been extended"',
    '"extension of the maturity date"',
    '"forbearance agreement"',
    # Added 2026-07-15 (measured, not guessed): surfaces the agreement
    # EXHIBIT itself where the 8-K body never says "forbearance agreement"
    # (EXYN 2026-06-22 ex10-1, missed by the three queries above; ~1 hit /
    # 30 days incremental). The beliefs-planned phrases "forbear until" and
    # "forbearance period expires" measured ZERO hits over the same window
    # and were deliberately NOT added — dead queries are ornament.
    '"agrees to forbear"',
)

_DEADLINE_TERM = re.compile(
    r"maturity\s+date|forbearance\s+(?:period|agreement)|"
    r"waiver\s+(?:period|shall\s+expire)", re.IGNORECASE)


def _all_dates_near(term: re.Pattern, text: str) -> list[str]:
    """ALL parseable dates within the window around each term hit.
    The proxy extractors' first-date-wins heuristic fails on 8-K prose,
    where the announcement date ('On July 10, 2026, the Company entered
    into...') leads every window; deadline extraction needs the full
    window population so the filter+modal can find the restated new
    date (measured on live text, 2026-07-14)."""
    found: list[str] = []
    for m in term.finditer(text):
        lo = max(0, m.start() - _WINDOW)
        hi = min(len(text), m.end() + _WINDOW)
        for dm in _US_DATE.finditer(text[lo:hi]):
            d = parse_us_date(dm.group(0))
            if d:
                found.append(d)
    return found


def extract_deadline_date(text: str,
                          filed: Optional[str] = None) -> Optional[str]:
    """Modal date near a deadline term, restricted to dates strictly
    after the filing date when one is given (a deadline already past at
    filing is history, not a catalyst). Modal beats first: extension
    amendments restate the new date several times and mention the old
    one once."""
    hits = _all_dates_near(_DEADLINE_TERM, text)
    if filed:
        hits = [d for d in hits if d > filed]
    if not hits:
        return None
    return Counter(hits).most_common(1)[0][0]


def scan_deadlines(date_from: str,
                   date_to: str) -> list[dict]:  # pragma: no cover - network
    """Sweep EDGAR FTS for 8-Ks carrying financing-deadline language.
    Dedupes on accession across the query list."""
    seen: set = set()
    out: list[dict] = []
    for q in DEADLINE_QUERIES:
        page = edgar.search_filings(
            q, forms=list(DEADLINE_FORMS),
            date_from=date_from, date_to=date_to)
        for r in parse_fts_hits(page):
            if r["accession"] and r["accession"] not in seen:
                seen.add(r["accession"])
                out.append(r)
    return out


def enrich_deadline(rec: dict) -> dict:  # pragma: no cover - network
    """Fetch the matched document (frequently the EX-10 exhibit itself)
    and attach the extracted deadline. The document remains the
    authority; this aims the read."""
    out = dict(rec)
    url = doc_url(rec)
    text = edgar.clean_html(edgar.http_get(url)) if url else ""
    out["doc_url"] = url
    out["deadline_date"] = extract_deadline_date(text, rec.get("filed"))
    return out


# ------- Federal Register / ITC feed (pure parse, network fetch) -------

FR_API = "https://www.federalregister.gov/api/v1/documents.json"
FR_AGENCY = "international-trade-commission"


def fr_query_url(term: str, pub_date_gte: str, per_page: int = 20) -> str:
    """Build the FR API query URL (kept pure for testing)."""
    params = [
        ("per_page", str(per_page)),
        ("order", "newest"),
        ("conditions[term]", term),
        ("conditions[agencies][]", FR_AGENCY),
        ("conditions[publication_date][gte]", pub_date_gte),
    ]
    return FR_API + "?" + urlencode(params, quote_via=quote)


def parse_fr_results(payload: dict) -> list[dict]:
    return [{
        "published": d.get("publication_date"),
        "title": d.get("title"),
        "html_url": d.get("html_url"),
        "raw_text_url": d.get("raw_text_url"),
    } for d in payload.get("results", [])]


def fr_itc_recent(term: str, days_back: int, *,
                  today: Optional[str] = None) -> list[dict]:  # pragma: no cover - network
    import urllib.request
    start = (date.fromisoformat(today) if today else date.today()) \
        - timedelta(days=days_back)
    url = fr_query_url(term, start.isoformat())
    req = urllib.request.Request(
        url, headers={"User-Agent": edgar.USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return parse_fr_results(json.loads(r.read()))


# ------- event store (pure, tested) -------

def _key(ev: dict) -> tuple:
    return (ev.get("symbol"), ev.get("event_type"), ev.get("event_date"))


def add_events(store: dict, events: list[dict]) -> int:
    """Dedupe on (symbol, event_type, event_date); returns count added.
    Every event must carry a source_url — an unsourced date is a rumor.
    An event dated on/before its filing date is a proven mis-extraction
    (a definitive proxy's vote/outside date is always future at filing;
    measured 2026-07-13: 6 of 21 raw extractions failed this) — dropped."""
    have = {_key(e) for e in store.setdefault("events", [])}
    added = 0
    for ev in events:
        if not ev.get("source_url"):
            raise ValueError(f"event without source_url: {ev!r}")
        if not ev.get("event_date"):
            continue
        filed = ev.get("filed")
        if filed and ev["event_date"] <= filed:
            continue
        if _key(ev) in have:
            continue
        store["events"].append(ev)
        have.add(_key(ev))
        added += 1
    return added


def upcoming(store: dict, today: str, horizon_days: int = 180) -> list[dict]:
    """Events dated in (today, today+horizon], soonest first."""
    lo = date.fromisoformat(today)
    hi = lo + timedelta(days=horizon_days)
    out = [e for e in store.get("events", [])
           if e.get("event_date")
           and lo < date.fromisoformat(e["event_date"]) <= hi]
    return sorted(out, key=lambda e: e["event_date"])


def load(path: str = EVENTFEED_PATH) -> dict:
    if not os.path.exists(path):
        return {"updated": "", "events": []}
    with open(path) as f:
        return json.load(f)


def save(data: dict, path: str = EVENTFEED_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
