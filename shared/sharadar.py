"""Sharadar SEP (Nasdaq Data Link) — survivorship-bias-free daily bars.

Purchased 2026-07-04 (operator). ~20,000 US companies including
delisted, back to 1998 (metadata often earlier). This module is the
ONLY sanctioned door to the feed; it exists chiefly to enforce one
integration law learned during acceptance QA (docs/
sharadar_qa_2026-07-04.md):

    SEP KEYS ALL HISTORY TO THE COMPANY'S FINAL TICKER.

Twitter's whole life is under TWTR (clean case), but SVB Financial is
under SIVBQ (its post-bankruptcy OTC symbol) and querying "SIVB"
returns NOTHING; META holds FB-era bars and querying "FB" returns
nothing; and "BBBY" returns Overstock/Beyond (which recycled the
ticker in 2025) while the real Bed Bath & Beyond lives under BBBYQ.
Querying SEP by a historical ticker without resolving it first is how
a study silently analyzes the WRONG COMPANY.

So: `resolve_ticker(symbol, as_of=...)` first (searches ticker +
relatedtickers, disambiguates by first/lastpricedate window), then
fetch bars by the resolved final ticker. `ingest_symbols()` does the
whole dance and lands bars in the shared.historicals store with the
resolution mapping recorded.

Costs/limits: authenticated Nasdaq Data Link allows ~300 calls/10s;
we throttle far below that. Key from NASDAQ_DATA_LINK_API_KEY.
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Iterable, Optional

import requests

from shared.historicals import STORE_PATH, _merge, load_store, save_store

BASE_URL = "https://data.nasdaq.com/api/v3/datatables/SHARADAR"
THROTTLE_S = 0.25

TICKER_COLUMNS = ("ticker,permaticker,name,exchange,isdelisted,category,"
                  "firstpricedate,lastpricedate,relatedtickers")


class SharadarError(Exception):
    pass


class AmbiguousTicker(SharadarError):
    """A symbol matches multiple companies; pass as_of to disambiguate."""


def _api_key() -> str:
    key = os.environ.get("NASDAQ_DATA_LINK_API_KEY", "").strip()
    if not key:
        raise SharadarError("NASDAQ_DATA_LINK_API_KEY not set")
    return key


def _datatable(table_name: str, **params) -> list[dict]:
    """Fetch a SHARADAR datatable with cursor pagination → list of dicts."""
    params = {k: v for k, v in params.items() if v is not None}
    params["api_key"] = _api_key()
    rows: list[dict] = []
    cursor = None
    while True:
        if cursor:
            params["qopts.cursor_id"] = cursor
        r = requests.get(f"{BASE_URL}/{table_name}.json", params=params, timeout=90)
        if r.status_code != 200:
            raise SharadarError(
                f"{table_name}: HTTP {r.status_code}: {r.text[:300]}")
        payload = r.json()
        dt = payload["datatable"]
        cols = [c["name"] for c in dt["columns"]]
        rows.extend(dict(zip(cols, row)) for row in dt["data"])
        cursor = (payload.get("meta") or {}).get("next_cursor_id")
        if not cursor:
            return rows
        time.sleep(THROTTLE_S)


def fetch_ticker_meta(symbols: Iterable[str]) -> list[dict]:
    """TICKERS rows (SEP table) for exact ticker matches."""
    syms = ",".join(sorted({s.strip().upper() for s in symbols if s.strip()}))
    if not syms:
        return []
    return _datatable("TICKERS", table="SEP", ticker=syms,
                      **{"qopts.columns": TICKER_COLUMNS})


TICKER_UNIVERSE_PATH = "cache/shared_sharadar_tickers.json"


def load_ticker_universe(
    path: str = TICKER_UNIVERSE_PATH, *, refresh: bool = False
) -> list[dict]:
    """The FULL SEP TICKERS table, cached locally.

    Needed because the API cannot filter on relatedtickers — a renamed
    company's old symbol (FB) matches nothing server-side; only a local
    sweep finds it inside META's relatedtickers. ~20k rows, a few
    paged calls; cache it once and persist under the shared prefix.
    """
    import json
    if not refresh and os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
            if data.get("rows"):
                return data["rows"]
        except (json.JSONDecodeError, OSError):
            pass
    rows = _datatable("TICKERS", table="SEP",
                      **{"qopts.columns": TICKER_COLUMNS,
                         "qopts.per_page": 10000})
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"fetched": datetime.utcnow().date().isoformat(),
                   "rows": rows}, f)
    os.replace(tmp, path)
    return rows


def _matches(row: dict, symbol: str) -> bool:
    if row.get("ticker", "").upper() == symbol:
        return True
    related = (row.get("relatedtickers") or "").upper().split()
    return symbol in related


def _in_window(row: dict, as_of: str) -> bool:
    first = row.get("firstpricedate") or "0000-00-00"
    last = row.get("lastpricedate") or "9999-99-99"
    return first <= as_of <= last


def resolve_ticker(
    symbol: str,
    *,
    as_of: Optional[str] = None,
    candidates: Optional[list[dict]] = None,
) -> dict:
    """Resolve a (possibly historical) symbol to its TICKERS row.

    Searches exact ticker AND relatedtickers. If multiple companies
    match (recycled tickers — the BBBY trap), `as_of` (YYYY-MM-DD, a
    date the symbol was known to trade) disambiguates via the price
    window; without it, ambiguity raises rather than guesses.

    `candidates` lets tests / bulk callers supply pre-fetched TICKERS
    rows; otherwise the API is queried (exact match first, then a
    relatedtickers sweep is NOT possible server-side, so bulk callers
    doing historical-symbol work should prefetch broadly).
    """
    symbol = symbol.strip().upper()
    if candidates is None:
        candidates = fetch_ticker_meta([symbol])
        if not any(_matches(r, symbol) for r in candidates):
            # Historical symbol: it only appears in relatedtickers of some
            # final-ticker row, which the API can't filter on — sweep the
            # locally cached full TICKERS universe instead.
            candidates = candidates + load_ticker_universe()
    hits = [r for r in candidates if _matches(r, symbol)]
    if as_of:
        day = str(as_of)[:10]
        windowed = [r for r in hits if _in_window(r, day)]
        if windowed:
            hits = windowed
        if len(hits) > 1:
            # Recycled ticker with overlapping lifetimes (the BBBY case:
            # old Bed Bath traded AS BBBY while the Overstock lineage —
            # whose FINAL ticker is now BBBY — traded as OSTK). Ownership
            # rule: a lineage for which `symbol` is a HISTORICAL name
            # (in relatedtickers, final ticker differs) owns the symbol
            # until it stops pricing; a lineage that renamed INTO the
            # symbol owns it only after every historical holder is gone.
            # Imprecise within the rename-boundary month — studies near a
            # boundary must verify by hand.
            historical = [r for r in hits
                          if r.get("ticker", "").upper() != symbol]
            final = [r for r in hits if r.get("ticker", "").upper() == symbol]
            live_then = [r for r in historical
                         if (r.get("lastpricedate") or "9999") >= day]
            if len(live_then) == 1:
                hits = live_then
            elif not live_then and len(final) == 1:
                hits = final
    if not hits:
        raise SharadarError(
            f"{symbol}: no TICKERS match (searched ticker + relatedtickers"
            f"{' + Q/F suffixes' if candidates is not None else ''}) — "
            "the name may predate coverage or need a manual final-ticker hint")
    if len(hits) > 1:
        desc = [(r["ticker"], r["name"], r.get("firstpricedate"),
                 r.get("lastpricedate")) for r in hits]
        raise AmbiguousTicker(
            f"{symbol}: {len(hits)} companies match {desc} — pass as_of "
            "(a date the symbol traded) to disambiguate")
    return hits[0]


def fetch_sep_bars(
    final_ticker: str,
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[dict]:
    """Raw SEP rows for one RESOLVED final ticker."""
    params = {"ticker": final_ticker.strip().upper(),
              "qopts.per_page": 10000}
    if date_from:
        params["date.gte"] = str(date_from)[:10]
    if date_to:
        params["date.lte"] = str(date_to)[:10]
    return _datatable("SEP", **params)


def fetch_sep_bulk_range(
    date_from: str, date_to: str, *, tickers: Optional[Iterable[str]] = None,
) -> list[dict]:
    """Raw SEP rows for a date range across MANY tickers in one paginated
    pull, instead of one call per name — the "bulk pipeline" half of
    backlog #9 (The Gauntlet). Confirmed working 2026-07-04: omitting
    `ticker` returns the full day's cross-section (~6,800 rows for a
    single trading day, one page at qopts.per_page=10000).

    Unlike `fetch_sep_bars`, no ticker resolution happens here — rows
    come back keyed to whatever ticker SEP has on file for that date,
    which is correct for point-in-time work (you want the ticker AS IT
    TRADED then) but means results are NOT automatically coherent with
    `shared.historicals` per-symbol keys the way `ingest_symbols` is;
    callers doing PIT universe/backtest work should consume rows
    directly (see `shared.gauntlet`) rather than merge them into
    `cache/shared_bars.json`, which is sized for per-symbol studies.
    """
    params: dict = {"date.gte": str(date_from)[:10], "date.lte": str(date_to)[:10],
                    "qopts.per_page": 10000}
    if tickers:
        params["ticker"] = ",".join(sorted({t.strip().upper() for t in tickers if t.strip()}))
    return _datatable("SEP", **params)


def to_shared_bars(sep_rows: list[dict]) -> list[dict]:
    """SEP rows → shared.historicals canonical bars.

    open/high/low/close in SEP are split-adjusted (matches the house's
    broker-bar convention); closeadj (split+dividend) rides along as
    `close_total_return` for studies that want it.
    """
    out = []
    for r in sep_rows:
        if not r.get("date") or r.get("close") is None:
            continue
        bar = {
            "date": str(r["date"])[:10],
            "open": float(r["open"]) if r.get("open") is not None else None,
            "high": float(r["high"]) if r.get("high") is not None else None,
            "low": float(r["low"]) if r.get("low") is not None else None,
            "close": float(r["close"]),
        }
        bar = {k: v for k, v in bar.items() if v is not None}
        if r.get("volume") is not None:
            bar["volume"] = int(float(r["volume"]))
        if r.get("closeadj") is not None:
            bar["close_total_return"] = float(r["closeadj"])
        out.append(bar)
    return sorted(out, key=lambda b: b["date"])


def ingest_symbols(
    symbols: Iterable[str],
    *,
    as_of: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    store_path: str = STORE_PATH,
) -> dict:
    """Resolve each symbol, fetch its bars, land them in the shared store.

    Bars are stored under the SYMBOL AS REQUESTED (so studies keyed to
    historical tickers stay coherent), with the resolution recorded in
    the report AND in the store entry's sources. Returns
    {"resolved": {sym: final_ticker}, "bars_added": {...},
     "failed": {sym: reason}} — failures are reported, never silent
    (they are the survivorship disclosure's raw material).
    """
    store = load_store(store_path)
    resolved: dict[str, str] = {}
    added: dict[str, int] = {}
    failed: dict[str, str] = {}
    stamp = datetime.utcnow().date().isoformat()
    for sym in sorted({s.strip().upper() for s in symbols if s.strip()}):
        try:
            row = resolve_ticker(sym, as_of=as_of or date_from)
            final = row["ticker"].upper()
            resolved[sym] = final
            bars = to_shared_bars(
                fetch_sep_bars(final, date_from=date_from, date_to=date_to))
            if not bars:
                failed[sym] = f"resolved to {final} but 0 bars in window"
                continue
            source = (f"sharadar SEP {stamp} (requested {sym} -> final "
                      f"{final}, permaticker {row.get('permaticker')})")
            added[sym] = _merge(store, sym, bars, source)
        except SharadarError as e:
            failed[sym] = str(e)
        time.sleep(THROTTLE_S)
    save_store(store, store_path)
    return {"resolved": resolved, "bars_added": added, "failed": failed}
