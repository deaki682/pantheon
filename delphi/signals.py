"""Momentum signals for the Delphi universe.

Ranks ~118 large-cap stocks by 13-week (65 trading day) price momentum.
Filters to names trading above their 20-day moving average.
"""
from __future__ import annotations

from .sleeve import MA_PERIOD, MOMENTUM_LOOKBACK


UNIVERSE = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO",
    "AMD", "CRM", "ADBE", "ORCL", "CSCO", "IBM", "ACN", "INTU", "NOW",
    # Financials
    "JPM", "V", "MA", "BAC", "WFC", "GS", "BLK", "SCHW", "AXP", "C",
    "MS", "PGR", "CME", "ICE",
    # Healthcare
    "UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT", "BMY",
    "AMGN", "MDT", "ISRG", "GILD", "CVS", "CI", "ELV",
    # Energy
    "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "OXY", "HAL",
    # Industrials + Defense
    "CAT", "DE", "HON", "UNP", "RTX", "GE", "LMT", "BA", "MMM", "EMR",
    "WM", "ITW", "GD", "NOC", "ETN",
    # Consumer Staples
    "PG", "KO", "PEP", "COST", "WMT", "MCD", "CL", "MO", "PM", "MDLZ", "KHC",
    # Consumer Discretionary
    "NKE", "SBUX", "TGT", "HD", "LOW", "TJX", "F", "GM",
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL", "WEC", "ED",
    # Semis
    "INTC", "MU", "MRVL", "TXN", "QCOM", "AMAT", "LRCX", "KLAC", "SNPS",
    # Media / Telecom
    "DIS", "CMCSA", "VZ", "T", "NFLX",
    # Fintech / Platform
    "PYPL", "SQ", "ABNB", "UBER",
]


def momentum(prices: list[float], lookback: int) -> float:
    """Simple return over `lookback` periods. prices[-1] is most recent."""
    if not prices or lookback <= 0 or len(prices) < lookback + 1:
        return 0.0
    base = prices[-(lookback + 1)]
    if base <= 0:
        return 0.0
    return prices[-1] / base - 1.0


def moving_average(prices: list[float], period: int) -> float | None:
    """Simple moving average of the last `period` closes."""
    if not prices or len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def rank_by_momentum(
    universe_prices: dict[str, list[float]],
    *,
    lookback: int = MOMENTUM_LOOKBACK,
    ma_period: int = MA_PERIOD,
) -> list[dict]:
    """Rank stocks by momentum, filtered to those above their MA.

    Returns list of dicts sorted by momentum descending:
      [{"symbol": str, "momentum": float, "price": float, "ma": float}, ...]
    """
    ranked: list[dict] = []
    for sym, prices in universe_prices.items():
        if not prices:
            continue
        mom = momentum(prices, lookback)
        ma = moving_average(prices, ma_period)
        price = prices[-1]
        if ma is not None and price >= ma:
            ranked.append({
                "symbol": sym,
                "momentum": mom,
                "price": price,
                "ma": ma,
            })
    ranked.sort(key=lambda x: x["momentum"], reverse=True)
    return ranked
