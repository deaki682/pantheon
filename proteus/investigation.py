"""proteus/investigation.py — the web-detective discipline, made structural.

Proteus at his best is an INVESTIGATOR of the living information web: he follows a
thread across dispersed, unstructured sources (news, filings, forums, industry
press, foreign reports) to find a NARRATIVE GAP — the market believes X, the
scattered evidence says Y, and Z forces the update. His superpower (roaming) and
his failure mode (skimming stale/hyped/single-source noise — Session 1 was fooled
by a five-month-stale price print) are the SAME faculty, so the discipline is not
optional: it is what separates a detective from a well-read guy repeating what he
read.

`proteus/journal.py` already validates the OUTPUT (a decision with a falsifiable
prediction + typed kill). This validates the RESEARCH BEHIND IT, before it earns a
book slot. The two rules, encoded:

  1. "THE WEB IS FOR LEADS, THE PRIMARY SOURCE IS FOR TRUTH." A load-bearing
     NUMERIC claim (a price, a share count, a date, a fundamental) must be
     confirmed against a PRIMARY source — an SEC filing, the broker tape, a
     regulatory docket, a court record — not a news paraphrase. Qualitative
     load-bearing claims can't be tape-confirmed, so they instead need
     TRIANGULATION.
  2. TRIANGULATION. Any load-bearing claim needs >=2 INDEPENDENT sources (two
     articles off the same wire are one source). Independence keys on the
     outlet/domain, not the source type.

And the thesis SHAPE that makes a web edge real rather than the obvious take: you
must be able to state the CONSENSUS you are betting against. If you can't say what
the market believes that is wrong, you have no edge — you have the headline
everyone already read. `assess_case` refuses a case that is single-source, has no
stated consensus-vs-variant gap, has no catalyst, rests on an unconfirmed number,
or is a single glance rather than a followed thread.

This is the harness. The roaming judgment is the live agent with WebSearch /
WebFetch; this module structures and gates it — the same "build the machine, not
the picks" move as Oracle's bear gate and Hermes's deal enumerator.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

# Primary = independently verifiable HARD fact. Everything else is a LEAD.
PRIMARY_SOURCE_TYPES = {"sec_filing", "broker_tape", "regulatory_docket", "court_record"}
LEAD_SOURCE_TYPES = {"news", "analyst", "forum", "social", "blog", "industry_press",
                     "podcast", "company_ir", "expert", "foreign_press", "other"}
CLAIM_KINDS = {"numeric", "qualitative"}

MIN_INDEPENDENT = 2        # triangulation floor for a load-bearing claim
MIN_TRAIL_HOPS = 2         # a single glance is not an investigation (synthesis is the job)


class InvestigationError(ValueError):
    pass


@dataclass
class Source:
    """One place a claim came from. `origin` is the independence key (outlet or
    domain) — two stories off the same wire share an origin and count once."""
    source_type: str
    origin: str = ""          # outlet / domain / publisher
    ref: str = ""             # url / accession / citation

    def is_primary(self) -> bool:
        return self.source_type in PRIMARY_SOURCE_TYPES

    def key(self) -> str:
        return (self.origin or self.source_type).strip().lower()


@dataclass
class Claim:
    """A factual assertion the thesis may lean on. `kind` numeric (a checkable
    number/date/fundamental) vs qualitative (a judgment/narrative fact).
    `load_bearing` = the thesis fails if this is wrong / it touches sizing."""
    text: str
    kind: str
    load_bearing: bool
    sources: list[Source] = field(default_factory=list)

    def independent_count(self) -> int:
        return len({s.key() for s in self.sources if s.key()})

    def has_primary(self) -> bool:
        return any(s.is_primary() for s in self.sources)


def claim_solid(claim: Claim) -> tuple[bool, str]:
    """Is this claim sturdy enough to bear weight? Color (non-load-bearing) always
    passes; a load-bearing claim must be triangulated, and if it's a NUMBER it must
    be primary-confirmed (the web is for leads, the tape/filing is for truth)."""
    if claim.kind not in CLAIM_KINDS:
        raise InvestigationError(f"claim.kind must be one of {sorted(CLAIM_KINDS)}")
    if not claim.load_bearing:
        return True, "color (not load-bearing)"
    if claim.independent_count() < MIN_INDEPENDENT:
        return False, f"single-source load-bearing claim — needs ≥{MIN_INDEPENDENT} independent sources (triangulate)"
    if claim.kind == "numeric" and not claim.has_primary():
        return False, "numeric load-bearing claim not confirmed against a primary source (web is for leads, tape/filing is for truth)"
    return True, "solid"


@dataclass
class NarrativeGap:
    consensus: str            # what the market currently believes
    variant: str              # what the corroborated evidence says instead
    catalyst: str             # what forces the market to update, and roughly when


@dataclass
class CaseFile:
    """A followed investigation: the lead, the narrative gap, the corroborated
    claims, and the ordered trail of hops (auditable — the edge IS the chain of
    dispersed dots, so the thesis is only as good as its cited path)."""
    symbol: str
    hypothesis: str
    narrative: NarrativeGap
    claims: list[Claim] = field(default_factory=list)
    trail: list[str] = field(default_factory=list)   # ordered hops, each a cited step

    def to_dict(self) -> dict:
        return asdict(self)


def assess_case(case: CaseFile) -> dict:
    """Gate a web investigation before it may become a journal `enter`. Returns
    {actionable, reasons, weak_claims, ...}. Actionable only when the thesis has a
    real consensus-vs-variant gap + a catalyst, at least one load-bearing claim,
    every load-bearing claim solid (triangulated + numeric ones primary-confirmed),
    and an actual followed trail (≥2 hops) rather than a single glance."""
    reasons: list[str] = []
    ng = case.narrative
    if len((ng.consensus or "").strip()) < 30:
        reasons.append("no stated CONSENSUS to bet against — if you can't say what the market "
                       "believes that's wrong, there's no edge, only the obvious take")
    if len((ng.variant or "").strip()) < 30:
        reasons.append("no VARIANT view — what does the evidence say instead?")
    if len((ng.catalyst or "").strip()) < 15:
        reasons.append("no CATALYST — what forces the market to update, and when?")
    if (ng.consensus or "").strip().lower() == (ng.variant or "").strip().lower() and (ng.consensus or "").strip():
        reasons.append("variant restates consensus — no gap, that's the obvious take")

    load_bearing = [c for c in case.claims if c.load_bearing]
    if not load_bearing:
        reasons.append("no LOAD-BEARING claim — a thesis with nothing that must be true is a vibe")
    weak: list[dict] = []
    for c in case.claims:
        ok, why = claim_solid(c)
        if not ok:
            weak.append({"claim": c.text, "why": why})
    if weak:
        reasons.append(f"{len(weak)} load-bearing claim(s) not solid (triangulation / primary-confirmation)")

    if len(case.trail) < MIN_TRAIL_HOPS:
        reasons.append(f"trail has <{MIN_TRAIL_HOPS} hops — a single glance is not an investigation; "
                       "Proteus's edge is synthesis across dispersed sources, not a lone datapoint")

    return {
        "symbol": case.symbol,
        "actionable": not reasons,
        "reasons": reasons,
        "weak_claims": weak,
        "n_load_bearing": len(load_bearing),
        "n_solid": sum(1 for c in load_bearing if claim_solid(c)[0]),
        "n_hops": len(case.trail),
    }
