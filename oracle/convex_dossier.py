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


# =====================================================================
# Primary-source verification gate (2026-07-06)
# =====================================================================
# The launch-gate diligence on 2026-07-06 killed 4 of 8 dossiers that a
# fundamentals-API pass had waved through as "convex":
#   - MNRO: P/B<1 was 100% GOODWILL; tangible book was NEGATIVE (-$5/sh).
#   - XRN : "debt-free ($1.15M)" MISSED a $652.7M credit facility — the fast
#           read took one balance-sheet line, not the full liability stack.
#   - SMHI: the "$20 fleet NAV" was an activist's claim in NO SEC filing; the
#           real audited book was ~$9, and the catalyst had already popped.
#   - GYRO: the "$11.79 floor" was a management liquidation PROJECTION melting
#           42% over 3.5yr, under active litigation, kill-condition already tripped.
# Every one shared a shape a fundamentals snapshot cannot see and a primary
# filing reveals. So `convex` (computed from self-reported numbers) is NO LONGER
# sufficient to fund a name. A dossier must additionally pass four primary-source
# traps — each the exact hole one of those four fell through — cited to actual
# filings. This makes tonight's four errors structurally impossible to fund again.

# What the floor actually IS, hardest -> softest, ordered by how tonight's names
# held up: countable cash (RNA/ARVN survived) > net-net > transacting assets
# (ALCO's land selling for real $/acre survived) > book (MNRO's goodwill mirage
# died) > asserted (SMHI's activist appraisal — not a floor at all — died).
FLOOR_BASIS = {
    "cash": 1.0, "net_net": 0.9, "transacting_asset": 0.75, "book": 0.55, "asserted": 0.0,
}

# A citation is PRIMARY if it points at an actual SEC filing, not a snapshot or
# a secondary recap. XRN's dossier cited "Robinhood fundamentals" as
# load-bearing — that is the tell this refuses to accept as a floor source.
#
# HARDENED 2026-07-06 (audit finding): the old bare-substring match let a
# snapshot-only citation pass on incidental characters — "s-1" matched
# "consensus-1.2%", "acc " matched "accrued", etc. Now split into (a) unambiguous
# domain/word markers matched as substrings, and (b) filing-type codes matched
# only on a word boundary, plus a real accession-number pattern.
import re as _re

_PRIMARY_SUBSTR = ("sec.gov", "edgar", "accession no", "accession number")
_PRIMARY_FORM_CODES = (
    r"10-k", r"10-q", r"8-k", r"20-f", r"6-k", r"def\s?14a", r"defa?14a",
    r"s-1", r"s-3", r"form\s?10", r"13[dg]", r"sc\s?to", r"424b\d?",
)
# accession numbers look like 0001234567-26-000123
_ACC_NO = _re.compile(r"\b\d{10}-\d{2}-\d{6}\b")
_FORM_RE = _re.compile(r"(?<![a-z0-9])(?:" + "|".join(_PRIMARY_FORM_CODES) + r")(?![a-z0-9])")


def is_primary_citation(c: str) -> bool:
    """True if the citation references a real SEC filing — an EDGAR/sec.gov URL, a
    real accession number, or a filing-type code on a WORD BOUNDARY — rather than a
    fundamentals snapshot (Robinhood/Yahoo) or a secondary recap (StockTitan/
    Seeking Alpha). Word-boundary matching stops incidental substrings ("s-1" in
    "consensus-1%", "acc " in "accrued") from faking a primary source."""
    s = (c or "").lower()
    if any(m in s for m in _PRIMARY_SUBSTR):
        return True
    if _ACC_NO.search(s):
        return True
    return bool(_FORM_RE.search(s))


def verify_dossier(
    dossier: dict,
    *,
    floor_basis: str,               # cash|net_net|transacting_asset|book|asserted — what the floor IS, per filings
    debt_reconciled_full_stack: bool,   # was debt taken off the FULL liability stack, not one line? (the XRN trap)
    catalyst_fired: bool,           # has the catalyst already re-rated the name? (the SMHI trap)
    book_survives_goodwill: Optional[bool] = None,  # for book floors: does tangible book (ex-goodwill) still support it? (the MNRO trap)
    primary_citations: Optional[list[str]] = None,  # defaults to the dossier's own citations
    verdict: str = "keep",          # keep | revise | kill (the reader's conclusion)
    notes: str = "",
    verified_by: str = "oracle",
) -> dict:
    """Stamp a primary-source verification onto a dossier and set `verified`.

    Runs the four traps that tonight's four kills each failed. A dossier only
    becomes `verified` (and thus fundable) if ALL traps pass AND the reader's
    verdict is keep/revise. On pass, it also RE-STAMPS floor_hardness from the
    true floor_basis — so a self-reported 'hard' on an asserted floor cannot
    survive contact with the verification."""
    _req(floor_basis in FLOOR_BASIS, f"floor_basis must be one of {sorted(FLOOR_BASIS)}")
    _req(verdict in {"keep", "revise", "kill"}, "verdict must be keep|revise|kill")
    cites = list(primary_citations if primary_citations is not None else dossier.get("citations", []))

    # The goodwill trap must FAIL-CLOSED for a book floor (2026-07-06 audit fix):
    # a `book` floor's whole risk is that reported book is goodwill/intangibles
    # (MNRO: tangible book −$5/sh). If the verifier did not affirmatively confirm
    # tangible book survives (book_survives_goodwill left None/unknown), a book
    # floor must NOT pass. For non-book floors (cash/net_net/transacting_asset)
    # goodwill is irrelevant, so unknown is fine — only an explicit False fails.
    if floor_basis == "book":
        book_ok = book_survives_goodwill is True
    else:
        book_ok = book_survives_goodwill is not False

    traps = {
        # each key is a specific tonight-kill made impossible:
        "primary_source_cited": any(is_primary_citation(c) for c in cites),   # XRN cited only a snapshot
        "floor_not_merely_asserted": floor_basis != "asserted",               # SMHI's $20 activist NAV
        "book_survives_goodwill": book_ok,                                     # MNRO's negative tangible book (fail-closed on book floors)
        "debt_reconciled_full_stack": bool(debt_reconciled_full_stack),        # XRN's missed credit line
        "catalyst_not_already_fired": not bool(catalyst_fired),                # SMHI's already-popped catalyst
    }
    passed = all(traps.values()) and verdict in {"keep", "revise"}

    dossier["verification"] = {
        "verified_at": datetime.utcnow().isoformat(),
        "verified_by": verified_by,
        "floor_basis": floor_basis,
        "traps": traps,
        "verdict": verdict,
        "notes": notes,
        "passed": passed,
    }
    dossier["verified"] = passed
    if passed:
        # rank on the VERIFIED floor hardness, not the self-reported one
        w = FLOOR_BASIS[floor_basis]
        dossier["floor_hardness"] = "hard" if w >= 0.9 else ("medium" if w >= 0.55 else "soft")
        dossier["convexity_score"] = round(
            convexity_score(dossier.get("asymmetry_score", 0.0),
                            dossier.get("horizon_months", DEFAULT_HORIZON_MONTHS),
                            dossier["floor_hardness"]), 4)
    return dossier


def is_fundable(dossier: dict) -> bool:
    """Book-eligible = convex (positive expectancy + real floor) AND
    primary-source-verified (passed the four traps) AND the catalyst hasn't
    fired. An UNVERIFIED dossier — however good its self-reported numbers — is
    NOT fundable. Each of tonight's four kills fails this gate."""
    return bool(dossier.get("convex") and dossier.get("verified")
                and not dossier.get("catalyst_fired_risk"))


def rank_fundable(dossiers: list[dict]) -> list[dict]:
    """The BOOK order — only verified, convex names, best convexity first. Use
    THIS, not rank_by_convexity, to select what actually gets capital.
    rank_by_convexity stays the pure-math research view; rank_fundable is the
    gated view that money flows through."""
    return sorted((d for d in dossiers if is_fundable(d)),
                  key=lambda d: -d.get("convexity_score", -9))
