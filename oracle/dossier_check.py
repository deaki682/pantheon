"""Dossier validation.

A dossier MUST have:
  - exactly 3 scenarios labeled 'bull', 'base', 'bear' with target + probability
  - probabilities sum ~ 1.0 (auto-normalized)
  - bull target >= bear target
  - 4 ratings (moat, runway, quality, management) on [0, 1] (auto-scaled from [0, 10])
  - at least one citation (SEC filing accession or URL)
"""
from __future__ import annotations

from typing import Any


REQUIRED_SCENARIOS = ("bull", "base", "bear")
REQUIRED_RATINGS = ("moat", "runway", "quality", "management")

# A candidate down this far from its 52-week high is a potential falling knife.
# Its dossier MUST explain what drove the decline (and the bear case) — a
# confident thesis on a name down 40%+ that doesn't say *why* it fell is exactly
# how a FISV-style knife rides an insider signal into the book.
DRAWDOWN_FLAG_THRESHOLD = 0.30
MIN_DECLINE_EXPLANATION_CHARS = 80


def drawdown_from_high(current_price: float, high_52w: float) -> float:
    """Fraction below the 52-week high (0.0 if data missing/invalid)."""
    if not high_52w or high_52w <= 0 or not current_price or current_price <= 0:
        return 0.0
    return max(0.0, 1.0 - current_price / high_52w)


class DossierError(ValueError):
    """Raised when a dossier fails structural validation."""


def normalize_rating(v: float) -> float:
    """Normalize a rating: if v is in (1, 10], divide by 10."""
    if v is None:
        return 0.0
    f = float(v)
    if f < 0:
        return 0.0
    if f > 1.0 and f <= 10.0:
        return f / 10.0
    if f > 10.0:
        return 1.0
    return f


def validate_dossier(d: dict[str, Any]) -> dict[str, Any]:
    """Validate and auto-normalize a dossier in place. Returns the dossier.

    Mutates: clips ratings to [0,1], scales 0-10 ratings, auto-normalizes
    scenario probabilities to sum to 1.0.
    """
    if "symbol" not in d or not str(d["symbol"]).strip():
        raise DossierError("dossier missing symbol")

    citations = d.get("citations") or []
    if not citations:
        raise DossierError(f"{d['symbol']}: no citations — every dossier must cite filings")

    ratings = d.get("ratings") or {}
    for key in REQUIRED_RATINGS:
        if key not in ratings:
            raise DossierError(f"{d['symbol']}: missing rating {key!r}")
        ratings[key] = normalize_rating(ratings[key])
    d["ratings"] = ratings

    scenarios = d.get("scenarios") or {}
    missing = [s for s in REQUIRED_SCENARIOS if s not in scenarios]
    if missing:
        raise DossierError(f"{d['symbol']}: missing scenarios {missing}")
    extra = [s for s in scenarios if s not in REQUIRED_SCENARIOS]
    if extra:
        raise DossierError(f"{d['symbol']}: unexpected scenarios {extra}")

    total_p = 0.0
    for key in REQUIRED_SCENARIOS:
        s = scenarios[key]
        if "target" not in s or "probability" not in s:
            raise DossierError(f"{d['symbol']}: scenario {key} needs target+probability")
        s["target"] = float(s["target"])
        s["probability"] = float(s["probability"])
        if s["target"] < 0:
            raise DossierError(f"{d['symbol']}: scenario {key} target < 0")
        if s["probability"] < 0:
            raise DossierError(f"{d['symbol']}: scenario {key} probability < 0")
        total_p += s["probability"]

    if total_p <= 0:
        raise DossierError(f"{d['symbol']}: scenario probabilities sum to zero")
    if abs(total_p - 1.0) > 1e-9:
        # auto-normalize
        for key in REQUIRED_SCENARIOS:
            scenarios[key]["probability"] = scenarios[key]["probability"] / total_p

    if scenarios["bull"]["target"] < scenarios["bear"]["target"]:
        raise DossierError(
            f"{d['symbol']}: bull target ({scenarios['bull']['target']}) "
            f"< bear target ({scenarios['bear']['target']})"
        )

    # Falling-knife gate: if 52-week-high data is present and the name is down
    # past the threshold, the dossier must explain the decline. We record the
    # drawdown either way so it's visible in review.
    high_52w = d.get("high_52w")
    drawdown = drawdown_from_high(d.get("current_price"), high_52w)
    d["drawdown_from_high"] = drawdown
    if high_52w and drawdown >= DRAWDOWN_FLAG_THRESHOLD:
        explanation = (d.get("decline_explanation") or "").strip()
        if len(explanation) < MIN_DECLINE_EXPLANATION_CHARS:
            raise DossierError(
                f"{d['symbol']}: down {drawdown:.0%} from its 52-week high — a "
                f"falling-knife candidate. Provide a `decline_explanation` covering "
                f"what drove the drop and the bear case before this dossier is valid."
            )

    return d
