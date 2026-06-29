"""Cohort lifecycle — batch-and-hold strategy.

A cohort is a set of positions selected at one point in time and held for
~12 months.  During the hold period, exits happen ONLY on thesis-break
conditions — never on rank drift or score freshness.

Thesis-break conditions (the only permitted exits during hold):
  1. fraud           — SEC investigation or fraud allegation
  2. going_concern   — bankruptcy filing or going-concern disclosure
  3. insider_reversal — insiders who accumulated begin net-selling
  4. drawdown        — position loss >= 40% from entry price
  5. thesis_exhausted — original catalyst resolved without price response
  6. thesis_break    — moat AND quality both collapsed (from exits.exit_signal)
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any

from .exits import exit_signal

DRAWDOWN_EXIT_THRESHOLD = 0.40


@dataclass
class CohortPosition:
    symbol: str
    entry_price: float
    entry_date: str
    thesis_snapshot: str
    sector: str = ""
    exit_date: str = ""
    exit_price: float = 0.0
    exit_reason: str = ""
    graded_return: float | None = None


@dataclass
class Cohort:
    cohort_id: str
    inception_date: str
    review_date: str
    status: str = "active"
    positions: dict[str, CohortPosition] = field(default_factory=dict)

    def active_symbols(self) -> list[str]:
        return [sym for sym, pos in self.positions.items() if not pos.exit_date]

    def is_active(self) -> bool:
        return self.status == "active"


def create_cohort(
    cohort_id: str,
    dossiers: list[dict],
    prices: dict[str, float],
    *,
    inception_date: str,
    review_date: str,
) -> Cohort:
    positions = {}
    for d in dossiers:
        sym = d["symbol"]
        price = prices.get(sym, d.get("current_price", 0.0))
        positions[sym] = CohortPosition(
            symbol=sym,
            entry_price=price,
            entry_date=inception_date,
            thesis_snapshot=d.get("thesis", ""),
            sector=d.get("sector", ""),
        )
    return Cohort(
        cohort_id=cohort_id,
        inception_date=inception_date,
        review_date=review_date,
        positions=positions,
    )


def check_thesis_break(
    symbol: str,
    cohort: Cohort,
    *,
    current_price: float,
    dossier: dict | None = None,
    insider_reversal: bool = False,
    fraud_flag: bool = False,
    going_concern_flag: bool = False,
    thesis_exhausted: bool = False,
) -> dict | None:
    """Check whether a cohort position should exit.

    Returns ``{reason, details}`` if a thesis-break condition is met,
    ``None`` if the position should hold.
    """
    pos = cohort.positions.get(symbol)
    if not pos or pos.exit_date:
        return None

    if fraud_flag:
        return {"reason": "fraud", "details": "SEC investigation or fraud allegation"}

    if going_concern_flag:
        return {"reason": "going_concern", "details": "bankruptcy or going-concern disclosure"}

    if insider_reversal:
        return {"reason": "insider_reversal", "details": "insiders who accumulated are now selling"}

    if pos.entry_price > 0 and current_price > 0:
        loss = (pos.entry_price - current_price) / pos.entry_price
        if loss >= DRAWDOWN_EXIT_THRESHOLD:
            return {
                "reason": "drawdown",
                "details": f"down {loss:.0%} from entry ${pos.entry_price:.2f}",
            }

    if thesis_exhausted:
        return {"reason": "thesis_exhausted", "details": "catalyst resolved without price response"}

    if dossier:
        sig = exit_signal(dossier, current_price)
        if sig["action"] == "sell" and sig["reason"] == "thesis_break":
            return {"reason": "thesis_break", "details": "moat and quality both collapsed"}

    return None


def record_exit(
    cohort: Cohort,
    symbol: str,
    *,
    exit_price: float,
    exit_date: str,
    exit_reason: str,
) -> None:
    pos = cohort.positions.get(symbol)
    if not pos:
        return
    pos.exit_date = exit_date
    pos.exit_price = exit_price
    pos.exit_reason = exit_reason
    if pos.entry_price > 0:
        pos.graded_return = (exit_price - pos.entry_price) / pos.entry_price


def grade_cohort(cohort: Cohort, final_prices: dict[str, float]) -> dict:
    """Grade all positions at cohort review.  Sets cohort status to 'closed'."""
    results: dict[str, Any] = {}
    for sym, pos in cohort.positions.items():
        if pos.exit_date:
            results[sym] = {
                "entry_price": pos.entry_price,
                "exit_price": pos.exit_price,
                "return": pos.graded_return,
                "exit_reason": pos.exit_reason,
                "held_to_horizon": False,
            }
        else:
            final_px = final_prices.get(sym, pos.entry_price)
            ret = (final_px - pos.entry_price) / pos.entry_price if pos.entry_price > 0 else 0.0
            pos.graded_return = ret
            results[sym] = {
                "entry_price": pos.entry_price,
                "final_price": final_px,
                "return": ret,
                "exit_reason": "",
                "held_to_horizon": True,
            }
    returns = [r["return"] for r in results.values() if r["return"] is not None]
    cohort.status = "closed"
    return {
        "cohort_id": cohort.cohort_id,
        "positions": results,
        "mean_return": sum(returns) / len(returns) if returns else 0.0,
        "n_held_to_horizon": sum(1 for r in results.values() if r["held_to_horizon"]),
        "n_thesis_break": sum(1 for r in results.values() if not r["held_to_horizon"]),
    }


def should_review(cohort: Cohort, today: str) -> bool:
    return today >= cohort.review_date


def save_cohort(path: str, cohort: Cohort) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {
        "cohort_id": cohort.cohort_id,
        "inception_date": cohort.inception_date,
        "review_date": cohort.review_date,
        "status": cohort.status,
        "positions": {sym: asdict(pos) for sym, pos in cohort.positions.items()},
    }
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load_cohort(path: str) -> Cohort | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    positions = {}
    for sym, pdata in data.get("positions", {}).items():
        positions[sym] = CohortPosition(**pdata)
    return Cohort(
        cohort_id=data["cohort_id"],
        inception_date=data["inception_date"],
        review_date=data["review_date"],
        status=data.get("status", "active"),
        positions=positions,
    )
