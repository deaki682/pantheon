"""Crash detection — who just got punished, and was it news or flow?

The load-bearing distinction (documented since the '90s): price moves WITH
news drift; price moves WITHOUT news revert. So a crash is only a fade
candidate when no fundamental event explains it — an earnings bomb is
Achilles' drift world, not Nemesis's reversal world. The news check itself
happens in the runbook (earnings calendar / 8-K lookups via MCP); this module
just measures the tape and carries the tag.

Pure stdlib, prices passed in.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

# A crash = today's move at least this many sigmas below the name's own
# recent daily vol, AND at least MIN_DROP absolute (z alone flags sleepy
# names on trivial moves).
Z_THRESH = -2.0
MIN_DROP = -0.04
VOL_WINDOW = 60          # trailing sessions for daily vol
CASCADE_MIN_PEERS = 3    # crashed same-sector peers to call it a cascade


def daily_returns(closes: list[float]) -> list[float]:
    out = []
    for a, b in zip(closes, closes[1:]):
        if a > 0:
            out.append(b / a - 1.0)
    return out


def crash_zscore(closes: list[float], *, vol_window: int = VOL_WINDOW) -> Optional[float]:
    """Today's return in units of the name's own trailing daily vol."""
    rets = daily_returns(closes)
    if len(rets) < vol_window // 2 + 1:
        return None
    today = rets[-1]
    hist = rets[-(vol_window + 1):-1] or rets[:-1]
    mean = sum(hist) / len(hist)
    var = sum((r - mean) ** 2 for r in hist) / len(hist)
    sd = math.sqrt(var)
    if sd <= 0:
        return None
    return (today - mean) / sd


@dataclass
class Crash:
    symbol: str
    day_return: float
    zscore: float
    price: float
    sector: str = ""
    news_driven: Optional[bool] = None   # None = not yet checked
    sector_cascade: bool = False


def detect_crashes(
    universe_prices: dict[str, list[float]],
    *,
    sectors: Optional[dict[str, str]] = None,
    z_thresh: float = Z_THRESH,
    min_drop: float = MIN_DROP,
    vol_window: int = VOL_WINDOW,
) -> list[Crash]:
    """Find today's crashed names: move <= z_thresh sigmas AND <= min_drop.

    universe_prices: {symbol: [daily closes, oldest first]} — liquid names
    only; reversal in illiquid small-caps is uncapturable after costs.
    sectors: optional {symbol: sector} for cascade tagging.
    """
    sectors = sectors or {}
    crashes: list[Crash] = []
    for sym, closes in universe_prices.items():
        if len(closes) < 2 or closes[-2] <= 0 or closes[-1] <= 0:
            continue
        day = closes[-1] / closes[-2] - 1.0
        if day > min_drop:
            continue
        z = crash_zscore(closes, vol_window=vol_window)
        if z is None or z > z_thresh:
            continue
        crashes.append(Crash(
            symbol=sym.upper(),
            day_return=round(day, 4),
            zscore=round(z, 2),
            price=float(closes[-1]),
            sector=sectors.get(sym, sectors.get(sym.upper(), "")),
        ))

    # cascade tag: several same-sector names crashing together = flow, not news
    by_sector: dict[str, int] = {}
    for c in crashes:
        if c.sector:
            by_sector[c.sector] = by_sector.get(c.sector, 0) + 1
    for c in crashes:
        c.sector_cascade = bool(c.sector) and by_sector.get(c.sector, 0) >= CASCADE_MIN_PEERS

    crashes.sort(key=lambda c: c.zscore)   # most violent first
    return crashes
