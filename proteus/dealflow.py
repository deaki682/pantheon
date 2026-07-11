"""Proteus v2 — tender-offer deal-flow scanner (odd-lot priority hunting).

Ledger context (docs/RESEARCH_LEDGER.md, read 2026-07-11): the tender
FAMILY is closed at statistical, all-holders, filing-anchor entries —
CEF TO-I filing anchor −1.81% (t −3.91), operating self-tenders −1.82%,
third-party 14D-9 residual +0.15% (a precise null), TO-C anchor
replication t −5.34. "Closed absent genuinely new structure."

This module hunts that new structure: the CONTRACTUAL odd-lot priority
clause (Rule 13e-4(f)(3) / Rule 14d-8 carve-outs) — holders of fewer
than 100 shares who tender ALL their shares are accepted with priority,
exempt from proration. The closed studies measured average post-filing
drift across every holder; this is a per-deal, capacity-capped (<100
shares) spread whose acceptance is contractual, not statistical.
Backlog #13 frames the same idea (kill spec: supply <12/yr, broker
can't deliver un-prorated acceptance, median $/event <$150).

THE SCANNER ONLY AIMS THE READ. Nothing this module emits is a buy
signal: extraction here is heuristic (regex over cleaned HTML), and the
Effort Law requires the actual filing — offer terms, the odd-lot clause
verbatim, proration mechanics, conditions — to be read before any
journal entry or order.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from typing import Optional

from shared import edgar

DEALFLOW_PATH = "cache/proteus_dealflow.json"

TENDER_FORMS = ("SC TO-I", "SC TO-T", "SC 14D9")

# FTS queries that surface odd-lot language. EDGAR FTS phrase-matches
# quoted strings; both clause spellings appear in real filings.
FTS_QUERIES = ('"odd lot"', '"fewer than 100 shares"')

# ------- clause detection (pure, tested) -------

_ODD_LOT_TERM = re.compile(
    r"\bodd\s*[- ]?\s*lots?\b|\b(?:fewer|less)\s+than\s+100\s+shares\b",
    re.IGNORECASE,
)

# Priority context: acceptance ahead of / exempt from proration.
_PRIORITY_CTX = re.compile(
    r"(?:not\s+(?:be\s+)?subject\s+to\s+proration"
    r"|without\s+proration"
    r"|before\s+proration"
    r"|priority\b"
    r"|accepted?\s+(?:for\s+(?:payment|purchase|exchange)\s+)?"
    r"(?:first|in\s+full))",
    re.IGNORECASE,
)

_WINDOW = 600  # chars of context around an odd-lot term to search for priority


def has_odd_lot_priority(text: str) -> bool:
    """True when an odd-lot term appears with proration-exemption/priority
    language nearby. Heuristic — the filing itself is the authority."""
    for m in _ODD_LOT_TERM.finditer(text):
        lo = max(0, m.start() - _WINDOW)
        hi = min(len(text), m.end() + _WINDOW)
        if _PRIORITY_CTX.search(text[lo:hi]):
            return True
    return False


# ------- term extraction (pure, tested) -------

_MONEY = r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)"

_DUTCH = re.compile(
    r"not\s+(?:less|lower)\s+than\s+" + _MONEY +
    r"\s+(?:nor|and\s+not|or)\s+(?:more|greater|higher)\s+than\s+" + _MONEY,
    re.IGNORECASE,
)

_FIXED = re.compile(
    r"(?:purchase\s+price\s+of|offer\s+(?:price\s+of|to\s+purchase[^.$]{0,120}?at)"
    r"|price\s+of)\s+" + _MONEY + r"\s+per\s+share",
    re.IGNORECASE,
)


def _to_float(s: str) -> float:
    return float(s.replace(",", ""))


def extract_offer_price(text: str) -> dict:
    """Return {kind: 'dutch'|'fixed'|'unknown', low, high}. For a Dutch
    auction the odd-lot economics must be computed at the LOW end — the
    final purchase price is unknowable at entry (conservative bound)."""
    m = _DUTCH.search(text)
    if m:
        lo, hi = _to_float(m.group(1)), _to_float(m.group(2))
        if 0 < lo <= hi:
            return {"kind": "dutch", "low": lo, "high": hi}
    m = _FIXED.search(text)
    if m:
        p = _to_float(m.group(1))
        if p > 0:
            return {"kind": "fixed", "low": p, "high": p}
    return {"kind": "unknown", "low": None, "high": None}


_MONTHS = {m.lower(): i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

_EXPIRY = re.compile(
    # gap allows "at 5:00 p.m., New York City time," between verb and date
    r"expir(?:e|es|ation)[\s\S]{0,160}?\bon\s+(?:\w+day,\s+)?"
    r"(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
    re.IGNORECASE,
)


def extract_expiration(text: str) -> Optional[str]:
    """First 'expire ... on <Month D, YYYY>' date as ISO, else None."""
    m = _EXPIRY.search(text)
    if not m:
        return None
    try:
        d = date(int(m.group(3)), _MONTHS[m.group(1).lower()], int(m.group(2)))
    except ValueError:
        return None
    return d.isoformat()


_CONDITION_FLAGS = {
    "financing_condition": re.compile(r"financing\s+condition", re.IGNORECASE),
    "minimum_tender_condition": re.compile(
        r"minimum\s+(?:tender\s+)?condition|minimum\s+number\s+of\s+shares",
        re.IGNORECASE),
    "going_private_13e3": re.compile(r"13e-3|going.private", re.IGNORECASE),
}


def condition_flags(text: str) -> dict:
    """Presence flags for risk terms the read must resolve — flags aim
    the read, they do not grade the risk."""
    return {k: bool(rx.search(text)) for k, rx in _CONDITION_FLAGS.items()}


# ------- FTS plumbing (pure parse, tested; network scan thin) -------

def parse_hits(payload: dict) -> list[dict]:
    """Map one EDGAR FTS response page to candidate records."""
    out = []
    for h in payload.get("hits", {}).get("hits", []):
        src = h.get("_source", {})
        _id = h.get("_id", "")
        acc, _, doc = _id.partition(":")
        ciks = src.get("ciks") or []
        names = src.get("display_names") or []
        out.append({
            "accession": acc,
            "doc": doc,
            "cik": ciks[0].lstrip("0") if ciks else "",
            "name": names[0] if names else "",
            "form": src.get("root_forms", [src.get("file_type", "")])[0]
                    if src.get("root_forms") else src.get("file_type", ""),
            "filed": src.get("file_date", ""),
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


def dedupe(records: list[dict]) -> list[dict]:
    """One record per accession number, first occurrence wins."""
    seen: set[str] = set()
    out = []
    for r in records:
        if r["accession"] and r["accession"] not in seen:
            seen.add(r["accession"])
            out.append(r)
    return out


def scan(date_from: str, date_to: str,
         forms: tuple = TENDER_FORMS,
         max_pages: int = 20) -> list[dict]:  # pragma: no cover - network
    """Sweep EDGAR FTS for tender filings carrying odd-lot language in the
    window. Returns deduped candidate records (unenriched)."""
    hits: list[dict] = []
    for q in FTS_QUERIES:
        offset = 0
        for _ in range(max_pages):
            page = edgar.search_filings(
                q, forms=list(forms), date_from=date_from, date_to=date_to,
                offset=offset)
            rows = parse_hits(page)
            hits.extend(rows)
            total = page.get("hits", {}).get("total", {}).get("value", 0)
            offset += 10
            if offset >= total or not rows:
                break
    return dedupe(hits)


def enrich(rec: dict, text: str) -> dict:
    """Attach extracted terms to a candidate. text = cleaned filing body."""
    out = dict(rec)
    out["odd_lot_priority"] = has_odd_lot_priority(text)
    out["offer"] = extract_offer_price(text)
    out["expiration"] = extract_expiration(text)
    out["flags"] = condition_flags(text)
    return out


# ------- filing index → substantive exhibit -------
#
# SC TO-I primary docs are frequently 2-page cover shells; the terms live
# in exhibit (a)(1)(A) "Offer to Purchase". Walk the filing index and pick
# the document most likely to carry the terms.

def index_url(rec: dict) -> str:
    if not (rec.get("cik") and rec.get("accession")):
        return ""
    return edgar.ARCHIVE_URL.format(
        cik=int(rec["cik"]),
        acc_no_clean=edgar.acc_no_clean(rec["accession"]),
        file="index.json",
    )


_OFFER_NAME = re.compile(r"offer|a1a|ex-?99|ex99|toi|to-i", re.IGNORECASE)


def best_document(files: list[dict]) -> str:
    """Choose the exhibit most likely to be the Offer to Purchase from an
    EDGAR index.json 'item' list ({name, size}). Preference: html docs
    whose name suggests the offer exhibit, then the largest html doc."""
    htmls = [f for f in files
             if str(f.get("name", "")).lower().endswith((".htm", ".html"))]
    if not htmls:
        return ""
    named = [f for f in htmls if _OFFER_NAME.search(str(f.get("name", "")))]
    pool = named or htmls
    pool = sorted(pool, key=lambda f: int(f.get("size") or 0), reverse=True)
    return str(pool[0].get("name", ""))


def fetch_offer_text(rec: dict) -> str:  # pragma: no cover - network
    """Fetch the substantive offer document's cleaned text for a candidate:
    walk index.json, pick best_document, fall back to the FTS doc."""
    iu = index_url(rec)
    name = ""
    if iu:
        try:
            idx = json.loads(edgar.http_get(iu))
            name = best_document(idx.get("directory", {}).get("item", []))
        except Exception:
            name = ""
    target = dict(rec)
    if name:
        target["doc"] = name
    url = doc_url(target)
    if not url:
        return ""
    return edgar.clean_html(edgar.http_get(url))


# ------- economics (pure, tested) -------

ODD_LOT_MAX_SHARES = 99


def economics(offer_low: float, last_price: float, expiration: Optional[str],
              as_of: Optional[str] = None,
              shares: int = ODD_LOT_MAX_SHARES) -> dict:
    """Conservative odd-lot economics: buy `shares` at last_price, tender
    at the LOW/announced price. Worst case at entry = the full cost basis
    (deal breaks, stock goes to zero) — bounded loss is the cost, never
    more. Annualization uses expiry + 7 calendar days for payment lag."""
    cost = last_price * shares
    gross = (offer_low - last_price) * shares
    pct = gross / cost if cost > 0 else 0.0
    days = None
    ann = None
    if expiration and as_of:
        try:
            d = (datetime.fromisoformat(expiration).date()
                 - datetime.fromisoformat(as_of).date()).days + 7
            if d > 0:
                days = d
                ann = pct * 365.0 / d
        except ValueError:
            pass
    return {
        "shares": shares,
        "cost_basis": round(cost, 2),
        "worst_case_loss": round(cost, 2),
        "gross_profit": round(gross, 2),
        "spread_pct": round(pct, 6),
        "days_to_payment": days,
        "annualized": round(ann, 4) if ann is not None else None,
    }


# ------- persistence -------

def load(path: str = DEALFLOW_PATH) -> dict:
    if not os.path.exists(path):
        return {"updated": "", "candidates": []}
    with open(path) as f:
        return json.load(f)


def save(data: dict, path: str = DEALFLOW_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
