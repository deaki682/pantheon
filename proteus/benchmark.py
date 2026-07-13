"""Proteus v2 — the benchmark stack (charter v2.1, art. 23).

Two lines, defined once, in code, never re-fit (protected under
art. 15 — weakening or re-fitting this definition is an integrity-gate
offense):

1. **The headline**: sleeve total return vs SPY total return over the
   same marks — the operator's honest "what if you'd just indexed" line.
2. **The deployment-adjusted line**: dollar excess vs what each bucket
   of capital was benchmarked to earn, interval by interval —

   ``excess_$ = ΔEquity − (risk₀·spy_ret + index_park₀·spy_ret
                            + (cash₀+tbill₀)·tbill_ret)``

   Capital at risk and index parks are benchmarked at SPY's own return
   (an index park IS the benchmark); cash and T-bill parks are
   benchmarked at the T-bill rate. A bull tape can't shame a working
   arb book, and a crash can't flatter one — in both directions.

Each curve mark carries the bucket decomposition at that instant:
``{date, equity, spy, risk_capital, cash_park, tbill_park, index_park}``.
Buckets must sum to equity (±1%); a mark without a decomposition is
treated as all-cash-park, which is the honest default for a flat book.
The T-bill rate is an INPUT (the review passes the live rate with its
source); the default is a standing journaled assumption, not a fit.
"""
from __future__ import annotations

from datetime import date as _date

TBILL_ANNUAL_DEFAULT = 0.04   # standing assumption; reviews pass the live rate
_BUCKETS = ("risk_capital", "cash_park", "tbill_park", "index_park")
_SUM_TOL = 0.01               # buckets must sum to equity within 1%


class BenchmarkError(ValueError):
    """A mark that misstates its own decomposition is refused."""


def _decompose(mark: dict) -> dict:
    """Bucket decomposition of one mark; flat default = all cash park."""
    if not any(k in mark for k in _BUCKETS):
        return {"risk_capital": 0.0, "cash_park": float(mark["equity"]),
                "tbill_park": 0.0, "index_park": 0.0}
    out = {k: float(mark.get(k, 0.0)) for k in _BUCKETS}
    total = sum(out.values())
    eq = float(mark["equity"])
    if eq > 0 and abs(total - eq) > _SUM_TOL * eq:
        raise BenchmarkError(
            f"mark {mark.get('date')}: buckets sum to {total:.2f} but "
            f"equity is {eq:.2f} — the decomposition must account for "
            "every dollar (art. 23)")
    return out


def headline(marks: list[dict]) -> dict:
    """Sleeve vs SPY total return over the same marks."""
    ms = [m for m in marks if m.get("equity") and m.get("spy")]
    if len(ms) < 2:
        return {"n_marks": len(ms), "sleeve_return": None, "spy_return": None,
                "excess": None}
    sleeve = ms[-1]["equity"] / ms[0]["equity"] - 1.0
    spy = ms[-1]["spy"] / ms[0]["spy"] - 1.0
    return {"n_marks": len(ms),
            "since": ms[0]["date"], "through": ms[-1]["date"],
            "sleeve_return": round(sleeve, 6), "spy_return": round(spy, 6),
            "excess": round(sleeve - spy, 6)}


def deployment_adjusted(marks: list[dict],
                        tbill_annual: float = TBILL_ANNUAL_DEFAULT) -> dict:
    """The deployment-adjusted line (art. 23). See module docstring for
    the once-defined formula."""
    ms = [m for m in marks if m.get("equity") and m.get("spy")]
    if len(ms) < 2:
        return {"n_intervals": 0, "excess_dollars": None}
    excess = 0.0
    risk_dollar_days = 0.0
    for prev, cur in zip(ms, ms[1:]):
        d0 = _decompose(prev)
        days = max(0, (_date.fromisoformat(str(cur["date"])[:10])
                       - _date.fromisoformat(str(prev["date"])[:10])).days)
        spy_ret = cur["spy"] / prev["spy"] - 1.0
        tbill_ret = tbill_annual * days / 365.0
        benched = ((d0["risk_capital"] + d0["index_park"]) * spy_ret
                   + (d0["cash_park"] + d0["tbill_park"]) * tbill_ret)
        excess += (cur["equity"] - prev["equity"]) - benched
        risk_dollar_days += d0["risk_capital"] * days
    return {"n_intervals": len(ms) - 1,
            "since": ms[0]["date"], "through": ms[-1]["date"],
            "tbill_annual": tbill_annual,
            "excess_dollars": round(excess, 2),
            "risk_dollar_days": round(risk_dollar_days, 2),
            "excess_per_risk_dollar_year": (
                round(excess / (risk_dollar_days / 365.0), 6)
                if risk_dollar_days > 0 else None)}
