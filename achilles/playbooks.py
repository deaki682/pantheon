"""Playbooks — the 6 event classes with parameters seeded from literature.

A playbook is the per-class drift estimate and exit parameters. Each starts
"uncalibrated" — sizes are halved in conservative_mode until enough live
data lets us recalibrate.

Literature attributions:
  - earnings_reaction: Bernard & Thomas (1989) PEAD
  - insider_cluster:   Cohen, Malloy & Pomorski (2012)
  - activist_13d:      Brav, Jiang, Partnoy & Thomas (2008)
  - ma_target:         Andrade & Stafford (2004)
  - spinoff_window:    McConnell, Ozbilgin & Wahal (2001)
  - guidance_revision: Tang (2014)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Playbook:
    event_class: str
    base_rate: float          # estimated drift / hit rate
    hold_days: int
    hard_stop_pct: float      # negative number, e.g. -0.08 for -8%
    profit_target_pct: float  # positive
    time_stop_days: int
    citation: str
    uncalibrated: bool = True
    disqualifiers: list[str] = field(default_factory=list)
    # Live tracking
    live_n: int = 0
    live_hits: int = 0
    expected_hit_rate: float = 0.0  # backtested baseline
    disabled: bool = False
    trail_armed_at: float = 0.0   # arm trailing stop when gain >= this (0 = off)
    trail_pct: float = 0.0        # trail distance from high-water (0 = off)


# Per-class disqualifier vocab. These tokens, if present in the filing or
# surrounding context, zero the score.
UNIVERSAL_DISQUALIFIERS = (
    "trading_halt",
    "delisting_notice",
    "bankruptcy_filing",
    "going_concern",
)

CLASS_DISQUALIFIERS = {
    "earnings_reaction": (
        "guidance_withdrawn",
        "going_concern",
    ),
    "insider_cluster": (
        "concurrent_dilution",
        "executive_departure",
    ),
    "activist_13d": (
        "13d_amendment_reduces_below_5pct",
    ),
    "ma_target": (
        "deal_termination_pending",
    ),
    "spinoff_window": (
        "spinoff_postponed",
    ),
    "guidance_revision": (
        "reaffirmation_only",
    ),
}


def build_playbooks() -> dict[str, Playbook]:
    """Construct the default uncalibrated playbooks."""
    pbs = {
        "earnings_reaction": Playbook(
            event_class="earnings_reaction",
            base_rate=0.55, hold_days=30, hard_stop_pct=-0.15,
            profit_target_pct=0.20, time_stop_days=45,
            citation="Bernard & Thomas (1989)",
            uncalibrated=False,
            expected_hit_rate=0.55,
            trail_armed_at=0.0, trail_pct=0.0,
        ),
        "insider_cluster": Playbook(
            event_class="insider_cluster",
            base_rate=0.58, hold_days=20, hard_stop_pct=-0.10,
            profit_target_pct=0.15, time_stop_days=30,
            citation="Cohen, Malloy & Pomorski (2012)",
            expected_hit_rate=0.58,
            disabled=True,
        ),
        "activist_13d": Playbook(
            event_class="activist_13d",
            base_rate=0.60, hold_days=5, hard_stop_pct=-0.07,
            profit_target_pct=0.10, time_stop_days=10,
            citation="Brav, Jiang, Partnoy & Thomas (2008)",
            expected_hit_rate=0.60,
            disabled=True,
        ),
        "ma_target": Playbook(
            event_class="ma_target",
            base_rate=0.65, hold_days=10, hard_stop_pct=-0.05,
            profit_target_pct=0.06, time_stop_days=15,
            citation="Andrade & Stafford (2004)",
            expected_hit_rate=0.65,
            disabled=True,
        ),
        "spinoff_window": Playbook(
            event_class="spinoff_window",
            base_rate=0.55, hold_days=15, hard_stop_pct=-0.08,
            profit_target_pct=0.12, time_stop_days=25,
            citation="McConnell, Ozbilgin & Wahal (2001)",
            expected_hit_rate=0.55,
            disabled=True,
        ),
        "guidance_revision": Playbook(
            event_class="guidance_revision",
            base_rate=0.55, hold_days=5, hard_stop_pct=-0.08,
            profit_target_pct=0.10, time_stop_days=10,
            citation="Tang (2014)",
            expected_hit_rate=0.55,
            disabled=True,
        ),
    }
    for cls, pb in pbs.items():
        pb.disqualifiers = list(CLASS_DISQUALIFIERS.get(cls, ()))
    return pbs


# ------- Attribution log: hit-rate tracking + auto-disable -------

AUTO_DISABLE_DELTA = 0.10  # 10 percentage points below expected -> disable


def record_outcome(pb: Playbook, *, hit: bool) -> None:
    pb.live_n += 1
    if hit:
        pb.live_hits += 1


def maybe_autodisable(pb: Playbook, *, min_n: int = 20) -> bool:
    if pb.live_n < min_n:
        return False
    live_rate = pb.live_hits / pb.live_n
    if pb.expected_hit_rate - live_rate >= AUTO_DISABLE_DELTA:
        pb.disabled = True
        return True
    return False


# ------- Calibration -------

def recalibrate(
    pb: Playbook,
    *,
    new_base_rate: float,
    new_hold_days: Optional[int] = None,
    new_hard_stop_pct: Optional[float] = None,
    new_profit_target_pct: Optional[float] = None,
) -> None:
    """Update playbook from validated backtester recommendations."""
    pb.base_rate = float(new_base_rate)
    pb.expected_hit_rate = float(new_base_rate)
    if new_hold_days is not None:
        pb.hold_days = int(new_hold_days)
    if new_hard_stop_pct is not None:
        pb.hard_stop_pct = float(new_hard_stop_pct)
    if new_profit_target_pct is not None:
        pb.profit_target_pct = float(new_profit_target_pct)
    pb.uncalibrated = False
