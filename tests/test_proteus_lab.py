"""Tests for the lab's one-way ratchet (shared.lab via the proteus shim)."""
import pytest

from proteus.lab import JournalError
from proteus import lab as L

MECH = ("Closed-end funds trading at extreme discounts into a board-mandated "
        "tender window face a price-insensitive arbitrage flow: activists who "
        "filed 13Ds must tender, and the fund must buy at NAV. The discount "
        "closes mechanically as the tender date approaches, independent of "
        "market direction, because the counterparty is contractually bound.")
WHO = ("Retail holders who sell into the discount out of boredom or tax-loss "
       "motives, without reading the tender terms.")
WHY = ("The names are sub-$300M and screened out by institutions; the tender "
       "terms live in N-2 amendments almost nobody parses.")
CLAIM = ("Discounts of >12% with an announced tender close by at least half "
         "within 40 trading days of the record date, measured over the full "
         "2020-2026 catalog.")

POP = ("Every closed-end fund tender offer announced 2020-01-01 to 2026-06-30, "
       "built from the complete EDGAR SC TO-I/N-23C-3 index — all announcements "
       "included regardless of outcome, delisted funds retained.")
METRIC = "Discount change from announcement to record date, vs sector CEF index."
CRIT = ("Supported if mean discount capture exceeds 4% with win rate >60% over "
        "the complete catalog; refuted if capture <=1%; else inconclusive.")

BIAS_OK = {k: ("Addressed in detail: " + v) for k, v in L.BIAS_CHECKLIST.items()}


def _lab_with_hypothesis():
    lab = L.load_lab("/nonexistent")
    L.new_strategy(lab, slug="cef_tender", date="2026-07-05",
                   sponsor="proteus",
                   mechanism=MECH, who_loses=WHO,
                   underutilized_because=WHY, falsifiable_claim=CLAIM)
    return lab


def _preregistered():
    lab = _lab_with_hypothesis()
    L.preregister(lab, "cef_tender", date="2026-07-05",
                  prereg_doc="docs/proteus_lab_prereg_cef_tender.md",
                  population_definition=POP, metric=METRIC,
                  success_criteria=CRIT)
    return lab


def test_hypothesis_requires_articulation():
    lab = L.load_lab("/nonexistent")
    with pytest.raises(JournalError):
        L.new_strategy(lab, slug="stub", date="2026-07-05",
                       sponsor="proteus",
                       mechanism="it goes up", who_loses=WHO,
                       underutilized_because=WHY, falsifiable_claim=CLAIM)
    assert lab["strategies"] == {}


def test_sponsor_required_and_recorded():
    lab = L.load_lab("/nonexistent")
    with pytest.raises(JournalError, match="sponsor"):
        L.new_strategy(lab, slug="orphan", date="2026-07-05", sponsor="  ",
                       mechanism=MECH, who_loses=WHO,
                       underutilized_because=WHY, falsifiable_claim=CLAIM)
    L.new_strategy(lab, slug="named", date="2026-07-05", sponsor="Operator",
                   mechanism=MECH, who_loses=WHO,
                   underutilized_because=WHY, falsifiable_claim=CLAIM)
    assert lab["strategies"]["named"]["sponsor"] == "operator"
    summary = L.pipeline_summary(lab)
    assert summary["hypotheses_ever"] == 1
    assert summary["by_sponsor"] == {"operator": 1}


def test_no_duplicate_slugs_and_counter_increments():
    lab = _lab_with_hypothesis()
    assert lab["hypotheses_ever"] == 1
    with pytest.raises(JournalError):
        L.new_strategy(lab, slug="cef_tender", date="2026-07-05",
                       sponsor="proteus",
                       mechanism=MECH, who_loses=WHO,
                       underutilized_because=WHY, falsifiable_claim=CLAIM)


def test_backtest_refused_without_prereg():
    lab = _lab_with_hypothesis()
    with pytest.raises(JournalError):
        L.record_backtest(lab, "cef_tender", date="2026-07-05", n=80,
                          mean_excess=0.05, verdict="supported",
                          bias_checklist=BIAS_OK)


def test_prereg_requires_docs_path():
    lab = _lab_with_hypothesis()
    with pytest.raises(JournalError):
        L.preregister(lab, "cef_tender", date="2026-07-05",
                      prereg_doc="notes.md", population_definition=POP,
                      metric=METRIC, success_criteria=CRIT)


def test_backtest_refused_with_incomplete_bias_checklist():
    lab = _preregistered()
    partial = dict(BIAS_OK)
    del partial["survivorship"]
    with pytest.raises(JournalError, match="survivorship"):
        L.record_backtest(lab, "cef_tender", date="2026-07-06", n=80,
                          mean_excess=0.05, verdict="supported",
                          bias_checklist=partial)
    stub = dict(BIAS_OK, look_ahead="n/a")
    with pytest.raises(JournalError, match="look_ahead"):
        L.record_backtest(lab, "cef_tender", date="2026-07-06", n=80,
                          mean_excess=0.05, verdict="supported",
                          bias_checklist=stub)


def test_backtest_records_shrunk_mean_and_one_decision_rule():
    lab = _preregistered()
    L.record_backtest(lab, "cef_tender", date="2026-07-06", n=80,
                      mean_excess=0.05, verdict="supported",
                      bias_checklist=BIAS_OK)
    bt = lab["strategies"]["cef_tender"]["backtest"]
    assert bt["mean_excess_shrunk"] == pytest.approx(80 * 0.05 / 100, abs=1e-6)
    # second cut at the same data is refused
    with pytest.raises(JournalError):
        L.record_backtest(lab, "cef_tender", date="2026-07-07", n=80,
                          mean_excess=0.06, verdict="supported",
                          bias_checklist=BIAS_OK)


def test_refuted_backtest_is_terminal():
    lab = _preregistered()
    L.record_backtest(lab, "cef_tender", date="2026-07-06", n=80,
                      mean_excess=-0.01, verdict="refuted",
                      bias_checklist=BIAS_OK)
    assert lab["strategies"]["cef_tender"]["status"] == "refuted"
    with pytest.raises(JournalError):
        L.start_forward_test(lab, "cef_tender", date="2026-07-07")


def test_forward_test_requires_supported_backtest():
    lab = _preregistered()
    L.record_backtest(lab, "cef_tender", date="2026-07-06", n=80,
                      mean_excess=0.02, verdict="inconclusive",
                      bias_checklist=BIAS_OK)
    with pytest.raises(JournalError):
        L.start_forward_test(lab, "cef_tender", date="2026-07-07")


def _forward_testing():
    lab = _preregistered()
    L.record_backtest(lab, "cef_tender", date="2026-07-06", n=80,
                      mean_excess=0.05, verdict="supported",
                      bias_checklist=BIAS_OK)
    L.start_forward_test(lab, "cef_tender", date="2026-07-07")
    return lab


def test_no_early_conclusion():
    lab = _forward_testing()
    for i in range(5):
        L.record_forward_grade(lab, "cef_tender", date="2026-08-01",
                               symbol=f"F{i}", excess=0.03)
    assert not L.evaluate_forward(lab, "cef_tender")["promotable"]
    with pytest.raises(JournalError, match="5/20"):
        L.conclude_forward(lab, "cef_tender", date="2026-08-02")


def test_validation_requires_positive_shrunk_mean():
    lab = _forward_testing()
    # 20 grades averaging +1bp: raw mean positive but shrunk stays positive
    # only if the signal is real relative to prior_n=20
    for i in range(20):
        L.record_forward_grade(lab, "cef_tender", date="2026-09-01",
                               symbol=f"W{i}", excess=0.02)
    verdict = L.evaluate_forward(lab, "cef_tender")
    assert verdict["n"] == 20
    assert verdict["mean_excess_shrunk"] == pytest.approx(20 * 0.02 / 40)
    assert verdict["promotable"]
    L.conclude_forward(lab, "cef_tender", date="2026-09-02")
    assert lab["strategies"]["cef_tender"]["status"] == "validated"
    assert L.live_citable(lab) == ["cef_tender"]


def test_negative_forward_test_refutes():
    lab = _forward_testing()
    for i in range(20):
        L.record_forward_grade(lab, "cef_tender", date="2026-09-01",
                               symbol=f"L{i}", excess=-0.01)
    L.conclude_forward(lab, "cef_tender", date="2026-09-02")
    assert lab["strategies"]["cef_tender"]["status"] == "refuted"
    assert L.live_citable(lab) == []


def test_shelving_needs_reason_and_settled_cannot_shelve():
    lab = _lab_with_hypothesis()
    with pytest.raises(JournalError):
        L.shelve(lab, "cef_tender", date="2026-07-05", reason="meh")
    L.shelve(lab, "cef_tender", date="2026-07-05",
             reason="Full N-23C-3 catalog not retrievable at current rate "
                    "limits; revisit when EDGAR bulk index is cached.")
    assert lab["strategies"]["cef_tender"]["status"] == "shelved"


def test_save_load_roundtrip(tmp_path):
    path = str(tmp_path / "lab.json")
    lab = _preregistered()
    L.save_lab(lab, path)
    loaded = L.load_lab(path)
    assert loaded["strategies"]["cef_tender"]["status"] == "preregistered"
    assert loaded["hypotheses_ever"] == 1
