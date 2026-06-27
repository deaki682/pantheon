"""Sector momentum signals.

Tracks the 11 SPDR sector ETFs at three timeframes (21/63/126 trading days)
and produces a composite score per sector plus relative strength vs SPY.
"""
from __future__ import annotations


# SPDR sector ETFs mapped to a canonical sector name.
SECTOR_MAP = {
    "XLK": "technology",
    "XLF": "financials",
    "XLE": "energy",
    "XLV": "healthcare",
    "XLI": "industrials",
    "XLP": "staples",
    "XLY": "discretionary",
    "XLU": "utilities",
    "XLRE": "real_estate",
    "XLB": "materials",
    "XLC": "communication",
}

TIMEFRAMES = (21, 63, 126)
TIMEFRAME_WEIGHTS = (0.2, 0.4, 0.4)


def momentum(prices: list[float], lookback: int) -> float:
    """Simple return over `lookback` periods. prices[-1] is most recent."""
    if not prices or lookback <= 0 or len(prices) < lookback + 1:
        return 0.0
    base = prices[-(lookback + 1)]
    if base <= 0:
        return 0.0
    return prices[-1] / base - 1.0


def composite_score(prices: list[float], spy_prices: list[float]) -> float:
    """Composite of 3 timeframes (weighted 0.2/0.4/0.4) + relative strength vs SPY.

    Returns a single float. The relative-strength term uses the 63-day window.
    """
    weighted = sum(
        w * momentum(prices, tf) for w, tf in zip(TIMEFRAME_WEIGHTS, TIMEFRAMES)
    )
    rs_sec = momentum(prices, 63)
    rs_spy = momentum(spy_prices, 63)
    relative = rs_sec - rs_spy
    return weighted + 0.25 * relative


def score_sectors(
    sector_prices: dict[str, list[float]],
    spy_prices: list[float],
) -> dict[str, float]:
    """Return {sector_name: composite_score} for each provided ETF.

    `sector_prices` keys are ETF tickers (XLK, XLF, ...). Output keys are the
    canonical sector names from SECTOR_MAP.
    """
    out: dict[str, float] = {}
    for etf, prices in sector_prices.items():
        sec_name = SECTOR_MAP.get(etf.upper())
        if not sec_name:
            continue
        out[sec_name] = composite_score(prices, spy_prices)
    return out


def rank_sectors(scores: dict[str, float]) -> list[tuple[str, float]]:
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
