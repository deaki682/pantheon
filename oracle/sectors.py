"""Sector mapping helper.

Map a symbol to its 11-sector GICS-style bucket. The actual lookup happens
via the broker (Robinhood fundamentals) at runtime; this module provides
the canonical sector list and a fallback heuristic.
"""
from __future__ import annotations


SECTORS = (
    "technology",
    "financials",
    "energy",
    "healthcare",
    "industrials",
    "staples",
    "discretionary",
    "utilities",
    "real_estate",
    "materials",
    "communication",
)


def normalize_sector(raw: str) -> str:
    """Normalize a free-form sector string to the canonical lowercase form."""
    if not raw:
        return ""
    s = raw.lower().replace("-", " ").replace("_", " ").strip()
    mapping = {
        "technology": "technology",
        "information technology": "technology",
        "tech": "technology",
        "financial services": "financials",
        "financial": "financials",
        "financials": "financials",
        "banks": "financials",
        "energy": "energy",
        "health care": "healthcare",
        "healthcare": "healthcare",
        "industrials": "industrials",
        "industrial": "industrials",
        "consumer staples": "staples",
        "consumer defensive": "staples",
        "consumer discretionary": "discretionary",
        "consumer cyclical": "discretionary",
        "utilities": "utilities",
        "utility": "utilities",
        "real estate": "real_estate",
        "reits": "real_estate",
        "basic materials": "materials",
        "materials": "materials",
        "communication services": "communication",
        "communications": "communication",
    }
    return mapping.get(s, s.replace(" ", "_"))


def sector_breadth(prices: dict[str, dict[str, float]]) -> float:
    """Fraction of sectors with non-negative momentum.

    `prices` shape: {sector: {"now": x, "then": y}} (e.g. 3-month look-back).
    """
    if not prices:
        return 0.0
    positive = 0
    valid = 0
    for sec, d in prices.items():
        then = d.get("then")
        now = d.get("now")
        # Prices are positive by definition; non-positive/missing values mean
        # corrupt data with undefined momentum — skip rather than let a negative
        # `then` flip the sign of the ratio.
        if then is None or now is None or then <= 0 or now <= 0:
            continue
        valid += 1
        if now / then - 1.0 >= 0:
            positive += 1
    return positive / valid if valid else 0.0
