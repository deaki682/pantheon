"""The conditional rotation matrix — computed, never assumed.

"Where does the money go when sector X crashes?" is answerable as conditional
co-movement: for every historical day the trigger sector fell hard, measure
every other sector's return over the FOLLOWING week (the tradeable window —
same-day repricing is not capturable). Destinations are the sectors whose
conditional forward return beats their own unconditional baseline with a
decent hit rate.

Live estimate from Jul-2024..Jul-2026 (XLK <= -2% days, n=51): XLB +0.94pp
excess, XLI +0.71pp, XLU +0.62pp @ 76% hit — and XLK itself +0.52pp (the
crashed sector is its own biggest bouncer). Regime-conditional: that sample is
a buy-the-dip era; 2022 would look different. Hence the ghost.

Pure stdlib; ETF close series passed in.
"""
from __future__ import annotations

from typing import Optional

TRIGGER_DROP = -0.02     # trigger-sector daily move that counts as a crash
FORWARD_DAYS = 5         # the following-week window
MIN_EVENTS = 10          # below this, the matrix is an anecdote — refuse
MIN_HIT_RATE = 0.60      # destination quality floors
MIN_EXCESS = 0.002       # +0.2pp over baseline


def _ret(series: list[float], i: int, j: int) -> float:
    return series[j] / series[i] - 1.0


def conditional_matrix(
    etf_closes: dict[str, list[float]],
    *,
    trigger_sym: str,
    trigger_drop: float = TRIGGER_DROP,
    forward_days: int = FORWARD_DAYS,
) -> dict:
    """Per-ETF conditional forward stats after trigger-sector crash days.

    etf_closes: {etf: [aligned daily closes, oldest first]} — series MUST be
    date-aligned (same sessions); pass ETFs from one venue family.
    Returns {n_events, trigger, per_etf: {etf: {cond, uncond, excess, hit_rate}}}.
    """
    trig = etf_closes.get(trigger_sym)
    if not trig:
        return {"n_events": 0, "trigger": trigger_sym, "per_etf": {}}
    n = min(len(v) for v in etf_closes.values())
    aligned = {s: v[-n:] for s, v in etf_closes.items()}
    trig = aligned[trigger_sym]

    events = [
        i for i in range(1, n - forward_days - 1)
        if _ret(trig, i - 1, i) <= trigger_drop
    ]
    per: dict[str, dict] = {}
    for sym, series in aligned.items():
        base_windows = range(1, n - forward_days - 1)
        uncond = [_ret(series, i, i + forward_days) for i in base_windows]
        cond = [_ret(series, i, i + forward_days) for i in events]
        if not cond or not uncond:
            continue
        m_c = sum(cond) / len(cond)
        m_u = sum(uncond) / len(uncond)
        per[sym] = {
            "cond": round(m_c, 5),
            "uncond": round(m_u, 5),
            "excess": round(m_c - m_u, 5),
            "hit_rate": round(sum(1 for x in cond if x > 0) / len(cond), 3),
        }
    return {"n_events": len(events), "trigger": trigger_sym, "per_etf": per}


def predicted_destinations(
    matrix: dict,
    *,
    top_n: int = 3,
    min_hit_rate: float = MIN_HIT_RATE,
    min_excess: float = MIN_EXCESS,
    min_events: int = MIN_EVENTS,
) -> list[dict]:
    """Rank destination ETFs from a conditional matrix, quality-floored.

    Excludes the trigger sector itself — its bounce is the FADE leg's claim;
    keeping the legs distinct is what makes the head-to-head test clean.
    Returns [] when the matrix has too few events to mean anything.
    """
    if matrix.get("n_events", 0) < min_events:
        return []
    trigger = matrix.get("trigger")
    rows = [
        {"symbol": s, **stats}
        for s, stats in matrix.get("per_etf", {}).items()
        if s != trigger
        and stats["hit_rate"] >= min_hit_rate
        and stats["excess"] >= min_excess
    ]
    rows.sort(key=lambda r: -r["excess"])
    return rows[:top_n]
