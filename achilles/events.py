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


def analyze_concurrent_items(labels: list[str], body_text: str, filing_items: str = "") -> dict:
    """Analyze concurrent 8-K items filed alongside an earnings reaction.

    When item 2.02 (earnings) appears with other items in the same 8-K,
    those concurrent signals modify the earnings event:
      - Guidance raised (7.01/8.01 + raised language) → strength boost
      - Guidance lowered/withdrawn → disqualifier
      - Restructuring (item 2.05/2.06) → disqualifier (kitchen-sink quarter)
      - M&A activity (item 2.01) → neutral (separate event)

    Returns {concurrent_boost: float, disqualifiers: list[str], items: list[str]}
    """
    result: dict = {"concurrent_boost": 1.0, "disqualifiers": [], "items": labels[:]}

    has_earnings = "earnings_reaction" in labels
    if not has_earnings:
        return result

    has_guidance = "guidance_revision" in labels
    if has_guidance and body_text:
        direction = guidance_direction(body_text)
        if direction == "raised":
            result["concurrent_boost"] = 1.2
            result["concurrent_guidance"] = "raised"
        elif direction == "lowered":
            result["disqualifiers"].append("concurrent_guidance_lowered")
            result["concurrent_guidance"] = "lowered"
        elif direction == "withdrawn":
            result["disqualifiers"].append("guidance_withdrawn")
            result["concurrent_guidance"] = "withdrawn"

    # Check raw 8-K items for restructuring signals
    # Items 2.05 (costs of exit/disposal) and 2.06 (material impairments)
    # signal a "kitchen-sink quarter" — dump all bad news with earnings
    if filing_items:
        from shared.edgar import parse_items
        raw_items = parse_items(filing_items)
        if "2.05" in raw_items or "2.06" in raw_items:
            result["disqualifiers"].append("concurrent_restructuring")

    return result


def build_event_for_filing(
    filing,
    *,
    body_text: str = "",
    today: str = "",
    surprise_pct: Optional[float] = None,
    earnings_surprise: Optional[object] = None,
    insider_boost: float = 1.0,
) -> list[Event]:
    """For non-cluster classes, build Event(s) directly from filing + optional body.

    For earnings_reaction events, pass surprise_pct (EPS surprise %) to scale
    event strength via the surprise curve. If None, strength defaults to 1.0.

    earnings_surprise: an EarningsSurprise dataclass. If provided and it's
      not a beat, earnings_reaction events are suppressed entirely.

    insider_boost: multiplier from pre-earnings insider cross-reference.
      Applied only to earnings_reaction events. Default 1.0 (no boost).
    """
    labels = classify_filing(filing)
    out: list[Event] = []

    # Analyze concurrent 8-K items for compound signals
    filing_items = getattr(filing, 'items', '') or ''
    concurrent = analyze_concurrent_items(labels, body_text, filing_items=filing_items)

    for lbl in labels:
        if lbl == "earnings_reaction":
            # If we have actual earnings data, only proceed on beats
            if earnings_surprise is not None:
                if not getattr(earnings_surprise, 'is_beat', False):
                    continue
                if surprise_pct is None:
                    surprise_pct = getattr(earnings_surprise, 'surprise_pct', None)

            strength = surprise_strength(surprise_pct)

            # Apply concurrent item boost (guidance raised in same 8-K)
            strength *= concurrent["concurrent_boost"]

            # Apply insider pre-earnings boost
            strength *= insider_boost

            # Cap at 1.5 — don't let compound signals overwhelm the model
            strength = min(1.5, strength)

            metadata = {
                "surprise_pct": surprise_pct,
                "insider_boost": insider_boost,
            }
            if concurrent["concurrent_boost"] != 1.0:
                metadata["concurrent_boost"] = concurrent["concurrent_boost"]
                metadata["concurrent_guidance"] = concurrent.get("concurrent_guidance", "")
            if concurrent["disqualifiers"]:
                metadata["disqualifiers"] = concurrent["disqualifiers"]

            out.append(Event(
                event_id=f"earn:{filing.symbol}:{filing.accession_no}",
                event_class="earnings_reaction",
                symbol=filing.symbol or "",
                filing_date=filing.filing_date,
                accession_no=filing.accession_no,
                strength=strength,
                metadata=metadata,
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
            # Skip standalone guidance events when already accounted for
            # as a concurrent boost on earnings
            if "earnings_reaction" in labels and concurrent["concurrent_boost"] != 1.0:
                continue
            ev = refine_guidance(filing, body_text)
            if ev:
                out.append(ev)
        elif lbl == "spinoff_window_candidate":
            ev = refine_spinoff(filing, body_text, today=today)
            if ev:
                out.append(ev)
    return out
