"""Tests for the Nemesis v2 spinoff ghost adapter.

The adapter's one hard invariant is the fair-comparison rule: judgment
features exist only on symbols the LLM actually reviewed, so llm_selected
lift compares picks vs reviewed-but-passed-over — never vs names nobody
read. Several tests below exist purely to pin that down.
"""
from types import SimpleNamespace

import pytest

from nemesis.ghost import HORIZON_DAYS, SOURCE, spinoff_report, spins_to_ghost
from shared.ghost import GhostEntry, grade_entries, open_entries


def _spin(sym, window="in_window", **kw):
    d = {"symbol": sym, "entry_window": window}
    d.update(kw)
    return d


def _px(mapping):
    return lambda s: mapping.get(s.upper())


def _graded(sym, ret, features, source=SOURCE):
    return GhostEntry(sym, "2026-07-02", 10.0, HORIZON_DAYS, source,
                      features=features, graded_return=ret)


class TestSpinsToGhost:
    def test_dict_input(self):
        out = spins_to_ghost([_spin("SPIN", market_cap=2e9)], _px({"SPIN": 25.0}))
        assert len(out) == 1
        c = out[0]
        assert c["symbol"] == "SPIN"
        assert c["price"] == 25.0
        assert c["horizon_days"] == HORIZON_DAYS
        assert c["source"] == SOURCE
        assert c["features"]["entry_window"] == "in_window"
        assert c["features"]["market_cap"] == 2e9

    def test_object_input(self):
        spin = SimpleNamespace(symbol="objx", entry_window="late", market_cap=5e8)
        out = spins_to_ghost([spin], _px({"OBJX": 12.0}))
        assert out[0]["symbol"] == "OBJX"          # upper-cased
        assert out[0]["features"]["entry_window"] == "late"
        assert out[0]["features"]["market_cap"] == 5e8

    def test_object_without_optional_attrs(self):
        # A bare object (no market_cap/verdict/...) must still open cleanly.
        spin = SimpleNamespace(symbol="BARE", entry_window="in_window")
        out = spins_to_ghost([spin], _px({"BARE": 8.0}))
        assert out[0]["features"] == {"entry_window": "in_window"}

    def test_unpriceable_skipped(self):
        spins = [_spin("NOPX"), _spin("ZERO"), _spin("NEG"), _spin("OK")]
        out = spins_to_ghost(
            spins, _px({"ZERO": 0.0, "NEG": -1.0, "OK": 10.0}),
        )
        assert [c["symbol"] for c in out] == ["OK"]

    def test_missing_symbol_skipped(self):
        assert spins_to_ghost([_spin("")], _px({"": 10.0})) == []

    def test_market_cap_omitted_when_absent(self):
        out = spins_to_ghost([_spin("NOCAP")], _px({"NOCAP": 10.0}))
        assert "market_cap" not in out[0]["features"]

    def test_fair_comparison_rule(self):
        # PICK: reviewed and selected. PASS: reviewed, passed over.
        # CTRL: never reviewed — even though it carries stale judgment
        # values, NONE of them may become features.
        spins = [
            _spin("PICK", verdict="own", conviction=0.8, incentive_alignment=0.7),
            _spin("PASS", verdict="avoid", conviction=0.2, incentive_alignment=0.1),
            _spin("CTRL", verdict="own", conviction=0.9, incentive_alignment=0.9),
        ]
        out = spins_to_ghost(
            spins, _px({"PICK": 1.0, "PASS": 1.0, "CTRL": 1.0}),
            reviewed=["PICK", "PASS"], selected=["PICK"],
        )
        feats = {c["symbol"]: c["features"] for c in out}
        assert feats["PICK"]["llm_selected"] is True
        assert feats["PICK"]["verdict"] == "own"
        assert feats["PICK"]["conviction"] == 0.8
        assert feats["PICK"]["incentive_alignment"] == 0.7
        assert feats["PASS"]["llm_selected"] is False
        assert feats["PASS"]["verdict"] == "avoid"
        # unreviewed -> flags ABSENT, not False: it is the buy-all control
        for key in ("llm_selected", "verdict", "conviction", "incentive_alignment"):
            assert key not in feats["CTRL"]

    def test_no_judgment_flags_when_no_review_pass(self):
        out = spins_to_ghost(
            [_spin("A", verdict="own", conviction=0.9)], _px({"A": 10.0}),
        )
        for key in ("llm_selected", "verdict", "conviction", "incentive_alignment"):
            assert key not in out[0]["features"]

    def test_reviewed_symbols_case_insensitive(self):
        out = spins_to_ghost(
            [_spin("mix")], _px({"MIX": 10.0}), reviewed=["mix"], selected=["MIX"],
        )
        assert out[0]["features"]["llm_selected"] is True

    def test_judgment_values_optional_on_reviewed(self):
        # Reviewed but the dossier fields never made it onto the spin dict:
        # llm_selected still applies; missing values are omitted, not invented.
        out = spins_to_ghost(
            [_spin("THIN")], _px({"THIN": 10.0}), reviewed=["THIN"], selected=[],
        )
        f = out[0]["features"]
        assert f["llm_selected"] is False
        assert "verdict" not in f and "conviction" not in f


class TestSpinoffReport:
    def test_empty_shape(self):
        r = spinoff_report([])
        assert r == {
            "n": 0, "mean_return": None, "hit_rate": None,
            "signal_lift": {},
            "conviction_terciles": {},
            "incentive_terciles": {},
            "verdict_groups": {},
            "window_groups": {},
        }

    def test_filters_foreign_sources(self):
        entries = [
            # retired v1 crash-fade ghost entry — must not pollute
            _graded("OLD", 0.50, {"leg": "fade"}, source="nemesis"),
            # another god sharing a ledger — must not pollute either
            _graded("PEAD", -0.30, {"rewarded": True}, source="pead"),
            _graded("NEW", 0.04, {"entry_window": "in_window"}),
        ]
        r = spinoff_report(entries)
        assert r["n"] == 1
        assert r["mean_return"] == pytest.approx(0.04)

    def test_llm_selected_lift(self):
        # Picks re-rate, reviewed-but-passed names bleed -> positive lift.
        # The unreviewed control has no llm_selected key and must be
        # excluded from both sides of the lift.
        entries = [
            _graded("P1", 0.30, {"entry_window": "in_window", "llm_selected": True}),
            _graded("P2", 0.10, {"entry_window": "in_window", "llm_selected": True}),
            _graded("X1", -0.10, {"entry_window": "in_window", "llm_selected": False}),
            _graded("X2", -0.02, {"entry_window": "in_window", "llm_selected": False}),
            _graded("C1", 0.99, {"entry_window": "in_window"}),   # unreviewed control
        ]
        lift = spinoff_report(entries)["signal_lift"]["llm_selected"]
        assert lift["n_on"] == 2 and lift["n_off"] == 2
        assert lift["mean_on"] == pytest.approx(0.20)
        assert lift["mean_off"] == pytest.approx(-0.06)
        assert lift["lift"] == pytest.approx(0.26)

    def test_verdict_and_window_groups(self):
        entries = [
            _graded("A", 0.20, {"entry_window": "in_window", "verdict": "own"}),
            _graded("B", -0.05, {"entry_window": "late", "verdict": "avoid"}),
            _graded("C", 0.10, {"entry_window": "in_window"}),  # unreviewed: no verdict
        ]
        r = spinoff_report(entries)
        assert r["verdict_groups"]["own"] == {"n": 1, "mean": pytest.approx(0.20)}
        assert r["verdict_groups"]["avoid"] == {"n": 1, "mean": pytest.approx(-0.05)}
        assert set(r["verdict_groups"]) == {"own", "avoid"}     # control absent
        assert r["window_groups"]["in_window"]["n"] == 2
        assert r["window_groups"]["late"]["n"] == 1

    def test_conviction_and_incentive_terciles(self):
        entries = [
            _graded(f"S{i}", ret, {
                "entry_window": "in_window",
                "conviction": conv,
                "incentive_alignment": conv,
            })
            for i, (conv, ret) in enumerate(
                [(0.1, -0.05), (0.2, 0.0), (0.5, 0.05), (0.6, 0.10),
                 (0.8, 0.20), (0.9, 0.30)]
            )
        ]
        r = spinoff_report(entries)
        assert r["conviction_terciles"]["n"] == 6
        assert r["conviction_terciles"]["monotonic"] is True
        assert r["incentive_terciles"]["monotonic"] is True

    def test_end_to_end_open_grade_report(self):
        spins = [
            _spin("WIN", verdict="own", conviction=0.8),
            _spin("LOSE", verdict="avoid", conviction=0.2),
            _spin("CTRL"),
        ]
        cands = spins_to_ghost(
            spins, _px({"WIN": 10.0, "LOSE": 10.0, "CTRL": 10.0}),
            reviewed=["WIN", "LOSE"], selected=["WIN"],
        )
        entries = open_entries(cands, today="2026-07-02")
        assert len(entries) == 3
        assert all(e.horizon_days == HORIZON_DAYS and e.source == SOURCE
                   for e in entries)

        # nothing grades before the 150-day horizon elapses
        assert grade_entries(entries, _px({"WIN": 14.0, "LOSE": 9.0, "CTRL": 10.5}),
                             today="2026-11-01") == 0
        n = grade_entries(entries, _px({"WIN": 14.0, "LOSE": 9.0, "CTRL": 10.5}),
                          today="2026-12-01")
        assert n == 3

        r = spinoff_report(entries)
        assert r["n"] == 3
        assert r["mean_return"] == pytest.approx((0.40 - 0.10 + 0.05) / 3)
        lift = r["signal_lift"]["llm_selected"]
        assert lift["n_on"] == 1 and lift["n_off"] == 1   # CTRL excluded
        assert lift["lift"] == pytest.approx(0.50)
        assert r["verdict_groups"]["own"]["mean"] == pytest.approx(0.40)
