"""Three-stage weekly funnel: universe → candidates → finalists → ONE pick.

Stage 1 (sieve):    ~7,000 SEC filers → ~50-200 with active signals
Stage 2 (rank):     Score by convergence, take top 10
Stage 3 (research): Deep catalyst dossier on each finalist → pick #1

Stages 1-2 are automated. Stage 3 is Claude's job (the /midas skill
orchestrates the deep research on each finalist).
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

from .scoring import (
    MIN_LISTING_DAYS,
    SIGNAL_CHANNELS,
    liquidity_ok,
    rank_candidates,
    score_candidate,
)

log = logging.getLogger(__name__)


@dataclass
class SignalHit:
    """A single signal firing on a symbol."""
    channel: str
    strength: float
    detail: str = ""


@dataclass
class ScanCandidate:
    """A symbol that passed Stage 1 with at least one active signal."""
    symbol: str
    market_cap: Optional[float] = None
    signals: dict[str, float] = field(default_factory=dict)
    signal_details: dict[str, str] = field(default_factory=dict)
    quality_value: float = 0.0
    sector: str = ""


def build_signal_map(
    symbol: str,
    *,
    insider_clusters: Optional[dict] = None,
    smart_money_holders: Optional[dict] = None,
    activist_symbols: Optional[set] = None,
    earnings_surprise: Optional[dict] = None,
    guidance_raised: Optional[set] = None,
) -> dict[str, float]:
    """Build the signal strength map for a single symbol.

    Each source is optional — the scan may not have all signals available
    for every name. Missing signals are 0 (not firing).
    """
    signals: dict[str, float] = {}
    sym = symbol.upper()

    if insider_clusters and sym in insider_clusters:
        cluster = insider_clusters[sym]
        n_insiders = cluster.get("insider_count", 0)
        signals["insider_cluster"] = min(1.0, n_insiders / 4.0)

    if earnings_surprise and sym in earnings_surprise:
        surprise = earnings_surprise[sym]
        if surprise.get("is_beat"):
            from achilles.scoring import surprise_strength
            signals["earnings_beat"] = surprise_strength(
                surprise.get("surprise_pct")
            )

    if smart_money_holders and sym in smart_money_holders:
        holders = smart_money_holders[sym]
        signals["smart_money"] = min(1.0, len(holders) / 3.0)

    if activist_symbols and sym in activist_symbols:
        signals["activist_13d"] = 1.0

    if guidance_raised and sym in guidance_raised:
        signals["guidance_raised"] = 1.0

    return signals


def _listing_too_recent(sym: str, ipo_dates: dict[str, str], today: str) -> bool:
    """True if the symbol listed less than MIN_LISTING_DAYS ago."""
    ipo = ipo_dates.get(sym)
    if not ipo:
        return False
    try:
        ipo_dt = datetime.strptime(ipo, "%Y-%m-%d").date()
        today_dt = datetime.strptime(today, "%Y-%m-%d").date()
        return (today_dt - ipo_dt).days < MIN_LISTING_DAYS
    except (ValueError, TypeError):
        return False


def stage1_sieve(
    universe: dict[str, str],
    *,
    insider_clusters: Optional[dict] = None,
    smart_money_holders: Optional[dict] = None,
    activist_symbols: Optional[set] = None,
    earnings_surprise: Optional[dict] = None,
    guidance_raised: Optional[set] = None,
    quality_scores: Optional[dict] = None,
    market_caps: Optional[dict] = None,
    ipo_dates: Optional[dict[str, str]] = None,
    today: Optional[str] = None,
) -> list[ScanCandidate]:
    """Stage 1: Filter universe to names with at least one active signal.

    universe: {symbol: cik} map (from shared.edgar.fetch_company_tickers)
    Each signal source is optional; pass whatever data you've gathered.
    """
    candidates = []
    market_caps = market_caps or {}
    quality_scores = quality_scores or {}
    ipo_dates = ipo_dates or {}
    today = today or datetime.utcnow().strftime("%Y-%m-%d")

    for sym in universe:
        sym_upper = sym.upper()
        mcap = market_caps.get(sym_upper)

        if mcap is not None and not liquidity_ok(mcap):
            continue

        if _listing_too_recent(sym_upper, ipo_dates, today):
            continue

        signals = build_signal_map(
            sym_upper,
            insider_clusters=insider_clusters,
            smart_money_holders=smart_money_holders,
            activist_symbols=activist_symbols,
            earnings_surprise=earnings_surprise,
            guidance_raised=guidance_raised,
        )

        active = {k: v for k, v in signals.items() if v > 0}
        if not active:
            continue

        candidates.append(ScanCandidate(
            symbol=sym_upper,
            market_cap=mcap,
            signals=signals,
            quality_value=quality_scores.get(sym_upper, 0.0),
        ))

    log.info("stage1_sieve: %d universe → %d with signals", len(universe), len(candidates))
    return candidates


def stage2_rank(candidates: list[ScanCandidate], *, top_n: int = 10) -> list[dict]:
    """Stage 2: Score all candidates by convergence, return top N."""
    scored = []
    for c in candidates:
        result = score_candidate(
            signals=c.signals,
            quality_value=c.quality_value,
            market_cap=c.market_cap,
        )
        result["symbol"] = c.symbol
        result["market_cap"] = c.market_cap
        result["signal_details"] = c.signal_details
        result["sector"] = c.sector
        scored.append(result)

    return rank_candidates(scored, top_n=top_n)


@dataclass
class WeeklyCatalystDossier:
    """Stage 3 output: deep research on a finalist for this week's pick."""
    symbol: str
    catalyst: str
    catalyst_timing: str
    bull_case: str
    bear_case: str
    priced_in_judgment: str
    pop_probability: float
    expected_magnitude: float
    expected_value: float
    current_price: float
    signals: dict = field(default_factory=dict)
    convergence_count: int = 0
    score: float = 0.0
    researched_at: str = ""
    sector: str = ""
    market_cap: Optional[float] = None


def pick_winner(dossiers: list[WeeklyCatalystDossier]) -> Optional[WeeklyCatalystDossier]:
    """Pick the single best candidate by score-weighted expected value.

    Raw EV alone lets noisy single-signal estimates beat higher-confidence
    multi-signal names. Multiplying by the convergence-adjusted score
    re-applies the 1x/2.5x/5x/8x weighting at the pick stage.
    """
    if not dossiers:
        return None
    return max(dossiers, key=lambda d: d.expected_value * d.score)


# ------- persistence -------

def save_scan(path: str, *, finalists: list[dict], pick: Optional[dict] = None) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {
        "finalists": finalists,
        "pick": pick,
    }
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def save_dossiers(path: str, dossiers: list[WeeklyCatalystDossier]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {"dossiers": [asdict(d) for d in dossiers]}
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def load_dossiers(path: str) -> list[WeeklyCatalystDossier]:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return [WeeklyCatalystDossier(**d) for d in data.get("dossiers", [])]
