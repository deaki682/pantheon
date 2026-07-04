import pytest

from plutus.overlay import (QualityRead, conviction_weights, apply_overlay,
                            PER_NAME_CAP, CASH_FLOOR, CONVICTION_MIN, CONVICTION_MAX)
from plutus.strategy import _rank_map


# ── composite ranking (pure) ──────────────────────────────────────────

def test_rank_map_ascending_and_descending():
    s = {"A": 1.0, "B": 2.0, "C": 3.0}
    asc = _rank_map(s, ascending=True)    # small = best
    assert asc["A"] == 0 and asc["C"] == 2
    desc = _rank_map(s, ascending=False)  # large = best
    assert desc["C"] == 0 and desc["A"] == 2


# ── conviction read clamping ──────────────────────────────────────────

def test_quality_read_clamps_conviction():
    assert QualityRead("X", True, 5.0).clamped() == CONVICTION_MAX
    assert QualityRead("X", True, 0.1).clamped() == CONVICTION_MIN
    assert QualityRead("X", True, 1.3).clamped() == pytest.approx(1.3)


# ── weighting: equal / conviction / cap-weight tilt ───────────────────

def test_equal_weight_when_flat_conviction_no_cap_lean():
    names = [f"S{i}" for i in range(10)]
    conv = {n: 1.0 for n in names}
    w = conviction_weights(names, conv, cap_blend=0.0)
    invest = 1.0 - CASH_FLOOR
    for n in names:
        assert w[n] == pytest.approx(invest / 10)
    assert sum(w.values()) == pytest.approx(invest)


def test_conviction_tilt_orders_weights():
    # realistic basket (24 names) where the concentration cap does not bind, so
    # the tilt is expressed proportionally to conviction.
    names = [f"S{i}" for i in range(24)]
    conv = {n: 1.0 for n in names}
    conv["HI"] = 1.5
    conv["LO"] = 0.5
    names += ["HI", "LO"]
    w = conviction_weights(names, conv, cap_blend=0.0)
    assert w["HI"] > w["S0"] > w["LO"]
    assert w["HI"] / w["LO"] == pytest.approx(3.0, rel=1e-6)  # 1.5 / 0.5


def test_cap_weight_lean_favors_larger_names():
    names = ["BIG", "SMALL"]
    conv = {"BIG": 1.0, "SMALL": 1.0}
    caps = {"BIG": 1_000_000.0, "SMALL": 1_000.0}
    w = conviction_weights(names, conv, caps, cap_blend=1.0, per_name_cap=1.0)
    assert w["BIG"] > w["SMALL"]  # equal conviction, cap lean tilts to BIG


def test_per_name_cap_enforced_and_redistributed():
    # a large basket (40 names) where 2x-equal < PER_NAME_CAP, so the hard 6%
    # ceiling binds: one monster conviction must still be capped at PER_NAME_CAP.
    names = [f"S{i}" for i in range(40)]
    conv = {n: 1.0 for n in names}
    conv["S0"] = 100.0
    w = conviction_weights(names, conv, cap_blend=0.0)
    assert w["S0"] <= PER_NAME_CAP + 1e-9
    # no name exceeds the cap; total never exceeds investable
    assert max(w.values()) <= PER_NAME_CAP + 1e-9
    assert sum(w.values()) <= (1.0 - CASH_FLOOR) + 1e-9


def test_cash_floor_leaves_residual():
    names = ["A", "B"]
    conv = {"A": 1.0, "B": 1.0}
    w = conviction_weights(names, conv, cap_blend=0.0)
    assert sum(w.values()) == pytest.approx(1.0 - CASH_FLOOR)
    assert 1.0 - sum(w.values()) == pytest.approx(CASH_FLOOR)


# ── apply_overlay: prune + weight ─────────────────────────────────────

def test_apply_overlay_prunes_dropped_names():
    cands = ["KEEP1", "DROP", "KEEP2", "NOREAD"]
    reads = {
        "KEEP1": QualityRead("KEEP1", True, 1.5, "cheap, cash-funded"),
        "DROP": QualityRead("DROP", False, 1.0, "financed buyback, PE 65"),
        "KEEP2": QualityRead("KEEP2", True, 1.0, "solid"),
        # NOREAD has no entry → dropped
    }
    w = apply_overlay(cands, reads, cap_blend=0.0)
    assert set(w.keys()) == {"KEEP1", "KEEP2"}
    assert w["KEEP1"] > w["KEEP2"]  # higher conviction


def test_apply_overlay_empty_when_all_dropped():
    cands = ["A", "B"]
    reads = {"A": QualityRead("A", False), "B": QualityRead("B", False)}
    assert apply_overlay(cands, reads) == {}  # sit in cash — legitimate


def test_apply_overlay_default_has_cap_lean():
    # with the deluxe default cap_blend, a bigger name gets more weight even at
    # equal conviction
    cands = ["BIG", "SMALL"]
    reads = {"BIG": QualityRead("BIG", True, 1.0), "SMALL": QualityRead("SMALL", True, 1.0)}
    caps = {"BIG": 5e11, "SMALL": 5e9}
    w = apply_overlay(cands, reads, caps)  # cap_blend defaults to 0.5
    assert w["BIG"] > w["SMALL"]
