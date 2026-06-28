"""XBRL fundamentals helpers.

This module exposes pure helpers over XBRL unit lists (quarterly, annual,
latest instant, TTM, YoY) plus a FundamentalSnapshot dataclass with ~18
fields and a data-quality scorer that grades from data rather than memory.

A 30-day TTL snapshot cache is provided with stale-fallback on fetch failure.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Optional


# ------- XBRL unit helpers -------
#
# An XBRL "unit" entry typically looks like:
#   {"start": "2023-01-01", "end": "2023-03-31", "val": 12345, "fp": "Q1",
#    "fy": 2023, "form": "10-Q", "filed": "2023-04-25"}
# For instant facts (assets, equity), only "end" is set.

def _is_quarterly(u: dict) -> bool:
    """Heuristic: a fact whose start/end span ~90 days and form != 10-K."""
    s = u.get("start")
    e = u.get("end")
    if not s or not e:
        return False
    try:
        ds = datetime.strptime(s, "%Y-%m-%d").date()
        de = datetime.strptime(e, "%Y-%m-%d").date()
    except ValueError:
        return False
    span = (de - ds).days
    return 80 <= span <= 100 and (u.get("form", "") != "10-K")


def _is_annual(u: dict) -> bool:
    s = u.get("start")
    e = u.get("end")
    if not s or not e:
        return False
    try:
        ds = datetime.strptime(s, "%Y-%m-%d").date()
        de = datetime.strptime(e, "%Y-%m-%d").date()
    except ValueError:
        return False
    span = (de - ds).days
    return 350 <= span <= 380


def quarterly(units: list[dict]) -> list[dict]:
    """Return only quarterly entries, sorted by end date ascending."""
    qs = [u for u in units if _is_quarterly(u)]
    qs.sort(key=lambda u: u.get("end", ""))
    return qs


def annual(units: list[dict]) -> list[dict]:
    """Return only annual entries, sorted by end date ascending."""
    ans = [u for u in units if _is_annual(u)]
    ans.sort(key=lambda u: u.get("end", ""))
    return ans


def latest_instant(units: list[dict]) -> Optional[dict]:
    """Most recent instant fact (end date only, no span)."""
    instants = [u for u in units if u.get("end") and not u.get("start")]
    if not instants:
        return None
    instants.sort(key=lambda u: u.get("end", ""))
    return instants[-1]


def ttm(units: list[dict]) -> Optional[float]:
    """Trailing-twelve-month sum from the 4 most recent unique quarterly entries.

    Returns None when fewer than 4 quarters of data are available.
    """
    qs = quarterly(units)
    # Dedup by end-date (keep the latest filed for a given end)
    by_end: dict[str, dict] = {}
    for u in qs:
        end = u.get("end")
        if not end:
            continue
        prev = by_end.get(end)
        if not prev or u.get("filed", "") > prev.get("filed", ""):
            by_end[end] = u
    sorted_ends = sorted(by_end.keys())
    if len(sorted_ends) < 4:
        return None
    last_four = sorted_ends[-4:]
    return float(sum(by_end[e].get("val", 0) for e in last_four))


def yoy(units: list[dict]) -> Optional[float]:
    """Year-over-year growth of TTM. Returns None if insufficient data."""
    qs = quarterly(units)
    by_end: dict[str, dict] = {}
    for u in qs:
        end = u.get("end")
        if not end:
            continue
        prev = by_end.get(end)
        if not prev or u.get("filed", "") > prev.get("filed", ""):
            by_end[end] = u
    ends = sorted(by_end.keys())
    if len(ends) < 8:
        return None
    cur = sum(by_end[e].get("val", 0) for e in ends[-4:])
    prior = sum(by_end[e].get("val", 0) for e in ends[-8:-4])
    if prior <= 0:
        return None
    return float(cur - prior) / float(prior)


# ------- Snapshot -------

@dataclass
class FundamentalSnapshot:
    symbol: str
    fetched_at: str = ""
    revenue_ttm: Optional[float] = None
    revenue_yoy: Optional[float] = None
    net_income_ttm: Optional[float] = None
    net_income_yoy: Optional[float] = None
    ocf_ttm: Optional[float] = None
    capex_ttm: Optional[float] = None
    free_cash_flow_ttm: Optional[float] = None
    sbc_ttm: Optional[float] = None  # stock-based compensation
    cash_and_equiv: Optional[float] = None
    debt_total: Optional[float] = None
    equity: Optional[float] = None
    shares_diluted: Optional[float] = None
    shares_basic: Optional[float] = None
    dilution_yoy: Optional[float] = None
    cash_runway_quarters: Optional[float] = None
    gross_margin_ttm: Optional[float] = None
    operating_margin_ttm: Optional[float] = None
    data_quality: float = 0.0


def build_snapshot(symbol: str, facts: dict) -> FundamentalSnapshot:
    """Build a snapshot from an XBRL facts dict.

    `facts` shape: {concept_name: {"units": {"USD": [unit, ...]}}, ...}

    Missing facts leave the corresponding field at None; data_quality
    decreases proportionally.
    """
    def units(concept: str, unit: str = "USD") -> list[dict]:
        c = facts.get(concept) or {}
        u = (c.get("units") or {}).get(unit) or []
        return list(u)

    def units_any(*concepts: str, unit: str = "USD") -> list[dict]:
        for c in concepts:
            us = units(c, unit)
            if us:
                return us
        return []

    snap = FundamentalSnapshot(symbol=symbol, fetched_at=datetime.utcnow().isoformat())

    snap.revenue_ttm = ttm(units_any("Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"))
    snap.revenue_yoy = yoy(units_any("Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"))
    snap.net_income_ttm = ttm(units("NetIncomeLoss"))
    snap.net_income_yoy = yoy(units("NetIncomeLoss"))
    snap.ocf_ttm = ttm(units("NetCashProvidedByUsedInOperatingActivities"))
    snap.capex_ttm = ttm(units_any("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"))
    if snap.ocf_ttm is not None and snap.capex_ttm is not None:
        snap.free_cash_flow_ttm = snap.ocf_ttm - snap.capex_ttm
    snap.sbc_ttm = ttm(units("ShareBasedCompensation"))

    cash_unit = latest_instant(units_any("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"))
    snap.cash_and_equiv = cash_unit.get("val") if cash_unit else None
    debt_unit = latest_instant(units_any("LongTermDebt", "LongTermDebtNoncurrent"))
    snap.debt_total = debt_unit.get("val") if debt_unit else None
    eq_unit = latest_instant(units_any("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"))
    snap.equity = eq_unit.get("val") if eq_unit else None

    sd = units_any("WeightedAverageNumberOfDilutedSharesOutstanding", unit="shares")
    sb = units_any("WeightedAverageNumberOfSharesOutstandingBasic", unit="shares")
    if sd:
        last = sd[-1]
        snap.shares_diluted = last.get("val")
    if sb:
        snap.shares_basic = sb[-1].get("val")
    if len(sd) >= 5:
        recent = sd[-1].get("val", 0)
        prior = sd[-5].get("val", 0)
        if prior:
            snap.dilution_yoy = (recent - prior) / abs(prior)

    if snap.cash_and_equiv is not None and snap.ocf_ttm is not None and snap.ocf_ttm < 0:
        burn_per_quarter = -snap.ocf_ttm / 4
        if burn_per_quarter > 0:
            snap.cash_runway_quarters = snap.cash_and_equiv / burn_per_quarter

    cogs_ttm = ttm(units_any("CostOfGoodsAndServicesSold", "CostOfRevenue"))
    if snap.revenue_ttm and cogs_ttm is not None:
        snap.gross_margin_ttm = (snap.revenue_ttm - cogs_ttm) / snap.revenue_ttm
    op_inc = ttm(units("OperatingIncomeLoss"))
    if snap.revenue_ttm and op_inc is not None:
        snap.operating_margin_ttm = op_inc / snap.revenue_ttm

    snap.data_quality = score_data_quality(snap)
    return snap


def score_data_quality(snap: FundamentalSnapshot) -> float:
    """Score 0..1 based on how many critical fields are populated.

    Grading from data, not from memory: we count what's actually filled.
    """
    critical = [
        "revenue_ttm", "net_income_ttm", "ocf_ttm", "cash_and_equiv",
        "equity", "shares_diluted",
    ]
    secondary = [
        "revenue_yoy", "free_cash_flow_ttm", "sbc_ttm", "debt_total",
        "gross_margin_ttm", "operating_margin_ttm", "dilution_yoy",
    ]
    crit_hits = sum(1 for k in critical if getattr(snap, k) is not None)
    sec_hits = sum(1 for k in secondary if getattr(snap, k) is not None)
    return 0.6 * (crit_hits / len(critical)) + 0.4 * (sec_hits / len(secondary))


# ------- Cache -------

_CACHE_TTL_DAYS = 30


def cache_path(cache_dir: str, symbol: str) -> str:
    return os.path.join(cache_dir, f"snapshot_{symbol.upper()}.json")


def load_cached_snapshot(cache_dir: str, symbol: str, ttl_days: int = _CACHE_TTL_DAYS) -> Optional[FundamentalSnapshot]:
    p = cache_path(cache_dir, symbol)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            d = json.load(f)
        fetched = d.get("fetched_at", "")
        if fetched:
            try:
                ts = datetime.fromisoformat(fetched)
                if datetime.utcnow() - ts > timedelta(days=ttl_days):
                    return None
            except ValueError:
                pass
        return FundamentalSnapshot(**d)
    except (json.JSONDecodeError, TypeError):
        return None


def save_cached_snapshot(cache_dir: str, snap: FundamentalSnapshot) -> None:
    os.makedirs(cache_dir, exist_ok=True)
    p = cache_path(cache_dir, snap.symbol)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(asdict(snap), f, indent=2, sort_keys=True)
    os.replace(tmp, p)


def load_stale(cache_dir: str, symbol: str) -> Optional[FundamentalSnapshot]:
    """Load even if stale. Use as a fallback when fresh fetch fails."""
    p = cache_path(cache_dir, symbol)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return FundamentalSnapshot(**json.load(f))
    except (json.JSONDecodeError, TypeError):
        return None
