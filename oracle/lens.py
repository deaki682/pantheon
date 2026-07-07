"""oracle/lens.py — Oracle's read lens for the shared cascade (2026-07-07).

Oracle's identity as two tiers the cascade runs over the WHOLE hunting ground:

  TRIAGE (cheap, recall-first, Sonnet)  — "is there ANY sign of a real, not-yet-
    priced inflection worth an expensive read?" Drops only the obvious-dead; when
    unsure, ADVANCE (a wrong drop is unrecoverable, a wrong advance is caught by
    the deep tier). This is the filter that finally becomes a READ instead of a
    no-edge number — the whole reason for the rebuild. Never Haiku: the 2026-07-07
    calibration proved a weaker brain confidently kills real inflections.

  DEEP (expensive, Opus, + the load-bearing gate) — the variant read that builds
    the dossier, then runs the BEAR×3 refutation gate (`resolve_bears`) and the
    blowup filter. A name is `fundable` only if it survives ≥3 independent,
    primary-cited critiques with a positive margin AND clears survival. The gate
    is DETERMINISTIC and lives here in `parse` — the model supplies the reads, the
    code adjudicates, so a credulous read can't smuggle a name through.

The model outputs are consumed via the injected `model_read`; this module only
builds the prompts and adjudicates the results, so it is fully unit-testable with
stubbed outputs (no tokens).
"""
from __future__ import annotations

from shared.read_cascade import Lens, Tier
from oracle.upside_dossier import (
    blowup_check,
    is_fundable,
    make_upside_dossier,
    resolve_bears,
)

TRIAGE_EST_TOKENS = 1500
DEEP_EST_TOKENS = 9000


def triage_prompt(p: dict) -> str:
    return (
        "You are TIER-1 of Oracle's cascade — a recall-first triage over under-covered "
        "small/mid-caps. Decide ONLY whether this name deserves a deeper, expensive read for a "
        "6-24 month, +50%+ upside thesis. You are NOT picking winners.\n"
        "ADVANCE if there is ANY plausible sign of a real, not-yet-priced inflection (accelerating "
        "revenue, a margin turn, a product ramp, a demand shift, a genuine turnaround).\n"
        "DROP only if clearly nothing: no trajectory, a secular decliner with nothing bending, a pure "
        "value trap, a pre-revenue lottery with no catalyst, an obvious shell. When unsure, ADVANCE.\n"
        f"Use what you know about {p.get('name','')} ({p['symbol']}) plus these numbers.\n"
        f"Evidence: {p}\n"
        "Return advance (bool), confidence 0..1, inflection_hint (the specific thing possibly bending, "
        "or 'none'), reason (one sentence)."
    )


def triage_keep(p: dict, v: dict) -> bool:
    return bool(v.get("advance"))


def deep_prompt(p: dict) -> str:
    return (
        "You are Oracle's DEEP read (senior analyst) on a name that cleared triage. Read it for a "
        "REAL, not-yet-priced inflection with +50%+ upside over a 6-24 month hold, and then ATTACK "
        "your own thesis. Return a JSON object with two parts:\n"
        "  \"dossier\": { business, thesis (the variant view, >=120 chars), inflection_type, "
        "inflection_evidence (cite a filing), upside_x (>=1.5), prob_upside (0..1), downside_pct "
        "(0..1), catalyst, catalyst_date, horizon_months (6..24), runway_months (number or "
        "'self_funding'), falsifiable_prediction, prediction_date, kill_condition, kill_type, "
        "kill_value, adversarial (the bear case), citations (>=1 primary SEC filing), current_price }\n"
        "  \"blowup\": { going_concern, fraud, delisting }  (booleans)\n"
        "  \"bears\": a list of >=3 INDEPENDENT critiques, each { critique_type, critique (the specific "
        "flaw), severity (0..1), defense (your primary-cited rebuttal), defense_citations (>=1 filing "
        "when you claim survival), concede (bool) }. A fatal-type critique (faked_earnings, "
        "guidance_contradiction, quality_of_deleveraging, one_time_driver, going_concern, "
        "secular_decline) must be answered IN FULL with a filing, or concede it.\n"
        f"Name: {p.get('name','')} ({p['symbol']}). Evidence: {p}"
    )


def deep_parse(raw: dict, p: dict) -> dict:
    """Adjudicate the deep read: build the dossier, run the blowup filter, then the
    load-bearing BEAR gate. Deterministic — the code decides fundability, not the
    model's own say-so. Any malformed/incomplete read fails the gate with a reason
    (a read that can't produce a disciplined dossier is not fundable)."""
    if not isinstance(raw, dict):
        return {"fundable": False, "reason": "deep read returned no structured object"}
    try:
        # symbol is authoritative from the packet, not the model's echo of it
        body = {k: v for k, v in raw["dossier"].items() if k != "symbol"}
        d = make_upside_dossier(p["symbol"], **body)
        b = raw.get("blowup") or {}
        blowup_check(d, going_concern=bool(b.get("going_concern")),
                     fraud=bool(b.get("fraud")), delisting=bool(b.get("delisting")))
        resolve_bears(d, raw.get("bears") or [])
        return {"fundable": is_fundable(d), "bear_verdict": d.get("bear_verdict"),
                "refutation_margin": d.get("refutation_margin"),
                "upside_x": d.get("upside_x"), "prob_upside": d.get("prob_upside"),
                "downside_pct": d.get("downside_pct"), "dossier": d,
                "reason": (d.get("bear_verdict") if not is_fundable(d) else "fundable")}
    except Exception as e:
        return {"fundable": False, "reason": f"deep read failed the gate: {e}"}


def deep_keep(p: dict, v: dict) -> bool:
    return bool(v.get("fundable"))


ORACLE_LENS = Lens(name="oracle", tiers=[
    Tier(name="triage", model="sonnet", effort="low",
         prompt=triage_prompt, keep=triage_keep, est_tokens=TRIAGE_EST_TOKENS),
    Tier(name="deep", model="opus", effort="high",
         prompt=deep_prompt, parse=deep_parse, keep=deep_keep, est_tokens=DEEP_EST_TOKENS),
])
