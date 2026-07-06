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
    size_upside_book,
)

PRIMARY = ["10-K FY2025 (accession 0001234567-26-000045)"]


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
def test_blowup_clean_passes_and_is_fundable():
    d = _dossier()
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    assert d["blowup"] is False
    assert is_fundable(d) is True


def test_no_floor_but_fundable():
    # The whole point: no floor_pct, no assets — but real upside + survives → fundable.
    d = _dossier(floor_pct=None)
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
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


# ---- ranking rewards upside magnitude --------------------------------------
def test_rank_rewards_bigger_annualized_er():
    small = _dossier(symbol="SMALL", upside_x=1.6, prob_upside=0.5, downside_pct=0.2)
    big = _dossier(symbol="BIG", upside_x=3.0, prob_upside=0.5, downside_pct=0.3)
    for d in (small, big):
        blowup_check(d, going_concern=False, fraud=False, delisting=False)
    ranked = rank_fundable([small, big])
    assert [d["symbol"] for d in ranked][0] == "BIG"


def test_rank_excludes_unfundable():
    ok = _dossier(symbol="OK")
    bad = _dossier(symbol="BAD", runway_months=1.0)
    for d in (ok, bad):
        blowup_check(d, going_concern=False, fraud=False, delisting=False)
    ranked = rank_fundable([ok, bad])
    assert [d["symbol"] for d in ranked] == ["OK"]


# ---- sizing: concentrate, cap, no dust -------------------------------------
def _fundable(sym, **over):
    d = _dossier(symbol=sym, **over)
    blowup_check(d, going_concern=False, fraud=False, delisting=False)
    return d


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
