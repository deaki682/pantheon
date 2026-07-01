"""Price/volume confirmation — direction + anti-manipulation, in one gate.

Buzz alone predicts volatility, not direction, and the stream is adversarial
(pumps manufacture talk). Real accelerating interest shows up as real
price AND volume, not just posts. So:

  - talk up + price up + volume elevated  = organic money moving -> tradeable long
  - talk up + price/volume flat           = manufactured chatter -> skip

That single check gives us a direction (up) and filters the astroturf that a
Reddit-sourced signal is most exposed to.

Pure stdlib, self-contained (no cross-god imports — buzz stays disconnected).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

RECENT_DAYS = 3            # the window over which talk is igniting
VOL_BASELINE_DAYS = 20     # trailing baseline for 'elevated volume'
MIN_VOLUME_RATIO = 1.5     # recent vs baseline to count as real participation
MIN_PRICE_CHANGE = 0.0     # price must be rising (direction anchor)


def _close(bar: dict) -> Optional[float]:
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
class Confirmation:
    confirmed: bool
    price_change_pct: Optional[float]
    volume_ratio: Optional[float]
    reason: str


def confirm(bars: list[dict], *, recent_days: int = RECENT_DAYS,
            baseline_days: int = VOL_BASELINE_DAYS,
            min_volume_ratio: float = MIN_VOLUME_RATIO,
            min_price_change: float = MIN_PRICE_CHANGE) -> Confirmation:
    """Does real price/volume back the buzz? bars = daily OHLCV, oldest first."""
    closes = [c for c in (_close(b) for b in bars) if c is not None and c > 0]
    vols = [_volume(b) for b in bars]
    if len(closes) < recent_days + 2:
        return Confirmation(False, None, None, "insufficient_history")

    price_change = (closes[-1] - closes[-1 - recent_days]) / closes[-1 - recent_days]

    recent_vol = vols[-recent_days:]
    base_slice = vols[-(baseline_days + recent_days):-recent_days] or vols[:-recent_days]
    avg_base = sum(base_slice) / len(base_slice) if base_slice else 0.0
    avg_recent = sum(recent_vol) / len(recent_vol) if recent_vol else 0.0
    vol_ratio = (avg_recent / avg_base) if avg_base > 0 else None

    price_ok = price_change > min_price_change
    vol_ok = vol_ratio is not None and vol_ratio >= min_volume_ratio

    if price_ok and vol_ok:
        reason = "confirmed"
    elif not price_ok and not vol_ok:
        reason = "no_price_no_volume"   # pure chatter, likely astroturf
    elif not price_ok:
        reason = "volume_without_price"  # moving but not up -> no long direction
    else:
        reason = "price_without_volume"  # thin move, unconfirmed participation

    return Confirmation(
        confirmed=bool(price_ok and vol_ok),
        price_change_pct=round(price_change, 4),
        volume_ratio=round(vol_ratio, 2) if vol_ratio is not None else None,
        reason=reason,
    )
