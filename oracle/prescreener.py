"""Lightweight pre-screen.

Given a fundamentals snapshot, decide whether the symbol is worth a full
dossier pass. Excludes obviously broken names cheaply.
"""
from __future__ import annotations

from shared.fundamentals import FundamentalSnapshot


def prescreen(snap: FundamentalSnapshot) -> dict:
    """Return {pass: bool, reasons: [str]}."""
    reasons: list[str] = []

    if snap.data_quality < 0.4:
        reasons.append("data_quality_low")

    if snap.revenue_ttm is not None and snap.revenue_ttm <= 0:
        reasons.append("no_revenue")

    if snap.shares_diluted is not None and snap.shares_diluted <= 0:
        reasons.append("no_shares")

    if snap.dilution_yoy is not None and snap.dilution_yoy > 0.5:
        reasons.append("dilutive")

    if (
        snap.cash_runway_quarters is not None
        and snap.cash_runway_quarters < 4
        and snap.ocf_ttm is not None
        and snap.ocf_ttm < 0
    ):
        reasons.append("short_runway")

    if snap.equity is not None and snap.equity < 0:
        reasons.append("negative_equity")

    return {"pass": not reasons, "reasons": reasons}


def batch_prescreen(snaps: list[FundamentalSnapshot]) -> list[dict]:
    """Return a list of {symbol, pass, reasons} for each snapshot."""
    return [{"symbol": s.symbol, **prescreen(s)} for s in snaps]
