"""Ghost Delphi — paper-only shadow of the momentum strategy.

Opens a paper position for the ENTIRE universe — including names below their
20-day MA and names the ranking passed over — because the unbought names are
the control groups that make the strategy's three claims testable:

  - momentum_terciles: does higher 65-day momentum predict higher forward
    return? (the primary signal)
  - signal_lift.above_ma: do names above their 20-day MA beat names below it?
    This is the MA trailing-stop premise. The live ranker pre-filters below-MA
    names, so WITHOUT the ghost opening them anyway there is no control group
    and the exit rule can only be believed, never measured.
  - signal_lift.selected: did the top-10 book beat the above-MA names it
    passed over? (tests ranking + LLM vetoes end-to-end)
  - signal_lift.vetoed: did the LLM's entry vetoes filter losers or kill
    winners? (flag set only on the reviewed candidate set, so the comparison
    is picks-vs-passed-over, not vs names the LLM never saw)

Engine is `shared.ghost`; entries are tagged source="momentum" and the report
filters to that source so retired-strategy entries can't pollute the verdict.
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, group_stats, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)
from .signals import momentum as momentum_of
from .signals import moving_average
from .sleeve import MA_PERIOD, MOMENTUM_LOOKBACK

DEFAULT_DELPHI_HORIZON_DAYS = 90
SOURCE = "momentum"


def universe_to_ghost(
    universe_prices: dict[str, list[float]],
    *,
    selected: Optional[Iterable[str]] = None,
    vetoed: Optional[Iterable[str]] = None,
    reviewed: Optional[Iterable[str]] = None,
    lookback: int = MOMENTUM_LOOKBACK,
    ma_period: int = MA_PERIOD,
    horizon_days: int = DEFAULT_DELPHI_HORIZON_DAYS,
) -> list[dict]:
    """Build ghost candidates for the FULL universe from raw price history.

    Deliberately does NOT use rank_by_momentum: that filters out below-MA
    names, and those are exactly the control group the above_ma lift needs.

    selected: symbols the live run actually holds (top-10 book). Flagged only
    on above-MA names — only they were eligible, so that's the fair comparison.
    vetoed / reviewed: the LLM's entry-judgment set. `vetoed` is flagged only
    on names in `reviewed` (the candidates the LLM actually looked at).
    """
    sel = {s.upper() for s in (selected or [])}
    veto = {s.upper() for s in (vetoed or [])}
    seen = {s.upper() for s in (reviewed or [])}
    flag_selection = selected is not None
    flag_vetoes = vetoed is not None

    out: list[dict] = []
    for sym, prices in universe_prices.items():
        sym = sym.upper()
        if not prices:
            continue
        px = float(prices[-1])
        if px <= 0:
            continue
        ma = moving_average(prices, ma_period)
        above = ma is not None and px >= ma
        features: dict = {
            "momentum": momentum_of(prices, lookback),
            "above_ma": bool(above),
        }
        if flag_selection and above:
            features["selected"] = sym in sel
        if flag_vetoes and sym in (seen | veto):
            features["vetoed"] = sym in veto
        out.append({
            "symbol": sym,
            "price": px,
            "horizon_days": horizon_days,
            "source": SOURCE,
            "features": features,
        })
    return out


def candidates_to_ghost(
    candidates: Iterable[dict], price_lookup: PriceLookup, *,
    horizon_days: int = DEFAULT_DELPHI_HORIZON_DAYS,
) -> list[dict]:
    """Adapter for pre-ranked candidate dicts ({symbol, momentum, price, ma}).

    Prefer universe_to_ghost for the weekly run — ranked lists are usually
    already MA-filtered, which silently drops the above_ma control group.
    """
    out: list[dict] = []
    for c in candidates:
        sym = (c.get("symbol") or "").upper()
        if not sym:
            continue
        px = price_lookup(sym)
        if px is None or px <= 0:
            continue
        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": horizon_days,
            "source": SOURCE,
            "features": {
                "momentum": c.get("momentum"),
                "above_ma": c.get("ma") is not None and c.get("price", 0) >= c.get("ma", 0),
            },
        })
    return out


def signal_report(entries: Iterable[GhostEntry]) -> dict:
    """Momentum-strategy validation from graded entries (source='momentum').

    momentum_terciles tests the ranking signal; signal_lift carries above_ma
    (the MA-exit premise), selected (the book vs passed-over), and vetoed
    (LLM judgment) once those flags exist on graded entries.
    """
    graded = [e for e in graded_only(entries) if e.source == SOURCE]
    if not graded:
        return {"n": 0, "mean_return": None, "hit_rate": None,
                "momentum_terciles": {}, "signal_lift": {}}
    return {
        **overall_stats(graded),
        "momentum_terciles": numeric_tercile_stats(graded, "momentum"),
        "signal_lift": boolean_lift(graded),
    }
