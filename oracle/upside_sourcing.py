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
REL_STRENGTH_MIN = 0.10     # 6-mo return beating the market by ≥10pp


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
      ret_6m, spy_ret_6m: 6-month total returns (fraction)
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

    r6, s6 = row.get("ret_6m"), row.get("spy_ret_6m")
    if r6 is not None and s6 is not None:
        rs = float(r6) - float(s6)
        if rs >= REL_STRENGTH_MIN:
            sig["rel_strength"] = min(1.0, rs / 0.50)

    if row.get("growth_catalyst"):     # a discrete opening event (new product/contract/approval)
        sig["growth_catalyst"] = 1.0
    return sig


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
    return {
        "symbol": (row.get("symbol") or row.get("ticker") or "").upper(),
        "mcap": row.get("mcap"), "coverage": row.get("coverage"),
        "sector": row.get("sector"), "theme": row.get("theme"),
        "special_situation": row.get("special_situation"),
        "nets": nets, "direction": ("both" if bottom and top else ("bottom_up" if bottom else "top_down")),
        "spotlight_score": spotlight_score(bottom, top),
        "open_question": "Is the inflection real, durable, large, and not-yet-arrived? (Stage-2 read)",
    }


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
