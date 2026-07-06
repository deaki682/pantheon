"""Oracle Stage-1 SPOTLIGHT — the two-direction screen that AIMS the reader
(docs/oracle_upside_spec.md §3 Stage 1).

This is NOT the edge — quants own these signals. Its only job is to point the
breadth-read (Stage 2) at the ~300 names in the neglected corner where an
inflection is plausibly happening, from two directions:

  bottom_up  — whose NUMBERS are already bending (acceleration, beat-and-raise,
               relative strength);
  top_down   — under-covered beneficiaries of a FORMING theme, whose own numbers
               may not have bent yet (the market hasn't connected them to the wave).

Everything is gated to the HUNTING GROUND first (spec I1): small/mid-cap, thinly
covered, or a fresh special situation. Oracle cedes the mega-cap momentum names
to the quants and only hunts where reading breadth is an edge. Pure functions over
a panel row so the logic is testable without a live data pull; the runner wires
real Sharadar/price/coverage data into the row shape.
"""
from __future__ import annotations

from typing import Any, Optional

# hunting-ground bounds (spec I1)
MCAP_MIN = 1e8
MCAP_MAX = 3e9
MCAP_MAX_SPECIAL = 5e9
COVERAGE_MAX = 4
SPECIAL_SITUATIONS = {"spinoff", "post_reorg", "ipo"}   # ipo<18mo handled by the caller

# signal thresholds (deliberately loose — recall-max; Stage 2 does precision)
ACCEL_MIN_PP = 2.0          # rev growth must ACCELERATE by ≥2pp q/q to count
MARGIN_TURN_MIN_PP = 1.0    # operating margin up ≥1pp q/q
EPS_BEAT_MIN = 0.02         # ≥2% EPS surprise
# RECENT trend, not 6-mo trailing (2026-07-06 fix). The first run's 6mo rel-strength
# net surfaced blowoff-and-fade names — spikes captured inside the window that had
# already deflated, which the read killed 6/9 on "already arrived". Recent
# (≈4–6wk) trend drops the faded names (they're negative recently), and a
# near-high penalty (below) sinks the ones that already repriced to their high.
RECENT_STRENGTH_MIN = 0.05  # recent (~5wk) return beating the market by ≥5pp
NEAR_HIGH_FRAC = 0.10       # within 10% of the window high = "arrived"; penalize
NEAR_HIGH_PENALTY = 0.4     # score multiplier for names sitting at their high


def in_hunting_ground(row: dict) -> bool:
    """Spec I1. A name qualifies if it's a thinly-covered small/mid-cap, OR a
    fresh special situation (which may run a bit larger). Mega-caps and
    well-covered names are OUT — the edge evaporates where the Street already reads."""
    mcap = row.get("mcap")
    if mcap is None or mcap <= 0:
        return False
    special = row.get("special_situation") in SPECIAL_SITUATIONS
    if special:
        return mcap <= MCAP_MAX_SPECIAL
    cov = row.get("coverage")
    covered_thin = (cov is None) or (int(cov) <= COVERAGE_MAX)
    return (MCAP_MIN <= mcap <= MCAP_MAX) and covered_thin


def _rev_growth_series(rev: list[float]) -> list[float]:
    """q/q-style growth between consecutive quarterly revenue points."""
    out = []
    for a, b in zip(rev, rev[1:]):
        if a and a > 0:
            out.append((b - a) / a)
    return out


def bottom_up_signals(row: dict) -> dict[str, float]:
    """Which bottom-up signals fire, with a strength each (spec §3 bottom_up).
    Expects trajectory fields on the row:
      revenue: [older..newer] quarterly revenue
      op_margin: [older..newer] quarterly operating margin (fraction)
      eps_surprise: latest EPS surprise (fraction)
      guidance_raised: bool
      ret_recent, spy_ret_recent: RECENT (~5wk) total returns (fraction) — the
        momentum measure. NOT 6-mo trailing (which surfaced faded spikes).
    """
    sig: dict[str, float] = {}
    rev = [float(x) for x in (row.get("revenue") or []) if x is not None]
    if len(rev) >= 3:
        g = _rev_growth_series(rev)
        if len(g) >= 2:
            accel_pp = (g[-1] - g[-2]) * 100.0
            if accel_pp >= ACCEL_MIN_PP and g[-1] > 0:
                sig["accel"] = min(1.0, accel_pp / 10.0)

    m = [float(x) for x in (row.get("op_margin") or []) if x is not None]
    if len(m) >= 2:
        turn_pp = (m[-1] - m[-2]) * 100.0
        if turn_pp >= MARGIN_TURN_MIN_PP:
            sig["margin_turn"] = min(1.0, turn_pp / 5.0)

    eps = row.get("eps_surprise")
    if eps is not None and float(eps) >= EPS_BEAT_MIN:
        beat = min(1.0, float(eps) / 0.10)
        if row.get("guidance_raised"):
            sig["beat_and_raise"] = beat
        else:
            sig["eps_beat"] = beat * 0.6

    rr, sr = row.get("ret_recent"), row.get("spy_ret_recent")
    if rr is not None and sr is not None:
        rs = float(rr) - float(sr)
        if rs >= RECENT_STRENGTH_MIN:      # RECENTLY trending up more than the market
            sig["rel_strength"] = min(1.0, rs / 0.25)

    if row.get("growth_catalyst"):     # a discrete opening event (new product/contract/approval)
        sig["growth_catalyst"] = 1.0
    return sig


def arrival_penalty(row: dict) -> float:
    """Down-weight names that have already REPRICED to their high (the 'arrived'
    failure mode the first run's read killed 6/9 on). `pct_below_high` is the
    distance below the window high (0 = at high, 0.4 = 40% below). A name within
    NEAR_HIGH_FRAC of its high is penalized; a name with room to run is not. Returns
    a multiplier in (0,1]. Unknown → 1.0 (no penalty)."""
    pbh = row.get("pct_below_high")
    if pbh is None:
        return 1.0
    return NEAR_HIGH_PENALTY if float(pbh) < NEAR_HIGH_FRAC else 1.0


def top_down_signal(row: dict, forming_themes: Optional[set[str]] = None) -> dict[str, float]:
    """Fires if the name is an under-covered beneficiary of a FORMING theme, even
    if its own numbers haven't bent yet (spec §3 top_down). The row carries a
    `theme` tag (mapped upstream from the business to a sector wave); we only keep
    it if that theme is currently forming and the name is genuinely under-covered."""
    themes = forming_themes or set()
    theme = row.get("theme")
    if not theme or theme not in themes:
        return {}
    cov = row.get("coverage")
    if cov is not None and int(cov) > COVERAGE_MAX:
        return {}     # if it's well covered, the theme is already priced through it
    return {"thematic": float(row.get("theme_strength", 0.6))}


def spotlight_score(bottom: dict, top: dict) -> float:
    """A recall-oriented score used ONLY to rank the read queue and as the A/B
    Arm-B baseline — never as a selection decision. More independent signals +
    stronger signals = read this one sooner. Not the edge."""
    n = len(bottom) + len(top)
    strength = sum(bottom.values()) + sum(top.values())
    return round(n * strength, 4) if n else 0.0


def screen_row(row: dict, forming_themes: Optional[set[str]] = None) -> Optional[dict]:
    """Apply Stage 1 to one panel row. Returns a candidate dict (or None if it
    doesn't clear the hunting ground or fires no signal). KEEP iff
    (bottom_up ∨ top_down) ∧ in_hunting_ground."""
    if not in_hunting_ground(row):
        return None
    bottom = bottom_up_signals(row)
    top = top_down_signal(row, forming_themes)
    if not bottom and not top:
        return None
    nets = sorted(list(bottom.keys()) + list(top.keys()))
    penalty = arrival_penalty(row)
    return {
        "symbol": (row.get("symbol") or row.get("ticker") or "").upper(),
        "mcap": row.get("mcap"), "coverage": row.get("coverage"),
        "sector": row.get("sector"), "theme": row.get("theme"),
        "special_situation": row.get("special_situation"),
        "nets": nets, "direction": ("both" if bottom and top else ("bottom_up" if bottom else "top_down")),
        "pct_below_high": row.get("pct_below_high"), "ret_recent": row.get("ret_recent"),
        "at_high": penalty < 1.0,
        "spotlight_score": round(spotlight_score(bottom, top) * penalty, 4),
        "open_question": "Is the inflection real, durable, large, and not-yet-arrived? (Stage-2 read)",
    }


# ---- Stage 1c: freshness / identity reconcile vs live Robinhood -------------
# The spotlight runs on the on-disk Sharadar panel, which carries two faults a
# live cross-check catches (measured 2026-07-06): (1) RECYCLED TICKERS — SF1 keys
# history to the final ticker, so "OSG" (Overseas Shipholding, taken private 2024)
# now resolves to an unrelated Ambac-successor insurer (the SIVB/BBBY LAW); and
# (2) the accel/margin proxy mis-fires on FINANCIALS (muni-bond LPs, insurers) and
# on micro-SHELLS (a 7-employee 2024 holdco whose "acceleration" is off ~zero).
# So before spending the (expensive) breadth read, reconcile the queue against a
# live get_equity_fundamentals pull (≤10 syms/call) and drop the artifacts. The
# assistant supplies `live` = {SYM: {sector, num_employees, pb_ratio, market_cap,
# description}} because the broker feed is not importable in a script.
_FINANCIAL_SECTORS = {"finance", "financial", "specialty insurance"}
SHELL_MAX_EMPLOYEES = 25
ARTIFACT_PB_MAX = 20.0          # extreme POSITIVE P/B = shell/data artifact (RHLD=40);
                                # negative P/B is fine (levered turnarounds: SABR/IRWD)


def reconcile_queue(candidates: list[dict], live: dict) -> tuple[list[dict], list[dict]]:
    """Drop the names a live cross-check exposes as un-fundable BEFORE the read.
    Returns (kept, dropped) — each dropped candidate stamped with `drop_reason`
    (never silently removed, spec I5). A candidate with NO live entry is KEPT but
    flagged `unreconciled` (couldn't verify — the read will check it)."""
    kept, dropped = [], []
    for c in candidates:
        f = live.get(c["symbol"])
        if not f:
            c = dict(c); c["unreconciled"] = True
            kept.append(c); continue
        sector = (f.get("sector") or "").strip().lower()
        emp = f.get("num_employees")
        pb = f.get("pb_ratio")
        reason = None
        if sector in _FINANCIAL_SECTORS:
            reason = f"financial sector ({f.get('sector')}) — accel/margin proxy meaningless"
        elif emp is not None and int(emp) < SHELL_MAX_EMPLOYEES:
            reason = f"micro-shell ({emp} employees) — acceleration off a near-zero base"
        elif pb is not None and float(pb) > ARTIFACT_PB_MAX:
            reason = f"P/B {pb} > {ARTIFACT_PB_MAX} — shell / data artifact"
        if reason:
            c = dict(c); c["drop_reason"] = reason
            dropped.append(c)
        else:
            kept.append(c)
    return kept, dropped


# The TRUE arrival gate needs the live 52-WEEK range, not a 6-month proxy. A name
# that bottomed 3 months ago and tripled shows "20% below its 6mo high" (looks
# early) but is 90% up its 52-week range (ARRIVED). Measured 2026-07-06: the read
# killed LIND/IRWD/NNBR/RRGB all on "already ran 2–4x" while the 6mo proxy waved
# them through. So compute range position from live Robinhood high_52_weeks /
# low_52_weeks and treat a name high in its range as arrived.
RANGE_POS_ARRIVED = 0.60        # > this far up the 52wk range = likely already repriced


def range_position(price: float, low_52w: float, high_52w: float) -> Optional[float]:
    """Where the price sits in its 52-week range: 0 = at the low, 1 = at the high.
    None if the range is degenerate."""
    if price is None or low_52w is None or high_52w is None:
        return None
    span = float(high_52w) - float(low_52w)
    if span <= 0:
        return None
    return max(0.0, min(1.0, (float(price) - float(low_52w)) / span))


def is_arrived_52w(f: dict) -> Optional[bool]:
    """True if the live fundamentals put the name high in its 52-week range (the
    real 'already ran' test). None if the range data is missing."""
    rp = range_position(f.get("last_price") or f.get("price"),
                        f.get("low_52_weeks"), f.get("high_52_weeks"))
    return None if rp is None else rp > RANGE_POS_ARRIVED


def screen_panel(panel: list[dict], forming_themes: Optional[set[str]] = None,
                 limit: Optional[int] = None) -> list[dict]:
    """Run Stage 1 over the whole panel; return candidates sorted by spotlight_score
    (the read-queue order). `limit` caps the queue handed to the (expensive)
    breadth read — but log what was dropped, never silently truncate (spec I5)."""
    cands = [c for c in (screen_row(r, forming_themes) for r in panel) if c]
    cands.sort(key=lambda c: -c["spotlight_score"])
    if limit is not None and len(cands) > limit:
        for c in cands[limit:]:
            c["queued"] = False
        kept = cands[:limit]
        for c in kept:
            c["queued"] = True
        return kept + cands[limit:]     # keep the tail in the record, flagged not-queued
    for c in cands:
        c["queued"] = True
    return cands
