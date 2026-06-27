"""Form 4 insider transaction parsing and cluster signal.

A "cluster buy" requires at least 2 distinct corporate insiders making
open-market buys of at least $10,000 each within a 2-day window.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Callable, Iterable, Optional


@dataclass
class InsiderTxn:
    symbol: str
    insider_name: str
    insider_title: str
    transaction_code: str  # "P" = open-market buy, "S" = sale
    transaction_date: str  # YYYY-MM-DD
    shares: float
    price: float
    dollars: float
    accession_no: str = ""

    @property
    def is_open_market_buy(self) -> bool:
        return self.transaction_code == "P" and self.shares > 0 and self.price > 0


def parse_form4(xml_text: str, *, accession_no: str = "") -> list[InsiderTxn]:
    """Parse a Form 4 XML body and return its non-derivative transactions.

    Robust to namespace variations and missing fields.
    """
    out: list[InsiderTxn] = []
    if not xml_text or "<" not in xml_text:
        return out
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out

    def find_text(node, path) -> str:
        if node is None:
            return ""
        el = node.find(path)
        if el is None:
            return ""
        # XBRL values often nested as <value>X</value>
        v = el.find("value")
        text = (v.text if v is not None else el.text) or ""
        return text.strip()

    symbol = find_text(root, ".//issuerTradingSymbol").upper()

    owner = root.find(".//reportingOwner")
    name = find_text(owner, "./reportingOwnerId/rptOwnerName") if owner is not None else ""
    rel = owner.find("./reportingOwnerRelationship") if owner is not None else None
    title_parts: list[str] = []
    if rel is not None:
        for tag in ("officerTitle", "isDirector", "isOfficer", "isTenPercentOwner"):
            t = find_text(rel, f"./{tag}")
            if tag == "officerTitle" and t:
                title_parts.append(t)
            elif t in ("1", "true"):
                title_parts.append(tag.replace("is", ""))
    title = ", ".join(p for p in title_parts if p)

    for tx in root.findall(".//nonDerivativeTransaction"):
        code = find_text(tx, "./transactionCoding/transactionCode")
        tdate = find_text(tx, "./transactionDate")
        shares_s = find_text(tx, "./transactionAmounts/transactionShares") or "0"
        price_s = find_text(tx, "./transactionAmounts/transactionPricePerShare") or "0"
        try:
            shares = float(shares_s)
            price = float(price_s)
        except ValueError:
            continue
        dollars = shares * price
        out.append(
            InsiderTxn(
                symbol=symbol,
                insider_name=name,
                insider_title=title,
                transaction_code=code,
                transaction_date=tdate,
                shares=shares,
                price=price,
                dollars=dollars,
                accession_no=accession_no,
            )
        )
    return out


# ------- Cluster signal -------

def cluster_signal(
    txns: Iterable[InsiderTxn],
    *,
    min_distinct: int = 2,
    min_dollars: float = 10_000.0,
    window_days: int = 2,
) -> Optional[dict]:
    """Return a cluster summary if the rules are met, else None.

    Rules:
      - >= `min_distinct` distinct insider names
      - each insider's open-market buys (code P) summing to >= `min_dollars`
      - all transactions within a `window_days`-day window
    """
    buys = [t for t in txns if t.is_open_market_buy and t.dollars >= 0]
    if not buys:
        return None
    # group by name, sum dollars
    by_name: dict[str, list[InsiderTxn]] = {}
    for t in buys:
        if t.dollars < 0:
            continue
        by_name.setdefault(t.insider_name, []).append(t)

    qualified: dict[str, list[InsiderTxn]] = {}
    for name, ts in by_name.items():
        total = sum(t.dollars for t in ts)
        if total >= min_dollars:
            qualified[name] = ts

    if len(qualified) < min_distinct:
        return None

    # Check the window: earliest and latest transaction across qualified insiders
    all_dates = []
    for ts in qualified.values():
        for t in ts:
            try:
                all_dates.append(datetime.strptime(t.transaction_date, "%Y-%m-%d").date())
            except ValueError:
                continue
    if not all_dates:
        return None
    span = (max(all_dates) - min(all_dates)).days
    if span > window_days:
        # Slide a window across the sorted dates: any contiguous group of
        # `min_distinct` insiders within `window_days` qualifies.
        sorted_dates = sorted(all_dates)
        ok = False
        for i in range(len(sorted_dates)):
            window_end = sorted_dates[i] + timedelta(days=window_days)
            insiders_in_window = set()
            for name, ts in qualified.items():
                for t in ts:
                    try:
                        td = datetime.strptime(t.transaction_date, "%Y-%m-%d").date()
                    except ValueError:
                        continue
                    if sorted_dates[i] <= td <= window_end:
                        insiders_in_window.add(name)
                        break
            if len(insiders_in_window) >= min_distinct:
                ok = True
                break
        if not ok:
            return None

    symbols = {t.symbol for t in buys if t.symbol}
    symbol = next(iter(symbols)) if symbols else ""
    total_dollars = sum(sum(t.dollars for t in ts) for ts in qualified.values())
    return {
        "symbol": symbol,
        "insider_count": len(qualified),
        "insiders": sorted(qualified.keys()),
        "total_dollars": total_dollars,
        "earliest_date": min(all_dates).isoformat(),
        "latest_date": max(all_dates).isoformat(),
    }


# ------- Universe scan -------

def scan_universe(
    symbols: list[str],
    fetcher: Callable[[str], list[InsiderTxn]],
    *,
    max_workers: int = 6,
    checkpoint_every: int = 200,
    on_checkpoint: Optional[Callable[[int, list[dict]], None]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> list[dict]:
    """Scan a universe of symbols for cluster buy signals.

    `fetcher(symbol)` returns the symbol's recent Form 4 transactions.
    Threaded across `max_workers`. Checkpoints every `checkpoint_every` symbols.
    """
    clusters: list[dict] = []
    done = 0
    total = len(symbols)
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futs = {exe.submit(fetcher, s): s for s in symbols}
        for fut in as_completed(futs):
            sym = futs[fut]
            try:
                txns = fut.result()
            except Exception:
                txns = []
            sig = cluster_signal(txns)
            if sig:
                if not sig.get("symbol"):
                    sig["symbol"] = sym
                clusters.append(sig)
            done += 1
            if on_progress:
                on_progress(done, total)
            if checkpoint_every > 0 and done % checkpoint_every == 0 and on_checkpoint:
                on_checkpoint(done, list(clusters))
    return clusters
