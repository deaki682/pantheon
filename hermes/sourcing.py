"""hermes/sourcing.py — comprehensive announced-deal enumeration (2026-07-07).

Fixes Hermes's sourcing SLIVER. Deal detection was session-driven ("build/refresh
the active cash-deal watchlist … Sources: news/EDGAR"), so the deal UNIVERSE was
whatever a given run happened to surface — incomplete, inconsistent, and worse: it
biases the whole experiment, because Arm B ("every DETECTED deal, mechanical") is
only an honest control if *detected == all deals*. A surfacing sliver makes the
LLM-lift measurement lie.

This enumerates announced deals EXHAUSTIVELY from the TARGET's own primary filings,
using the same EDGAR daily-index form sweep the house proved for spinoffs
(`nemesis.spinoffs.tenb_from_daily_indexes`) and forced sellers — the "complete
population, no search engine" path that measured 100% recall vs ~12% for keyword
search. Target-filed merger paper is the complete trail:

  - a one-step merger requiring a vote files a DEFM14A (definitive) — often a
    PREM14A first;
  - a merger by written consent (no vote) files a DEFM14C / PREM14C;
  - a two-step tender offer draws an SC 14D9 (the target's recommendation).

Every announced US deal that reaches a shareholder decision leaves one of these,
keyed to the TARGET's CIK — which is the name Hermes longs. (Acquirer-side paper
like SC TO-T is deliberately NOT swept: it is keyed to the buyer, not the target.)

What this module does NOT do: decide cash-vs-stock, read the offer price, or
compute the spread. Those need the filing body and are the session's per-deal LLM
read — so every candidate carries `requires_read=True` (mirroring Oracle's
`requires_item4_read`). Completeness is this module's only job; the break-risk read
and the -15% stop stay exactly where they are.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Optional

from shared import edgar

# Target-filed merger/tender forms → the deal channel each represents. These are
# the COMPLETE announced-deal trail from the target's side. Note DEFM14A ("M" =
# merger, no space) is distinct from the regular annual proxy "DEF 14A" (a space)
# — the escaped alternation below matches only the merger forms, never the annual.
DEAL_FORMS: dict[str, str] = {
    "DEFM14A": "definitive merger proxy (shareholder vote)",
    "PREM14A": "preliminary merger proxy (earlier signal)",
    "DEFM14C": "merger information statement (written consent, no vote)",
    "PREM14C": "preliminary merger information statement",
    "SC 14D9": "target recommendation on a tender offer (two-step)",
}

# One regex over an EDGAR daily form.idx line:  FORM (+/A)  COMPANY  CIK  DATE  FILE
_FORM_ALT = "|".join(re.escape(f) for f in DEAL_FORMS)
_LINE = re.compile(
    rf"^({_FORM_ALT})(/A)?\s+(.+?)\s{{2,}}(\d+)\s+(\d{{4}}-?\d{{2}}-?\d{{2}})\s+(\S+)\s*$"
)


@dataclass
class DealCandidate:
    """One announced-deal target, deduped to the TARGET's CIK across every merger
    filing it made in the window. `requires_read` is always True: the session's
    LLM read confirms cash-vs-stock, the offer price, and a live below-offer spread
    before any capital — this row only guarantees the deal was not MISSED."""
    cik: str
    company: str
    symbol: Optional[str]
    channels: list[str]            # deal-form labels seen (e.g. definitive + preliminary)
    forms: list[str]               # raw form codes seen (DEFM14A, SC 14D9, …)
    first_filed: str
    last_filed: str
    n_filings: int
    requires_read: bool = True
    why: str = ("announced deal from primary filings — the read must confirm "
                "cash-vs-stock, the offer price, and a live below-offer spread")

    def to_dict(self) -> dict:
        return asdict(self)


def parse_index_text(text: str, day_iso: str, acc: dict) -> dict:
    """Pure parser: fold one daily form.idx body into `acc` ({cik10: entry}).

    Network-free so tests can feed captured index text. Groups by CIK because a
    single deal files repeatedly (PREM14A → DEFM14A, plus amendments); the CIK is
    the only stable join key (tickers arrive late, names get restyled between
    amendments). Regular annual proxies ("DEF 14A", with the space) do not match
    the merger-form alternation and are silently — and correctly — excluded.
    """
    for line in text.splitlines():
        m = _LINE.match(line)
        if not m:
            continue
        base_form, _amend, company, cik_raw, _dt, _file = m.groups()
        cik = edgar.cik10(cik_raw)
        e = acc.setdefault(cik, {"company": company.strip(), "forms": set(),
                                 "dates": [], "n": 0})
        e["forms"].add(base_form)
        e["dates"].append(day_iso)
        e["n"] += 1
        # keep the shortest (usually cleanest) company rendering
        if company.strip() and len(company.strip()) < len(e["company"]):
            e["company"] = company.strip()
    return acc


def finalize(acc: dict, cik_to_symbol: Optional[dict] = None) -> list[DealCandidate]:
    """Turn the CIK accumulator into DealCandidates, newest-filing first (a deal
    that just filed is the freshest, most-actionable spread). Tickers backfilled
    from the EDGAR CIK→ticker map when provided (else left None for the read)."""
    cik_to_symbol = cik_to_symbol or {}
    out: list[DealCandidate] = []
    for cik, e in acc.items():
        dates = sorted(e["dates"])
        forms = sorted(e["forms"])
        out.append(DealCandidate(
            cik=cik, company=e["company"], symbol=cik_to_symbol.get(cik),
            channels=[DEAL_FORMS[f] for f in forms], forms=forms,
            first_filed=dates[0] if dates else "", last_filed=dates[-1] if dates else "",
            n_filings=e["n"],
        ))
    out.sort(key=lambda c: (c.last_filed, c.cik), reverse=True)
    return out


def new_candidates(cands: list[DealCandidate], tracked_ciks) -> list[DealCandidate]:
    """Drop deals already tracked (in the sleeve / A/B), keyed by CIK — the sweep
    re-runs a trailing window every session, so this is what keeps it from
    re-detecting the same deal each pass."""
    seen = {edgar.cik10(c) for c in tracked_ciks}
    return [c for c in cands if c.cik not in seen]


def _daily_index_url(d: date) -> str:
    return (f"https://www.sec.gov/Archives/edgar/daily-index/{d.year}"
            f"/QTR{(d.month - 1) // 3 + 1}/form.{d.strftime('%Y%m%d')}.idx")


def sweep_deals(date_from: str, date_to: str,
                cik_to_symbol: Optional[dict] = None) -> list[DealCandidate]:  # pragma: no cover - network
    """Enumerate EVERY announced-deal target that filed merger/tender paper in
    [date_from, date_to], from EDGAR's daily form indexes — the complete
    population, no keyword. Deals close over weeks/months, so callers pass a
    trailing window (e.g. 120 days). A holiday/transient fetch failure is skipped;
    the session-cadence overlap re-covers the window and heals the gap, exactly as
    the spinoff scanner does.
    """
    acc: dict = {}
    d = date.fromisoformat(date_from)
    end = date.fromisoformat(date_to)
    while d <= end:
        if d.weekday() < 5:  # weekday indexes only
            try:
                body = edgar.http_get(_daily_index_url(d))
                text = body if isinstance(body, str) else body.decode("latin-1", errors="replace")
                parse_index_text(text, d.isoformat(), acc)
            except Exception:
                pass  # holiday or transient; trailing-window overlap self-heals
        d += timedelta(days=1)
    return finalize(acc, cik_to_symbol)
