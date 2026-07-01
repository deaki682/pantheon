"""The catalyst calendar — the load-bearing spine (Phase 1).

Over a five-trading-day window the only durable edge is a scheduled or
forecastable event. This module normalizes heterogeneous event sources
(earnings today; FDA / econ / index-rebalance / lockup connectors later)
into one clean table for the coming week.

Pure stdlib, data passed in. The /catalyst skill does the MCP fetching and
hands raw rows to these functions — same fetch-then-compute split the gods use.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

# Roughly in order of tractability over a weekly horizon.
EVENT_TYPES = {
    "earnings",
    "fda",          # PDUFA / clinical readout — binary, date-known
    "econ",         # CPI / FOMC / jobs / PCE — market-wide re-rating
    "index_rebal",  # S&P / Russell — forced mechanical flow
    "lockup",       # post-IPO supply shock
    "ex_div",
    "buyback",
    "other",
}


def next_week_window(today: Optional[date] = None, days: int = 7) -> tuple[date, date]:
    """The coming week: [today, today+days]."""
    today = today or date.today()
    return today, today + timedelta(days=days)


def _parse_date(d) -> Optional[date]:
    if isinstance(d, date) and not isinstance(d, datetime):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        try:
            return datetime.strptime(d[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _flt(x) -> Optional[float]:
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def make_event(
    *,
    ticker: str,
    event_type: str,
    event_date,
    timing: str = "",
    is_binary: bool = False,
    consensus: Optional[dict] = None,
    source: str = "",
    confidence: float = 0.5,
    today: Optional[date] = None,
    **extra,
) -> dict:
    """Normalize one catalyst to the canonical row schema.

    expected_priced_move_pct starts None and is filled in by the expectations
    overlay once options data is attached.
    """
    today = today or date.today()
    d = _parse_date(event_date)
    ev = {
        "ticker": ticker.upper(),
        "event_type": event_type if event_type in EVENT_TYPES else "other",
        "event_date": d.isoformat() if d else None,
        "timing": timing,  # 'am' | 'pm' | ''
        "days_until": (d - today).days if d else None,
        "is_binary": bool(is_binary),
        "expected_priced_move_pct": None,
        "consensus": consensus or {},
        "source": source,
        "confidence": float(confidence),
    }
    ev.update(extra)
    return ev


def normalize_earnings(rows, *, today: Optional[date] = None) -> list[dict]:
    """Robinhood get_earnings_calendar rows -> normalized earnings events.

    - Dedups on (symbol, report.date) — the feed occasionally double-lists.
    - Skips reports that already happened (eps.actual populated): a resolved
      print is history, not a forecastable catalyst.
    - confidence tracks report.verified (tentative dates are downweighted).
    """
    today = today or date.today()
    seen: set = set()
    out: list[dict] = []
    for r in rows or []:
        sym = (r.get("symbol") or "").upper()
        rep = r.get("report") or {}
        d = rep.get("date")
        if not sym or not d:
            continue
        key = (sym, d)
        if key in seen:
            continue
        seen.add(key)
        eps = r.get("eps") or {}
        if eps.get("actual") not in (None, ""):
            continue  # already reported
        out.append(
            make_event(
                ticker=sym,
                event_type="earnings",
                event_date=d,
                timing=rep.get("timing", ""),
                is_binary=True,
                consensus={"eps_est": _flt(eps.get("estimate"))},
                source="robinhood:earnings_calendar",
                confidence=0.9 if rep.get("verified") else 0.5,
                today=today,
                verified=bool(rep.get("verified")),
            )
        )
    return out


def build_calendar(*event_lists, start: Optional[date] = None, end: Optional[date] = None) -> list[dict]:
    """Merge event lists, clip to [start, end] if given, and sort for review.

    Sort: soonest first, then higher confidence, then ticker. This is an
    ordering for a human to scan — NOT a predictive ranking (that's a later,
    deliberately-unbuilt phase).
    """
    events = [e for lst in event_lists for e in (lst or [])]
    if start and end:
        lo, hi = start.isoformat(), end.isoformat()
        events = [e for e in events if e["event_date"] and lo <= e["event_date"] <= hi]
    events.sort(
        key=lambda e: (
            e["days_until"] if e["days_until"] is not None else 999,
            -e["confidence"],
            e["ticker"],
        )
    )
    return events
