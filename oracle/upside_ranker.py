"""oracle/upside_ranker.py — the systematic best-first ranker (2026-07-06).

The complete Stage-1 machine (docs/oracle_upside_spec.md §3). Run EVERY net over
the WHOLE panel, compose them into ONE priority score, and emit a fully-ordered
best-first queue with a per-net breakdown. No hand-picking, no sliver — the read
works down the machine's ranking to whatever depth the budget allows, and every
name that was screened is in the record (ranked or dropped-with-reason).

Two passes, because live Robinhood is ≤10 symbols/call (can't live-verify 5,000):
  1. rank_all(panel, ...)         — compose the on-disk nets over the WHOLE universe.
  2. reconcile_top(ranked, live)  — live-verify the top slice: drop financials/
                                    shells/recycled tickers, compute the true
                                    52wk range_reversal, penalize arrived names.
So thousands are ranked, hundreds are live-verified, dozens are read — a funnel,
not a sliver.

NETS (each contributes 0..1; a net with no input contributes 0 and is logged
INACTIVE — the architecture is complete, wiring a feed activates a net without
touching the ranker):
  acceleration      revenue accel + margin turn (fundamental 2nd derivative)
  recent_strength   recent (~5wk) relative trend
  range_reversal    LOW in 52wk range + recent upturn — the VALIDATED washout profile
  earnings_surprise beat-and-raise (needs an earnings feed)
  thematic          under-covered beneficiary of a forming theme (needs a themes map)
  special_situation spinoff / post-reorg / recent IPO (needs an events feed)
  value_floor       cheap vs tangible book / net cash (downside-conviction bonus)

Weights are explicit and calibratable — Stage-7 memory maps hit-rate per
inflection_type back onto per-net weights over time.
"""
from __future__ import annotations

from typing import Optional

from oracle.upside_sourcing import (
    bottom_up_signals,
    in_hunting_ground,
    is_arrived_52w,
    range_position,
    reconcile_queue,
    top_down_signal,
)

# Default net weights. range_reversal leads (the measured 2026-07-06 profile: the
# read's keeps were the low-in-52wk-range names); acceleration + earnings_surprise
# are the fundamental 2nd-derivative core; thematic/special_situation are the
# forward/structural nets; value_floor is a downside-conviction bonus, not a driver.
DEFAULT_WEIGHTS = {
    "acceleration": 1.0,
    "recent_strength": 0.8,
    "range_reversal": 1.3,
    "earnings_surprise": 1.1,
    "thematic": 0.7,
    "special_situation": 0.7,
    "value_floor": 0.5,
}
ALL_NETS = tuple(DEFAULT_WEIGHTS.keys())


# ---- individual nets (0..1) -------------------------------------------------
def net_acceleration(row: dict) -> Optional[float]:
    """Fundamental 2nd-derivative: revenue acceleration + margin turn. None if the
    trajectory data isn't present (net INACTIVE for this row)."""
    if not row.get("revenue") and not row.get("op_margin"):
        return None
    s = bottom_up_signals(row)
    vals = [s.get("accel", 0.0), s.get("margin_turn", 0.0)]
    return max(vals) if any(vals) else 0.0


def net_recent_strength(row: dict) -> Optional[float]:
    if row.get("ret_recent") is None or row.get("spy_ret_recent") is None:
        return None
    return bottom_up_signals(row).get("rel_strength", 0.0)


def net_range_reversal(row: dict) -> Optional[float]:
    """The VALIDATED washout profile: LOW in the 52-week range AND recently turning
    up. Score = (1 - range_pos) gated by a positive recent trend. Needs the TRUE
    52wk range (range_pos) — populated from live fundamentals in reconcile_top;
    None on the on-disk pass unless a range_pos proxy is present."""
    rp = row.get("range_pos")
    if rp is None:
        return None
    turning = (row.get("ret_recent") or 0.0) > (row.get("spy_ret_recent") or 0.0)
    return round((1.0 - float(rp)) * (1.0 if turning else 0.5), 4)


def net_earnings_surprise(row: dict) -> Optional[float]:
    """Beat-and-raise. Needs eps_surprise (and optionally guidance_raised). None if
    no earnings feed for this row (net INACTIVE)."""
    eps = row.get("eps_surprise")
    if eps is None:
        return None
    beat = max(0.0, min(1.0, float(eps) / 0.10))
    return min(1.0, beat * (1.4 if row.get("guidance_raised") else 1.0))


def net_thematic(row: dict, themes: Optional[set] = None) -> Optional[float]:
    if not row.get("theme"):
        return None
    return top_down_signal(row, themes or set()).get("thematic", 0.0)


def net_special_situation(row: dict) -> Optional[float]:
    """Spinoff / post-reorg / recent IPO — the structural class where big upside
    hides. None if the events feed didn't tag this row."""
    ss = row.get("special_situation")
    if not ss:
        return None
    return 1.0


def net_value_floor(row: dict) -> Optional[float]:
    """Downside-conviction bonus: how cheap vs a real floor (net cash / tangible
    book). Not a driver — it can't make a name rise — but a hard floor de-risks a
    convex bet. Expects `price_to_tangible_book` (P/TB) and/or `net_cash_ratio`
    (net cash / marketcap). None if neither present."""
    ptb = row.get("price_to_tangible_book")
    ncr = row.get("net_cash_ratio")
    if ptb is None and ncr is None:
        return None
    score = 0.0
    if ptb is not None and ptb > 0:
        # P/TB 1.0 -> 0.5, 0.5 -> 1.0, >=2 -> 0
        score = max(score, max(0.0, min(1.0, (2.0 - float(ptb)) / 1.5)))
    if ncr is not None and ncr > 0:
        score = max(score, min(1.0, float(ncr)))    # net cash >= marketcap -> 1.0
    return round(score, 4)


_NET_FUNCS = {
    "acceleration": net_acceleration,
    "recent_strength": net_recent_strength,
    "range_reversal": net_range_reversal,
    "earnings_surprise": net_earnings_surprise,
    "thematic": lambda r: None,        # replaced below to accept themes
    "special_situation": net_special_situation,
    "value_floor": net_value_floor,
}


def net_scores(row: dict, themes: Optional[set] = None) -> dict:
    """Every net's contribution for one row. Only nets with an input present appear
    (a None-returning net is INACTIVE for this row and simply absent)."""
    out = {}
    for name, fn in _NET_FUNCS.items():
        v = net_thematic(row, themes) if name == "thematic" else fn(row)
        if v is not None:
            out[name] = float(v)
    return out


def composite_score(scores: dict, weights: Optional[dict] = None) -> float:
    """Weighted sum of the active nets. Not normalized by weight-sum: a name that
    fires MORE independent nets scores higher (corroboration across orthogonal
    signals is itself evidence), which is the whole point of a multi-net machine."""
    w = weights or DEFAULT_WEIGHTS
    return round(sum(w.get(k, 0.0) * v for k, v in scores.items()), 4)


# ---- pass 1: rank the WHOLE universe on the on-disk nets --------------------
def rank_all(panel: list[dict], *, themes: Optional[set] = None,
             weights: Optional[dict] = None) -> dict:
    """Compose every net over the whole panel and return a best-first ranking plus
    a coverage report. NOTHING is hand-picked and nothing is silently dropped:
    out-of-hunting-ground and no-signal names are recorded in the coverage counts.
    Returns {ranked, coverage} where ranked is best-first with a per-net breakdown."""
    themes = themes or set()
    ranked, dropped = [], {"out_of_ground": 0, "no_signal": 0}
    active_seen, inactive_candidates = set(), {n: 0 for n in ALL_NETS}
    for row in panel:
        sym = (row.get("symbol") or row.get("ticker") or "").upper()
        if not in_hunting_ground(row):
            dropped["out_of_ground"] += 1
            continue
        scores = net_scores(row, themes)
        for n in ALL_NETS:
            if n in scores:
                active_seen.add(n)
            else:
                inactive_candidates[n] += 1
        if not scores or composite_score(scores, weights) <= 0:
            dropped["no_signal"] += 1
            continue
        ranked.append({
            "symbol": sym, "mcap": row.get("mcap"), "sector": row.get("sector"),
            "theme": row.get("theme"), "special_situation": row.get("special_situation"),
            "nets": scores, "n_nets": len(scores),
            "composite": composite_score(scores, weights),
            "ret_recent": row.get("ret_recent"),
        })
    ranked.sort(key=lambda c: -c["composite"])
    for i, c in enumerate(ranked):
        c["rank"] = i + 1
    coverage = {
        "n_panel": len(panel),
        "n_ranked": len(ranked),
        "dropped": dropped,
        "active_nets": sorted(active_seen),
        # a net is INACTIVE if it never fired for any in-ground row (no feed wired)
        "inactive_nets": sorted(n for n in ALL_NETS if n not in active_seen),
    }
    return {"ranked": ranked, "coverage": coverage}


# ---- pass 2: live-verify the top slice -------------------------------------
def reconcile_top(ranked: list[dict], live: dict, *,
                  weights: Optional[dict] = None, arrived_drop: bool = True) -> dict:
    """Live-verify the top slice: drop financials/shells/recycled tickers
    (reconcile_queue), compute the TRUE 52wk range_reversal net from live
    high/low/price, drop or down-weight names ARRIVED in their range, and
    RE-SCORE the composite with range_reversal now active. Returns the finalized
    machine queue (best-first) + a drop log. `live` = {SYM: {sector, num_employees,
    pb_ratio, high_52_weeks, low_52_weeks, last_price, ...}}."""
    kept, dropped = reconcile_queue(ranked, live)          # financials/shells/artifacts
    finalized, arrived = [], []
    for c in kept:
        f = live.get(c["symbol"]) or {}
        rp = range_position(f.get("last_price") or f.get("price"),
                            f.get("low_52_weeks"), f.get("high_52_weeks"))
        if rp is not None:
            c = dict(c)
            c["range_pos"] = round(rp, 4)
            arrived_flag = is_arrived_52w({**f, "last_price": f.get("last_price") or f.get("price")})
            if arrived_flag and arrived_drop:
                c["drop_reason"] = f"arrived: {rp:.0%} up its 52wk range"
                arrived.append(c)
                continue
            # activate the range_reversal net with the true range and re-score
            turning = (c.get("ret_recent") or 0.0) > 0
            c["nets"] = {**c["nets"], "range_reversal": round((1.0 - rp) * (1.0 if turning else 0.5), 4)}
            c["composite"] = composite_score(c["nets"], weights)
            c["n_nets"] = len(c["nets"])
        finalized.append(c)
    finalized.sort(key=lambda c: -c["composite"])
    for i, c in enumerate(finalized):
        c["final_rank"] = i + 1
    return {"queue": finalized, "dropped_reconcile": dropped, "dropped_arrived": arrived}
