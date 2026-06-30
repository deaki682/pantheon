"""Momentum compounder — always fully invested.

No regime filter. The trailing stop (price < 20-day MA) IS the risk
management. When a name breaks its MA it gets sold; if fewer than 10
names are above their MAs, the portfolio simply holds fewer positions
with the remainder in cash.
"""
from __future__ import annotations


def rotation_plan() -> dict:
    """Return a plan dict. Always fully invested — no regime gating."""
    return {
        "regime": "momentum",
        "risk_budget": 1.0,
    }
