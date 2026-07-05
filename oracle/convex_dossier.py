"""Convex dossiers — the reframed Oracle's edge (docs/oracle_reframe_2026-07-05.md).

The old dossier confirmed dead signals ("insider + quality + cheap"). A convex
dossier establishes ASYMMETRY and names the STRUCTURAL reason the price is
wrong. Every field below is load-bearing; the builder refuses a dossier that
can't state its floor, its structural mispricing, and a checkable kill.

asymmetry_score = P(upside)·(upside_x − 1) − (1 − P(upside))·floor_pct
  — the expected payoff of the bet in return terms. Positive = favorable
  asymmetry. This, NOT a lens-conviction number, is the selection signal.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

WHY_MISPRICED_TYPES = {"neglect", "forced_seller", "hard_catalyst"}
KILL_TYPES = {"price_level", "drawdown_pct", "thesis_date", "filing_event"}
# triggers the house has measured at ~zero — a thesis that reduces to these is noise
DEAD_TRIGGERS = ("insider", "quality lens", "trades cheap", "undervalued", "buyback")


class ConvexDossierError(ValueError):
    pass


def asymmetry_score(floor_pct: float, upside_x: float, prob_upside: float) -> float:
    """Expected asymmetric payoff (return units). floor_pct is the worst
    plausible LOSS as a positive fraction (0.25 = −25%); upside_x is the win
    multiple (1.8 = +80%); prob_upside is P(the upside case)."""
    return prob_upside * (upside_x - 1.0) - (1.0 - prob_upside) * floor_pct


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise ConvexDossierError(msg)


def make_convex_dossier(
    symbol: str,
    *,
    business: str,
    thesis: str,                    # must name the mechanism + who is wrong (>=120 chars)
    floor_pct: float,               # worst plausible loss, positive fraction (0<..<=1)
    upside_x: float,                # win multiple, >=1.0 (1.5 = +50%)
    prob_upside: float,             # P(upside case), 0..1
    why_mispriced_type: str,        # neglect | forced_seller | hard_catalyst
    why_mispriced: str,             # the STRUCTURAL reason (>=40 chars)
    catalyst: str,                  # the specific catalyst
    catalyst_date: str,             # ISO date or "" if undated
    falsifiable_prediction: str,    # a dated, checkable claim (>=20 chars)
    prediction_date: str,
    kill_condition: str,            # the promise-not-suggestion exit
    kill_condition_type: str,       # price_level | drawdown_pct | thesis_date | filing_event
    kill_condition_value: Any,      # float | date | str per type
    adversarial: str,               # "what does the disciplined house know against this?" (>=60)
    citations: list[str],
    current_price: float,
    spy_price: float = 0.0,
    sector: str = "",
    lens_score: float = 0.0,        # the OLD mechanical score — kept ONLY as the A/B baseline input
    author: str = "oracle",
) -> dict[str, Any]:
    sym = symbol.upper()
    _req(bool(sym), "symbol required")
    _req(len(thesis) >= 120, "thesis must name the mechanism + who is wrong (>=120 chars)")
    _req(0.0 < float(floor_pct) <= 1.0, "floor_pct must be a positive fraction in (0,1] — no floor = growth gamble, not an Oracle name")
    _req(float(upside_x) >= 1.0, "upside_x must be >=1.0 (a win multiple)")
    _req(0.0 <= float(prob_upside) <= 1.0, "prob_upside must be in [0,1]")
    _req(why_mispriced_type in WHY_MISPRICED_TYPES,
         f"why_mispriced_type must be one of {sorted(WHY_MISPRICED_TYPES)} — name the STRUCTURE, not 'the market underappreciates it'")
    _req(len(why_mispriced) >= 40, "why_mispriced must state the structural reason (>=40 chars)")
    _req(bool(catalyst), "catalyst required — what re-rates it")
    _req(len(falsifiable_prediction) >= 20, "falsifiable_prediction required (dated, checkable)")
    _req(kill_condition_type in KILL_TYPES, f"kill_condition_type must be one of {sorted(KILL_TYPES)}")
    _req(len(adversarial) >= 60, "adversarial pass required (>=60 chars) — what does the house know against this?")
    _req(float(current_price) > 0, "current_price must be > 0")

    # soft flag: does the thesis lean on a house-refuted trigger?
    hay = (thesis + " " + why_mispriced).lower()
    dead_trigger_risk = any(t in hay for t in DEAD_TRIGGERS)

    score = asymmetry_score(float(floor_pct), float(upside_x), float(prob_upside))
    now = datetime.utcnow().isoformat()
    return {
        "symbol": sym, "spec": "convex", "author": author, "created_at": now,
        "business": business, "thesis": thesis, "sector": sector,
        "current_price": float(current_price), "spy_price": float(spy_price),
        # --- asymmetry (the edge) ---
        "floor_pct": float(floor_pct), "upside_x": float(upside_x),
        "prob_upside": float(prob_upside), "asymmetry_score": round(score, 4),
        "convex": bool(score > 0 and float(upside_x) >= 1.5),
        # --- structural mispricing (G2) + catalyst (G4) ---
        "why_mispriced_type": why_mispriced_type, "why_mispriced": why_mispriced,
        "catalyst": catalyst, "catalyst_date": catalyst_date,
        # --- discipline ---
        "falsifiable_prediction": falsifiable_prediction, "prediction_date": prediction_date,
        "kill_condition": kill_condition, "kill_condition_type": kill_condition_type,
        "kill_condition_value": kill_condition_value, "adversarial": adversarial,
        "dead_trigger_risk": dead_trigger_risk,
        "citations": list(citations),
        # --- A/B baseline input (NOT a selection signal) ---
        "lens_score": float(lens_score),
    }


def rank_by_asymmetry(dossiers: list[dict]) -> list[dict]:
    """The selection order: best asymmetric payoff first. Convex names only —
    a non-convex dossier (negative score or thin upside) is not book-worthy."""
    convex = [d for d in dossiers if d.get("convex")]
    return sorted(convex, key=lambda d: -d.get("asymmetry_score", -9))
