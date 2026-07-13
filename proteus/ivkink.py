"""Proteus v2 — ATM-IV term-structure kink detector (the priced/unpriced screen).

The playbook's inverted sourcing doctrine (2026-07-12): any event on a
retail calendar is presumptively priced — "neglected" must be measured in
the CHAIN, not in market cap. This module is the mechanical middle stage
between an eventfeed hit and the expensive document read: given a verified
event date and the chain's ATM implied vols per expiry, does the term
structure show a kink (elevated forward variance) at the interval
containing the event?

  - Kink present  -> the market has dated the event -> PRICED -> drop it,
    no document read; out-handicapping specialists is not the edge.
  - No kink       -> the market hasn't dated the event -> UNPRICED -> the
    mispricing is structural; the name earns its document read.
  - Bad inputs    -> UNRELIABLE -> never traded around, never cited.

The math: total implied variance to expiry i is iv_i^2 * T_i. The forward
variance over the interval (T_i, T_j] is (iv_j^2*T_j - iv_i^2*T_i)/(T_j -
T_i); a dated event adds variance to exactly the intervals that contain
it, so the event interval's forward VOL is compared against the median
forward vol of every other interval. The zeroth interval (as-of date ->
first expiry) carries the first expiry's own vol.

Data honesty (charter art. 19 — order-time data integrity): this module
never fetches. The caller assembles points from live broker quotes
(`point_from_quotes` guards the known traps: zero-bid contracts, far-from-
spot strikes, missing IV) and is responsible for running it on MARKET-HOURS
quotes — overnight IV marks are stale and a term-structure read off them is
exactly the kind of secondary-source number art. 19 forbids near sizing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from statistics import median
from typing import Optional

YEAR_DAYS = 365.0

# A forward vol this many times the median of the other intervals reads as
# a dated-event hump. Deliberately modest: the screen's job is to find the
# ABSENCE of a kink, and a soft threshold errs toward PRICED (dropping the
# name), never toward manufacturing an UNPRICED read.
KINK_RATIO_PRICED = 1.25

# Fewer expiries than this cannot support a median baseline worth trusting
# (3 intervals minimum: the event's plus two others).
MIN_EXPIRIES = 4

# An "ATM" strike further than this from spot is not ATM; its IV carries
# skew, not the term structure.
MAX_ATM_DISTANCE_PCT = 0.10

# No real equity option trades below 1% implied vol; a mark under this is a
# degenerate placeholder (seen live 2026-07-13: zero-bid merger-target puts
# quoting IV 0.0002 with delta -1), and blending it with a real leg
# manufactures a front-point dip — exactly the false kink the screen exists
# to avoid.
MIN_LEG_IV = 0.01

VERDICTS = ("PRICED", "UNPRICED", "UNRELIABLE")


@dataclass(frozen=True)
class ExpiryPoint:
    """One expiry's ATM implied vol, already quality-gated."""
    expiration: str          # ISO date
    t_years: float           # year fraction from as-of date, > 0
    iv: float                # decimal vol (0.30 = 30%), > 0


def year_frac(asof: str, expiry: str) -> float:
    return (_date.fromisoformat(expiry) - _date.fromisoformat(asof)).days / YEAR_DAYS


def nearest_strike(strikes, spot: float) -> Optional[float]:
    """Closest listed strike to spot, or None if the list is empty."""
    xs = [float(s) for s in strikes if s not in (None, "")]
    return min(xs, key=lambda k: abs(k - spot)) if xs else None


def _iv(quote: dict) -> Optional[float]:
    for key in ("implied_volatility", "iv"):
        v = quote.get(key)
        try:
            if v not in (None, "") and float(v) > 0:
                return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _has_bid(quote: dict) -> bool:
    try:
        return float(quote.get("bid_price") or quote.get("bid") or 0) > 0
    except (TypeError, ValueError):
        return False


def point_from_quotes(*, asof: str, expiration: str, strike: float,
                      spot: float, call_quote: dict,
                      put_quote: dict) -> tuple[Optional[ExpiryPoint], str]:
    """Build one term-structure point from a live ATM call/put quote pair.

    Returns (point, "") or (None, reason). The gates are the house's scar
    tissue: a strike far from spot measures skew, not term structure, and
    each leg is admitted on its OWN merits — its own live bid and a
    non-degenerate IV. The first live run (2026-07-13, EQH) showed why
    pair-level gating lies: a zero-bid put carrying IV 0.0002 blended with
    a real 39% call IV halves the front point and manufactures a kink.
    """
    if spot <= 0:
        return None, "spot <= 0"
    if abs(strike - spot) / spot > MAX_ATM_DISTANCE_PCT:
        return None, (f"strike {strike} is {abs(strike - spot) / spot:.0%} "
                      f"from spot — not ATM")
    ivs, dropped = [], []
    for leg, quote in (("call", call_quote), ("put", put_quote)):
        if not _has_bid(quote):
            dropped.append(f"{leg}: zero bid")
            continue
        v = _iv(quote)
        if v is None:
            dropped.append(f"{leg}: no implied vol")
            continue
        if v < MIN_LEG_IV:
            dropped.append(f"{leg}: degenerate iv {v:g} < {MIN_LEG_IV}")
            continue
        ivs.append(v)
    if not ivs:
        return None, ("no admissible leg (zero bid on both legs, missing or "
                      "degenerate marks) — " + "; ".join(dropped))
    t = year_frac(asof, expiration)
    if t <= 0:
        return None, "expiration not after as-of date"
    return ExpiryPoint(expiration, t, sum(ivs) / len(ivs)), ""


def term_structure(points: list[ExpiryPoint]) -> list[ExpiryPoint]:
    """Sorted, deduped (first point per expiry wins), positive-T/iv only."""
    seen: set[str] = set()
    out = []
    for p in sorted(points, key=lambda p: p.t_years):
        if p.expiration in seen or p.t_years <= 0 or p.iv <= 0:
            continue
        seen.add(p.expiration)
        out.append(p)
    return out


def forward_vols(ts: list[ExpiryPoint]) -> list[dict]:
    """Per-interval forward vols; interval 0 runs as-of -> first expiry.

    A negative forward variance (an inverted structure the arithmetic
    can't support) clamps to 0 and is flagged — it means the marks
    disagree with themselves and the read downstream must not trust it.
    """
    if not ts:
        return []
    out = [{
        "t0": 0.0, "t1": ts[0].t_years,
        "expiry0": None, "expiry1": ts[0].expiration,
        "fwd_vol": ts[0].iv, "clamped": False,
    }]
    for a, b in zip(ts, ts[1:]):
        fwd_var = (b.iv ** 2 * b.t_years - a.iv ** 2 * a.t_years) / (b.t_years - a.t_years)
        out.append({
            "t0": a.t_years, "t1": b.t_years,
            "expiry0": a.expiration, "expiry1": b.expiration,
            "fwd_vol": max(fwd_var, 0.0) ** 0.5, "clamped": fwd_var < 0,
        })
    return out


def _event_interval_index(ts: list[ExpiryPoint], asof: str,
                          event_date: str) -> Optional[int]:
    """Index into forward_vols of the interval containing the event."""
    ev = _date.fromisoformat(event_date)
    if ev <= _date.fromisoformat(asof):
        return None
    for i, p in enumerate(ts):
        if ev <= _date.fromisoformat(p.expiration):
            return i          # interval ending at expiry i (0 = asof->first)
    return None               # event beyond the last listed expiry


def kink_read(points: list[ExpiryPoint], *, asof: str, event_date: str,
              symbol: str = "", kink_ratio_priced: float = KINK_RATIO_PRICED,
              min_expiries: int = MIN_EXPIRIES) -> dict:
    """The journal-ready verdict: PRICED / UNPRICED / UNRELIABLE.

    UNRELIABLE is a real verdict, not a default to argue with: too few
    expiries, an event outside the chain, clamped (self-inconsistent)
    marks in the intervals that matter, or a degenerate baseline all mean
    the chain cannot answer the question today.
    """
    ts = term_structure(points)
    fw = forward_vols(ts)
    result = {
        "symbol": symbol,
        "asof": asof,
        "event_date": event_date,
        "n_expiries": len(ts),
        "term_structure": [
            {"expiration": p.expiration, "t_years": round(p.t_years, 4),
             "iv": round(p.iv, 4)} for p in ts],
        "forward_vols": [
            {**f, "t0": round(f["t0"], 4), "t1": round(f["t1"], 4),
             "fwd_vol": round(f["fwd_vol"], 4)} for f in fw],
        "kink_ratio_priced": kink_ratio_priced,
        "verdict": "UNRELIABLE",
        "kink_ratio": None,
        "event_interval": None,
        "baseline_fwd_vol": None,
        "reason": "",
    }

    if len(ts) < min_expiries:
        result["reason"] = (f"{len(ts)} usable expiries < {min_expiries} — "
                            "no baseline")
        return result
    idx = _event_interval_index(ts, asof, event_date)
    if idx is None:
        result["reason"] = "event date outside the chain's expiry range"
        return result
    event_fw = fw[idx]
    others = [f["fwd_vol"] for i, f in enumerate(fw) if i != idx and not f["clamped"]]
    if event_fw["clamped"]:
        result["reason"] = "event interval forward variance is negative — marks self-inconsistent"
        return result
    if len(others) < 2:
        result["reason"] = "fewer than 2 clean non-event intervals — no baseline"
        return result
    baseline = median(others)
    if baseline <= 0:
        result["reason"] = "baseline forward vol is zero — marks degenerate"
        return result

    ratio = event_fw["fwd_vol"] / baseline
    result.update({
        "event_interval": {k: event_fw[k] for k in ("expiry0", "expiry1")},
        "baseline_fwd_vol": round(baseline, 4),
        "kink_ratio": round(ratio, 4),
        "verdict": "PRICED" if ratio >= kink_ratio_priced else "UNPRICED",
        "reason": (f"forward vol {event_fw['fwd_vol']:.1%} in the event "
                   f"interval vs {baseline:.1%} median elsewhere"),
    })
    return result
