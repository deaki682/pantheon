"""Entry-window state machine — "are the forced sellers done?" in code.

When a spinco starts trading, index funds that received shares through the
parent must sell them regardless of price (wrong index, wrong size bucket).
That mandate-driven supply is the whole reason the entry exists — and it is
finite. Nemesis never buys at distribution; it waits for two mechanical
tells that the forced flow has cleared:

  1. Volume normalization — day-one volume is dominated by the dump, so we
     compare the last five sessions against the first five. When recent
     volume falls to half or less of the opening burst, the mandate-driven
     supply has been absorbed.
  2. Price stabilization — the series low is behind us (older than the last
     five sessions) and the last close sits above it. Forced sellers make
     new lows; when the lows stop, they are done.

Both must hold, inside a bounded day-count window, before the god may act.
The window is deliberately dumb: it reads bars, not filings. The judgment
call (incentives, dumped liabilities, forced-seller size) belongs to the
LLM dossier, which reads documents and never predicts prices. This module
only answers "is now mechanically the time?".

FROZEN constants: the thresholds below are pre-registered in spirit. The
ghost's buy-all control enters every spinco at its window trigger, so the
trigger definition IS the experiment. Changing any of these mid-stream
invalidates every comparison against trades already graded — treat them as
part of the strategy's identity, not tuning knobs.

Pure stdlib, self-contained (no cross-god imports).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ---- FROZEN — changing these invalidates all prior ghost comparisons ----
MIN_TRADING_DAYS = 10      # earliest possible entry; before this the dump can't be judged
MAX_TRADING_DAYS = 90      # after ~one quarter the forced-seller thesis is stale
VOL_NORM_RATIO = 0.5       # last-5-day avg volume <= 50% of first-5-day avg
STAB_SESSIONS = 5          # the series low must be older than the last 5 sessions

STATES = ("pre_window", "in_window", "late")


def _close(bar: dict) -> Optional[float]:
    """Broker payloads disagree on the key and the type; tolerate both."""
    for k in ("close_price", "close"):
        v = bar.get(k)
        if v not in (None, ""):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
    return None


def _volume(bar: dict) -> float:
    try:
        return float(bar.get("volume", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


@dataclass
class WindowState:
    """One snapshot of the mechanical entry gate for a spinco.

    state is one of STATES:
      pre_window — too early, or the forced sellers are still visibly active
      in_window  — both tells fired inside the day-count bounds: Nemesis may buy
      late       — past MAX_TRADING_DAYS; the anomaly has decayed, do not chase
    """
    trading_days: int
    vol_ratio: Optional[float]
    volume_normalized: bool
    price_stabilized: bool
    state: str


def assess_window(bars: list[dict]) -> WindowState:
    """Classify where a spinco sits in its entry window.

    bars = daily bars for the spinco, oldest first, STARTING AT ITS FIRST
    TRADING DAY — the caller slices; day-one volume must be in the series
    or the normalization ratio is meaningless. Bars whose close cannot be
    parsed as a positive number are skipped entirely (a half-formed bar
    must not corrupt either the day count or the low).
    """
    valid = [(c, _volume(b)) for c, b in ((_close(b), b) for b in bars)
             if c is not None and c > 0]
    closes = [c for c, _ in valid]
    vols = [v for _, v in valid]
    trading_days = len(valid)

    # Volume normalization: last-5 average vs first-5 average. The first
    # five sessions carry the dump, so they are the denominator. With
    # fewer than 10 valid bars the two windows would overlap and the
    # ratio would flatter itself — refuse to compute it.
    vol_ratio: Optional[float] = None
    if trading_days >= 2 * STAB_SESSIONS:
        first_avg = sum(vols[:STAB_SESSIONS]) / STAB_SESSIONS
        last_avg = sum(vols[-STAB_SESSIONS:]) / STAB_SESSIONS
        if first_avg > 0:
            vol_ratio = round(last_avg / first_avg, 4)
    volume_normalized = vol_ratio is not None and vol_ratio <= VOL_NORM_RATIO

    # Price stabilization: the overall low must be strictly older than the
    # last STAB_SESSIONS sessions. A tied low inside the recent window is
    # a NEW low for this purpose — forced sellers still pressing. The
    # min-of-recent > min-of-all comparison encodes both that and the
    # "last close above the low" requirement (the last close is one of
    # the recent sessions).
    price_stabilized = False
    if trading_days >= MIN_TRADING_DAYS:
        overall_min = min(closes)
        recent_min = min(closes[-STAB_SESSIONS:])
        price_stabilized = recent_min > overall_min and closes[-1] > overall_min

    if trading_days > MAX_TRADING_DAYS:
        state = "late"
    elif (MIN_TRADING_DAYS <= trading_days <= MAX_TRADING_DAYS
            and volume_normalized and price_stabilized):
        state = "in_window"
    else:
        state = "pre_window"

    return WindowState(
        trading_days=trading_days,
        vol_ratio=vol_ratio,
        volume_normalized=volume_normalized,
        price_stabilized=price_stabilized,
        state=state,
    )
