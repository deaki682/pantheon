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
        "created_at": datetime.utcnow().isoformat(),
    }
    validate_dossier(d)
    derived = compute_derived(d, current_price=current_price, horizon_years=horizon_years)
    d["derived"] = derived
    d["conviction"] = potential_to_conviction(derived["potential_score"])
    return d


def rescore_dossier(d: dict[str, Any], *, current_price: float) -> dict[str, Any]:
    """Recompute derived metrics + conviction at a new price."""
    # compute_derived assumes a well-formed dossier (scenarios + ratings). Unlike
    # build_dossier, rescore receives an existing dossier that could have been
    # loaded from disk or hand-edited — validate so a malformed one raises a clear
    # DossierError instead of a cryptic KeyError deep in the math.
    validate_dossier(d)
    d["current_price"] = float(current_price)
    derived = compute_derived(d, current_price=current_price, horizon_years=d.get("horizon_years", 2.0))
    d["derived"] = derived
    d["conviction"] = potential_to_conviction(derived["potential_score"])
    return d


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
