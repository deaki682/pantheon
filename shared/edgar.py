"""SEC EDGAR client.

- Filings index: data.sec.gov/submissions/CIK<10digit>.json
- Full-text search: efts.sec.gov/LATEST/search-index?q=...
- Filing body: www.sec.gov/Archives/edgar/data/<cik>/<acc-no>/...
- HTML cleaning and section extraction (risk factors, MD&A, business).

User-Agent is required by SEC. Use the configured UA below.

This module wraps requests but is structured so the network calls live in
small functions that tests can stub.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import quote

import threading

try:
    import requests
except ImportError:  # pragma: no cover - tests run without network
    requests = None  # type: ignore


USER_AGENT = "fluffy-waffle-oracle deaki682@gmail.com"
_HEADERS = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"}

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_clean}/{file}"


# ------- Global rate limiter -------
#
# SEC rate-limits to 10 req/s per IP. We enforce 8/s in a thread-safe gate so
# any caller (sequential or threaded) shares one global budget. Threads
# wanting to fan out (scan_universe with max_workers > 1) can do so safely.

class _RateLimiter:
    def __init__(self, max_per_sec: float = 8.0):
        self._lock = threading.Lock()
        self._min_interval = 1.0 / max_per_sec
        self._last_call = 0.0

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()

    def set_rate(self, max_per_sec: float) -> None:
        with self._lock:
            self._min_interval = 1.0 / max_per_sec


_RATE = _RateLimiter(max_per_sec=8.0)


def set_rate_limit(max_per_sec: float) -> None:
    """Caller hook to tune the global SEC rate limit (default 8/s)."""
    _RATE.set_rate(max_per_sec)


def cik10(cik) -> str:
    """Zero-pad a CIK to 10 digits."""
    return str(int(cik)).zfill(10)


def acc_no_clean(acc_no: str) -> str:
    """Strip dashes from an accession number."""
    return acc_no.replace("-", "")


# ------- HTTP layer -------

_BACKOFF_MAX_TRIES = 5


def _get(url: str, params: Optional[dict] = None, *, timeout: float = 20.0) -> str:
    if requests is None:
        raise RuntimeError("requests not available")
    last_exc: Optional[Exception] = None
    for attempt in range(_BACKOFF_MAX_TRIES):
        _RATE.acquire()
        try:
            r = requests.get(url, params=params, headers=_HEADERS, timeout=timeout)
        except Exception as e:
            last_exc = e
            # network blip: bounded exponential backoff
            time.sleep(min(60.0, 2.0 ** attempt))
            continue
        if r.status_code == 429 or r.status_code == 503:
            # SEC throttle. Honor Retry-After if present, else exponential.
            ra = r.headers.get("Retry-After", "")
            try:
                sleep_s = float(ra) if ra else min(120.0, 5.0 * (2 ** attempt))
            except ValueError:
                sleep_s = min(120.0, 5.0 * (2 ** attempt))
            time.sleep(sleep_s)
            continue
        if r.status_code >= 400:
            r.raise_for_status()
        return r.text
    if last_exc:
        raise last_exc
    raise RuntimeError(f"http_get gave up after {_BACKOFF_MAX_TRIES} retries: {url}")


def http_get(url: str, params: Optional[dict] = None, *, timeout: float = 20.0) -> str:
    """Public, rate-limited HTTP GET used by all lens fetchers. Tests can
    monkeypatch this to avoid network."""
    return _get(url, params=params, timeout=timeout)


# ------- Filings -------

@dataclass
class Filing:
    cik: str
    accession_no: str
    form: str
    filing_date: str  # YYYY-MM-DD
    primary_document: str = ""
    items: str = ""  # e.g. "2.02,9.01" for 8-K
    symbol: str = ""

    @property
    def acc_clean(self) -> str:
        return acc_no_clean(self.accession_no)

    @property
    def primary_url(self) -> str:
        if not self.primary_document:
            return ""
        return ARCHIVE_URL.format(
            cik=int(self.cik), acc_no_clean=self.acc_clean, file=self.primary_document
        )


def parse_submissions_recent(payload: dict, *, symbol: str = "") -> list[Filing]:
    """Parse the 'recent' section of a submissions.json payload."""
    out: list[Filing] = []
    recent = payload.get("filings", {}).get("recent", {})
    cik = str(payload.get("cik", "")).lstrip("0") or "0"
    accs = recent.get("accessionNumber", [])
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    primaries = recent.get("primaryDocument", [])
    items = recent.get("items", [""] * len(accs))
    n = len(accs)
    for i in range(n):
        out.append(
            Filing(
                cik=cik,
                accession_no=accs[i],
                form=forms[i] if i < len(forms) else "",
                filing_date=dates[i] if i < len(dates) else "",
                primary_document=primaries[i] if i < len(primaries) else "",
                items=items[i] if i < len(items) else "",
                symbol=symbol,
            )
        )
    return out


def fetch_submissions(cik) -> dict:  # pragma: no cover - network
    url = SUBMISSIONS_URL.format(cik=cik10(cik))
    return json.loads(_get(url))


COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def fetch_company_tickers() -> dict[str, str]:
    """Fetch SEC's master ticker → zero-padded CIK map. Cached on disk after first call."""
    raw = json.loads(_get(COMPANY_TICKERS_URL))
    out: dict[str, str] = {}
    for row in raw.values():
        sym = str(row.get("ticker", "")).upper().strip()
        cik = str(row.get("cik_str", "")).strip()
        if sym and cik:
            out[sym] = cik.zfill(10)
    return out


def fetch_company_tickers_rows() -> list[dict]:  # pragma: no cover - network
    """Raw SEC company_tickers rows ({cik_str, ticker, title}).

    Unlike fetch_company_tickers (which discards the title), this keeps the
    issuer name so callers can build a name→ticker index.
    """
    raw = json.loads(_get(COMPANY_TICKERS_URL))
    return list(raw.values())


def fetch_company_facts(cik) -> dict:  # pragma: no cover - network
    """Fetch the full XBRL company-facts payload for a CIK."""
    url = COMPANY_FACTS_URL.format(cik=cik10(cik))
    return json.loads(_get(url))


# ------- Full-text search -------

def search_filings(
    query: str,
    forms: Optional[list[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    offset: int = 0,
) -> dict:  # pragma: no cover - network
    """One page of EDGAR full-text search. FTS pages at 10 hits; callers
    that need the full result set must loop on `offset` (the API's `from`
    param) until hits.total.value is exhausted."""
    params = {"q": query}
    if forms:
        params["forms"] = ",".join(forms)
    if date_from:
        params["dateRange"] = "custom"
        params["startdt"] = date_from
    if date_to:
        params["enddt"] = date_to
    if offset:
        params["from"] = str(offset)
    return json.loads(_get(SEARCH_URL, params=params))


# ------- Body / HTML -------

_HTML_TAG = re.compile(r"<[^>]+>")
_SCRIPT = re.compile(r"<script\b.*?</script>", re.IGNORECASE | re.DOTALL)
_STYLE = re.compile(r"<style\b.*?</style>", re.IGNORECASE | re.DOTALL)
_WS = re.compile(r"\s+")
_NBSP = re.compile(r"&nbsp;|\xa0")


def clean_html(html: str) -> str:
    """Strip script/style, drop tags, collapse whitespace, decode common entities."""
    s = _SCRIPT.sub(" ", html)
    s = _STYLE.sub(" ", s)
    s = _HTML_TAG.sub(" ", s)
    s = _NBSP.sub(" ", s)
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'").replace("&quot;", '"')
    s = _WS.sub(" ", s)
    return s.strip()


# Section markers — case-insensitive, allow Item 1A./1A/1.A variations.
_SECTION_PATTERNS = {
    "risk_factors": re.compile(
        r"item\s*1a\.?\s*[—–\-:]?\s*risk\s+factors", re.IGNORECASE
    ),
    "mdna": re.compile(
        r"item\s*7\.?\s*[—–\-:]?\s*management'?s?\s+discussion", re.IGNORECASE
    ),
    "business": re.compile(
        r"item\s*1\.?\s*[—–\-:]?\s*business", re.IGNORECASE
    ),
}

_SECTION_TERMINATORS = re.compile(
    r"item\s*(1b|2|7a|8)\.?", re.IGNORECASE
)


def extract_section(text: str, key: str) -> str:
    pat = _SECTION_PATTERNS.get(key)
    if not pat:
        return ""
    m = pat.search(text)
    if not m:
        return ""
    start = m.end()
    end_m = _SECTION_TERMINATORS.search(text, pos=start)
    end = end_m.start() if end_m else min(len(text), start + 120_000)
    return text[start:end].strip()


def fetch_body(filing: Filing) -> str:  # pragma: no cover - network
    if not filing.primary_url:
        return ""
    return _get(filing.primary_url)


# ------- 8-K item classification -------

def parse_items(items_str: str) -> set[str]:
    """Return a set of normalized item codes from the comma/space separated string."""
    if not items_str:
        return set()
    raw = re.split(r"[,\s]+", items_str.strip())
    out: set[str] = set()
    for item in raw:
        item = item.strip().rstrip(".")
        if not item:
            continue
        # Normalize "Item 2.02" -> "2.02"
        item = re.sub(r"(?i)^item\s*", "", item)
        out.add(item)
    return out


def classify_8k(items_str: str) -> list[str]:
    """Return a list of human-readable event labels for an 8-K based on its items."""
    items = parse_items(items_str)
    labels: list[str] = []
    if "2.02" in items:
        labels.append("earnings_reaction")
    if "2.01" in items:
        labels.append("ma_target")
    if "7.01" in items or "8.01" in items:
        labels.append("guidance_revision")
    if "1.03" in items:
        labels.append("bankruptcy")
    if "3.01" in items:
        labels.append("delisting")
    return labels


# ------- Guidance body regex -------

_GUIDANCE_RAISED = re.compile(
    r"\b(rais|increas|upward|above\s+prior)\w*\b.{0,80}?\bguidance\b", re.IGNORECASE | re.DOTALL
)
_GUIDANCE_LOWERED = re.compile(
    r"\b(lower|reduc|cut|downward|below\s+prior)\w*\b.{0,80}?\bguidance\b", re.IGNORECASE | re.DOTALL
)
_GUIDANCE_WITHDRAWN = re.compile(
    r"\bwithdraw\w*\b.{0,80}?\bguidance\b|\bguidance\b.{0,80}?\bwithdraw\w*\b",
    re.IGNORECASE | re.DOTALL,
)
_GUIDANCE_REAFFIRMED = re.compile(
    r"\b(reaffirm|maintain|reiterat)\w*\b.{0,80}?\bguidance\b", re.IGNORECASE | re.DOTALL
)


def guidance_direction(text: str) -> str:
    """Return one of 'raised' | 'lowered' | 'withdrawn' | 'reaffirmed' | 'unknown'."""
    # Order matters — check withdrawn first because 'lower' phrases often co-occur.
    if _GUIDANCE_WITHDRAWN.search(text):
        return "withdrawn"
    if _GUIDANCE_RAISED.search(text):
        return "raised"
    if _GUIDANCE_LOWERED.search(text):
        return "lowered"
    if _GUIDANCE_REAFFIRMED.search(text):
        return "reaffirmed"
    return "unknown"


# ------- Spinoff ex-date extraction -------

_EXDATE_CTX = re.compile(
    r"(?:ex[\-\s]?date|distribution\s+date|record\s+date|ex[\-\s]?dividend)",
    re.IGNORECASE,
)
_DATE_LITERAL = re.compile(
    r"([A-Z][a-z]+\.?)\s+(\d{1,2}),\s*(\d{4})", re.IGNORECASE,
)
_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


def extract_ex_date(text: str) -> Optional[str]:
    """Search for a date literal near an ex-date/distribution-date marker."""
    m = _EXDATE_CTX.search(text)
    if not m:
        return None
    window = text[m.end(): m.end() + 200]
    dm = _DATE_LITERAL.search(window)
    if not dm:
        return None
    mon_raw, day_raw, year_raw = dm.group(1), dm.group(2), dm.group(3)
    key = mon_raw.lower().rstrip(".")
    mon = _MONTHS.get(key[:4]) or _MONTHS.get(key[:3])
    if not mon:
        return None
    try:
        return f"{int(year_raw):04d}-{mon:02d}-{int(day_raw):02d}"
    except ValueError:
        return None
