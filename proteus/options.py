"""Proteus v2 — long-option accounting + chain-pricing glue.

Built 2026-07-11 (session 4) to clear the playbook's BUILD PRECONDITION:
before any options order the sleeve needs an honest place for a contract
to live, and the entry checklist (cache/proteus_playbook.md) needs its
arithmetic computed from the chain, not eyeballed.

Scope is deliberately the EXECUTABLE menu only — Robinhood Level 2 long
calls/puts. Max loss on a long option is the premium paid; the bounded-loss
invariant is satisfied by construction and the computed worst case is
stored on the position at entry (charter invariant 1). Covered calls /
cash-secured puts / multi-leg spreads have no accounting here yet — they
get built if and when they become executable and a thesis wants them.

Priced-move math is NOT reimplemented: the glue calls
catalyst.expectations (straddle_move / one_sigma_move / edge_vs_priced /
implied_move_from_chain), the house's maintained implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date
from typing import Optional

from catalyst.expectations import (          # noqa: F401  (re-exported glue)
    edge_vs_priced,
    implied_move_from_chain,
    one_sigma_move,
    straddle_move,
)

MULTIPLIER = 100                 # standard US equity option contract size
OPTION_TYPES = ("call", "put")

# Playbook gate 2: expiry must clear the latest plausible catalyst date by
# at least this buffer — a thesis that is right a week late must still pay.
CATALYST_EXPIRY_BUFFER_DAYS = 14

# Playbook gate 5: a bid-ask spread wider than this fraction of the premium
# must be justified in writing or the trade is skipped (the fill is the cost).
SPREAD_JUSTIFY_PCT = 0.10


def occ_symbol(underlying: str, expiration: str, option_type: str, strike: float) -> str:
    """Canonical OCC contract symbol, e.g. SPY260918C00760000."""
    if option_type not in OPTION_TYPES:
        raise ValueError(f"option_type must be call|put, got {option_type!r}")
    exp = _date.fromisoformat(expiration)
    thousandths = round(float(strike) * 1000)
    return (f"{underlying.upper().strip()}{exp.strftime('%y%m%d')}"
            f"{'C' if option_type == 'call' else 'P'}{thousandths:08d}")


def contract_mid(bid, ask, mark=None, last=None) -> Optional[float]:
    """Mid price of a contract: mark, else bid/ask mid, else last."""
    for v in (mark,):
        try:
            if v not in (None, "") and float(v) > 0:
                return float(v)
        except (TypeError, ValueError):
            pass
    try:
        if bid not in (None, "") and ask not in (None, ""):
            b, a = float(bid), float(ask)
            if a > 0 and a >= b >= 0:
                return (b + a) / 2.0
    except (TypeError, ValueError):
        pass
    try:
        if last not in (None, "") and float(last) > 0:
            return float(last)
    except (TypeError, ValueError):
        pass
    return None


def spread_pct(bid, ask) -> Optional[float]:
    """Bid-ask spread as a fraction of the mid — playbook gate 5's number."""
    try:
        b, a = float(bid), float(ask)
    except (TypeError, ValueError):
        return None
    if a <= 0 or b < 0 or a < b:
        return None
    mid = (a + b) / 2.0
    return (a - b) / mid if mid > 0 else None


def breakeven_move_pct(spot: float, strike: float, option_type: str,
                       premium: float) -> Optional[float]:
    """Signed underlying move (vs spot) needed to break even AT EXPIRY.

    Call: spot must rise to strike + premium. Put: fall to strike - premium.
    Positive = up-move required, negative = down-move required.
    """
    if not spot or spot <= 0 or premium is None or premium < 0 or strike <= 0:
        return None
    if option_type == "call":
        return (strike + premium) / spot - 1.0
    if option_type == "put":
        return (strike - premium) / spot - 1.0
    return None


def days_between(start: str, end: str) -> int:
    return (_date.fromisoformat(end) - _date.fromisoformat(start)).days


def expiry_clears_catalyst(catalyst_date: str, expiration: str,
                           buffer_days: int = CATALYST_EXPIRY_BUFFER_DAYS) -> bool:
    """Playbook gate 2: expiration >= catalyst + buffer."""
    return days_between(catalyst_date, expiration) >= buffer_days


def priced_read(*, spot: float, atm_call_mid: float, atm_put_mid: float,
                my_expected_move_pct: float, direction: int,
                strike: float, option_type: str, premium: float,
                bid, ask) -> dict:
    """The journal-ready arithmetic block for playbook gates 3 and 5.

    Everything the entry checklist wants written down BEFORE the order:
    what the chain prices, what I expect, the residual edge, the move the
    contract needs just to break even, and the liquidity toll.
    """
    priced = straddle_move(atm_call_mid, atm_put_mid, spot)
    sigma = one_sigma_move(atm_call_mid, atm_put_mid, spot)
    edge = edge_vs_priced(my_expected_move_pct, priced, direction)
    breakeven = breakeven_move_pct(spot, strike, option_type, premium)
    spread = spread_pct(bid, ask)

    def _r(v):
        return round(v, 4) if v is not None else None

    return {
        "spot": spot,
        "priced_move_pct": _r(priced),
        "one_sigma_pct": _r(sigma),
        "my_expected_move_pct": _r(my_expected_move_pct),
        "edge_vs_priced_pct": _r(edge),
        "breakeven_move_pct": _r(breakeven),
        "spread_pct": _r(spread),
        # epsilon so "exactly at the line" doesn't trip on float noise
        "spread_needs_justification": bool(
            spread is not None and spread > SPREAD_JUSTIFY_PCT + 1e-9),
    }


# ---------------------------------------------------------------- positions

@dataclass
class OptionPosition:
    occ: str                  # canonical OCC symbol (the position key)
    underlying: str
    option_type: str          # call | put
    strike: float
    expiration: str           # YYYY-MM-DD
    contracts: int
    entry_premium: float      # per-share premium paid
    cost: float               # contracts * entry_premium * MULTIPLIER
    max_loss: float           # == cost for a long option (invariant 1, at entry)
    entry_date: str
    spy_entry: float
    catalyst_date: str        # the dated catalyst the thesis rides (gate 2)
    horizon_days: int
    confidence: float
    edge_class: str


@dataclass
class ClosedOptionTrade:
    occ: str
    underlying: str
    option_type: str
    strike: float
    expiration: str
    contracts: int
    entry_premium: float
    exit_premium: float       # 0.0 == expired worthless
    cost: float
    proceeds: float
    entry_date: str
    exit_date: str
    exit_reason: str
    net_return: float         # exit_premium / entry_premium - 1
    spy_return: float
    excess: float
    confidence: float
    edge_class: str
    horizon_days: int
