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
) -> dict[str, Any]:
    """Build, validate, and return a dossier with derived fields filled in."""
    d: dict[str, Any] = {
        "symbol": symbol.upper(),
        "business": business,
        "thesis": thesis,
        "scenarios": scenarios,
        "ratings": ratings,
        "citations": list(citations),
        "horizon_years": float(horizon_years),
        "current_price": float(current_price),
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
