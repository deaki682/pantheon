"""The read-cascade harness, tested with a STUBBED model — zero tokens. This is
the whole point of the injected `model_read` seam: the full pipeline (routing,
budget cap, gating, coverage, dedup) runs end-to-end for free, so a harness bug
can never survive to a real run. The only thing NOT covered here is whether the
real reads have edge — that's the paid calibration, deliberately kept separate."""
import pytest

from shared.read_cascade import (
    CascadeResult,
    Lens,
    Tier,
    build_packet,
    estimate_cost,
    run_cascade,
)


def make_reader(fn):
    """A stub model_read: applies `fn(req)->raw` to each request, in order."""
    def _read(reqs):
        return [fn(r) for r in reqs]
    return _read


def _pk(sym, **kw):
    return build_packet(symbol=sym, **kw)


# A two-tier test lens. Triage advances on verdict['advance']; deep runs a tiny
# "gate" in parse (survived = defended and not conceded) and keeps on 'fundable'.
def _triage_tier(est=500):
    return Tier(name="triage", model="sonnet", effort="low",
                prompt=lambda p: f"triage {p['symbol']}",
                keep=lambda p, v: bool(v.get("advance")), est_tokens=est)


def _deep_gate(raw, packet):
    # deterministic "gate": fundable iff the read defended it and conceded nothing
    return {**raw, "fundable": bool(raw.get("defended") and not raw.get("conceded"))}


def _deep_tier(est=5000):
    return Tier(name="deep", model="opus", effort="high",
                prompt=lambda p: f"deep {p['symbol']}",
                parse=_deep_gate, keep=lambda p, v: bool(v.get("fundable")), est_tokens=est)


LENS = Lens(name="test", tiers=[_triage_tier(), _deep_tier()])


# ---- routing: cheap tier filters, expensive tier + gate decides -------------
def test_two_tier_routing():
    packets = [_pk("A"), _pk("B"), _pk("C"), _pk("D")]
    # triage advances A,B,C (drops D); deep funds only A
    triage = {"A": {"advance": True}, "B": {"advance": True}, "C": {"advance": True}, "D": {"advance": False}}
    deep = {"A": {"defended": True, "conceded": False},   # -> fundable
            "B": {"defended": True, "conceded": True},    # conceded -> not fundable
            "C": {"defended": False, "conceded": False}}  # not defended -> not fundable

    def fn(req):
        return (triage if req["model"] == "sonnet" else deep)[req["symbol"]]

    r = run_cascade(packets, LENS, make_reader(fn), budget_tokens=10_000_000)
    assert [s["symbol"] for s in r.survivors] == ["A"]
    assert r.coverage["triage"] == {"read": 4, "advanced": 3, "dropped": 1, "skipped_budget": 0}
    assert r.coverage["deep"] == {"read": 3, "advanced": 1, "dropped": 2, "skipped_budget": 0}
    # every non-survivor is recorded with the tier that killed it — no silent loss
    killed = {(d.symbol, d.tier) for d in r.dropped}
    assert killed == {("D", "triage"), ("B", "deep"), ("C", "deep")}
    # the survivor carries both tier verdicts
    assert r.survivors[0]["triage_verdict"]["advance"] is True
    assert r.survivors[0]["deep_verdict"]["fundable"] is True


def test_dedup_reads_each_name_once():
    packets = [_pk("A"), _pk("A"), _pk("B")]
    seen_syms = []

    def fn(req):
        seen_syms.append(req["symbol"])
        return {"advance": True, "defended": True, "conceded": False}

    r = run_cascade(packets, LENS, make_reader(fn), budget_tokens=10_000_000)
    # A read once per tier, not twice
    assert seen_syms.count("A") == 2  # once in triage, once in deep — never duplicated within a tier
    assert r.coverage["triage"]["read"] == 2  # A, B (deduped), not 3


# ---- budget: a hard ceiling with HONEST truncation, never silent ------------
def test_budget_cap_truncates_and_logs():
    packets = [_pk(s) for s in "ABCDE"]
    # triage est 500/name; a tiny 1000 budget affords only 2 triage reads, and
    # then nothing at the deep tier — the 2 triage survivors get starved there.
    r = run_cascade(packets, LENS, make_reader(lambda req: {"advance": True, "defended": True, "conceded": False}),
                    budget_tokens=1000)  # 1000 // 500 = 2 reads
    assert r.coverage["triage"]["read"] == 2
    assert r.budget_hit is True
    # CONSERVATION: every name is accounted for — nothing silently vanishes.
    # C,D,E skipped at triage; A,B read at triage then starved at the deep tier.
    assert set(r.skipped_for_budget) == {"A", "B", "C", "D", "E"}
    assert r.coverage["triage"]["skipped_budget"] == 3
    assert r.survivors == []


def test_realistic_budget_binds_on_deep_not_triage():
    # the intended cascade shape: the cheap tier reads the WHOLE field, and the
    # expensive tier is where the budget actually binds.
    packets = [_pk(s) for s in "ABCDEF"]  # 6 names
    fn = lambda req: {"advance": True, "defended": True, "conceded": False}
    # triage 6*500=3000; remaining 15000 // 5000 = 3 deep reads
    r = run_cascade(packets, LENS, make_reader(fn), budget_tokens=18_000)
    assert r.coverage["triage"]["read"] == 6      # cheap tier covered everything
    assert r.coverage["deep"]["read"] == 3        # deep binds: 3 of 6 survivors afforded
    assert r.budget_hit is True
    assert len(r.skipped_for_budget) == 3         # the 3 deep-starved names are named


def test_full_budget_reads_everything():
    packets = [_pk(s) for s in "ABCDE"]
    r = run_cascade(packets, LENS, make_reader(lambda req: {"advance": False}),
                    budget_tokens=10_000_000)
    assert r.budget_hit is False and r.skipped_for_budget == []
    assert r.coverage["triage"]["read"] == 5


def test_actual_token_spend_overrides_estimate():
    packets = [_pk("A"), _pk("B")]
    # verdicts report ACTUAL tokens; spend should reflect those, not the est
    r = run_cascade(packets, Lens("t", [_triage_tier()]), make_reader(lambda req: {"advance": False, "_tokens": 123}),
                    budget_tokens=10_000_000)
    assert r.spent_tokens == 246  # 2 reads * 123 actual, not 2*500 est


# ---- dry-run cost, no model touched ----------------------------------------
def test_estimate_cost_projects_down_the_cascade():
    est = estimate_cost(100, LENS, keep_rate=0.4, price_per_1k_tokens=3.0)
    assert est["per_tier"][0] == {"tier": "triage", "model": "sonnet", "reads": 100, "est_tokens": 50_000}
    assert est["per_tier"][1] == {"tier": "deep", "model": "opus", "reads": 40, "est_tokens": 200_000}
    assert est["est_total_tokens"] == 250_000
    assert est["est_cost_usd"] == round(250_000 / 1000 * 3.0, 2)


# ---- edges -----------------------------------------------------------------
def test_empty_packets():
    r = run_cascade([], LENS, make_reader(lambda req: {}), budget_tokens=1_000)
    assert r.survivors == [] and r.dropped == [] and r.spent_tokens == 0
    assert r.skipped_for_budget == []


def test_model_read_must_be_one_to_one():
    packets = [_pk("A"), _pk("B")]
    bad = lambda reqs: [{"advance": True}]  # returns 1 for 2 reqs
    with pytest.raises(ValueError):
        run_cascade(packets, LENS, bad, budget_tokens=10_000)


def test_zero_budget_reads_nothing():
    packets = [_pk("A")]
    r = run_cascade(packets, LENS, make_reader(lambda req: {"advance": True}), budget_tokens=0)
    assert r.survivors == [] and r.skipped_for_budget == ["A"] and r.budget_hit is True


def test_build_packet_shape():
    p = build_packet(symbol="xyz", name="XYZ Inc", mcap_musd=500.0,
                     revenue_trajectory=[10, 12, 15], theme="ai")
    assert p["symbol"] == "XYZ" and p["name"] == "XYZ Inc" and p["mcap_musd"] == 500.0
    assert p["revenue_trajectory"] == [10, 12, 15]
    assert p["theme"] == "ai"  # god-specific extra fields pass through
