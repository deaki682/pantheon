"""Oracle upside dossiers — the reframed engine (docs/oracle_upside_spec.md).

Oracle's job: pick the few under-covered names with the biggest REAL upside over
a 6–24 month hold, get big on them, hold to the thesis. Scored one way — forward
return vs SPY over the hold.

This module is the DETERMINISTIC spine (spec §4–6): the dossier writer (refuses a
name without significant, mechanism-backed upside), the expected-return ranker
(rewards upside magnitude, unlike the retired floor-hardness convexity metric),
the blowup filter (a SURVIVAL gate, not a floor — "don't step on a landmine
before the thesis pays"), the conviction sizer (concentrate 3–6, hold caps), and
the typed exit predicates (a drawdown is NEVER an exit; only a typed thesis-break
is). The EDGE itself — the breadth-read variant view — lives in the LLM stages of
the runbook, not here; this module makes everything around the edge auditable.

Supersedes oracle.convex_dossier for SELECTION. The old gate refused a name
without a floor; this one refuses a name without upside. Floors survive only as
an OPTIONAL conviction bonus (`floor_pct`) and as the lineage of the blowup
filter's primary-source discipline.
"""
from __future__ import annotations

import re as _re
from datetime import datetime
from typing import Any, Callable, Optional

# ---- enums / thresholds (spec §4, §5) --------------------------------------
INFLECTION_TYPES = {
    "earnings_accel", "margin_turn", "product_ramp", "demand_shift",
    "adoption_s_curve", "capital_return", "turnaround", "thematic_rerate",
}
KILL_TYPES = {"price_level", "fundamental_break", "dilution_event", "thesis_date", "filing_event"}

UPSIDE_X_MIN = 1.5          # the mandate: ≥ +50% target over the hold
HORIZON_MIN, HORIZON_MAX = 6.0, 24.0
ALREADY_RUN_CAP = 0.50      # recent run off the pre-catalyst base past which the upside has fired
RUNWAY_BUFFER_MONTHS = 6.0  # runway must clear the horizon by this much to "survive to thesis"

# I2 value-trap tells — a thesis whose MECHANISM reduces to these is not an upside
# thesis (cheapness is not a reason to rise). Flagged; the Stage-3 bear enforces.
DEAD_TELLS = (
    "undervalued", "trades cheap", "is cheap", "below book", "trades below",
    "insider", "quality lens", "deep value", "mispriced and cheap",
)


class UpsideDossierError(ValueError):
    pass


def _req(cond: bool, msg: str) -> None:
    if not cond:
        raise UpsideDossierError(msg)


# ---- scoring (spec §5) -----------------------------------------------------
def expected_return(upside_x: float, prob_upside: float, downside_pct: float) -> float:
    """E[return] over the whole hold. upside_x is the win multiple (1.8=+80%),
    prob_upside is P(upside case), downside_pct is the loss if wrong (positive
    fraction, 0.4=−40%). Downside is NOT gated small — a big upside carries a big
    possible loss and that is priced here, not vetoed."""
    return prob_upside * (upside_x - 1.0) - (1.0 - prob_upside) * downside_pct


def annualized_er(er: float, horizon_months: float) -> float:
    """Annualize the whole-hold expectancy so a +60% in 9 months isn't buried
    under a +60% in 24. Horizon clamped to the mandate window [6,24]."""
    h = min(HORIZON_MAX, max(HORIZON_MIN, float(horizon_months)))
    return er * (12.0 / h)


def calib_weight(inflection_type: str, calibration: Optional[dict] = None) -> float:
    """The measured hit-rate for this inflection_type (Stage-7 memory), default
    0.5 until ≥5 graded (so an untested type is neither rewarded nor buried)."""
    if not calibration:
        return 0.5
    row = calibration.get(inflection_type) or {}
    if int(row.get("n", 0)) < 5:
        return 0.5
    return float(row.get("hit_rate", 0.5))


# ---- primary-citation discipline (lineage: convex_dossier §verify) ---------
_PRIMARY_SUBSTR = ("sec.gov", "edgar", "accession no", "accession number")
_PRIMARY_FORM_CODES = (
    r"10-k", r"10-q", r"8-k", r"20-f", r"6-k", r"def\s?14a", r"defa?14a",
    r"s-1", r"s-3", r"form\s?10", r"13[dg]", r"424b\d?",
)
_ACC_NO = _re.compile(r"\b\d{10}-\d{2}-\d{6}\b")
_FORM_RE = _re.compile(r"(?<![a-z0-9])(?:" + "|".join(_PRIMARY_FORM_CODES) + r")(?![a-z0-9])")


def is_primary_citation(c: str) -> bool:
    """True if the citation points at a real SEC filing (EDGAR/sec.gov URL, a real
    accession number, or a filing-type code on a word boundary) — not a snapshot
    (Robinhood/Yahoo) or a secondary recap. Word-boundary matching stops
    incidental substrings ('s-1' in 'consensus-1%') from faking a primary source."""
    s = (c or "").lower()
    if any(m in s for m in _PRIMARY_SUBSTR):
        return True
    if _ACC_NO.search(s):
        return True
    return bool(_FORM_RE.search(s))


# ---- the writer (spec §4) --------------------------------------------------
def make_upside_dossier(
    symbol: str,
    *,
    business: str,
    thesis: str,                       # variant view: what the 6–24mo hold holds that consensus underweights (≥120)
    inflection_type: str,              # one of INFLECTION_TYPES — what is BENDING
    inflection_evidence: str,          # the SPECIFIC number/fact the trajectory is bending (≥40), cite a filing
    upside_x: float,                   # 6–24mo target multiple, ≥ 1.5 (the mandate)
    prob_upside: float,                # P(upside case) — also conviction in sizing
    downside_pct: float,               # loss if wrong, positive fraction (0,1]
    catalyst: str,                     # what makes the market SEE it
    catalyst_date: str,                # ISO or "" if undated
    horizon_months: float,             # months to the re-rating, ∈ [6,24]
    runway_months: Any,                # float months of cash, or "self_funding"
    falsifiable_prediction: str,       # dated, checkable (≥20)
    prediction_date: str,
    kill_condition: str,
    kill_type: str,                    # one of KILL_TYPES
    kill_value: Any,
    adversarial: str,                  # the bear case (≥60)
    citations: list[str],
    current_price: float,
    spy_price: float = 0.0,
    sector: str = "",
    coverage: Optional[int] = None,    # # analysts (hunting-ground context)
    theme: str = "",                   # cluster key for the correlation cap
    recent_runup_pct: float = 0.0,     # run off the pre-catalyst base — the already-run guard
    lens_score: float = 0.0,           # spotlight score — A/B baseline input ONLY, never selection
    floor_pct: Optional[float] = None, # OPTIONAL downside floor → conviction bonus, never required
    author: str = "oracle",
) -> dict[str, Any]:
    sym = symbol.upper()
    _req(bool(sym), "symbol required")
    _req(len(thesis) >= 120, "thesis must be the variant view — what consensus underweights over 6–24mo (≥120 chars)")
    _req(inflection_type in INFLECTION_TYPES,
         f"inflection_type must be one of {sorted(INFLECTION_TYPES)} — name what is BENDING, not 'it's cheap'")
    _req(len(inflection_evidence) >= 40, "inflection_evidence must cite the SPECIFIC number/fact bending (≥40 chars)")
    _req(float(upside_x) >= UPSIDE_X_MIN, f"upside_x must be ≥ {UPSIDE_X_MIN} — Oracle funds significant upside, not coupons")
    _req(0.0 <= float(prob_upside) <= 1.0, "prob_upside must be in [0,1]")
    _req(0.0 < float(downside_pct) <= 1.0, "downside_pct must be a positive fraction in (0,1]")
    _req(HORIZON_MIN <= float(horizon_months) <= HORIZON_MAX,
         f"horizon_months must be in [{HORIZON_MIN},{HORIZON_MAX}] — the mandate window")
    _req(bool(catalyst), "catalyst required — what makes the market see it")
    _req(len(falsifiable_prediction) >= 20, "falsifiable_prediction required (dated, checkable, ≥20)")
    _req(kill_type in KILL_TYPES, f"kill_type must be one of {sorted(KILL_TYPES)}")
    _req(len(adversarial) >= 60, "adversarial (the bear case) required (≥60 chars)")
    _req(float(current_price) > 0, "current_price must be > 0")
    _req(any(is_primary_citation(c) for c in citations),
         "at least one PRIMARY citation (SEC filing/accession/form) — a snapshot is not evidence")

    er = expected_return(float(upside_x), float(prob_upside), float(downside_pct))
    aer = annualized_er(er, float(horizon_months))

    hay = (thesis + " " + inflection_evidence).lower()
    dead_tell_risk = any(t in hay for t in DEAD_TELLS)
    already_run = float(recent_runup_pct) >= ALREADY_RUN_CAP

    # qualifies (intrinsic — pre-blowup): significant upside, positive expectancy,
    # in-window, not already run. Fundability additionally needs the blowup check.
    qualifies = bool(float(upside_x) >= UPSIDE_X_MIN and er > 0
                     and HORIZON_MIN <= float(horizon_months) <= HORIZON_MAX
                     and not already_run)

    return {
        "symbol": sym, "spec": "upside", "author": author,
        "created_at": datetime.utcnow().isoformat(),
        "business": business, "thesis": thesis, "sector": sector,
        "coverage": coverage, "theme": theme,
        "current_price": float(current_price), "spy_price": float(spy_price),
        # --- the upside (the edge, quantified) ---
        "inflection_type": inflection_type, "inflection_evidence": inflection_evidence,
        "upside_x": float(upside_x), "prob_upside": float(prob_upside),
        "downside_pct": float(downside_pct),
        "expected_return": round(er, 4), "annualized_er": round(aer, 4),
        "horizon_months": float(horizon_months),
        "recent_runup_pct": float(recent_runup_pct), "already_run": already_run,
        "qualifies": qualifies,
        # --- catalyst + survival ---
        "catalyst": catalyst, "catalyst_date": catalyst_date,
        "runway_months": runway_months,
        # --- discipline ---
        "falsifiable_prediction": falsifiable_prediction, "prediction_date": prediction_date,
        "kill_condition": kill_condition, "kill_type": kill_type, "kill_value": kill_value,
        "adversarial": adversarial, "dead_tell_risk": dead_tell_risk,
        "citations": list(citations),
        # --- optional conviction bonus (NOT required, NOT a gate) ---
        "floor_pct": (float(floor_pct) if floor_pct is not None else None),
        # --- A/B baseline input (never a selection signal) ---
        "lens_score": float(lens_score),
        # --- set by blowup_check / bear (Stage 3) ---
        "blowup_checked": False, "blowup": None, "blowup_flags": {},
        "bear_verdict": "keep",
    }


# ---- blowup filter (spec §6.3) — a SURVIVAL gate, not a floor ---------------
def blowup_check(
    dossier: dict,
    *,
    going_concern: bool,
    fraud: bool,
    delisting: bool,
    primary_grounded: Optional[bool] = None,   # defaults to the dossier's own citation check
    notes: str = "",
    checked_by: str = "oracle",
) -> dict:
    """Stamp the survival gate. ¬blowup iff the name survives to the thesis with
    no landmine: runway clears the horizon, no going-concern/fraud/delisting, and
    the upside path is primary-source-grounded. Sets `blowup`, `blowup_checked`,
    and re-derives `fundable`. This REPLACES floor verification — a name with no
    assets but a real path to +150% and enough runway passes; a great thesis on a
    company that dilutes 80% before it plays out does not."""
    runway = dossier.get("runway_months")
    horizon = float(dossier.get("horizon_months", HORIZON_MAX))
    survives = (runway == "self_funding") or (
        isinstance(runway, (int, float)) and float(runway) >= horizon + RUNWAY_BUFFER_MONTHS)
    grounded = (primary_grounded if primary_grounded is not None
                else any(is_primary_citation(c) for c in dossier.get("citations", [])))

    flags = {
        "survives_to_thesis": bool(survives),
        "no_going_concern": not bool(going_concern),
        "no_fraud": not bool(fraud),
        "no_delisting": not bool(delisting),
        "primary_grounded": bool(grounded),
    }
    blew = not all(flags.values())
    dossier["blowup_checked"] = True
    dossier["blowup"] = blew
    dossier["blowup_flags"] = flags
    dossier["blowup_note"] = notes
    dossier["blowup_checked_by"] = checked_by
    dossier["fundable"] = is_fundable(dossier)
    return dossier


def is_fundable(dossier: dict) -> bool:
    """Book-eligible = qualifies (significant upside, +EV, in-window, not already
    run) AND the blowup check has RUN and PASSED AND the Stage-3 bear did not
    refute it. An unchecked dossier is not fundable — survival must be affirmed."""
    return bool(
        dossier.get("qualifies")
        and dossier.get("blowup_checked")
        and dossier.get("blowup") is False
        and dossier.get("bear_verdict", "keep") != "refuted"
    )


# ---- ranking (spec §5) -----------------------------------------------------
def rank_fundable(dossiers: list[dict], calibration: Optional[dict] = None) -> list[dict]:
    """The BOOK order: fundable names only, best rank_key first. rank_key =
    annualized expected return × the measured hit-rate for the inflection_type —
    so a bold upside at decent odds in a proven-real inflection_type leads. This
    is the deterministic order money flows through; the reading (Stages 2–3) is
    what put these names here."""
    out = []
    for d in dossiers:
        if not is_fundable(d):
            continue
        d = dict(d)
        d["rank_key"] = round(d.get("annualized_er", 0.0)
                              * calib_weight(d.get("inflection_type", ""), calibration), 4)
        out.append(d)
    return sorted(out, key=lambda d: -d.get("rank_key", -9))


# ---- sizing (spec §4 Stage 4, §6.2) — FIRST-CLASS --------------------------
def size_upside_book(
    ranked: list[dict],
    equity: float,
    *,
    invested_target: float = 0.90,
    min_positions: int = 3,
    max_positions: int = 6,
    min_weight: float = 0.06,
    max_name_weight: float = 0.30,
    max_cluster_weight: float = 0.40,
    fragility_lambda: float = 1.0,
    cluster_key: Optional[Callable[[dict], str]] = None,
    calibration: Optional[dict] = None,
) -> dict[str, float]:
    """Concentrate the book into the best 3–6 names, conviction-weighted, DOWNSIDE-
    aware, and hold the risk caps. weight_raw ∝ conviction · (upside_x − 1) ·
    calib_hit_rate · (1 − λ·downside_pct) — conviction × the SIZE of the move × how
    real that inflection type has proven × a FRAGILITY HAIRCUT. The haircut fixes a
    real flaw (2026-07-06): the old formula ignored downside, so the name with the
    biggest upside got the biggest position even when it could go to ZERO (SABR was
    sized largest despite a −55% downside). Sizing by upside magnitude alone
    concentrates into the tail; the (1 − λ·downside) term pushes the fragile,
    can-go-to-zero names BELOW the safer ones with comparable edge. Then: cap any
    name at max_name_weight, cap any correlation cluster at max_cluster_weight, drop
    anything below min_weight, normalise the survivors to invested_target·equity.

    This is where 6–24mo upside is actually made: getting big on the best few.
    Equal-weighting or dusting the budget across many names is a FAILURE MODE (F4).

    Caps are fractions of EQUITY (absolute risk limits). We start at the conviction
    target (summing to invested_target) and only ever clamp DOWN — a name past its
    cap, or a cluster past its cap, is trimmed and the freed room becomes CASH, not
    force-fed into lower-conviction names. So a book dominated by one capped
    high-conviction name is deliberately UNDER-invested rather than diluted.
    """
    if equity <= 0 or not ranked:
        return {}
    if cluster_key is None:
        cluster_key = lambda d: (d.get("theme") or d.get("sector") or d.get("symbol") or "")

    picks = ranked[:max_positions]
    by_sym = {d["symbol"]: d for d in picks}
    raw = {}
    for d in picks:
        conv = float(d.get("prob_upside", 0.0))
        move = max(0.0, float(d.get("upside_x", 1.0)) - 1.0)     # SIZE of the move
        cw = calib_weight(d.get("inflection_type", ""), calibration)
        dn = float(d.get("downside_pct", 0.0) or 0.0)           # loss if wrong
        frag = max(0.1, 1.0 - fragility_lambda * dn)            # FRAGILITY HAIRCUT — a
        raw[d["symbol"]] = max(0.0, conv * move * cw * frag)    # can-go-to-zero name can't lead
    tot = sum(raw.values())
    if tot <= 0:
        return {}

    # conviction target as a fraction of equity, summing to invested_target
    w = {s: invested_target * raw[s] / tot for s in raw}
    # per-name cap (clamp down; freed room -> cash)
    for s in w:
        w[s] = min(w[s], max_name_weight)
    # correlation-cluster cap (scale a cluster down; freed room -> cash)
    clusters: dict[str, list[str]] = {}
    for s in w:
        clusters.setdefault(cluster_key(by_sym[s]), []).append(s)
    for members in clusters.values():
        ctot = sum(w[s] for s in members)
        if ctot > max_cluster_weight and ctot > 0:
            scale = max_cluster_weight / ctot
            for s in members:
                w[s] *= scale
    # drop view-diluting dust below the meaningful floor
    w = {s: v for s, v in w.items() if v >= min_weight}
    return {s: round(v * float(equity), 2) for s, v in w.items()}


# ---- exit predicates (spec §6.1) — a drawdown is NEVER an exit --------------
def evaluate_exit(
    dossier: dict,
    *,
    current_price: Optional[float] = None,
    as_of_date: Optional[str] = None,      # ISO "YYYY-MM-DD"
    fundamental_deteriorated: bool = False,  # growth decelerated / margins reversed, from a FILING
    dilution_event: bool = False,            # dilutive raise beyond thesis / going-concern raise
    going_concern: bool = False,
    catalyst_occurred: Optional[bool] = None,  # None=unknown, only matters once catalyst_date passed
) -> dict:
    """Return {"exit": bool, "reason": str|None}. Exit ONLY on a typed thesis-break
    (spec §6.1). A drawdown, a red day, rank drift, sector-out-of-favor, or boredom
    are NEVER exits — holding the eventual +200% name through a −25% wobble is the
    whole point of Stage 5. Re-underwrite on FACTS, never on price alone."""
    d = dossier
    # price_level — only if the kill was explicitly typed to a price (rare)
    if d.get("kill_type") == "price_level" and current_price is not None:
        try:
            lvl = float(d.get("kill_value"))
            if float(current_price) <= lvl:
                return {"exit": True, "reason": f"price_level: {current_price} ≤ kill {lvl}"}
        except (TypeError, ValueError):
            pass
    if fundamental_deteriorated:
        return {"exit": True, "reason": "fundamental_break: growth/margin reversed vs thesis (filing)"}
    if dilution_event or going_concern:
        return {"exit": True, "reason": "dilution_event: dilutive raise / going-concern"}
    # catalyst_fail / thesis_date — date-gated
    if as_of_date:
        cd = d.get("catalyst_date") or ""
        if cd and as_of_date >= cd and catalyst_occurred is False:
            return {"exit": True, "reason": f"catalyst_fail: {cd} passed, catalyst did not occur"}
        pd = d.get("prediction_date") or ""
        if pd and as_of_date >= pd:
            return {"exit": True, "reason": f"thesis_date: {pd} reached without the re-rating"}
    return {"exit": False, "reason": None}
