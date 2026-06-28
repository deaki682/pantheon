"""Dossier creation and scoring.

A dossier is built from filings + fundamentals. The LLM-driven content
(thesis paragraph, scenario probabilities) is provided by the caller —
this module handles structure, derived math, and persistence.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .dossier_check import validate_dossier
from .positioning import compute_derived, potential_to_conviction


def make_dossier(
    symbol: str,
    *,
    business: str,
    thesis: str,
    scenarios: dict[str, dict],
    ratings: dict[str, float],
    citations: list[str],
    horizon_years: float = 2.0,
    current_price: float = 0.0,
    sector: str = "",
    author: str = "oracle",
    high_52w: float = 0.0,
    decline_explanation: str = "",
) -> dict[str, Any]:
    """Build, validate, and return a dossier with derived fields filled in.

    `high_52w` + `decline_explanation` feed the falling-knife gate: a name down
    >30% from its 52-week high must explain the decline or validation fails.
    """
    now = datetime.utcnow().isoformat()
    d: dict[str, Any] = {
        "symbol": symbol.upper(),
        "business": business,
        "thesis": thesis,
        "scenarios": scenarios,
        "ratings": ratings,
        "citations": list(citations),
        "horizon_years": float(horizon_years),
        "current_price": float(current_price),
        "high_52w": float(high_52w),
        "decline_explanation": decline_explanation,
        "sector": sector,
        "author": author,
        "created_at": now,
        # priced_at records WHEN current_price was captured, separate from
        # created_at. A rebalance that rewrites scenarios without re-pulling
        # quotes leaves priced_at stale — the gap is the audit trail.
        "priced_at": now if current_price > 0 else None,
        # scenario_price records what price the scenarios were anchored to.
        # rescore updates current_price but leaves scenario_price alone —
        # the gap between the two is real price drift since the thesis was written.
        "scenario_price": float(current_price) if current_price > 0 else None,
    }
    validate_dossier(d)
    derived = compute_derived(d, current_price=current_price, horizon_years=horizon_years)
    d["derived"] = derived
    d["conviction"] = potential_to_conviction(derived["potential_score"])
    return d


def rescore_dossier(d: dict[str, Any], *, current_price: float) -> dict[str, Any]:
    """Recompute derived metrics + conviction at a new price.

    Always refreshes `priced_at` — the contract is that current_price and
    priced_at move together so a reader can never mistake a stale price for fresh.
    """
    # compute_derived assumes a well-formed dossier (scenarios + ratings). Unlike
    # build_dossier, rescore receives an existing dossier that could have been
    # loaded from disk or hand-edited — validate so a malformed one raises a clear
    # DossierError instead of a cryptic KeyError deep in the math.
    d["current_price"] = float(current_price)
    d["priced_at"] = datetime.utcnow().isoformat()
    validate_dossier(d)
    derived = compute_derived(d, current_price=current_price, horizon_years=d.get("horizon_years", 2.0))
    d["derived"] = derived
    d["conviction"] = potential_to_conviction(derived["potential_score"])
    return d


def update_scenarios(
    d: dict[str, Any],
    scenarios: dict[str, dict],
    *,
    current_price: float,
) -> dict[str, Any]:
    """Rewrite a dossier's scenarios (e.g. balanced/adversarial reframing).

    REQUIRES a fresh `current_price` — the whole point is that thesis and price
    move together. A rebalance pass that changes the thesis but reuses a stale
    price is exactly the failure mode this helper exists to prevent.
    """
    d["scenarios"] = scenarios
    d["scenario_price"] = float(current_price)
    return rescore_dossier(d, current_price=current_price)


def save_dossiers(path: str, dossiers: list[dict]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"dossiers": dossiers, "saved_at": datetime.utcnow().isoformat()}, f, indent=2)
    os.replace(tmp, path)


def load_dossiers(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        d = json.load(f)
    return d.get("dossiers", [])


def rank(dossiers: list[dict]) -> list[dict]:
    """Sort by potential_score descending."""
    def k(d):
        return d.get("derived", {}).get("potential_score", 0.0)
    return sorted(dossiers, key=k, reverse=True)


def price_age_hours(d: dict[str, Any], *, now: datetime | None = None) -> float | None:
    """Hours since current_price was captured, or None if priced_at is missing."""
    pa = d.get("priced_at")
    if not pa:
        return None
    try:
        captured = datetime.fromisoformat(pa)
    except (TypeError, ValueError):
        return None
    ref = now or datetime.utcnow()
    return max(0.0, (ref - captured).total_seconds() / 3600.0)


# ---------------------------------------------------------------------------
# Staleness detection
# ---------------------------------------------------------------------------

STALE_AGE_HOURS = 14 * 24  # 14 days
STALE_PRICE_DRIFT = 0.20   # 20% move since scenarios were written


def check_staleness(
    dossiers: list[dict[str, Any]],
    *,
    now: datetime | None = None,
    age_hours: float = STALE_AGE_HOURS,
    drift_threshold: float = STALE_PRICE_DRIFT,
) -> list[dict[str, Any]]:
    """Flag dossiers that need re-research.

    A dossier is stale if:
      1. Its thesis is older than `age_hours` (default 14 days), OR
      2. The current price has drifted >``drift_threshold`` (default 20%)
         from ``scenario_price`` — the price the scenarios were anchored to.

    Returns a list of ``{symbol, reasons: [str], age_hours, drift_pct}``
    dicts, sorted by most-stale first.
    """
    ref = now or datetime.utcnow()
    flagged: list[dict[str, Any]] = []
    for d in dossiers:
        sym = d.get("symbol", "?")
        reasons: list[str] = []
        age = price_age_hours(d, now=ref)
        drift = 0.0

        if age is None:
            reasons.append("no priced_at timestamp")
        elif age > age_hours:
            reasons.append(f"thesis is {age / 24:.1f} days old")

        anchor = d.get("scenario_price") or 0
        price = d.get("current_price", 0)
        if anchor > 0 and price > 0:
            drift = abs(price - anchor) / anchor
            if drift >= drift_threshold:
                reasons.append(
                    f"price ${price:.2f} drifted {drift:.0%} from scenario anchor ${anchor:.2f}"
                )
        elif not anchor and price > 0:
            reasons.append("no scenario_price anchor")

        if reasons:
            flagged.append({
                "symbol": sym,
                "reasons": reasons,
                "age_hours": age,
                "drift_pct": drift,
            })

    flagged.sort(key=lambda f: (f["age_hours"] or 1e9, -f["drift_pct"]), reverse=True)
    return flagged
