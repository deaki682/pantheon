"""Momentum signals for the Delphi universe.

Ranks ~118 large-cap stocks by 13-week (65 trading day) price momentum.
Filters to names trading above their 20-day moving average. Provides
context functions for LLM judgment at exit and entry decision points.
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


# ── LLM judgment context builders ────────────────────────────────────


def exit_candidates(
    positions: dict,
    prices: dict[str, float],
    lookback_prices: dict[str, list[float]],
    *,
    ma_period: int = MA_PERIOD,
) -> list[dict]:
    """Identify positions where price < MA with context for LLM exit review.

    The mechanical system would sell all of these. The LLM reviews each
    and decides: exit (confirm the sell), hold (override — keep through
    noise), or reduce (sell half).
    """
    candidates: list[dict] = []
    for sym, pos in positions.items():
        px = prices.get(sym)
        if px is None:
            continue
        hist = lookback_prices.get(sym, [])
        ma = moving_average(hist, ma_period)
        if ma is None or px >= ma:
            continue
        candidates.append({
            "symbol": sym,
            "price": px,
            "ma": round(ma, 2),
            "pct_below_ma": round((px - ma) / ma, 4),
            "entry_price": pos.avg_price,
            "return_since_entry": round((px - pos.avg_price) / pos.avg_price, 4),
            "shares": pos.shares,
            "entry_date": getattr(pos, "entry_date", None),
        })
    return candidates


def enrich_with_signals(
    candidates: list[dict],
    *,
    insider_clusters: dict | None = None,
    smart_money: dict | None = None,
) -> list[dict]:
    """Add cross-signal context from Oracle caches for LLM entry review.

    Annotates each candidate with insider buying and smart money flags
    so the LLM can factor convergence into entry/veto decisions.
    """
    clusters = insider_clusters or {}
    sm = smart_money or {}
    for c in candidates:
        sym = c["symbol"]
        cluster = clusters.get(sym)
        c["insider_buying"] = cluster is not None
        if cluster:
            c["insider_count"] = cluster.get("n_insiders", 0)
            c["insider_dollars"] = cluster.get("total_value", 0)
        holders = sm.get(sym)
        c["smart_money"] = holders is not None
        if holders:
            c["smart_money_holders"] = (
                holders if isinstance(holders, int)
                else len(holders) if isinstance(holders, list) else 0
            )
    return candidates


def breadth(
    universe_prices: dict[str, list[float]],
    *,
    ma_period: int = MA_PERIOD,
) -> dict:
    """Compute market breadth — % of universe above MA.

    Returns context for LLM risk-budget judgment.
    """
    total = 0
    above = 0
    for sym, hist in universe_prices.items():
        if sym not in UNIVERSE or not hist:
            continue
        total += 1
        ma = moving_average(hist, ma_period)
        if ma is not None and hist[-1] >= ma:
            above += 1
    pct = above / total if total > 0 else 0.0
    return {"above_ma": above, "total": total, "pct_above_ma": round(pct, 4)}
