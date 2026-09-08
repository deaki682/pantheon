"""Proteus hosting of lab forward books (directive D6, accepted 2026-09-01).

Two backtested-but-unforwarded lab hypotheses get their forward
populations logged as a rider on Proteus's daily EDGAR pass:

- ``tender_target_14d9``  — every INITIAL "SC 14D9" (third-party tender
  target recommendation). Backtest read a statistical null; the forward
  book grades that null on fresh data.
- ``cef_tender_toc_anchor`` — every "SC TO-C" (tender pre-commencement
  communication). The CEF-or-not classification is a manual in-session
  call, recorded per row; only CEF rows belong to the hypothesis.

This module only LOGS the population (dedup on accession) into
``cache/proteus_labhost_forward.json``. Entry marks (next close), the
+25-trading-day maturity, and grading vs SPY are session work; verdicts
belong to the house lab, which reads this file — Proteus never writes
``cache/lab_registry.json``.

Population source is the daily form index (form-level, NOT the sweep's
FTS phrase families — a phrase-filtered subset would bias the book).
"""
from __future__ import annotations

import json
import os
from typing import Callable, Optional

import requests

BOOK_PATH = "cache/proteus_labhost_forward.json"
UA = {"User-Agent": "pantheon research deaki682@gmail.com"}
IDX_URL = "https://www.sec.gov/Archives/edgar/daily-index/{year}/QTR{q}/form.{ymd}.idx"
FORMS = {"SC 14D9": "tender_target_14d9", "SC TO-C": "cef_tender_toc_anchor"}


def parse_form_idx(text: str) -> list:
    """Parse a daily form.idx into rows for the two hosted forms.

    Initial filings only — amendments (``/A``) restate, they don't
    start a clock.
    """
    rows = []
    for line in text.splitlines():
        form = line[:12].strip()
        if form not in FORMS:
            continue
        rest = line[12:].rstrip("\n")
        # Fixed-ish columns: company, CIK, date, filename. The filename
        # (last token) carries the accession; CIK and date sit before it.
        toks = rest.split()
        if len(toks) < 4:
            continue
        filename = toks[-1]
        date = toks[-2]
        cik = toks[-3]
        company = " ".join(toks[:-3])
        accession = os.path.basename(filename).replace(".txt", "")
        rows.append(
            {
                "slug": FORMS[form],
                "form": form,
                "company": company,
                "cik": cik,
                "date": date,
                "accession": accession,
            }
        )
    return rows


def fetch_form_idx(ymd: str, fetch: Optional[Callable] = None) -> str:
    """GET the daily form index for YYYY-MM-DD; '' when not yet published."""
    y, m, _ = ymd.split("-")
    q = (int(m) - 1) // 3 + 1
    url = IDX_URL.format(year=y, q=q, ymd=ymd.replace("-", ""))
    if fetch is None:
        resp = requests.get(url, headers=UA, timeout=30)
        if resp.status_code in (403, 404):
            # SEC serves 403 (not 404) for a daily index not yet published.
            return ""
        resp.raise_for_status()
        return resp.text
    return fetch(url)


def load_book(path: str = BOOK_PATH) -> dict:
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    return {
        "name": "proteus_labhost_forward",
        "hosting": "D6 accepted 2026-09-01: forward populations for "
        "tender_target_14d9 (all initial SC 14D9) and cef_tender_toc_anchor "
        "(SC TO-C, CEF rows only after manual classification). Entry = first "
        "close after the filing date; maturity = +25 trading days; grade = "
        "CAR vs SPY. Lab lifts grades from here; Proteus never writes the "
        "lab registry.",
        "rows": [],
    }


def log_days(dates: list, path: str = BOOK_PATH, fetch: Optional[Callable] = None) -> dict:
    """Idempotently append the hosted-form rows for the given dates.

    Returns {"new": [...], "skipped_days": [...]} — a date whose index
    is not yet published (overnight lag) lands in skipped_days so the
    next session retries it.
    """
    book = load_book(path)
    seen = {r["accession"] for r in book["rows"]}
    new, skipped = [], []
    for ymd in dates:
        text = fetch_form_idx(ymd, fetch=fetch)
        if not text:
            skipped.append(ymd)
            continue
        for row in parse_form_idx(text):
            if row["accession"] in seen:
                continue
            seen.add(row["accession"])
            row.update(
                {
                    "status": "logged",
                    "classification": None,
                    "symbol": None,
                    "entry_close": None,
                    "entry_date": None,
                    "grade": None,
                }
            )
            book["rows"].append(row)
            new.append(row)
    with open(path, "w") as fh:
        json.dump(book, fh, indent=1)
    return {"new": new, "skipped_days": skipped}
