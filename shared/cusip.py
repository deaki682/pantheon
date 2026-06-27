"""CUSIP → ticker resolution.

13F information tables identify each holding by CUSIP + issuer *name*, never by
ticker. To join smart-money holdings into the (ticker-keyed) Oracle screen we
resolve CUSIPs to tickers via OpenFIGI — the authoritative mapping — and fall
back to a normalized name match against SEC's company_tickers title map for any
CUSIP OpenFIGI can't resolve.

Both the OpenFIGI POST and the name index are injectable so tests run offline.
"""
from __future__ import annotations

import json
import re
import time
from typing import Callable, Iterable, Optional

try:
    import requests
except ImportError:  # pragma: no cover - tests run without network
    requests = None  # type: ignore


OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"

# A POST-JSON callable: (url, json_body) -> response text. Injectable for tests.
PostJson = Callable[[str, list], str]


def _default_post(url: str, body: list, *, timeout: float = 20.0) -> str:  # pragma: no cover - network
    if requests is None:
        raise RuntimeError("requests not available")
    headers = {"Content-Type": "application/json"}
    for attempt in range(5):
        r = requests.post(url, json=body, headers=headers, timeout=timeout)
        if r.status_code == 429:
            # OpenFIGI throttle (free tier: 25 req/min). Back off and retry.
            time.sleep(min(60.0, 3.0 * (2 ** attempt)))
            continue
        if r.status_code >= 400:
            r.raise_for_status()
        return r.text
    raise RuntimeError("openfigi: gave up after retries")


_default_post_impl: PostJson = _default_post


def set_default_post(poster: PostJson) -> None:
    """Tests use this to swap in a stub OpenFIGI POST."""
    global _default_post_impl
    _default_post_impl = poster


def _pick_ticker(data_entries: list) -> str:
    """From OpenFIGI `data` entries for one CUSIP, choose the US ticker.

    A CUSIP can map to listings on several exchanges; we want the US composite.
    """
    if not data_entries:
        return ""
    for e in data_entries:
        if e.get("exchCode") == "US" and e.get("ticker"):
            return str(e["ticker"]).upper()
    return str((data_entries[0] or {}).get("ticker", "")).upper()


def resolve_cusips_openfigi(
    cusips: Iterable[str], *, post: Optional[PostJson] = None, batch_size: int = 10,
) -> dict[str, str]:
    """Map CUSIP → ticker via OpenFIGI. Unmappable CUSIPs are simply omitted.

    Batches requests (OpenFIGI's unauthenticated tier allows ≤10 jobs/request).
    A failed batch is skipped, not retried as a whole — the name fallback covers
    anything missing.
    """
    do_post = post or _default_post_impl
    uniq = list(dict.fromkeys(c.strip() for c in cusips if c and c.strip()))
    out: dict[str, str] = {}
    for i in range(0, len(uniq), batch_size):
        batch = uniq[i:i + batch_size]
        body = [{"idType": "ID_CUSIP", "idValue": c} for c in batch]
        try:
            payload = json.loads(do_post(OPENFIGI_URL, body))
        except Exception:
            continue
        if not isinstance(payload, list):
            continue
        for cusip, result in zip(batch, payload):
            t = _pick_ticker((result or {}).get("data") or [])
            if t:
                out[cusip] = t
    return out


# ------- Name-match fallback -------

_NAME_NONALNUM = re.compile(r"[^A-Z0-9 ]+")
_NAME_NOISE = re.compile(
    r"\b(INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|PLC|LLC|LP|"
    r"NV|SA|AG|AB|SE|HOLDINGS|HOLDING|GROUP|THE|COM|CL|CLASS|NEW|ADR|"
    r"A|B|C)\b"
)


def normalize_name(name: str) -> str:
    """Normalize an issuer name for fuzzy equality (drop punctuation + suffixes)."""
    s = (name or "").upper().replace("&", " AND ")
    # Delete intra-token punctuation first so "N.V." -> "NV" (a known suffix)
    # rather than splitting into "N V".
    s = s.replace(".", "").replace("'", "")
    s = _NAME_NONALNUM.sub(" ", s)
    s = _NAME_NOISE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def build_name_ticker_index(company_tickers) -> dict[str, str]:
    """Build {normalized issuer name → ticker} from SEC company_tickers rows.

    Accepts the raw SEC structure (a dict of {idx: {cik_str, ticker, title}})
    or any iterable of those row dicts. First ticker wins on collision.
    """
    rows = company_tickers.values() if isinstance(company_tickers, dict) else company_tickers
    out: dict[str, str] = {}
    for row in rows:
        ticker = str(row.get("ticker", "")).upper().strip()
        key = normalize_name(str(row.get("title", "")))
        if key and ticker and key not in out:
            out[key] = ticker
    return out


def resolve_ticker(cusip: str, name: str, cusip_map: dict, name_index: dict) -> str:
    """Resolve one holding to a ticker: CUSIP first (authoritative), then name."""
    t = cusip_map.get((cusip or "").strip())
    if t:
        return t
    return name_index.get(normalize_name(name), "")
