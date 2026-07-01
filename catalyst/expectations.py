"""The expectations overlay (Phase 2) — what the market already expects.

The load-bearing idea of the whole engine:

    edge = expected_outcome - what_the_market_already_expects

The single most useful input is the options-implied move: the options market
literally prices how big a move it expects around an event. Your thesis is only
tradeable to the extent it *disagrees* with this number. If you expect a 12%
move and the chain has priced 8%, the 4-point residual is the idea. If you
expect 8% and it priced 8%, there is nothing there — the move is in the price.

Pure stdlib. Option contracts are fetched by the /catalyst skill and passed in.
"""
from __future__ import annotations

import math
from typing import Optional

# 1-sigma move = straddle/spot * sqrt(2/pi). straddle/spot alone is the
# practitioner's quick read of the priced move.
SIGMA_FROM_STRADDLE = math.sqrt(2.0 / math.pi)  # ~0.7979


def implied_move_from_iv(iv_annualized: Optional[float], days: Optional[float]) -> Optional[float]:
    """Expected 1-sigma move over `days` from annualized IV."""
    if iv_annualized is None or days is None or days <= 0:
        return None
    return iv_annualized * math.sqrt(days / 365.0)


def straddle_move(call_price, put_price, spot) -> Optional[float]:
    """Practitioner quick read: (ATM call + ATM put) / spot = priced move."""
    if not spot or spot <= 0 or call_price is None or put_price is None:
        return None
    if call_price < 0 or put_price < 0:
        return None
    return (call_price + put_price) / spot


def one_sigma_move(call_price, put_price, spot) -> Optional[float]:
    """The straddle-implied move scaled to an actual 1-standard-deviation figure."""
    m = straddle_move(call_price, put_price, spot)
    return None if m is None else m * SIGMA_FROM_STRADDLE


def edge_vs_priced(my_expected_move_pct, priced_move_pct, direction: int = 1) -> Optional[float]:
    """Signed surprise vs what's priced. Positive = you expect MORE than priced.

    direction in {+1, -1}: your view on which way the surprise breaks.
    """
    if my_expected_move_pct is None or priced_move_pct is None:
        return None
    return direction * (my_expected_move_pct - priced_move_pct)


def _mid(contract: dict) -> Optional[float]:
    """Mid price of a contract from mark, or bid/ask, or last."""
    m = contract.get("mark") if contract.get("mark") not in (None, "") else None
    if m is not None:
        try:
            return float(m)
        except (TypeError, ValueError):
            pass
    bid, ask = contract.get("bid"), contract.get("ask")
    try:
        if bid not in (None, "") and ask not in (None, ""):
            b, a = float(bid), float(ask)
            if a > 0:
                return (b + a) / 2.0
    except (TypeError, ValueError):
        pass
    last = contract.get("last") if contract.get("last") not in (None, "") else None
    try:
        return float(last) if last is not None else None
    except (TypeError, ValueError):
        return None


def pick_atm_straddle(spot, contracts, event_date: Optional[str] = None) -> Optional[dict]:
    """Select the ATM call+put for the nearest expiry on/after the event.

    contracts: [{'strike', 'type': 'call'|'put', 'expiration': 'YYYY-MM-DD',
                 'mark'|'bid'/'ask'|'last'}]

    Returns {expiry, strike, call, put} using the strike closest to spot that
    has a priceable call AND put in that expiry, or None if none exists.
    """
    if not spot or spot <= 0 or not contracts:
        return None

    # group priceable contracts by expiry
    by_exp: dict[str, dict] = {}
    for c in contracts:
        exp = c.get("expiration") or c.get("expiration_date")
        strike = c.get("strike") if c.get("strike") is not None else c.get("strike_price")
        typ = (c.get("type") or "").lower()
        if not exp or strike is None or typ not in ("call", "put"):
            continue
        price = _mid(c)
        if price is None or price <= 0:
            continue
        try:
            strike = float(strike)
        except (TypeError, ValueError):
            continue
        slot = by_exp.setdefault(exp, {})
        slot.setdefault(strike, {})[typ] = price

    if not by_exp:
        return None

    # choose the nearest expiry on/after the event (else the nearest available)
    exps = sorted(by_exp)
    chosen = None
    if event_date:
        after = [e for e in exps if e >= event_date]
        chosen = after[0] if after else exps[-1]
    else:
        chosen = exps[0]

    strikes = by_exp[chosen]
    paired = [k for k, v in strikes.items() if "call" in v and "put" in v]
    if not paired:
        return None
    atm = min(paired, key=lambda k: abs(k - spot))
    return {
        "expiry": chosen,
        "strike": atm,
        "call": strikes[atm]["call"],
        "put": strikes[atm]["put"],
    }


def implied_move_from_chain(spot, contracts, event_date: Optional[str] = None) -> Optional[dict]:
    """End-to-end: ATM straddle -> priced move for one name.

    Returns {priced_move_pct, one_sigma_pct, expiry, strike, call, put, spot}
    or None if no priceable ATM straddle exists (illiquid name).
    """
    atm = pick_atm_straddle(spot, contracts, event_date)
    if not atm:
        return None
    move = straddle_move(atm["call"], atm["put"], spot)
    if move is None:
        return None
    return {
        "priced_move_pct": round(move, 4),
        "one_sigma_pct": round(move * SIGMA_FROM_STRADDLE, 4),
        "expiry": atm["expiry"],
        "strike": atm["strike"],
        "call": atm["call"],
        "put": atm["put"],
        "spot": spot,
    }
