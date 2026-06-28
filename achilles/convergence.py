"""Signal convergence — stacks Oracle data into conviction for sizing.

The core insight from backtesting: PEAD alpha comes from neglect.
High-quality well-covered names price earnings beats within hours.
Low-quality neglected names take weeks. The drift IS the neglect.

This module does two things:
  1. neglect_premium() — inverts Oracle quality into a scoring factor.
     Replaces company_quality in the multiplicative score.
  2. conviction_multiplier() — stacks PEAD-predictive signals into a
     position-sizing multiplier. More convergence → bigger bet.

Scoring gates entry. Convergence scales size. Separate concerns.

Evidence (Achilles backtest, 2025-07 to 2026-06):
  - Oracle quality ~0.30 → +$45 PnL, 55% hit rate
  - Oracle quality ~0.74 → -$30 PnL, 42% hit rate
  - Insider pre-activity + earnings beat → 2-3x drift (Cohen et al. 2012)

Only signals that predict PEAD returns are used for conviction:
  - Surprise magnitude (larger gap = more drift)
  - Neglect / low coverage (slower price discovery = longer drift)
  - Insider pre-activity (informed buying validates the beat)
  - Concurrent guidance (double catalyst)

Fundamental quality signals (revenue growth, FCF, margins) were tested
and found to be ANTI-correlated with PEAD returns. They proxy for analyst
coverage: well-covered names price beats instantly. Removed from conviction.
"""
from __future__ import annotations

from typing import Optional


# ── neglect premium ──────────────────────────────────────────────────

def neglect_premium(oracle_quality: Optional[float] = None) -> float:
    """Invert Oracle quality into a PEAD neglect factor.

    Returns [0.3, 1.0] where 1.0 = maximum neglect = strongest drift.

    quality=0.0 → neglect=1.0  (junk nobody watches — maximum PEAD)
    quality=0.5 → neglect=0.65 (moderate coverage)
    quality=1.0 → neglect=0.3  (well-followed — drift absorbed fast)
    quality=None → neglect=0.85 (no data = likely neglected)
    """
    if oracle_quality is None:
        return 0.85
    q = max(0.0, min(1.0, float(oracle_quality)))
    return max(0.3, 1.0 - 0.7 * q)


# ── convergence signals ─────────────────────────────────────────────

def _surprise_signal(surprise_pct: Optional[float]) -> float:
    """Large earnings surprise adds sizing conviction.

    Bigger surprise = more drift. Directly measures the information
    gap between market expectations and reality.
    """
    if surprise_pct is None:
        return 0.0
    mag = abs(surprise_pct)
    if mag > 30:
        return 0.5
    if mag > 15:
        return 0.35
    if mag > 8:
        return 0.15
    return 0.0


def _dilution_penalty(dilution_yoy: Optional[float]) -> float:
    """Heavy dilution is a red flag — reduce conviction."""
    if dilution_yoy is None:
        return 0.0
    if dilution_yoy > 0.10:
        return -0.3
    return 0.0


def conviction_multiplier(
    *,
    surprise_pct: Optional[float] = None,
    insider_preactivity: bool = False,
    concurrent_guidance: bool = False,
    oracle_quality: Optional[float] = None,
    dilution_yoy: Optional[float] = None,
    **_kwargs,
) -> float:
    """Stack PEAD-predictive signals into a position sizing multiplier.

    Base = 1.0x. Returns [~0.7, ~3.0] depending on signal convergence.
    Only uses signals empirically validated to predict PEAD drift:
      - Surprise magnitude (information gap)
      - Neglect (slow price discovery)
      - Insider pre-activity (informed validation)
      - Concurrent guidance (double catalyst)
      - Heavy dilution (penalty)
    """
    mult = 1.0
    mult += _surprise_signal(surprise_pct)
    mult += _dilution_penalty(dilution_yoy)

    if insider_preactivity:
        mult += 0.5

    if concurrent_guidance:
        mult += 0.3

    # Neglect: the dominant signal. Less-covered names get bigger
    # positions because information processing takes longer.
    mult += neglect_premium(oracle_quality) * 0.5

    return max(0.5, mult)


# ── prescreener data extraction ──────────────────────────────────────

def extract_convergence_signals(
    symbol: str,
    *,
    prescreener_rows: Optional[dict] = None,
    event_metadata: Optional[dict] = None,
    oracle_quality: Optional[float] = None,
) -> dict:
    """Extract all convergence signals for a symbol from Oracle data.

    Returns a dict suitable for passing to conviction_multiplier(**signals).
    """
    signals: dict = {}
    event_metadata = event_metadata or {}

    if prescreener_rows and symbol.upper() in prescreener_rows:
        snap = prescreener_rows[symbol.upper()]
        signals["dilution_yoy"] = snap.get("dilution_yoy")

    signals["surprise_pct"] = event_metadata.get("surprise_pct")
    signals["insider_preactivity"] = bool(event_metadata.get("insider_boost"))
    signals["concurrent_guidance"] = bool(event_metadata.get("concurrent_guidance"))
    signals["oracle_quality"] = oracle_quality

    return signals


def build_prescreener_lookup(rows: list[dict]) -> dict[str, dict]:
    """Build {SYMBOL: snapshot_dict} from prescreener rows list."""
    out: dict[str, dict] = {}
    for r in rows:
        snap = r.get("snapshot")
        if not isinstance(snap, dict):
            continue
        sym = (snap.get("symbol") or "").upper()
        if sym:
            out[sym] = snap
    return out
