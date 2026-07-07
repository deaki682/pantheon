"""The Oracle/Proteus lenses on the shared cascade — proving the tonight-built
gates (resolve_bears, assess_case) actually decide fundability inside the harness,
with STUBBED model output (zero tokens). This is the 'one machine, two lenses'
wiring test."""
from oracle.lens import ORACLE_LENS, deep_parse as oracle_deep_parse
from proteus.lens import PROTEUS_LENS, deep_parse as proteus_deep_parse
from shared.read_cascade import build_packet, run_cascade

CITE = ["10-Q Q1-FY2026 (accession 0001234567-26-000045)"]

_GOOD_DOSSIER = dict(
    business="A thinly-covered maker of industrial widgets.",
    thesis=("Revenue growth is re-accelerating as the new product line ramps into a demand shift the "
            "two remaining analysts have not modelled; consensus underweights the 24-month trajectory."),
    inflection_type="product_ramp",
    inflection_evidence="Product-line revenue grew 41% q/q in the latest 10-Q, up from 12% (accel).",
    upside_x=2.2, prob_upside=0.45, downside_pct=0.35,
    catalyst="Next two prints confirm the ramp; a covering analyst initiates.",
    catalyst_date="2026-11-01", horizon_months=12.0, runway_months=30.0,
    falsifiable_prediction="Revenue growth stays above 30% y/y through FY2026.",
    prediction_date="2027-03-01", kill_condition="Growth decelerates below 15% y/y.",
    kill_type="fundamental_break", kill_value="growth<15%",
    adversarial="The ramp could be a pull-forward; if the new line cannibalises the base, growth stalls.",
    citations=list(CITE), current_price=10.0,
)
_GOOD_BEARS = [
    {"critique_type": "guidance_contradiction", "critique": "Next-quarter guidance implies deceleration, not the reaccel.",
     "severity": 0.8, "defense": "The 10-Q MD&A guides FY revenue +30-32%, ABOVE trailing; the decel misreads one seasonal quarter.",
     "defense_citations": list(CITE), "concede": False},
    {"critique_type": "one_time_driver", "critique": "The margin turn looks like a one-time cost credit.",
     "severity": 0.6, "defense": "Gross margin ex-credit is still +240bps; the 10-Q reconciles the $2M credit vs an $18M gain.",
     "defense_citations": list(CITE), "concede": False},
    {"critique_type": "valuation_priced_in", "critique": "At ~1.9x sales the ramp may be priced in.",
     "severity": 0.5, "defense": "Comps trade ~3.2x on similar growth; the 10-K discloses backlog not yet in consensus.",
     "defense_citations": ["10-K FY2025 (accession 0001234567-26-000045)"], "concede": False},
]


# ---- Oracle deep parse runs the BEAR gate ----------------------------------
def test_oracle_deep_parse_funds_a_survivor():
    raw = {"dossier": _GOOD_DOSSIER, "blowup": {"going_concern": False, "fraud": False, "delisting": False},
           "bears": _GOOD_BEARS}
    v = oracle_deep_parse(raw, build_packet(symbol="ABCD"))
    assert v["fundable"] is True and v["bear_verdict"] == "survived"


def test_oracle_deep_parse_refuses_fatal_conceded():
    raw = {"dossier": _GOOD_DOSSIER, "blowup": {"going_concern": False, "fraud": False, "delisting": False},
           "bears": _GOOD_BEARS + [{"critique_type": "faked_earnings",
                                    "critique": "The GAAP profit is entirely a one-time equity-sale gain.",
                                    "severity": 0.9, "defense": "", "defense_citations": [], "concede": True}]}
    v = oracle_deep_parse(raw, build_packet(symbol="ABCD"))
    assert v["fundable"] is False


def test_oracle_deep_parse_malformed_read_not_fundable():
    v = oracle_deep_parse({"dossier": {"symbol": "X"}}, build_packet(symbol="X"))  # missing required fields
    assert v["fundable"] is False and "failed the gate" in v["reason"]


def test_oracle_cascade_end_to_end():
    packets = [build_packet(symbol="GOOD"), build_packet(symbol="MEH")]
    triage = {"GOOD": {"advance": True}, "MEH": {"advance": False}}
    deep = {"GOOD": {"dossier": _GOOD_DOSSIER, "blowup": {}, "bears": _GOOD_BEARS}}

    def model_read(reqs):
        return [(triage[r["symbol"]] if r["model"] == "sonnet" else deep[r["symbol"]]) for r in reqs]

    r = run_cascade(packets, ORACLE_LENS, model_read, budget_tokens=10_000_000)
    assert [s["symbol"] for s in r.survivors] == ["GOOD"]          # MEH dropped at triage, GOOD funded
    assert r.survivors[0]["deep_verdict"]["fundable"] is True


# ---- Proteus deep parse runs the investigation gate ------------------------
def _good_case():
    return {
        "hypothesis": "Supplier revenue spike implies an un-modeled ramp at the customer",
        "narrative": {"consensus": "The Street models XYZ's core segment as flat and prices it ex-growth.",
                      "variant": "A key supplier's disclosed backlog and two trade reports imply a volume ramp not in consensus.",
                      "catalyst": "Next print (~6 weeks) should show the ramp; a covering analyst may re-rate."},
        "claims": [
            {"text": "supplier backlog +60% QoQ", "kind": "numeric", "load_bearing": True,
             "sources": [{"source_type": "sec_filing", "origin": "sec.gov", "ref": "acc-1"},
                         {"source_type": "news", "origin": "industryweek.com", "ref": "u1"}]},
            {"text": "the customer is XYZ per two trade reports", "kind": "qualitative", "load_bearing": True,
             "sources": [{"source_type": "news", "origin": "industryweek.com", "ref": "u2"},
                         {"source_type": "news", "origin": "theinformation.com", "ref": "u3"}]},
        ],
        "trail": ["supplier 10-Q backlog jump", "trade press names the customer", "XYZ tape near 52wk low"],
    }


def test_proteus_deep_parse_actions_a_real_gap():
    v = proteus_deep_parse(_good_case(), build_packet(symbol="XYZ"))
    assert v["actionable"] is True


def test_proteus_deep_parse_refuses_single_glance():
    case = _good_case()
    case["trail"] = ["read one article"]
    v = proteus_deep_parse(case, build_packet(symbol="XYZ"))
    assert v["actionable"] is False


def test_proteus_deep_parse_refuses_unconfirmed_number():
    case = _good_case()
    # strip the primary source off the numeric load-bearing claim
    case["claims"][0]["sources"] = [{"source_type": "news", "origin": "reuters.com", "ref": "u"},
                                    {"source_type": "news", "origin": "bloomberg.com", "ref": "u"}]
    v = proteus_deep_parse(case, build_packet(symbol="XYZ"))
    assert v["actionable"] is False


def test_proteus_cascade_end_to_end():
    packets = [build_packet(symbol="XYZ"), build_packet(symbol="NUL")]
    triage = {"XYZ": {"advance": True}, "NUL": {"advance": False}}
    deep = {"XYZ": _good_case()}

    def model_read(reqs):
        return [(triage[r["symbol"]] if r["model"] == "sonnet" else deep[r["symbol"]]) for r in reqs]

    r = run_cascade(packets, PROTEUS_LENS, model_read, budget_tokens=10_000_000)
    assert [s["symbol"] for s in r.survivors] == ["XYZ"]
    assert r.survivors[0]["deep_verdict"]["actionable"] is True
