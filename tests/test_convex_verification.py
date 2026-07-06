"""Primary-source verification gate (2026-07-06).

Regression test for the gate that would have blocked all four of the launch-gate
kills (XRN/SMHI/MNRO/GYRO) while passing the four survivors (RNA/ARVN/VTSI/ALCO).
Each trap corresponds to a specific real failure; if any of these assertions
breaks, the gate has stopped encoding tonight's lesson.
"""
import pytest

from oracle.convex_dossier import (
    make_convex_dossier, verify_dossier, is_fundable, rank_fundable,
    is_primary_citation,
)


def _dossier(sym="TEST", floor_pct=0.25, upside_x=1.6, prob_upside=0.4, runup=0.0):
    return make_convex_dossier(
        sym, business="a real small-cap business description",
        thesis="t" * 130, floor_pct=floor_pct, upside_x=upside_x, prob_upside=prob_upside,
        why_mispriced_type="neglect", why_mispriced="w" * 45, catalyst="a specific catalyst",
        catalyst_date="2026-12-31", falsifiable_prediction="p" * 25, prediction_date="2027-01-01",
        kill_condition="k", kill_condition_type="drawdown_pct", kill_condition_value=0.25,
        adversarial="a" * 65, citations=[], current_price=10.0, recent_runup_pct=runup)


def _verify(d, **kw):
    base = dict(floor_basis="cash", debt_reconciled_full_stack=True, catalyst_fired=False,
                book_survives_goodwill=None, primary_citations=["10-Q acc 0001-26-000001"],
                verdict="keep")
    base.update(kw)
    return verify_dossier(d, **base)


def test_primary_citation_detection():
    assert is_primary_citation("10-Q acc 0001628280-26-033669")
    assert is_primary_citation("https://www.sec.gov/Archives/edgar/data/123/x.htm")
    assert is_primary_citation("FY2025 10-K")
    assert is_primary_citation("Schedule 13D 2026-06-22")
    # snapshots and secondary recaps are NOT primary
    assert not is_primary_citation("Robinhood fundamentals 2026-07-02")
    assert not is_primary_citation("StockTitan recap")
    assert not is_primary_citation("Yahoo Finance quote")


def test_unverified_dossier_is_not_fundable():
    d = _dossier()
    assert d.get("convex") is True          # self-reported numbers are fine
    assert not d.get("verified")            # but it has not been verified
    assert not is_fundable(d)               # so it cannot be funded


def test_verified_cash_floor_is_fundable():
    d = _verify(_dossier())
    assert d["verified"] is True
    assert is_fundable(d) is True
    assert d["floor_hardness"] == "hard"    # cash floor re-stamped hard


# --- the four traps, each a real tonight-kill ---

def test_trap_xrn_snapshot_only_and_missed_debt():
    # XRN: cited only a fundamentals snapshot AND missed a $652.7M credit line
    d = _verify(_dossier("XRN"), primary_citations=["Robinhood fundamentals"],
                debt_reconciled_full_stack=False, floor_basis="book", verdict="kill")
    assert d["verification"]["traps"]["primary_source_cited"] is False
    assert d["verification"]["traps"]["debt_reconciled_full_stack"] is False
    assert not is_fundable(d)


def test_trap_smhi_asserted_floor_and_fired_catalyst():
    # SMHI: "$20 NAV" was an activist claim in no filing; catalyst already popped
    d = _verify(_dossier("SMHI"), floor_basis="asserted", catalyst_fired=True, verdict="kill")
    assert d["verification"]["traps"]["floor_not_merely_asserted"] is False
    assert d["verification"]["traps"]["catalyst_not_already_fired"] is False
    assert not is_fundable(d)


def test_trap_mnro_goodwill_masks_negative_tangible_book():
    # MNRO: P/B<1 was 100% goodwill; tangible book negative
    d = _verify(_dossier("MNRO"), floor_basis="book", book_survives_goodwill=False, verdict="kill")
    assert d["verification"]["traps"]["book_survives_goodwill"] is False
    assert not is_fundable(d)


def test_trap_gyro_asserted_projection_floor():
    # GYRO: "$11.79 floor" was a melting management projection, not an audited NAV
    d = _verify(_dossier("GYRO"), floor_basis="asserted", verdict="kill")
    assert d["verification"]["traps"]["floor_not_merely_asserted"] is False
    assert not is_fundable(d)


def test_the_full_launch_gate_separation():
    """All four kills BLOCKED, all four survivors PASS — the property the gate exists for."""
    kills = {
        "XRN":  dict(floor_basis="book", debt_reconciled_full_stack=False, catalyst_fired=False,
                     primary_citations=["Robinhood fundamentals"], verdict="kill"),
        "SMHI": dict(floor_basis="asserted", catalyst_fired=True, verdict="kill"),
        "MNRO": dict(floor_basis="book", book_survives_goodwill=False, verdict="kill"),
        "GYRO": dict(floor_basis="asserted", verdict="kill"),
    }
    survivors = {
        "RNA":  dict(floor_basis="cash", verdict="revise"),
        "ARVN": dict(floor_basis="cash", verdict="revise"),
        "VTSI": dict(floor_basis="cash", verdict="revise"),
        "ALCO": dict(floor_basis="transacting_asset", verdict="revise"),
    }
    for sym, kw in kills.items():
        assert not is_fundable(_verify(_dossier(sym), **kw)), f"{sym} kill slipped through"
    for sym, kw in survivors.items():
        assert is_fundable(_verify(_dossier(sym), **kw)), f"{sym} survivor wrongly blocked"


def test_rank_fundable_excludes_unverified():
    verified = _verify(_dossier("AAA", floor_pct=0.2, upside_x=1.5, prob_upside=0.5))
    unverified = _dossier("BBB", floor_pct=0.2, upside_x=2.0, prob_upside=0.6)  # better math, not verified
    ranked = rank_fundable([verified, unverified])
    assert [d["symbol"] for d in ranked] == ["AAA"]  # unverified excluded despite better numbers


def test_kill_verdict_blocks_even_if_traps_pass():
    # a reader can veto with verdict=kill even when the mechanical traps pass
    d = _verify(_dossier(), verdict="kill")
    assert d["verified"] is False
    assert not is_fundable(d)


# --- 2026-07-06 audit fixes: gate fail-open holes closed ---
from oracle import convex_dossier as _cd


def test_primary_citation_rejects_incidental_substrings():
    # snapshot-only citations must NOT pass on incidental characters
    assert _cd.is_primary_citation("Q3 consensus-1.2% miss, StockTitan recap") is False
    assert _cd.is_primary_citation("Robinhood fundamentals; accrued interest note") is False
    assert _cd.is_primary_citation("Yahoo Finance key statistics") is False
    # real primary sources still pass
    assert _cd.is_primary_citation("10-Q filed 2026-05-14") is True
    assert _cd.is_primary_citation("SEC accession 0001171843-26-003419") is True
    assert _cd.is_primary_citation("https://www.sec.gov/Archives/edgar/data/...") is True


def test_book_floor_goodwill_trap_fails_closed_on_unknown():
    d = _cd.make_convex_dossier(
        "TST", business="b", thesis="x" * 130,
        floor_pct=0.2, upside_x=1.5, prob_upside=0.5,
        why_mispriced_type="neglect", why_mispriced="y" * 45,
        catalyst="c", catalyst_date="", falsifiable_prediction="p" * 25,
        prediction_date="2027-01-01", kill_condition="k", kill_condition_type="thesis_date",
        kill_condition_value="2027-01-01", adversarial="z" * 65,
        citations=["10-K accession 0001234567-26-000001"], current_price=1.0)
    # book floor + goodwill UNKNOWN (None) must NOT verify (MNRO trap)
    _cd.verify_dossier(d, floor_basis="book", debt_reconciled_full_stack=True,
                       catalyst_fired=False, book_survives_goodwill=None, verdict="keep")
    assert d["verified"] is False
    # explicit confirmation passes
    _cd.verify_dossier(d, floor_basis="book", debt_reconciled_full_stack=True,
                       catalyst_fired=False, book_survives_goodwill=True, verdict="keep")
    assert d["verified"] is True
    # a CASH floor with unknown goodwill still passes (goodwill irrelevant)
    _cd.verify_dossier(d, floor_basis="cash", debt_reconciled_full_stack=True,
                       catalyst_fired=False, book_survives_goodwill=None, verdict="keep")
    assert d["verified"] is True
