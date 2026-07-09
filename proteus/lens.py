"""proteus/lens.py — Proteus's read lens for the shared cascade (2026-07-07).

Proteus as two tiers the cascade runs over the WHOLE market (filter off) — the
machine-native detective the rebuild is for, instead of one session skimming a
handful of salient names:

  TRIAGE (cheap, recall-first, Sonnet) — "is there ANY live dislocation or thread
    worth pulling here?" This is what makes his 'whole-market sweep' real rather
    than a fiction: a cheap read actually touches the field.

  DEEP (expensive, Opus, + the investigation gate) — the detective read that
    assembles a CaseFile (the narrative gap: consensus vs corroborated variant +
    catalyst, the claims with their sources, the followed trail) and runs
    `assess_case`. Actionable only if it's a real gap (not the obvious take), every
    load-bearing NUMBER is primary-confirmed (the web is for leads, the tape/filing
    is for truth), every load-bearing claim is triangulated across >=2 independent
    sources, and it's a followed investigation (>=2 hops), not a single glance. The
    gate is DETERMINISTIC and lives here in `parse`.

Fully unit-testable with stubbed model output (no tokens).
"""
from __future__ import annotations

from shared.read_cascade import Lens, Tier
from proteus.investigation import CaseFile, Claim, NarrativeGap, Source, assess_case

TRIAGE_EST_TOKENS = 1500
DEEP_EST_TOKENS = 9000


def triage_prompt(p: dict) -> str:
    return (
        "You are TIER-1 of Proteus's whole-market sweep — a recall-first triage. Decide ONLY whether "
        "this name has a live dislocation or a thread worth pulling for a deeper, expensive detective "
        "read (any mispricing, any asset class, any thesis-type). You are NOT deciding to trade.\n"
        "ADVANCE if there is ANY plausible sign of a mispricing, forced flow, special situation, "
        "narrative gap, or unusual move worth investigating. DROP only if clearly nothing. When "
        "unsure, ADVANCE.\n"
        f"Use what you know about {p.get('name','')} ({p['symbol']}) plus these numbers.\n"
        f"Evidence: {p}\n"
        "Return advance (bool), confidence 0..1, thread_hint (the specific thing to pull, or 'none'), "
        "reason (one sentence)."
    )


def triage_keep(p: dict, v: dict) -> bool:
    return bool(v.get("advance"))


def deep_prompt(p: dict) -> str:
    return (
        "You are Proteus's DEEP detective read on a name that cleared triage. Follow the thread across "
        "dispersed sources to a NARRATIVE GAP and return a JSON CaseFile:\n"
        "  \"hypothesis\": the lead you're investigating.\n"
        "  \"narrative\": { consensus (what the market believes and prices), variant (what the "
        "corroborated evidence says instead), catalyst (what forces the update, and roughly when) }.\n"
        "  \"claims\": a list of { text, kind ('numeric'|'qualitative'), load_bearing (bool), sources: "
        "[ { source_type ('sec_filing'|'broker_tape'|'regulatory_docket'|'court_record'|'news'|"
        "'analyst'|'forum'|'industry_press'|'foreign_press'|'company_ir'|'other'), origin (outlet/"
        "domain), ref (url/accession) } ] }. EVERY load-bearing claim needs >=2 INDEPENDENT sources "
        "(distinct outlets/domains — triangulate); a load-bearing NUMBER must ALSO include at least one "
        "PRIMARY source among them (sec_filing/broker_tape/regulatory_docket/court_record — the web is "
        "for leads, the tape/filing is for truth).\n"
        "  \"trail\": the ordered hops you followed (>=2) — the edge is synthesis, not a lone datapoint.\n"
        f"Name: {p.get('name','')} ({p['symbol']}). Evidence: {p}"
    )


def deep_parse(raw: dict, p: dict) -> dict:
    """Adjudicate the detective read: rebuild the CaseFile and run the investigation
    gate. Deterministic — a single-glance, obvious-take, or unconfirmed-number case
    is refused here regardless of how confident the read sounded. Malformed reads
    fail the gate with a reason."""
    if not isinstance(raw, dict):
        return {"actionable": False, "reason": "deep read returned no structured object"}
    try:
        ng = raw.get("narrative") or {}
        claims = []
        for c in raw.get("claims") or []:
            sources = [Source(source_type=s.get("source_type", "other"),
                              origin=s.get("origin", ""), ref=s.get("ref", ""))
                       for s in (c.get("sources") or [])]
            claims.append(Claim(text=c.get("text", ""), kind=c.get("kind", "qualitative"),
                                load_bearing=bool(c.get("load_bearing")), sources=sources))
        case = CaseFile(
            symbol=p["symbol"], hypothesis=raw.get("hypothesis", ""),
            narrative=NarrativeGap(consensus=ng.get("consensus", ""), variant=ng.get("variant", ""),
                                   catalyst=ng.get("catalyst", "")),
            claims=claims, trail=list(raw.get("trail") or []))
        res = assess_case(case)
        return {"actionable": res["actionable"],
                "reason": ("actionable" if res["actionable"] else "; ".join(res["reasons"])[:200]),
                "n_load_bearing": res["n_load_bearing"], "n_hops": res["n_hops"], "case": case.to_dict()}
    except Exception as e:
        return {"actionable": False, "reason": f"deep read failed the gate: {e}"}


def deep_keep(p: dict, v: dict) -> bool:
    return bool(v.get("actionable"))


PROTEUS_LENS = Lens(name="proteus", tiers=[
    Tier(name="triage", model="sonnet", effort="low",
         prompt=triage_prompt, keep=triage_keep, est_tokens=TRIAGE_EST_TOKENS),
    Tier(name="deep", model="opus", effort="high",
         prompt=deep_prompt, parse=deep_parse, keep=deep_keep, est_tokens=DEEP_EST_TOKENS),
])
