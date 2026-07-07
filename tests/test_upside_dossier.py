import pytest

from oracle.upside_dossier import (
    UpsideDossierError,
    annualized_er,
    blowup_check,
    calib_weight,
    evaluate_exit,
    expected_return,
    is_fundable,
    is_primary_citation,
    make_upside_dossier,
    rank_fundable,
    resolve_bears,
    size_upside_book,
)

PRIMARY = ["10-K FY2025 (accession 0001234567-26-000045)"]
_CITE = ["10-Q Q1-FY2026 (accession 0001234567-26-000045)"]

# Three independent critiques, each answered with a primary-cited defense — the
# canonical SURVIVED bear pass. Distinct types, none fatal-landing, margin > 0.
def _good_bears():
    return [
        {"critique_type": "guidance_contradiction",
         "critique": "The re-acceleration is contradicted by next-quarter guidance implying deceleration.",
         "severity": 0.8,
         "defense": "The 10-Q MD&A guides FY revenue +30–32%, ABOVE the trailing rate; the 'decel' misreads one seasonal quarter.",
         "defense_citations": list(_CITE), "concede": False},
        {"critique_type": "one_time_driver",
         "critique": "The margin turn looks like a one-time cost credit rather than a structural improvement.",
         "severity": 0.6,
         "defense": "Gross margin ex-credit is still +240bps; the 10-Q reconciles the credit at $2M against an $18M gross-profit gain.",
         "defense_citations": list(_CITE), "concede": False},
        {"critique_type": "valuation_priced_in",
         "critique": "At ~1.9x sales the ramp may already be priced into the multiple by the market.",
         "severity": 0.5,
         "defense": "Direct comps trade ~3.2x on similar growth; the 10-K discloses backlog implying the ramp is not yet in consensus numbers.",
         "defense_citations": ["10-K FY2025 (accession 0001234567-26-000045)"], "concede": False},
    ]


def _resolved(d):
    """A dossier taken all the way through the gate: survive-to-thesis + BEAR×3."""
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    resolve_bears(d, _good_bears())
    return d


def _dossier(**over):
    kw = dict(
        symbol="ABCD",
        business="A thinly-covered maker of industrial widgets.",
        thesis=("Revenue growth is re-accelerating as the new product line ramps into a demand "
                "shift the two remaining analysts have not modelled; consensus underweights the "
                "24-month trajectory and the margin flow-through of the ramp."),
        inflection_type="product_ramp",
        inflection_evidence="Product-line revenue grew 41% q/q in the latest 10-Q, up from 12% (accel).",
        upside_x=2.2,
        prob_upside=0.45,
        downside_pct=0.35,
        catalyst="Next two prints confirm the ramp; a covering analyst initiates.",
        catalyst_date="2026-11-01",
        horizon_months=12.0,
        runway_months=30.0,
        falsifiable_prediction="Revenue growth stays above 30% y/y through FY2026.",
        prediction_date="2027-03-01",
        kill_condition="Growth decelerates below 15% y/y on any print.",
        kill_type="fundamental_break",
        kill_value="growth<15%",
        adversarial=("The ramp could be a pull-forward; if the new line cannibalises the base, "
                     "blended growth stalls and the multiple compresses."),
        citations=list(PRIMARY),
        current_price=10.0,
        spy_price=500.0,
        sector="Industrials",
        coverage=2,
        theme="",
    )
    kw.update(over)
    return make_upside_dossier(**kw)


# ---- scoring ---------------------------------------------------------------
def test_expected_return_math():
    assert expected_return(2.0, 0.5, 0.4) == pytest.approx(0.5 * 1.0 - 0.5 * 0.4)


def test_annualized_clamps_window():
    er = 0.6
    # a 6-mo hold annualizes ×2; a 24-mo hold ×0.5; below/above clamp to the window
    assert annualized_er(er, 6) == pytest.approx(er * 2.0)
    assert annualized_er(er, 24) == pytest.approx(er * 0.5)
    assert annualized_er(er, 3) == pytest.approx(er * 2.0)   # clamps up to 6
    assert annualized_er(er, 48) == pytest.approx(er * 0.5)  # clamps down to 24


def test_calib_weight_defaults_until_five():
    assert calib_weight("product_ramp", None) == 0.5
    assert calib_weight("product_ramp", {"product_ramp": {"n": 3, "hit_rate": 0.9}}) == 0.5
    assert calib_weight("product_ramp", {"product_ramp": {"n": 8, "hit_rate": 0.7}}) == 0.7


# ---- the writer refuses the wrong shapes -----------------------------------
def test_refuses_upside_below_minimum():
    with pytest.raises(UpsideDossierError):
        _dossier(upside_x=1.3)   # not significant upside


def test_refuses_out_of_window_horizon():
    with pytest.raises(UpsideDossierError):
        _dossier(horizon_months=36)


def test_refuses_bad_inflection_type():
    with pytest.raises(UpsideDossierError):
        _dossier(inflection_type="its_cheap")


def test_refuses_snapshot_only_citation():
    with pytest.raises(UpsideDossierError):
        _dossier(citations=["Robinhood fundamentals snapshot", "Yahoo Finance"])


def test_accepts_and_computes():
    d = _dossier()
    assert d["qualifies"] is True
    assert d["expected_return"] == pytest.approx(expected_return(2.2, 0.45, 0.35), abs=1e-4)
    assert d["already_run"] is False


def test_dead_tell_flag_but_not_refused():
    # "undervalued" in the thesis flags dead_tell_risk (Stage-3 bear enforces) but
    # does not hard-refuse — an inflection thesis may mention valuation in passing.
    d = _dossier(thesis=(
        "The stock is undervalued but more importantly product revenue is re-accelerating hard "
        "into a demand shift the two analysts miss; the 24-month ramp trajectory is underweighted "
        "and margins inflect with scale."))
    assert d["dead_tell_risk"] is True
    assert d["qualifies"] is True


def test_already_run_disqualifies():
    d = _dossier(recent_runup_pct=0.6)
    assert d["already_run"] is True
    assert d["qualifies"] is False


def test_negative_expectancy_disqualifies():
    d = _dossier(upside_x=1.5, prob_upside=0.1, downside_pct=0.9)
    assert d["qualifies"] is False   # E[·] < 0


# ---- blowup filter (survival, not floor) -----------------------------------
def test_blowup_clean_passes_but_needs_bear_pass():
    # Survival alone is no longer enough — the name must also survive its own
    # BEAR×3 before it is fundable (the gate the 2026-07-06 book skipped).
    d = _dossier()
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    assert d["blowup"] is False
    assert is_fundable(d) is False          # bears not resolved yet
    resolve_bears(d, _good_bears())
    assert d["bear_verdict"] == "survived"
    assert is_fundable(d) is True


def test_no_floor_but_fundable():
    # The whole point: no floor_pct, no assets — but real upside + survives blowup
    # AND survives the bear pass → fundable.
    d = _resolved(_dossier(floor_pct=None))
    assert d["floor_pct"] is None
    assert is_fundable(d) is True


def test_short_runway_blows_up():
    d = _dossier(runway_months=12.0, horizon_months=12.0)  # 12 < 12+6 buffer
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    assert d["blowup"] is True
    assert d["blowup_flags"]["survives_to_thesis"] is False
    assert is_fundable(d) is False


def test_self_funding_survives():
    d = _dossier(runway_months="self_funding")
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    assert d["blowup_flags"]["survives_to_thesis"] is True


def test_going_concern_blows_up():
    d = _dossier()
    blowup_check(d, going_concern=True, fraud=False, delisting=False)
    assert d["blowup"] is True
    assert is_fundable(d) is False


def test_unchecked_is_not_fundable():
    d = _dossier()
    assert is_fundable(d) is False   # blowup_check never ran


def test_bear_refuted_not_fundable():
    d = _dossier()
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    d["bear_verdict"] = "refuted"
    assert is_fundable(d) is False


# ---- the adversarial gate (BEAR×3, load-bearing) ---------------------------
def test_resolve_bears_survives_and_scores_margin():
    d = _resolved(_dossier())
    assert d["bear_resolved"] is True
    assert d["bear_verdict"] == "survived"
    assert d["fatal_landed"] is False
    assert d["n_distinct_critique_types"] == 3
    assert d["refutation_margin"] > 0            # all three defended → +Σseverity
    assert 0.0 < d["refutation_margin_norm"] <= 1.0


def test_fewer_than_three_distinct_bears_refuted():
    d = _dossier()
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    resolve_bears(d, _good_bears()[:2])          # only two angles
    assert d["bear_verdict"] == "refuted"
    assert is_fundable(d) is False


def test_fatal_critique_conceded_refutes_despite_positive_margin():
    # Three soft critiques survive (margin positive), but a fourth FATAL one is
    # conceded — the mirage shape. A fatal landing overrides a positive margin.
    d = _dossier()
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    bears = _good_bears() + [{
        "critique_type": "faked_earnings",
        "critique": "The reported GAAP profit is entirely a one-time equity-sale gain, not operations.",
        "severity": 0.9, "defense": "", "defense_citations": [], "concede": True}]
    resolve_bears(d, bears)
    assert d["fatal_landed"] is True
    assert d["bear_verdict"] == "refuted"
    assert is_fundable(d) is False


def test_uncited_defense_does_not_survive():
    # A fatal critique answered WITHOUT a primary citation is only 'partial' →
    # fatal_landed → refuted. A snapshot defense cannot neutralize a real bear.
    d = _dossier()
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    bears = _good_bears()[:2] + [{
        "critique_type": "guidance_contradiction",
        "critique": "Management's own next-quarter guide implies the growth rate rolls over hard.",
        "severity": 0.7,
        "defense": "I think the guide is just conservative sandbagging by the team, they always do this.",
        "defense_citations": ["Yahoo Finance article"], "concede": False}]
    resolve_bears(d, bears)
    assert d["bears"][-1]["verdict"] == "partial"
    assert d["fatal_landed"] is True
    assert d["bear_verdict"] == "refuted"


def test_negative_margin_refuted():
    # Bear case outweighs the defense: mostly conceded → margin ≤ 0 → refuted.
    d = _dossier()
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    bears = [
        {"critique_type": "competitive_erosion",
         "critique": "A larger competitor just undercut price across the core product line.",
         "severity": 0.7, "defense": "", "defense_citations": [], "concede": True},
        {"critique_type": "demand_softening",
         "critique": "End-market bookings are flat-to-down for two consecutive quarters now.",
         "severity": 0.6, "defense": "", "defense_citations": [], "concede": True},
        {"critique_type": "dilution_overhang",
         "critique": "A convertible matures inside the horizon and will likely be settled in stock.",
         "severity": 0.5, "defense": "", "defense_citations": [], "concede": True}]
    resolve_bears(d, bears)
    assert d["refutation_margin"] < 0
    assert d["bear_verdict"] == "refuted"


def test_resolve_bears_rejects_bad_critique_type():
    d = _dossier()
    with pytest.raises(UpsideDossierError):
        resolve_bears(d, [{"critique_type": "vibes", "critique": "x" * 50,
                           "severity": 0.5, "defense": "", "defense_citations": []}])


# ---- ranking rewards upside magnitude --------------------------------------
def test_rank_rewards_bigger_annualized_er():
    small = _resolved(_dossier(symbol="SMALL", upside_x=1.6, prob_upside=0.5, downside_pct=0.2))
    big = _resolved(_dossier(symbol="BIG", upside_x=3.0, prob_upside=0.5, downside_pct=0.3))
    ranked = rank_fundable([small, big])
    assert [d["symbol"] for d in ranked][0] == "BIG"


def test_rank_excludes_unfundable():
    ok = _resolved(_dossier(symbol="OK"))
    bad = _resolved(_dossier(symbol="BAD", runway_months=1.0))   # blows up on survival
    ranked = rank_fundable([ok, bad])
    assert [d["symbol"] for d in ranked] == ["OK"]


# ---- sizing: concentrate, cap, no dust -------------------------------------
def _fundable(sym, **over):
    return _resolved(_dossier(symbol=sym, **over))


def test_sizing_concentrates_top_names():
    ranked = rank_fundable([
        _fundable("A", upside_x=3.0, prob_upside=0.6, sector="s1"),
        _fundable("B", upside_x=2.5, prob_upside=0.5, sector="s2"),
        _fundable("C", upside_x=2.0, prob_upside=0.5, sector="s3"),
        _fundable("D", upside_x=1.8, prob_upside=0.4, sector="s4"),
        _fundable("E", upside_x=1.6, prob_upside=0.4, sector="s5"),
        _fundable("F", upside_x=1.6, prob_upside=0.3, sector="s6"),
        _fundable("G", upside_x=1.6, prob_upside=0.3, sector="s7"),
    ])
    book = size_upside_book(ranked, equity=100_000.0)
    assert 3 <= len(book) <= 6                    # concentrated, not all 7
    assert book["A"] == max(book.values())        # highest conviction × move leads
    assert sum(book.values()) <= 90_000.0 + 1.0   # invested target


def test_sizing_per_name_cap():
    ranked = rank_fundable([
        _fundable("A", upside_x=5.0, prob_upside=0.9, sector="s1"),
        _fundable("B", upside_x=1.6, prob_upside=0.3, sector="s2"),
        _fundable("C", upside_x=1.6, prob_upside=0.3, sector="s3"),
    ])
    book = size_upside_book(ranked, equity=100_000.0)
    # no single name past 30% of equity
    assert max(book.values()) <= 0.30 * 100_000.0 + 1.0


def test_sizing_cluster_cap():
    # four names all in one theme must not exceed the 40% cluster cap combined
    ranked = rank_fundable([
        _fundable("A", upside_x=3.0, prob_upside=0.7, theme="AI"),
        _fundable("B", upside_x=3.0, prob_upside=0.7, theme="AI"),
        _fundable("C", upside_x=3.0, prob_upside=0.7, theme="AI"),
        _fundable("D", upside_x=2.0, prob_upside=0.6, theme="Energy"),
    ])
    book = size_upside_book(ranked, equity=100_000.0,
                            cluster_key=lambda d: d.get("theme") or "")
    ai = sum(v for k, v in book.items() if k in {"A", "B", "C"})
    assert ai <= 0.40 * 100_000.0 + 1.0           # ≤40% of equity (absolute cluster cap)


def test_sizing_empty():
    assert size_upside_book([], equity=100_000.0) == {}


def _weak_bears():
    # Survives (no fatal type, margin > 0) but less decisively than _good_bears:
    # one non-fatal critique is only PARTIAL (uncited), so the margin is smaller.
    return [
        {"critique_type": "valuation_priced_in",
         "critique": "At the current multiple a good chunk of the ramp may already be discounted.",
         "severity": 0.5, "defense": "Comps sit ~3x on similar growth; backlog is disclosed in the 10-K.",
         "defense_citations": ["10-K FY2025 (accession 0001234567-26-000045)"], "concede": False},
        {"critique_type": "competitive_erosion",
         "critique": "A larger vendor could bundle a competing product and pressure win rates.",
         "severity": 0.6, "defense": "They mostly serve a different tier, I believe.",
         "defense_citations": [], "concede": False},          # uncited → partial
        {"critique_type": "demand_softening",
         "critique": "Macro could soften the end-market and slow the bookings trajectory.",
         "severity": 0.4, "defense": "Bookings grew 22% in the 10-Q with coverage ratio rising.",
         "defense_citations": list(_CITE), "concede": False},
    ]


def test_refutation_margin_tilts_sizing():
    # Two names identical in upside/conviction/downside; only how decisively each
    # survived its bears differs. The higher refutation margin gets the bigger bet.
    strong = _dossier(symbol="STRONG", sector="s1")
    blowup_check(strong, going_concern=False, fraud=False, delisting=False)
    resolve_bears(strong, _good_bears())                 # norm = 1.0
    weak = _dossier(symbol="WEAK", sector="s2")
    blowup_check(weak, going_concern=False, fraud=False, delisting=False)
    resolve_bears(weak, _weak_bears())                   # survives, lower norm
    assert strong["bear_verdict"] == weak["bear_verdict"] == "survived"
    assert weak["refutation_margin_norm"] < strong["refutation_margin_norm"]
    # comparably-sized fillers so neither STRONG nor WEAK is pinned at the 30% cap
    # (a capped name can't express the margin tilt) — the tilt shows in the gap.
    fillers = [_fundable(s, upside_x=2.0, prob_upside=0.45, sector=f"f{i}")
               for i, s in enumerate(["F1", "F2", "F3", "F4"])]
    book = size_upside_book(rank_fundable([strong, weak] + fillers), equity=100_000.0)
    assert book["STRONG"] < 0.30 * 100_000.0        # not cap-pinned
    assert book["STRONG"] > book["WEAK"]


def test_sizing_fragility_haircut_demotes_can_go_to_zero():
    # Identical conviction + upside, but FRAGILE can go to zero (big downside) and
    # SAFE can't. The fragile name must get LESS. (Fillers keep caps from binding.)
    ranked = rank_fundable([
        _fundable("FRAGILE", upside_x=2.5, prob_upside=0.5, downside_pct=0.60, sector="s1"),
        _fundable("SAFE", upside_x=2.5, prob_upside=0.5, downside_pct=0.20, sector="s2"),
        _fundable("F1", upside_x=2.0, prob_upside=0.4, downside_pct=0.3, sector="s3"),
        _fundable("F2", upside_x=2.0, prob_upside=0.4, downside_pct=0.3, sector="s4"),
    ])
    book = size_upside_book(ranked, equity=100_000.0)
    assert book["SAFE"] > book["FRAGILE"]


def test_sizing_haircut_flips_low_ev_fragile_and_lambda_off_recovers_old():
    # SABR-like: high upside*conviction but LOW expected value (−55% downside). The
    # old downside-blind sizer made it the LARGEST; the haircut puts a steadier,
    # higher-EV name above it. lambda=0 recovers the old (flawed) behavior.
    names = [
        _fundable("SABRLIKE", upside_x=2.0, prob_upside=0.40, downside_pct=0.55, sector="s1"),
        _fundable("STEADY", upside_x=1.6, prob_upside=0.55, downside_pct=0.25, sector="s2"),
        _fundable("F1", upside_x=2.0, prob_upside=0.4, downside_pct=0.3, sector="s3"),
        _fundable("F2", upside_x=2.0, prob_upside=0.4, downside_pct=0.3, sector="s4"),
    ]
    ranked = rank_fundable(names)
    on = size_upside_book(ranked, equity=100_000.0)               # haircut ON (default)
    assert on["STEADY"] > on["SABRLIKE"]
    off = size_upside_book(ranked, equity=100_000.0, fragility_lambda=0.0)   # old behavior
    assert off["SABRLIKE"] > off["STEADY"]


# ---- exit predicates: drawdown is never an exit ----------------------------
def test_drawdown_alone_never_exits():
    d = _dossier(current_price=10.0)
    # price fell 40% but no typed break → HOLD
    out = evaluate_exit(d, current_price=6.0, fundamental_deteriorated=False)
    assert out["exit"] is False


def test_fundamental_break_exits():
    d = _dossier()
    out = evaluate_exit(d, fundamental_deteriorated=True)
    assert out["exit"] is True and "fundamental_break" in out["reason"]


def test_dilution_exits():
    d = _dossier()
    assert evaluate_exit(d, dilution_event=True)["exit"] is True
    assert evaluate_exit(d, going_concern=True)["exit"] is True


def test_catalyst_fail_exits_after_date():
    d = _dossier(catalyst_date="2026-11-01")
    # before the date: hold; after with no catalyst: exit
    assert evaluate_exit(d, as_of_date="2026-10-01", catalyst_occurred=False)["exit"] is False
    out = evaluate_exit(d, as_of_date="2026-12-01", catalyst_occurred=False)
    assert out["exit"] is True and "catalyst_fail" in out["reason"]


def test_thesis_date_exits():
    d = _dossier(prediction_date="2027-03-01")
    out = evaluate_exit(d, as_of_date="2027-04-01")
    assert out["exit"] is True and "thesis_date" in out["reason"]


def test_price_level_kill_when_typed():
    d = _dossier(kill_type="price_level", kill_value=5.0)
    assert evaluate_exit(d, current_price=4.5)["exit"] is True
    assert evaluate_exit(d, current_price=6.0)["exit"] is False


# ---- citation helper -------------------------------------------------------
def test_primary_citation_detection():
    assert is_primary_citation("10-Q filed 2026-05-06") is True
    assert is_primary_citation("accession 0001234567-26-000045") is True
    assert is_primary_citation("https://www.sec.gov/...") is True
    assert is_primary_citation("Robinhood fundamentals") is False
    assert is_primary_citation("consensus-1.2% growth") is False
