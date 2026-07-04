"""Batched price-history plumbing + the delisted-bars archive.

Robinhood's `get_equity_historicals` caps at ~10 symbols per call, and
its raw responses are large enough to blow session context when pasted
around. The house pattern this module standardizes (born from Proteus's
2026-07-04 backtest, where every god will eventually land):

1. `plan_batches(symbols)` → chunks of <=9 symbols per tool call.
2. The session writes each raw tool result STRAIGHT to a scratch file
   (never re-quotes it in conversation).
3. `ingest_raw(path)` parses whatever shape came back and merges it
   into the compact per-symbol store at `cache/shared_bars.json`.
4. `coverage(store, symbols, ...)` reports who has bars and who is
   MISSING — the survivorship-bias disclosure every study must print.

The ARCHIVE half addresses the structural hole: Robinhood serves no
bars for delisted/renamed tickers, even for dates they actively traded.
When a study obtains such bars from any other source (vendor export,
hand-collected, another cache), `archive_bars()` deposits them — with a
mandatory source citation — into `cache/shared_bars_archive.json` so
the next study starts from coverage instead of re-hitting the wall.
Deposit deliberately (delisted names, hard-won series): the archive is
persisted to claude/live and should stay small, not mirror every
routine fetch.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Iterable, Optional

STORE_PATH = "cache/shared_bars.json"
ARCHIVE_PATH = "cache/shared_bars_archive.json"

MAX_SYMBOLS_PER_CALL = 9  # broker caps at ~10; leave headroom for SPY et al.

# Field aliases seen in broker/tool payloads → canonical bar fields.
_FIELD_ALIASES = {
    "date": ("date", "begins_at", "begins_at_utc", "timestamp"),
    "open": ("open", "open_price"),
    "high": ("high", "high_price"),
    "low": ("low", "low_price"),
    "close": ("close", "close_price", "adjusted_close"),
    "volume": ("volume",),
}


def plan_batches(
    symbols: Iterable[str], batch_size: int = MAX_SYMBOLS_PER_CALL
) -> list[list[str]]:
    """Dedupe (order-preserving, upper-cased) and chunk for tool calls."""
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    seen: dict[str, None] = {}
    for s in symbols:
        sym = str(s).strip().upper()
        if sym:
            seen.setdefault(sym)
    ordered = list(seen)
    return [ordered[i:i + batch_size] for i in range(0, len(ordered), batch_size)]


def _canon_bar(raw: dict) -> Optional[dict]:
    bar: dict = {}
    for canon, aliases in _FIELD_ALIASES.items():
        for a in aliases:
            if a in raw and raw[a] is not None:
                bar[canon] = raw[a]
                break
    if "date" not in bar or "close" not in bar:
        return None
    bar["date"] = str(bar["date"])[:10]
    for k in ("open", "high", "low", "close"):
        if k in bar:
            try:
                bar[k] = float(bar[k])
            except (TypeError, ValueError):
                bar.pop(k)
    if "close" not in bar:
        return None
    if "volume" in bar:
        try:
            bar["volume"] = int(float(bar["volume"]))
        except (TypeError, ValueError):
            bar.pop("volume")
    return bar


def _looks_like_bars(v) -> bool:
    return (
        isinstance(v, list)
        and bool(v)
        and all(isinstance(b, dict) for b in v)
        and _canon_bar(v[0]) is not None
    )


def extract_bars(raw) -> dict[str, list[dict]]:
    """Pull {symbol: [canonical bars]} out of a raw tool payload.

    Tolerates the shapes we've actually seen: {sym: [bars]},
    {"results": [{"symbol": ..., "historicals": [...]}]}, or a bare
    list of such per-symbol dicts. Unknown shapes yield {} rather than
    guessing.
    """
    out: dict[str, list[dict]] = {}

    def _take(sym: str, bars: list) -> None:
        canon = [b for b in (_canon_bar(x) for x in bars) if b]
        if canon:
            out.setdefault(sym.upper(), []).extend(canon)

    if isinstance(raw, dict):
        rows = raw.get("results")
        if isinstance(rows, list):
            raw = rows  # fall through to the list handler
        else:
            for k, v in raw.items():
                if isinstance(k, str) and _looks_like_bars(v):
                    _take(k, v)
            return out
    if isinstance(raw, list):
        for row in raw:
            if not isinstance(row, dict):
                continue
            sym = row.get("symbol") or row.get("ticker")
            bars = row.get("historicals") or row.get("bars") or row.get("data_points")
            if sym and _looks_like_bars(bars or []):
                _take(str(sym), bars)
    return out


def _merge(store: dict, symbol: str, bars: list[dict], source: str) -> int:
    """Merge bars into store["symbols"][symbol]; returns bars added."""
    entry = store.setdefault("symbols", {}).setdefault(
        symbol, {"bars": [], "sources": []}
    )
    by_date = {b["date"]: b for b in entry["bars"]}
    added = 0
    for b in bars:
        if b["date"] not in by_date:
            added += 1
        by_date[b["date"]] = b  # newest ingest wins on collision
    entry["bars"] = [by_date[d] for d in sorted(by_date)]
    if source and source not in entry["sources"]:
        entry["sources"].append(source)
    entry["updated"] = datetime.utcnow().isoformat()
    return added


def load_store(path: str = STORE_PATH) -> dict:
    if not os.path.exists(path):
        return {"symbols": {}}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"symbols": {}}
    data.setdefault("symbols", {})
    return data


def save_store(store: dict, path: str = STORE_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(store, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def ingest_raw(
    raw_path: str, store_path: str = STORE_PATH, *, source: str = "robinhood"
) -> dict[str, int]:
    """Parse a raw tool-output file and merge into the store.

    Returns {symbol: bars_added}. Raises if the file parses to nothing —
    a silent-empty ingest is how survivorship holes hide.
    """
    with open(raw_path) as f:
        raw = json.load(f)
    per_sym = extract_bars(raw)
    if not per_sym:
        raise ValueError(
            f"{raw_path}: no bars recognized — unexpected payload shape?"
        )
    store = load_store(store_path)
    added = {sym: _merge(store, sym, bars, source) for sym, bars in per_sym.items()}
    save_store(store, store_path)
    return added


def bars_for(symbol: str, store: dict) -> list[dict]:
    return store.get("symbols", {}).get(symbol.upper(), {}).get("bars", [])


def coverage(
    store: dict,
    symbols: Iterable[str],
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> dict:
    """Per-symbol coverage report + explicit `missing` list.

    Every study that batches history MUST print this — the `missing`
    list is the survivorship-bias disclosure (typically delisted or
    renamed names the broker can't serve).
    """
    report: dict = {"symbols": {}, "missing": []}
    for s in symbols:
        sym = str(s).strip().upper()
        bars = bars_for(sym, store)
        if start:
            bars = [b for b in bars if b["date"] >= start]
        if end:
            bars = [b for b in bars if b["date"] <= end]
        if not bars:
            report["missing"].append(sym)
        else:
            report["symbols"][sym] = {
                "bars": len(bars),
                "first": bars[0]["date"],
                "last": bars[-1]["date"],
            }
    return report


def archive_bars(
    symbol: str,
    bars: list[dict],
    *,
    source: str,
    note: str = "",
    delisted: bool = False,
    archive_path: str = ARCHIVE_PATH,
) -> int:
    """Deposit hard-won bars (esp. delisted names) into the archive.

    `source` is mandatory and must be specific (URL, vendor+export date,
    filing) — an unsourced series is inadmissible in any future study.
    Returns bars added.
    """
    sym = str(symbol).strip().upper()
    if not sym:
        raise ValueError("symbol required")
    if not source or len(source.strip()) < 8:
        raise ValueError(
            "source required and must be specific (URL / vendor + date)"
        )
    canon = [b for b in (_canon_bar(x) for x in bars) if b]
    if not canon:
        raise ValueError("no valid bars (need at least date + close)")
    store = load_store(archive_path)
    added = _merge(store, sym, canon, source.strip())
    entry = store["symbols"][sym]
    entry["delisted"] = bool(delisted or entry.get("delisted"))
    if note:
        entry["note"] = note
    save_store(store, archive_path)
    return added
