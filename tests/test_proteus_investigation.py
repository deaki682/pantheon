"""The web-detective discipline: a Proteus web thesis may reach the book only as a
followed, triangulated, narrative-gap investigation — never a single-source glance
or an unconfirmed number off a news paraphrase."""
import pytest

from proteus.investigation import (
    CaseFile,
    Claim,
    InvestigationError,
    NarrativeGap,
    Source,
    assess_case,
    claim_solid,
)


def _news(origin):
    return Source("news", origin=origin, ref=f"https://{origin}/x")


def _filing():
    return Source("sec_filing", origin="sec.gov", ref="accession 0001-24-000001")


# ---- claim-level: web is for leads, primary is for truth -------------------
def test_numeric_load_bearing_needs_primary_confirmation():
    # two independent NEWS sources triangulate, but a number still needs the tape/filing
    c = Claim("EPS grew 40%", kind="numeric", load_bearing=True,
              sources=[_news("reuters.com"), _news("bloomberg.com")])
    ok, why = claim_solid(c)
    assert ok is False and "primary" in why


def test_numeric_load_bearing_solid_with_primary():
    c = Claim("share count fell 12%", kind="numeric", load_bearing=True,
              sources=[_news("reuters.com"), _filing()])
    assert claim_solid(c)[0] is True


def test_qualitative_load_bearing_needs_triangulation_not_primary():
    # a judgment can't be tape-confirmed, but one source isn't enough
    one = Claim("management has a history of broken guidance", kind="qualitative",
                load_bearing=True, sources=[_news("bloomberg.com")])
    assert claim_solid(one)[0] is False
    two = Claim("management has a history of broken guidance", kind="qualitative",
                load_bearing=True, sources=[_news("bloomberg.com"), _news("wsj.com")])
    assert claim_solid(two)[0] is True


def test_same_wire_is_one_source():
    # two stories off the same outlet do NOT triangulate
    c = Claim("x", kind="qualitative", load_bearing=True,
              sources=[Source("news", origin="reuters.com", ref="a"),
                       Source("news", origin="reuters.com", ref="b")])
    assert c.independent_count() == 1
    assert claim_solid(c)[0] is False


def test_color_claim_always_passes():
    assert claim_solid(Claim("nice office", kind="qualitative", load_bearing=False))[0] is True


def test_bad_kind_raises():
    with pytest.raises(InvestigationError):
        claim_solid(Claim("x", kind="vibes", load_bearing=True))


# ---- case-level: narrative gap + followed trail ----------------------------
def _good_case():
    return CaseFile(
        symbol="XYZ",
        hypothesis="Supplier revenue spike implies an un-modeled ramp at the customer",
        narrative=NarrativeGap(
            consensus="The Street models XYZ's core segment as flat and prices it as ex-growth.",
            variant="A key supplier's disclosed backlog and two industry reports imply a volume ramp not in consensus numbers.",
            catalyst="Next print (≈6 weeks) should show the ramp; a covering analyst is likely to re-rate."),
        claims=[
            Claim("supplier backlog +60% QoQ", kind="numeric", load_bearing=True,
                  sources=[_filing(), _news("industryweek.com")]),
            Claim("the customer is XYZ per two trade reports", kind="qualitative", load_bearing=True,
                  sources=[_news("industryweek.com"), _news("theinformation.com")]),
        ],
        trail=["supplier 10-Q backlog jump", "trade press names the customer", "XYZ tape near 52wk low"],
    )


def test_good_case_is_actionable():
    r = assess_case(_good_case())
    assert r["actionable"] is True and r["reasons"] == []
    assert r["n_load_bearing"] == 2 and r["n_solid"] == 2


def test_single_glance_not_actionable():
    case = _good_case()
    case.trail = ["read one article"]
    r = assess_case(case)
    assert r["actionable"] is False
    assert any("single glance" in x for x in r["reasons"])


def test_obvious_take_no_gap_rejected():
    case = _good_case()
    case.narrative = NarrativeGap(consensus="It's a great company and everyone knows it.",
                                  variant="It's a great company and everyone knows it.",
                                  catalyst="earnings")
    r = assess_case(case)
    assert r["actionable"] is False
    assert any("obvious take" in x or "restates consensus" in x for x in r["reasons"])


def test_unconfirmed_number_sinks_the_case():
    case = _good_case()
    case.claims[0] = Claim("supplier backlog +60% QoQ", kind="numeric", load_bearing=True,
                           sources=[_news("reuters.com"), _news("bloomberg.com")])  # no primary
    r = assess_case(case)
    assert r["actionable"] is False and len(r["weak_claims"]) == 1


def test_no_load_bearing_claim_is_a_vibe():
    case = _good_case()
    for c in case.claims:
        c.load_bearing = False
    r = assess_case(case)
    assert r["actionable"] is False
    assert any("vibe" in x for x in r["reasons"])
