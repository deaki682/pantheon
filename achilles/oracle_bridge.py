"""Oracle bridge — read Oracle's research for Achilles scoring.

Oracle does the slow work: screens, dossiers, insider monitoring.
Achilles does the fast work: detects catalysts and enters.

This module reads Oracle's caches to replace Achilles's hardcoded
quality defaults with real research:
  - Dossier conviction → company_quality factor in scoring
  - Prescreener quality → fallback when no dossier exists
  - Insider cluster cache → pre-earnings insider cross-reference
  - Screen scores → multi-lens composite for watchlist ranking
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

log = logging.getLogger("achilles.oracle_bridge")

# Cache paths (must match monitor.py constants)
DOSSIER_PATH = "cache/oracle_dossiers.json"
PRESCREENER_PATH = "cache/oracle_prescreener.json"
INSIDER_CLUSTER_PATH = "cache/oracle_insider_clusters.json"
SCREEN_PATH = "cache/oracle_screen.json"


def _load_json(path: str, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


# ── dossier conviction ────────────────────────────────────────────────

def load_dossier_convictions(path: str = DOSSIER_PATH) -> dict[str, float]:
    """Read Oracle dossiers and extract conviction scores.

    Returns {SYMBOL: conviction} where conviction is [0, 1].
    """
    data = _load_json(path, [])
    out: dict[str, float] = {}

    # Handle both list and dict formats
    dossiers = data if isinstance(data, list) else data.get("dossiers", [])
    if isinstance(dossiers, dict):
        dossiers = list(dossiers.values())

    for d in dossiers:
        if not isinstance(d, dict):
            continue
        sym = (d.get("symbol") or "").upper()
        conviction = d.get("conviction")
        if sym and conviction is not None:
            try:
                out[sym] = float(conviction)
            except (TypeError, ValueError):
                pass
    if out:
        log.info("Oracle dossiers: %d conviction scores loaded", len(out))
    return out


# ── prescreener quality ──────────────────────────────────────────────

def load_prescreener_quality(path: str = PRESCREENER_PATH) -> dict[str, float]:
    """Read Oracle prescreener and compute quality scores.

    Uses the same component scoring as shared.quality but from cached
    snapshot data. Returns {SYMBOL: quality_score} in [0, 1].
    """
    data = _load_json(path, {})
    out: dict[str, float] = {}

    # Handle format: {"rows": [...]} or {"SYMBOL": {snapshot...}} or [...]
    rows = data
    if isinstance(data, dict):
        rows = data.get("rows", [])
        if not rows and "rows" not in data:
            # Try flat dict format: {SYMBOL: {snapshot}}
            for sym, info in data.items():
                if isinstance(info, dict):
                    snap = info.get("snapshot", info)
                    q = _quality_from_snapshot(snap)
                    if q is not None:
                        out[sym.upper()] = q
            if out:
                log.info("Oracle prescreener: %d quality scores loaded", len(out))
            return out

    for row in rows:
        if not isinstance(row, dict):
            continue
        sym = (row.get("symbol") or "").upper()
        snap = row.get("snapshot") or row
        if not isinstance(snap, dict):
            continue
        q = _quality_from_snapshot(snap)
        if sym and q is not None:
            out[sym] = q

    if out:
        log.info("Oracle prescreener: %d quality scores loaded", len(out))
    return out


def _quality_from_snapshot(snap: dict) -> Optional[float]:
    """Compute quality score from a prescreener snapshot dict.

    Mirrors shared.quality component scoring:
      gross_margin, operating_margin, fcf_margin, revenue_growth, dilution
    """
    scores: list[float] = []

    gm = snap.get("gross_margin_ttm")
    if gm is not None and 0 <= gm <= 1.0:
        scores.append(min(1.0, max(0.0, gm / 0.5)))

    om = snap.get("operating_margin_ttm")
    if om is not None and -1.0 <= om <= 1.0:
        scores.append(min(1.0, max(0.0, (om + 0.1) / 0.3)))

    rev = snap.get("revenue_ttm")
    fcf = snap.get("free_cash_flow_ttm")
    if fcf is not None and rev and abs(rev) > 0:
        margin = fcf / rev
        if 0 <= margin <= 1.0:
            scores.append(min(1.0, max(0.0, margin / 0.2)))

    rg = snap.get("revenue_yoy")
    if rg is not None:
        scores.append(min(1.0, max(0.0, (rg + 0.05) / 0.3)))

    dil = snap.get("dilution_yoy")
    if dil is not None:
        scores.append(min(1.0, max(0.0, 1.0 - dil * 10)))

    if not scores:
        return None
    # Penalize sparse data: divide by max(n, 3) so a single component
    # can't read as "perfect quality"
    return sum(scores) / max(len(scores), 3)


# ── insider cluster cache ─────────────────────────────────────────────

def load_insider_activity(path: str = INSIDER_CLUSTER_PATH) -> dict[str, dict]:
    """Read Oracle's insider cluster cache.

    Returns {SYMBOL: cluster_info} where cluster_info has:
      insider_count, total_dollars, latest_date, insiders
    """
    data = _load_json(path, {})
    clusters = data.get("clusters", []) if isinstance(data, dict) else data
    if isinstance(clusters, dict):
        clusters = list(clusters.values())

    out: dict[str, dict] = {}
    for c in clusters:
        if not isinstance(c, dict):
            continue
        sym = (c.get("symbol") or "").upper()
        if sym:
            out[sym] = c
    if out:
        log.info("Oracle insider clusters: %d symbols with activity", len(out))
    return out


# ── screen scores ─────────────────────────────────────────────────────

def load_screen_scores(path: str = SCREEN_PATH) -> dict[str, dict]:
    """Read Oracle's multi-lens screen scores.

    Returns {SYMBOL: {score, lenses: {insider_cluster, smart_money, ...}}}
    """
    data = _load_json(path, {})
    rows = data.get("rows", data.get("survivors", data.get("top", []))) if isinstance(data, dict) else data
    out: dict[str, dict] = {}
    for item in rows:
        if not isinstance(item, dict):
            continue
        sym = (item.get("symbol") or "").upper()
        if sym:
            out[sym] = item
    return out


# ── composite quality ─────────────────────────────────────────────────

QUALITY_DEFAULT = 0.5  # Penalize unknown names (was 0.7 hardcoded)


def company_quality(
    symbol: str,
    *,
    dossier_convictions: dict[str, float],
    prescreener_quality: dict[str, float],
    screen_scores: Optional[dict[str, dict]] = None,
) -> float:
    """Compute the company_quality factor for Achilles scoring.

    Priority:
      1. Oracle dossier conviction (0-1) — deepest research
      2. Prescreener quality score (0-1) — fundamental quality
      3. Default 0.5 — penalize unknown names

    When both dossier and prescreener exist, blend them:
      quality = 0.6 * conviction + 0.4 * prescreener_quality
    This weights Oracle's human-in-the-loop conviction higher than
    the mechanical quality screen.
    """
    sym = symbol.upper()

    conviction = dossier_convictions.get(sym)
    quality = prescreener_quality.get(sym)

    if conviction is not None and quality is not None:
        return 0.6 * conviction + 0.4 * quality

    if conviction is not None:
        return conviction

    if quality is not None:
        return quality

    # Check if it's at least on Oracle's screen (some signal)
    if screen_scores and sym in screen_scores:
        screen = screen_scores[sym]
        return max(0.5, screen.get("score", 0.5))

    return QUALITY_DEFAULT


# ── pre-earnings insider cross-reference ──────────────────────────────

def has_insider_preactivity(
    symbol: str,
    *,
    insider_activity: dict[str, dict],
    filing_date: str = "",
    lookback_days: int = 30,
) -> tuple[bool, float]:
    """Check if insiders were buying before an earnings announcement.

    Returns (has_activity, boost_factor):
      - (True, 1.3) if insiders bought within lookback_days before filing
      - (False, 1.0) otherwise

    The 1.3x boost is conservative — academic literature (Cohen, Malloy &
    Pomorski 2012) shows insider-predicted beats have 2-3x higher drift,
    but we start conservative and let Ghost Achilles calibrate.
    """
    sym = symbol.upper()
    cluster = insider_activity.get(sym)
    if not cluster:
        return (False, 1.0)

    latest_date = cluster.get("latest_date", "")
    if not latest_date or not filing_date:
        # Can't check timing, but insiders are active — small boost
        return (True, 1.15)

    # Check if insider activity was within lookback window before filing
    try:
        from datetime import datetime
        filing_dt = datetime.strptime(filing_date, "%Y-%m-%d")
        insider_dt = datetime.strptime(latest_date, "%Y-%m-%d")
        days_before = (filing_dt - insider_dt).days
        if 0 <= days_before <= lookback_days:
            # Insiders bought before earnings — strong signal
            insider_count = cluster.get("insider_count", 2)
            boost = min(1.5, 1.2 + 0.05 * insider_count)
            return (True, boost)
    except ValueError:
        pass

    return (False, 1.0)
