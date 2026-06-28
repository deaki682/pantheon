"""Lens fetchers — actually pull the data each lens needs.

Each fetcher takes a `http_get` callable so tests can stub the network.
By default it uses the rate-limited `shared.edgar.http_get`.

The four lenses:
  - Insider clusters (per-symbol Form 4 fan-out, fed to scan_universe)
  - Smart-money 13F holdings (per-manager 13F-HR information-table fetch)
  - Activist 13D (one EDGAR full-text search, paginated)
  - Broad quality (per-symbol XBRL company-facts -> FundamentalSnapshot -> prescreen)
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Callable, Iterable, Optional

from shared.edgar import (
    ARCHIVE_URL, COMPANY_FACTS_URL, SEARCH_URL, SUBMISSIONS_URL,
    Filing, acc_no_clean, cik10, http_get, parse_submissions_recent,
)
from shared.fundamentals import build_snapshot
from shared.insiders import InsiderTxn, parse_form4

from .prescreener import prescreen


# Caller-overridable HTTP. Default is the rate-limited one.
HttpGet = Callable[..., str]
_default_http: HttpGet = http_get


def set_default_http(getter: HttpGet) -> None:
    """Tests use this to swap in a stub."""
    global _default_http
    _default_http = getter


# ------- helpers -------

def _strip_xsl_prefix(doc: str) -> str:
    """Form 4 `primaryDocument` is frequently the XSL *viewer* path, e.g.
    ``xslF345X06/wk-form4_123.xml`` — that URL serves the human-readable HTML
    rendering, not the raw XML. The machine-readable XML lives at the same file
    name with the leading ``xsl*/`` segment removed. Strip it so we fetch XML."""
    head, slash, tail = doc.partition("/")
    if slash and head.lower().startswith("xsl"):
        return tail
    return doc


def _form4_url(filing: Filing) -> str:
    """The Form 4 XML body lives in the filing index. We construct the URL to the
    primary XML document. The primary_document is usually an .xml file for Form 4
    filings; if it ends in .htm, fall back to the index.json listing."""
    if not filing.primary_document:
        return ""
    return ARCHIVE_URL.format(
        cik=int(filing.cik) if filing.cik else 0,
        acc_no_clean=acc_no_clean(filing.accession_no),
        file=_strip_xsl_prefix(filing.primary_document),
    )


def _filings_index(cik: str, accession_no: str) -> str:
    """The filing index JSON listing all files in a single submission."""
    acc = acc_no_clean(accession_no)
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/index.json"


# ------- Lens 1: Insider clusters -------

def fetch_insider_txns_for_symbol(
    symbol: str,
    cik: str,
    *,
    days_back: int = 60,
    today: Optional[str] = None,
    http: Optional[HttpGet] = None,
) -> list[InsiderTxn]:
    """Fetch recent Form 4 filings for one CIK and parse the underlying XML
    to InsiderTxn rows."""
    get = http or _default_http
    today_s = today or datetime.utcnow().strftime("%Y-%m-%d")
    try:
        cutoff = (datetime.strptime(today_s, "%Y-%m-%d") - timedelta(days=days_back)).strftime("%Y-%m-%d")
    except ValueError:
        cutoff = ""
    try:
        payload = json.loads(get(SUBMISSIONS_URL.format(cik=cik10(cik))))
    except Exception:
        return []
    filings = parse_submissions_recent(payload, symbol=symbol)
    form4s = [f for f in filings if f.form == "4" and (not cutoff or f.filing_date >= cutoff)]
    txns: list[InsiderTxn] = []
    for f in form4s:
        f.cik = str(int(cik))
        url = _form4_url(f)
        if not url:
            continue
        try:
            body = get(url)
        except Exception:
            continue
        # If primary_document was HTML, body won't be XML — skip.
        if "<ownershipDocument" not in body:
            continue
        txns.extend(parse_form4(body, accession_no=f.accession_no))
    return txns


def make_form4_fetcher(
    sym_to_cik: dict[str, str],
    *,
    days_back: int = 60,
    today: Optional[str] = None,
    http: Optional[HttpGet] = None,
) -> Callable[[str], list[InsiderTxn]]:
    """Build the per-symbol fetcher that shared.insiders.scan_universe expects."""
    def fetcher(symbol: str) -> list[InsiderTxn]:
        cik = sym_to_cik.get(symbol.upper())
        if not cik:
            return []
        return fetch_insider_txns_for_symbol(symbol, cik, days_back=days_back, today=today, http=http)
    return fetcher


# ------- Lens 2: Smart-money 13F holdings -------

def find_latest_13fhr_accession(cik: str, *, http: Optional[HttpGet] = None) -> Optional[str]:
    """For a 13F filer CIK, return the accession number of the most recent 13F-HR."""
    get = http or _default_http
    try:
        payload = json.loads(get(SUBMISSIONS_URL.format(cik=cik10(cik))))
    except Exception:
        return None
    filings = parse_submissions_recent(payload, symbol="")
    for f in filings:
        if (f.form or "").upper().strip() == "13F-HR":
            return f.accession_no
    return None


def fetch_13f_information_table_xml(
    cik: str, accession_no: str, *, http: Optional[HttpGet] = None
) -> str:
    """Fetch the information-table XML for a 13F filing. The file name is
    convention-driven; we list the filing index and pick the *_information*.xml
    document."""
    get = http or _default_http
    try:
        index_payload = json.loads(get(_filings_index(cik, accession_no)))
    except Exception:
        return ""
    items = index_payload.get("directory", {}).get("item", []) or []
    candidates = [it.get("name", "") for it in items if it.get("name", "").lower().endswith(".xml")]
    # Prefer files containing 'informationtable' or 'infotable'
    info = [n for n in candidates if "informationtable" in n.lower() or "infotable" in n.lower()]
    chosen = info[0] if info else (candidates[0] if candidates else "")
    if not chosen:
        return ""
    url = ARCHIVE_URL.format(
        cik=int(cik), acc_no_clean=acc_no_clean(accession_no), file=chosen,
    )
    try:
        return get(url)
    except Exception:
        return ""


# ------- Lens 3: Activist 13D (EDGAR full-text search) -------

# display_names entries look like "Acme Inc.  (ACME)  (CIK 0001158780)".
# The ticker is the parenthesized token immediately preceding the (CIK ...) one;
# many filers (private subjects) have no ticker at all.
_DISPLAY_TICKER = re.compile(r"\(([A-Za-z0-9][A-Za-z0-9.\-]{0,9})\)\s*\(CIK", re.IGNORECASE)


def _ticker_from_display_names(display_names) -> str:
    """Extract the subject company's ticker from an EDGAR FTS display_names list.

    display_names[0] is the subject company (the issuer whose shares were
    acquired) — that's the symbol we want. Returns "" when no ticker is present.
    """
    if not display_names:
        return ""
    m = _DISPLAY_TICKER.search(display_names[0] or "")
    return m.group(1).upper() if m else ""


def search_recent_13d(
    *,
    date_from: str,
    date_to: str,
    http: Optional[HttpGet] = None,
    max_pages: int = 10,
) -> list[Filing]:
    """Search EDGAR full-text for Schedule 13D filings in [date_from, date_to].
    Returns fresh 13Ds (excludes /A amendments).

    EDGAR FTS quirks this navigates around:
      - The form token is ``SCHEDULE 13D`` (``SC 13D`` matches nothing).
      - An empty ``q`` param 500s; a form-only "browse" query omits ``q``.
      - ``from=0`` also 500s, so page 0 must omit the ``from`` param entirely.
      - The subject ticker is not a field; it's embedded in ``display_names``.
    """
    get = http or _default_http
    out: list[Filing] = []
    seen: set[str] = set()
    for page in range(max_pages):
        params = {
            "forms": "SCHEDULE 13D",
            "startdt": date_from,
            "enddt": date_to,
        }
        if page > 0:
            params["from"] = str(page * 10)
        try:
            raw = get(SEARCH_URL, params=params)
            payload = json.loads(raw)
        except Exception:
            break
        hits = payload.get("hits", {}).get("hits", [])
        if not hits:
            break
        for h in hits:
            source = h.get("_source", {}) or {}
            form = (source.get("form") or "").upper()
            if form.endswith("/A"):
                continue  # amendment — we only want fresh 13Ds
            acc = source.get("adsh", "") or h.get("_id", "")
            if not acc or acc in seen:
                continue
            seen.add(acc)
            ciks = source.get("ciks", []) or []
            cik = str(ciks[0]) if ciks else ""
            symbol = _ticker_from_display_names(source.get("display_names", []))
            out.append(Filing(
                cik=cik,
                accession_no=acc,
                form="SC 13D",
                filing_date=source.get("file_date", "") or source.get("filing_date", ""),
                symbol=symbol,
            ))
    return out


# ------- Lens 4: Broad quality screen -------

def fetch_quality_snapshot_for_symbol(
    symbol: str, cik: str, *, http: Optional[HttpGet] = None
) -> dict:
    """Per-symbol XBRL fundamentals -> snapshot -> prescreen result.

    Returns {symbol, pass, reasons, snapshot} where snapshot is the
    FundamentalSnapshot serialized to a dict.
    """
    get = http or _default_http
    try:
        payload = json.loads(get(COMPANY_FACTS_URL.format(cik=cik10(cik))))
    except Exception:
        return {"symbol": symbol, "pass": False, "reasons": ["fetch_failed"], "snapshot": None}
    facts = (payload.get("facts") or {}).get("us-gaap") or {}
    snap = build_snapshot(symbol, facts)
    pre = prescreen(snap)
    from dataclasses import asdict
    return {
        "symbol": symbol,
        "pass": pre["pass"],
        "reasons": pre["reasons"],
        "snapshot": asdict(snap),
    }


def scan_universe_quality(
    sym_to_cik: dict[str, str],
    *,
    checkpoint_every: int = 200,
    on_checkpoint: Optional[Callable[[int, list[dict]], None]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
    http: Optional[HttpGet] = None,
) -> list[dict]:
    """Sequential per-symbol quality screen. Checkpointed every N names.

    Sequential (not threaded) by default: the per-symbol fetch is one request,
    and SEC's 8-10/s rate is well-served by sequential calls. Threading would
    require care to not double-acquire the rate-limit gate.
    """
    out: list[dict] = []
    total = len(sym_to_cik)
    done = 0
    for sym, cik in sym_to_cik.items():
        try:
            row = fetch_quality_snapshot_for_symbol(sym, cik, http=http)
        except Exception:
            row = {"symbol": sym, "pass": False, "reasons": ["fetch_error"], "snapshot": None}
        out.append(row)
        done += 1
        if on_progress:
            on_progress(done, total)
        if checkpoint_every > 0 and done % checkpoint_every == 0 and on_checkpoint:
            on_checkpoint(done, list(out))
    return out


# ------- Combine -------

def combine_lenses(
    universe: Iterable[str],
    *,
    insider_clusters: Iterable[dict] = (),
    smart_money: dict[str, list[str]] | None = None,
    activist_symbols: Iterable[str] = (),
    quality_rows: Iterable[dict] = (),
    prices: dict[str, float] | None = None,
    sector_map: dict[str, str] | None = None,
    sector_breadth_value: float = 0.0,
) -> list[dict]:
    """Insider-first combine: only names with at least one insider signal get scored.

    Entry criteria: at least one insider lens must fire (cluster buy, smart-money
    13F, or activist 13D). Valuation or quality alone no longer qualify — the
    insider signal IS the edge; without it this is just a generic value screen.

    Valuation is computed from the quality snapshot + current price.
    """
    from shared.fundamentals import FundamentalSnapshot
    from shared.quality import valuation_score as compute_valuation
    from .screener import multi_lens_score, quality_score

    insider_syms = {c.get("symbol", "").upper() for c in insider_clusters if c.get("symbol")}
    sm = {s.upper() for s in (smart_money or {})}
    act = {s.upper() for s in activist_symbols}
    px = prices or {}
    sec_map = sector_map or {}
    qmap: dict[str, dict] = {}
    for row in quality_rows:
        sym = row.get("symbol", "").upper()
        if sym:
            qmap[sym] = row

    universe_set = {s.upper() for s in universe}
    out: list[dict] = []
    for sym in sorted(universe_set):
        qrow = qmap.get(sym) or {}
        snap_dict = qrow.get("snapshot") or {}

        # Reconstruct snapshot for scoring
        try:
            snap = FundamentalSnapshot(**{k: v for k, v in snap_dict.items() if k in FundamentalSnapshot.__dataclass_fields__})
        except Exception:
            snap = FundamentalSnapshot(symbol=sym)

        shares = snap_dict.get("shares_diluted") or snap_dict.get("shares_basic")
        price = px.get(sym)
        mcap = (shares * price) if (shares and price) else 0.0

        # Compute valuation score (the new primary axis)
        v = compute_valuation(snap, mcap) if mcap > 0 else 0.0

        # Quality score (only for names with sufficient data)
        q = quality_score(snap) if qrow.get("pass") else 0.0

        hit_insider = (sym in insider_syms) or (sym in sm) or (sym in act)

        if not hit_insider:
            continue

        row = multi_lens_score(
            sym,
            insider_cluster=sym in insider_syms,
            smart_money=sym in sm,
            activist_13d=sym in act,
            quality=q,
            valuation=v,
            sector_breadth=sector_breadth_value,
        )
        if sec_map.get(sym):
            row["sector"] = sec_map[sym]
        if shares:
            row["shares"] = shares
        if mcap > 0:
            row["market_cap"] = mcap
        out.append(row)
    return out
