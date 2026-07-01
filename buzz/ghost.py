"""Ghost Buzz — paper-only shadow that validates each layer before real capital.

The engine (open/grade/mark/persist/analysis) lives in `shared.ghost`; this is
Buzz's adapter. It opens paper positions on ALL accelerating candidates —
confirmed AND unconfirmed — so the report can measure, from graded outcomes,
whether each layer actually earns its place:

  - confirmation_lift: do price/volume-CONFIRMED names beat unconfirmed ones?
    (is the anti-manipulation gate real, or is raw acceleration enough?)
  - llm_recommended lift: do the LLM's picks beat the reviewed names it passed on?
    (is the "serious thinking" real, or theater?)
  - insider_backed lift: do names with insider buying beat those without?
    (does the authenticity gate help?)
  - accel_terciles: does MORE acceleration predict MORE forward return?

This is the check convergence-Midas never ran — belief validated by data, not
hardcoded multipliers.
"""
from __future__ import annotations

from typing import Iterable, Optional

from shared.ghost import (  # noqa: F401
    GhostEntry, PriceLookup, append_equity_point, boolean_lift, grade_entries,
    graded_only, load_ledger, mark_to_market, numeric_tercile_stats,
    open_entries, overall_stats, save_ledger,
)

HORIZON_DAYS = 5   # weekly hold


def candidates_to_ghost(
    candidates: Iterable,
    price_lookup: PriceLookup,
    *,
    recommended: Optional[Iterable[str]] = None,
    insider_backed: Optional[Iterable[str]] = None,
) -> list[dict]:
    """Convert BuzzCandidate objects into ghost candidate dicts.

    Opens EVERY accelerating candidate (confirmed and not) so the confirmation
    gate itself is testable. Each entry carries:
      - confirmed / new_entrant (bool), accel_ratio / volume_ratio (numeric)
      - llm_recommended (bool) — set only on the reviewed (confirmed) set, so the
        lift compares picks vs passed-over names, not vs names never looked at.
      - insider_backed (bool) — same: set only on the reviewed set.

    recommended / insider_backed are symbol iterables the /buzz skill produces
    during its LLM/authenticity pass. Left None, those flags are simply omitted
    (a run with no LLM pass just can't measure LLM lift yet).
    """
    rec = {s.upper() for s in (recommended or [])}
    ins = {s.upper() for s in (insider_backed or [])}
    reviewed_recs = recommended is not None
    reviewed_ins = insider_backed is not None

    out: list[dict] = []
    for c in candidates:
        sym = (getattr(c, "ticker", "") or "").upper()
        if not sym:
            continue
        px = price_lookup(sym)
        if px is None or float(px) <= 0:
            continue

        features: dict = {
            "confirmed": bool(c.confirmed),
            "new_entrant": bool(c.new_entrant),
            "accel_ratio": float(c.accel_ratio),
        }
        if c.volume_ratio is not None:
            features["volume_ratio"] = float(c.volume_ratio)

        # LLM/insider flags only make sense on the reviewed (confirmed) set —
        # attaching them to unconfirmed names the LLM never saw would pollute lift.
        if reviewed_recs and c.confirmed:
            features["llm_recommended"] = sym in rec
        if reviewed_ins and c.confirmed:
            features["insider_backed"] = sym in ins

        out.append({
            "symbol": sym,
            "price": float(px),
            "horizon_days": HORIZON_DAYS,
            "source": "buzz",
            "features": features,
        })
    return out


def buzz_report(entries: Iterable[GhostEntry]) -> dict:
    """Validation report from graded entries.

    signal_lift is the heart of it: confirmation, LLM recommendation, and
    insider backing each show up as a boolean lift — keep the layers that lift,
    drop the ones that don't.
    """
    graded = graded_only(entries)
    if not graded:
        return {
            "n": 0, "mean_return": None, "hit_rate": None,
            "signal_lift": {},
            "accel_terciles": {},
            "volume_terciles": {},
        }
    return {
        **overall_stats(graded),
        "signal_lift": boolean_lift(graded),
        "accel_terciles": numeric_tercile_stats(graded, "accel_ratio"),
        "volume_terciles": numeric_tercile_stats(graded, "volume_ratio"),
    }
