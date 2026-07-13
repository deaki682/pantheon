"""Proteus v2 — IV-kink detector tests (proteus/ivkink.py)."""
import math

import pytest

from proteus import ivkink
from proteus.ivkink import ExpiryPoint, kink_read, point_from_quotes

ASOF = "2026-07-13"


def _pt(expiration: str, iv: float) -> ExpiryPoint:
    return ExpiryPoint(expiration, ivkink.year_frac(ASOF, expiration), iv)


def _flat(iv: float = 0.30):
    return [_pt(e, iv) for e in
            ("2026-08-14", "2026-09-18", "2026-10-16", "2026-12-18", "2027-01-15")]


def test_flat_structure_reads_unpriced():
    out = kink_read(_flat(), asof=ASOF, event_date="2026-09-25", symbol="X")
    assert out["verdict"] == "UNPRICED"
    assert out["kink_ratio"] == pytest.approx(1.0, abs=0.01)
    assert out["event_interval"] == {"expiry0": "2026-09-18",
                                     "expiry1": "2026-10-16"}


def test_event_hump_reads_priced():
    # Bump total variance at the expiry straddling the event: the forward
    # vol in (9/18, 10/16] jumps far above the flat 30% baseline.
    pts = _flat()
    bumped = [_pt("2026-10-16", 0.45) if p.expiration == "2026-10-16" else p
              for p in pts]
    out = kink_read(bumped, asof=ASOF, event_date="2026-09-25")
    assert out["verdict"] == "PRICED"
    assert out["kink_ratio"] > ivkink.KINK_RATIO_PRICED


def test_event_before_first_expiry_uses_spot_interval():
    pts = _flat()
    bumped = [_pt("2026-08-14", 0.50) if p.expiration == "2026-08-14" else p
              for p in pts]
    out = kink_read(bumped, asof=ASOF, event_date="2026-07-23")
    assert out["event_interval"] == {"expiry0": None, "expiry1": "2026-08-14"}
    assert out["verdict"] == "PRICED"


def test_too_few_expiries_is_unreliable():
    out = kink_read(_flat()[:3], asof=ASOF, event_date="2026-09-25")
    assert out["verdict"] == "UNRELIABLE"
    assert "expiries" in out["reason"]


def test_event_beyond_last_expiry_is_unreliable():
    out = kink_read(_flat(), asof=ASOF, event_date="2027-06-01")
    assert out["verdict"] == "UNRELIABLE"
    assert "outside" in out["reason"]


def test_event_on_or_before_asof_is_unreliable():
    out = kink_read(_flat(), asof=ASOF, event_date=ASOF)
    assert out["verdict"] == "UNRELIABLE"


def test_inverted_event_interval_is_unreliable():
    # Total variance FALLS into the event expiry: negative forward
    # variance, clamped, and the read refuses rather than trusting it.
    pts = _flat()
    inverted = [_pt("2026-10-16", 0.18) if p.expiration == "2026-10-16" else p
                for p in pts]
    out = kink_read(inverted, asof=ASOF, event_date="2026-09-25")
    assert out["verdict"] == "UNRELIABLE"
    assert "self-inconsistent" in out["reason"]


def test_forward_vol_arithmetic():
    a, b = _pt("2026-08-14", 0.30), _pt("2026-09-18", 0.35)
    fw = ivkink.forward_vols([a, b])
    assert fw[0]["fwd_vol"] == pytest.approx(0.30)
    expect = math.sqrt((0.35 ** 2 * b.t_years - 0.30 ** 2 * a.t_years)
                       / (b.t_years - a.t_years))
    assert fw[1]["fwd_vol"] == pytest.approx(expect)


def test_term_structure_dedupes_and_sorts():
    pts = [_pt("2026-09-18", 0.30), _pt("2026-08-14", 0.28),
           _pt("2026-09-18", 0.99)]
    ts = ivkink.term_structure(pts)
    assert [p.expiration for p in ts] == ["2026-08-14", "2026-09-18"]
    assert ts[1].iv == 0.30  # first point per expiry wins


def test_nearest_strike():
    assert ivkink.nearest_strike([90, 95, 100, 105], 101.2) == 100
    assert ivkink.nearest_strike([], 100) is None


def test_point_from_quotes_gates():
    good_call = {"bid_price": "1.20", "ask_price": "1.40",
                 "implied_volatility": "0.32"}
    good_put = {"bid_price": "1.10", "ask_price": "1.30",
                "implied_volatility": "0.34"}
    p, why = point_from_quotes(asof=ASOF, expiration="2026-08-14",
                               strike=100, spot=101, call_quote=good_call,
                               put_quote=good_put)
    assert why == "" and p is not None
    assert p.iv == pytest.approx(0.33)

    # zero bid both legs -> refused
    dead = {"bid_price": "0", "ask_price": "5.00", "implied_volatility": "0.3"}
    p, why = point_from_quotes(asof=ASOF, expiration="2026-08-14", strike=100,
                               spot=101, call_quote=dead, put_quote=dead)
    assert p is None and "zero bid" in why

    # far-from-spot strike -> refused (skew, not term structure)
    p, why = point_from_quotes(asof=ASOF, expiration="2026-08-14", strike=80,
                               spot=101, call_quote=good_call,
                               put_quote=good_put)
    assert p is None and "not ATM" in why

    # no IV either leg -> refused
    noiv = {"bid_price": "1.20", "ask_price": "1.40"}
    p, why = point_from_quotes(asof=ASOF, expiration="2026-08-14", strike=100,
                               spot=101, call_quote=noiv, put_quote=noiv)
    assert p is None and "implied vol" in why

    # expiration on/before asof -> refused
    p, why = point_from_quotes(asof=ASOF, expiration=ASOF, strike=100,
                               spot=101, call_quote=good_call,
                               put_quote=good_put)
    assert p is None and "after" in why


def test_point_from_quotes_per_leg_admission():
    """Each leg is admitted on its own bid and a non-degenerate IV — a
    zero-bid or garbage-IV leg never blends into the point (the live EQH
    false-kink of 2026-07-13)."""
    good_call = {"bid_price": "1.20", "ask_price": "1.40",
                 "implied_volatility": "0.386611"}

    # zero-bid put with a degenerate IV: point rests on the call ALONE
    dead_put = {"bid_price": "0", "ask_price": "2.45",
                "implied_volatility": "0.000224"}
    p, why = point_from_quotes(asof=ASOF, expiration="2026-08-14", strike=100,
                               spot=101, call_quote=good_call,
                               put_quote=dead_put)
    assert why == "" and p is not None
    assert p.iv == pytest.approx(0.386611)   # NOT the 0.19 blend

    # a bid-carrying leg with a degenerate IV is still refused
    degenerate_bid_put = {"bid_price": "0.10", "ask_price": "2.45",
                          "implied_volatility": "0.0008"}
    p, why = point_from_quotes(asof=ASOF, expiration="2026-08-14", strike=100,
                               spot=101, call_quote=good_call,
                               put_quote=degenerate_bid_put)
    assert why == "" and p is not None
    assert p.iv == pytest.approx(0.386611)

    # both legs inadmissible (one no-bid, one degenerate) -> refused
    nobid_call = {"bid_price": "0", "ask_price": "0.05",
                  "implied_volatility": "0.30"}
    p, why = point_from_quotes(asof=ASOF, expiration="2026-08-14", strike=100,
                               spot=101, call_quote=nobid_call,
                               put_quote=degenerate_bid_put)
    assert p is None and "no admissible leg" in why
    assert "zero bid" in why and "degenerate" in why


def test_result_is_json_serializable():
    import json
    out = kink_read(_flat(), asof=ASOF, event_date="2026-09-25")
    json.dumps(out)  # must not raise
