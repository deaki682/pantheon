"""Dossier validation.

A dossier MUST have:
  - exactly 3 scenarios labeled 'bull', 'base', 'bear' with target + probability
  - probabilities sum ~ 1.0 (auto-normalized)
  - bull target >= bear target
  - 4 ratings (moat, runway, quality, management) on [0, 1] (auto-scaled from [0, 10])
  - at least one citation (SEC filing accession or URL)
  - broker-verified current_price and high_52w (when current_price > 0)
"""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

REQUIRED_SCENARIOS = ("bull", "base", "bear")
REQUIRED_RATINGS = ("moat", "runway", "quality", "management")

# A candidate down this far from its 52-week high is a potential falling knife.
# Its dossier MUST explain what drove the decline (and the bear case) — a
# confident thesis on a name down 40%+ that doesn't say *why* it fell is exactly
# how a FISV-style knife rides an insider signal into the book.
DRAWDOWN_FLAG_THRESHOLD = 0.30
MIN_DECLINE_EXPLANATION_CHARS = 80

GOING_CONCERN_RUNWAY_THRESHOLD = 0.3
GOING_CONCERN_LOSS_THRESHOLD = 0.80  # bear target < 20% of current price
MIN_GOING_CONCERN_EXPLANATION_CHARS = 80

# Broker cross-check: if the LLM-supplied price or 52w high diverges from
# the broker value by more than this fraction, reject the dossier.
PRICE_DIVERGENCE_TOLERANCE = 0.05

# Prose floor: thesis/business must be an articulated read, not a stub.
# Added 2026-07-04 (LLM integration audit, finding #4) — previously neither
# field was checked at all, so make_dossier(thesis="", business="") passed
# validation and could enter the annual cohort selection ranked on scenario
# math alone. Mirrors nemesis/dossier.py's _PROSE_FIELDS/_MIN_PROSE gate.
# 40 is comfortably below every real dossier on file (thesis >= 579 chars,
# business >= 188 chars) — this catches stubs, not terse-but-real prose.
PROSE_FIELDS = ("thesis", "business")
MIN_PROSE_CHARS = 40


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

    for name in PROSE_FIELDS:
        val = str(d.get(name) or "")
        if len(val) < MIN_PROSE_CHARS:
            raise DossierError(
                f"{d['symbol']}: {name} must be at least {MIN_PROSE_CHARS} chars "
                f"(got {len(val)}) — an unarticulated read is not research"
            )

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

    # Broker market-data verification: when broker values are present,
    # cross-check against the LLM-supplied values and use the broker as
    # authoritative. A >5% divergence means the LLM hallucinated the number.
    current_price = d.get("current_price") or 0
    broker_price = d.get("broker_price")
    broker_high = d.get("broker_high_52w")
    if current_price > 0:
        if broker_price is not None and broker_price > 0:
            divergence = abs(current_price - broker_price) / broker_price
            if divergence > PRICE_DIVERGENCE_TOLERANCE:
                raise DossierError(
                    f"{d['symbol']}: current_price ${current_price:.2f} diverges "
                    f"{divergence:.0%} from broker price ${broker_price:.2f} "
                    f"(tolerance {PRICE_DIVERGENCE_TOLERANCE:.0%}). "
                    f"Use the broker-sourced price."
                )
        elif broker_price is None:
            log.warning(
                "%s: no broker_price supplied — current_price $%.2f is unverified",
                d.get("symbol"), current_price,
            )
            d["price_verified"] = False

        if broker_high is not None and broker_high > 0:
            high_52w_claimed = d.get("high_52w") or 0
            if high_52w_claimed > 0:
                divergence = abs(high_52w_claimed - broker_high) / broker_high
                if divergence > PRICE_DIVERGENCE_TOLERANCE:
                    raise DossierError(
                        f"{d['symbol']}: high_52w ${high_52w_claimed:.2f} diverges "
                        f"{divergence:.0%} from broker 52-week high ${broker_high:.2f} "
                        f"(tolerance {PRICE_DIVERGENCE_TOLERANCE:.0%}). "
                        f"Use the broker-sourced value."
                    )
            d["high_52w"] = broker_high
        elif broker_high is None and (d.get("high_52w") or 0) > 0:
            log.warning(
                "%s: no broker_high_52w supplied — high_52w $%.2f is unverified",
                d.get("symbol"), d.get("high_52w", 0),
            )

    if broker_price is not None and broker_high is not None:
        d["price_verified"] = True

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

    # Going-concern gate: a low-runway name whose bear case implies near-total
    # loss must explain why equity survives. A $1.50 bear target on a $15 stock
    # with 0.3 runway is exactly the scenario where covenants, debt maturities,
    # or cash burn can take equity to zero — the model must prove the floor.
    current_price = d.get("current_price") or 0
    bear_target = scenarios["bear"]["target"]
    runway = ratings.get("runway", 1.0)
    d["going_concern_flag"] = False
    if current_price > 0 and runway < GOING_CONCERN_RUNWAY_THRESHOLD:
        implied_loss = 1.0 - bear_target / current_price
        if implied_loss >= GOING_CONCERN_LOSS_THRESHOLD:
            d["going_concern_flag"] = True
            gc_explanation = (d.get("going_concern_explanation") or "").strip()
            if len(gc_explanation) < MIN_GOING_CONCERN_EXPLANATION_CHARS:
                raise DossierError(
                    f"{d['symbol']}: runway rating {runway:.1f} with bear case "
                    f"implying {implied_loss:.0%} loss (${bear_target:.2f} vs "
                    f"${current_price:.2f}). Provide a `going_concern_explanation` "
                    f"covering debt covenants, cash runway, and why equity survives "
                    f"before this dossier is valid."
                )

    return d
