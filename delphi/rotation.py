"""Market regime + sector rotation.

Regimes (read from broader market state):
  - risk-on:    SPY 3m > +2% AND breadth > 50%  -> top 3 sectors, full budget
  - risk-off:   SPY 3m < -5% OR  breadth < 30%  -> 100% cash
  - cautious:   SPY 1m < -3%                     -> top 2, half budget,
                                                   positive composite required
  - neutral:    everything else                  -> top 3, 75% budget
"""
from __future__ import annotations

from .signals import momentum, rank_sectors


def breadth(scores: dict[str, float]) -> float:
    """Fraction of sectors with positive composite score."""
    if not scores:
        return 0.0
    return sum(1 for v in scores.values() if v > 0) / len(scores)


def classify_regime(
    spy_1m: float, spy_3m: float, sector_breadth: float
) -> str:
    """Return one of 'risk_on' | 'risk_off' | 'cautious' | 'neutral'."""
    if spy_3m < -0.05 or sector_breadth < 0.30:
        return "risk_off"
    if spy_3m > 0.02 and sector_breadth > 0.50:
        return "risk_on"
    if spy_1m < -0.03:
        return "cautious"
    return "neutral"


def regime_params(regime: str) -> dict:
    """Return rotation parameters for a regime."""
    return {
        "risk_on":  {"risk_budget": 1.00, "top_n": 3, "require_positive": False},
        "neutral":  {"risk_budget": 0.75, "top_n": 3, "require_positive": False},
        "cautious": {"risk_budget": 0.50, "top_n": 2, "require_positive": True},
        "risk_off": {"risk_budget": 0.00, "top_n": 0, "require_positive": False},
    }[regime]


def choose_sectors(
    scores: dict[str, float], regime: str
) -> list[str]:
    """Pick the top-N sectors per the regime, applying the require-positive filter."""
    params = regime_params(regime)
    top_n = params["top_n"]
    require_positive = params["require_positive"]
    ranked = rank_sectors(scores)
    if require_positive:
        ranked = [(s, v) for s, v in ranked if v > 0]
    return [s for s, _ in ranked[:top_n]]


def rotation_plan(
    spy_prices: list[float], sector_scores: dict[str, float]
) -> dict:
    """Top-level: from SPY prices + sector composites, return a plan dict.

    {regime, breadth, risk_budget, sectors: [name, ...]}
    """
    spy_1m = momentum(spy_prices, 21)
    spy_3m = momentum(spy_prices, 63)
    b = breadth(sector_scores)
    regime = classify_regime(spy_1m, spy_3m, b)
    params = regime_params(regime)
    return {
        "regime": regime,
        "breadth": b,
        "spy_1m": spy_1m,
        "spy_3m": spy_3m,
        "risk_budget": params["risk_budget"],
        "sectors": choose_sectors(sector_scores, regime),
    }
