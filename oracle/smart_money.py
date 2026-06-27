"""13F holdings and 13D activist filings parsing.

13F: quarterly disclosure of holdings by institutional managers > $100M AUM.
13D: filed when an investor acquires > 5% of a public company with intent
to influence (i.e. activist). 13G is the passive variant. We track 13D
"fresh" filings (NOT amendments).
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable


# Curated smart-money managers (well-known long-horizon funds whose holdings
# we want to track). The list is intentionally short — quality over coverage.
SMART_MONEY_FUNDS = {
    "BERKSHIRE HATHAWAY",
    "BAUPOST GROUP",
    "PERSHING SQUARE",
    "GREENLIGHT CAPITAL",
    "OAKMARK",
    "TWEEDY BROWNE",
    "RUANE CUNNIFF",
    "FIRST EAGLE",
    "WEDGEWOOD",
    "AKRE CAPITAL",
}


@dataclass
class Holding:
    symbol: str
    cusip: str
    shares: float
    value: float
    manager: str = ""


def parse_13f_information_table(xml_text: str, *, manager: str = "") -> list[Holding]:
    """Parse a 13F-HR information table XML into a list of Holdings.

    Robust to namespace prefixes.
    """
    out: list[Holding] = []
    if not xml_text or "<" not in xml_text:
        return out
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out

    for info in root.iter():
        if not info.tag.endswith("infoTable"):
            continue
        name_el = next((c for c in info if c.tag.endswith("nameOfIssuer")), None)
        cusip_el = next((c for c in info if c.tag.endswith("cusip")), None)
        value_el = next((c for c in info if c.tag.endswith("value")), None)
        shrs_el = next((c for c in info if c.tag.endswith("shrsOrPrnAmt")), None)
        shares = 0.0
        if shrs_el is not None:
            n = next((c for c in shrs_el if c.tag.endswith("sshPrnamt")), None)
            try:
                shares = float(n.text) if n is not None and n.text else 0.0
            except ValueError:
                shares = 0.0
        try:
            value = float(value_el.text) if value_el is not None and value_el.text else 0.0
        except ValueError:
            value = 0.0
        out.append(
            Holding(
                symbol=(name_el.text or "").strip().upper() if name_el is not None else "",
                cusip=(cusip_el.text or "").strip() if cusip_el is not None else "",
                shares=shares,
                value=value,
                manager=manager,
            )
        )
    return out


def smart_money_holders(holdings_by_manager: dict[str, list[Holding]]) -> dict[str, list[str]]:
    """Group holdings by symbol -> list of smart-money managers holding it.

    Only counts managers in SMART_MONEY_FUNDS.
    """
    out: dict[str, list[str]] = {}
    for manager, hs in holdings_by_manager.items():
        m = manager.upper()
        if not any(name in m for name in SMART_MONEY_FUNDS):
            continue
        for h in hs:
            if not h.symbol or h.shares <= 0:
                continue
            out.setdefault(h.symbol, []).append(manager)
    return out


# 13D activist parsing — much simpler: we just want fresh filings.

def is_fresh_13d(form: str) -> bool:
    """Returns True for SC 13D (not amendments)."""
    f = (form or "").strip().upper()
    return f == "SC 13D" or f == "13D"


def activist_signal(filings: Iterable) -> list[str]:
    """Given an iterable of Filing objects, return symbols with fresh 13D filings."""
    out: list[str] = []
    for f in filings:
        form = getattr(f, "form", "")
        if is_fresh_13d(form):
            sym = getattr(f, "symbol", "") or ""
            if sym:
                out.append(sym.upper())
    return list(dict.fromkeys(out))  # dedup, preserve order
