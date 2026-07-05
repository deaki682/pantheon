"""Convex dossiers — the reframed Oracle's edge (docs/oracle_reframe_2026-07-05.md).

The old dossier confirmed dead signals ("insider + quality + cheap"). A convex
dossier establishes ASYMMETRY and names the STRUCTURAL reason the price is
wrong. Every field below is load-bearing; the builder refuses a dossier that
can't state its floor, its structural mispricing, and a checkable kill.

asymmetry_score = P(upside)·(upside_x − 1) − (1 − P(upside))·floor_pct
  — the expected payoff of the bet in return terms, over its whole horizon.
  Positive = favorable asymmetry.

convexity_score = annualize(asymmetry_score) · floor_hardness_weight
  — the SELECTION metric. Two corrections the raw asymmetry_score can't make
  on its own (both surfaced by the 2026-07-05 forced-seller scan):
    1. Annualize by horizon — a bounded +30% in 6 months should not rank
       below a low-odds 3x that needs 3 years. Raw asymmetry ignored time and
       over-weighted distant biotech optionality.
    2. Weight by floor hardness — a hard asset/net-cash floor deserves full
       credit; a soft/contingent floor (zoning, thin tangible book) is
       discounted, because a floor that might not hold is not really a floor.
  The `convex` FLAG is now "positive expectancy + a real (bounded) floor" —
  NOT "big multiple". A near-certain bounded win (buy $1 of net cash for $0.80
  with a forced buyer — the Tang/Concentra shape) is the PUREST convexity even
  at a 1.3x multiple; the old upside_x>=1.5 gate wrongly dropped it.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

WHY_MISPRICED_TYPES = {"neglect", "forced_seller", "hard_catalyst"}
KILL_TYPES = {"price_level", "drawdown_pct", "thesis_date", "filing_event"}
# triggers the house has measured at ~zero — a thesis that reduces to these is noise
DEAD_TRIGGERS = ("insider", "quality lens", "trades cheap", "undervalued", "buyback")

# floor hardness — how much to trust the stated floor. asset/net-cash = hard;
# book/tangible-book = medium; contingent (zoning, liquidation timing, soft
# marks) = soft. A soft floor earns less than half a hard one in the ranking.
FLOOR_HARDNESS_WEIGHT = {"hard": 1.0, "medium": 0.7, "soft": 0.45}
FLOOR_REALITY_CAP = 0.60      # a "floor" worse than -60% is not a floor -> not convex
DEFAULT_HORIZON_MONTHS = 12.0
# The "already fired" guard (added 2026-07-05 after BOLD ranked #1 on a price
# taken AFTER a +79% single-day catalyst pop). A convex bet must be entered
# BEFORE the catalyst re-rates the floor-to-ceiling gap; buying after the pop
# forfeits the convexity and inherits the deal-break downside. A name that has
# already run past this cap off its pre-catalyst base is NOT convex — the
# asymmetry has fired. Pass recent_runup_pct from the price history.
RUNUP_FIRED_CAP = 0.50


class ConvexDossierError(ValueError):
    pass


def asymmetry_score(floor_pct: float, upside_x: float, prob_upside: float) -> float:
    """Expected asymmetric payoff (return units) over the whole horizon.
    floor_pct is the worst plausible LOSS as a positive fraction (0.25 = −25%);
    upside_x is the win multiple (1.8 = +80%); prob_upside is P(the upside case)."""
    return prob_upside * (upside_x - 1.0) - (1.0 - prob_upside) * floor_pct


def convexity_score(asymmetry: float, horizon_months: float,
                    floor_hardness: str = "medium") -> float:
    """The selection metric: annualized expected asymmetry, discounted by how
    HARD the floor is.

    - Annualize by 12/horizon_months so a bounded near-term win isn't buried
      under a low-odds far-off multiple (a +30% in 6mo beats a +30% in 3yr).
    - Multiply by the floor-hardness weight so a real asset/cash floor outranks
      a soft/contingent one at equal expectancy.
    horizon_months is floored at 1.0 (a sub-month catalyst doesn't earn a 12x
    annualization blow-up)."""
    h = max(1.0, float(horizon_months))
    w = FLOOR_HARDNESS_WEIGHT.get(floor_hardness, 0.7)
    return (asymmetry * (12.0 / h)) * w


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
    floor_hardness: str = "medium",  # hard (asset/net-cash) | medium (book) | soft (contingent)
    horizon_months: Optional[float] = None,  # months to the re-rating; default 12
    recent_runup_pct: float = 0.0,   # % run off the pre-catalyst base — the "already fired" check
    author: str = "oracle",
) -> dict[str, Any]:
    sym = symbol.upper()
    _req(bool(sym), "symbol required")
    _req(len(thesis) >= 120, "thesis must name the mechanism + who is wrong (>=120 chars)")
    _req(0.0 < float(floor_pct) <= 1.0, "floor_pct must be a positive fraction in (0,1] — no floor = growth gamble, not an Oracle name")
    _req(float(upside_x) >= 1.0, "upside_x must be >=1.0 (a win multiple)")
    _req(0.0 <= float(prob_upside) <= 1.0, "prob_upside must be in [0,1]")
    _req(floor_hardness in FLOOR_HARDNESS_WEIGHT,
         f"floor_hardness must be one of {sorted(FLOOR_HARDNESS_WEIGHT)} — how hard is the floor, really?")
    hz = DEFAULT_HORIZON_MONTHS if horizon_months is None else float(horizon_months)
    _req(hz > 0, "horizon_months must be > 0 (months to the re-rating)")
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
    # the "already fired" guard: has the catalyst already re-rated the name?
    catalyst_fired_risk = float(recent_runup_pct) >= RUNUP_FIRED_CAP

    score = asymmetry_score(float(floor_pct), float(upside_x), float(prob_upside))
    cscore = convexity_score(score, hz, floor_hardness)
    now = datetime.utcnow().isoformat()
    return {
        "symbol": sym, "spec": "convex", "author": author, "created_at": now,
        "business": business, "thesis": thesis, "sector": sector,
        "current_price": float(current_price), "spy_price": float(spy_price),
        # --- asymmetry (the edge) ---
        "floor_pct": float(floor_pct), "upside_x": float(upside_x),
        "prob_upside": float(prob_upside), "asymmetry_score": round(score, 4),
        "floor_hardness": floor_hardness, "horizon_months": hz,
        "convexity_score": round(cscore, 4),
        "recent_runup_pct": float(recent_runup_pct),
        "catalyst_fired_risk": catalyst_fired_risk,
        # convex = positive expectancy + a REAL (bounded) floor + the catalyst
        # has NOT already fired. The old upside_x>=1.5 gate wrongly dropped
        # bounded near-certain wins; the missing runup guard wrongly KEPT names
        # bought at the top of a pop (BOLD, +79% before the scan priced it).
        "convex": bool(score > 0 and float(floor_pct) <= FLOOR_REALITY_CAP
                       and not catalyst_fired_risk),
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


def rank_by_convexity(dossiers: list[dict]) -> list[dict]:
    """The selection order: best convexity_score first (annualized asymmetry,
    floor-hardness weighted). Convex names only — a non-convex dossier (negative
    expectancy, or no real floor) is not book-worthy. This is the fix for the
    raw-asymmetry ranking that over-weighted distant biotech multiples over
    hard-floor near-catalyst names."""
    convex = [d for d in dossiers if d.get("convex")]
    return sorted(convex, key=lambda d: -d.get("convexity_score", -9))


# back-compat alias — the runbook/tests may still call rank_by_asymmetry; it now
# ranks by the improved convexity_score (annualized + floor-hardness weighted).
def rank_by_asymmetry(dossiers: list[dict]) -> list[dict]:
    return rank_by_convexity(dossiers)
