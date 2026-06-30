"""Momentum compounder — risk budget for LLM judgment.

No regime filter. The trailing stop (price < 20-day MA) IS the risk
management. The LLM can modulate risk_budget based on market breadth
and macro context — not as a binary on/off, but as a dial (0.5–1.0)
that controls how much of the portfolio is invested.
"""
from __future__ import annotations


def rotation_plan(*, risk_budget: float | None = None) -> dict:
    """Return a plan dict.

    risk_budget defaults to 1.0 (fully invested). The LLM can lower it
    when breadth deteriorates or macro signals flash caution. Never goes
    below 0.5 — Delphi doesn't go to cash, she just gets cautious.
    """
    rb = risk_budget if risk_budget is not None else 1.0
    rb = max(0.5, min(1.0, rb))
    return {
        "regime": "momentum",
        "risk_budget": rb,
    }
