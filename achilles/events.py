"""Event refinement and aggregation.

Some filings can't be classified at the filing level alone:
  - Form 4: a single insider buy is a candidate; the cluster check requires
    aggregation across multiple insiders within a 2-day window.
  - Guidance 8-Ks: items 7.01/8.01 need a body read to determine direction.
    Reaffirmations are dropped.
  - Spinoff 10-12B: need ex-date extraction to confirm we're in the trading
    window (-7 to +21 days).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Optional

from shared.edgar import extract_ex_date, guidance_direction
from shared.insiders import InsiderTxn, cluster_signal

from .classify import classify_filing
from .scoring import surprise_strength


SPINOFF_PRE_DAYS = 7
SPINOFF_POST_DAYS = 21


@dataclass
class Event:
    event_id: str
    event_class: str
    symbol: str
    filing_date: str
    accession_no: str
    strength: float = 1.0  # per-class quality of evidence (0..1)
    metadata: dict = field(default_factory=dict)


def aggregate_insider_clusters(txns: Iterable[InsiderTxn]) -> list[Event]:
    """Group Form 4 buys by symbol and emit a cluster Event per qualifying symbol."""
    by_symbol: dict[str, list[InsiderTxn]] = {}
    for t in txns:
        if not t.symbol:
            continue
        by_symbol.setdefault(t.symbol.upper(), []).append(t)
    out: list[Event] = []
    for sym, group in by_symbol.items():
        sig = cluster_signal(group)
        if not sig:
            continue
        # Use the latest accession in the cluster as event id stem
        latest = max(group, key=lambda t: t.transaction_date)
        # Strength scales with insider count (capped at 1.0 by 4+ insiders).
        strength = min(1.0, sig["insider_count"] / 4.0)
        out.append(Event(
            event_id=f"cluster:{sym}:{sig['latest_date']}",
            event_class="insider_cluster",
            symbol=sym,
            filing_date=sig["latest_date"],
            accession_no=latest.accession_no or "",
            strength=strength,
            metadata=sig,
        ))
    return out


def refine_guidance(filing, body_text: str) -> Optional[Event]:
    direction = guidance_direction(body_text or "")
    if direction in ("reaffirmed", "unknown"):
        return None
    strength = {"raised": 1.0, "lowered": 0.8, "withdrawn": 0.6}[direction]
    return Event(
        event_id=f"guidance:{filing.symbol}:{filing.accession_no}",
        event_class="guidance_revision",
        symbol=filing.symbol or "",
        filing_date=filing.filing_date,
        accession_no=filing.accession_no,
        strength=strength,
        metadata={"direction": direction},
    )


def refine_spinoff(filing, body_text: str, *, today: str) -> Optional[Event]:
    ex_date = extract_ex_date(body_text or "")
    if not ex_date:
        return None
    try:
        ex_dt = datetime.strptime(ex_date, "%Y-%m-%d").date()
        td_dt = datetime.strptime(today, "%Y-%m-%d").date()
    except ValueError:
        return None
    delta_days = (ex_dt - td_dt).days
    if delta_days < -SPINOFF_POST_DAYS or delta_days > SPINOFF_PRE_DAYS:
        # Outside trading window
        return None
    return Event(
        event_id=f"spinoff:{filing.symbol}:{filing.accession_no}",
        event_class="spinoff_window",
        symbol=filing.symbol or "",
        filing_date=filing.filing_date,
        accession_no=filing.accession_no,
        strength=0.8,
        metadata={"ex_date": ex_date, "delta_days": delta_days},
    )


def build_event_for_filing(
    filing,
    *,
    body_text: str = "",
    today: str = "",
    surprise_pct: Optional[float] = None,
) -> list[Event]:
    """For non-cluster classes, build Event(s) directly from filing + optional body.

    For earnings_reaction events, pass surprise_pct (EPS surprise %) to scale
    event strength via the surprise curve. If None, strength defaults to 1.0.
    """
    labels = classify_filing(filing)
    out: list[Event] = []
    for lbl in labels:
        if lbl == "earnings_reaction":
            strength = surprise_strength(surprise_pct)
            out.append(Event(
                event_id=f"earn:{filing.symbol}:{filing.accession_no}",
                event_class="earnings_reaction",
                symbol=filing.symbol or "",
                filing_date=filing.filing_date,
                accession_no=filing.accession_no,
                strength=strength,
                metadata={"surprise_pct": surprise_pct},
            ))
        elif lbl == "activist_13d":
            out.append(Event(
                event_id=f"13d:{filing.symbol}:{filing.accession_no}",
                event_class="activist_13d",
                symbol=filing.symbol or "",
                filing_date=filing.filing_date,
                accession_no=filing.accession_no,
                strength=1.0,
            ))
        elif lbl == "ma_target":
            out.append(Event(
                event_id=f"ma:{filing.symbol}:{filing.accession_no}",
                event_class="ma_target",
                symbol=filing.symbol or "",
                filing_date=filing.filing_date,
                accession_no=filing.accession_no,
                strength=1.0,
            ))
        elif lbl == "guidance_revision":
            ev = refine_guidance(filing, body_text)
            if ev:
                out.append(ev)
        elif lbl == "spinoff_window_candidate":
            ev = refine_spinoff(filing, body_text, today=today)
            if ev:
                out.append(ev)
    return out
