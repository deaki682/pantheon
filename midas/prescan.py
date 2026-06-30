"""Midas weekly pre-scan — fresh signal data independent of Oracle's quarterly cache.

Oracle's lens caches (insider clusters, smart money, activist 13D) are
built quarterly across ~7,000 filers. By the time Midas runs on Sunday,
the oldest insider signals can be 6+ weeks stale. This module provides
fast, targeted weekly data gathering so Midas scores convergence on
THIS WEEK's signals, not Oracle's leftovers.

Four independent data paths:
  1. Fresh Form 4 search — EDGAR FTS for insider filings in last 14 days
  2. Recent earnings beats — all reporters from last 5 trading days
  3. Volume anomalies — computed from price historicals
  4. Short squeeze candidates — high short float from finviz screener
"""
from __future__ import annotations

import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

FINVIZ_SHORT_URL = (
    "https://finviz.com/screener.ashx?v=131&f=sh_short_o20&o=-shortfloat"
)


SHORT_FLOAT_MIN = 20.0


def parse_finviz_short_text(text: str) -> dict[str, float]:
    """Parse ticker:short_float pairs from WebFetch output of finviz screener.

    Handles multiple formats:
      "ACME: Short Float 45.20% | Short Ratio 3.5"
      "ACME: 45.20%"
      "ACME  45.20%"
    Returns {symbol: short_float_pct} for all parsed rows.
    """
    results: dict[str, float] = {}
    for line in text.splitlines():
        m = re.match(
            r".*?([A-Z]{1,5})\b.*?(?:Short Float\s+)?(\d+\.?\d*)\s*%",
            line,
        )
        if m:
            sym = m.group(1)
            pct = float(m.group(2))
            if pct >= SHORT_FLOAT_MIN:
                results[sym] = pct
    return results


def form4_fts_to_clusters(
    fts_results: dict[str, list[dict]],
    *,
    min_filers: int = 2,
) -> dict[str, dict]:
    """Convert search_recent_form4() output to insider cluster format.

    fts_results: {symbol: [{"filer": name, "filing_date": date, "accession": acc}]}
    Returns: {symbol: {"insider_count": n, "filing_count": n, "latest_date": date}}

    Only includes symbols with min_filers+ distinct filers (default 2).
    Compatible with build_signal_map's insider_clusters parameter.
    """
    clusters: dict[str, dict] = {}
    for sym, filings in fts_results.items():
        distinct_filers = {f["filer"] for f in filings if f.get("filer")}
        if len(distinct_filers) >= min_filers:
            clusters[sym] = {
                "insider_count": len(distinct_filers),
                "filing_count": len(filings),
                "latest_date": max(
                    (f.get("filing_date", "") for f in filings),
                    default="",
                ),
            }
    return clusters


def merge_insider_clusters(
    oracle_cache: dict[str, dict],
    fresh_clusters: dict[str, dict],
) -> dict[str, dict]:
    """Merge Oracle's quarterly cache with fresh weekly Form 4 data.

    Fresh data takes precedence — if a symbol appears in both, the fresh
    cluster replaces the stale one. Oracle's cache provides breadth;
    fresh data provides timeliness.
    """
    merged = {}
    for sym, cluster in oracle_cache.items():
        merged[sym.upper()] = cluster
    for sym, cluster in fresh_clusters.items():
        merged[sym.upper()] = cluster
    return merged


def compute_volume_anomalies(
    historicals: dict[str, list[dict]],
    *,
    recent_days: int = 5,
    baseline_days: int = 30,
) -> dict[str, float]:
    """Compute volume ratio (recent vs baseline) from price historicals.

    historicals: {symbol: [{"volume": v, ...}, ...]} — daily bars, oldest first.
    Returns: {symbol: ratio} for symbols where ratio > 1.0.
    """
    anomalies: dict[str, float] = {}
    for sym, bars in historicals.items():
        if len(bars) < recent_days + 5:
            continue
        volumes = [float(b.get("volume", 0)) for b in bars if b.get("volume")]
        if len(volumes) < recent_days + 5:
            continue
        baseline = volumes[-(baseline_days):-recent_days] if len(volumes) >= baseline_days else volumes[:-recent_days]
        recent = volumes[-recent_days:]
        if not baseline or not recent:
            continue
        avg_baseline = sum(baseline) / len(baseline)
        avg_recent = sum(recent) / len(recent)
        if avg_baseline <= 0:
            continue
        ratio = avg_recent / avg_baseline
        if ratio > 1.0:
            anomalies[sym] = round(ratio, 2)
    return anomalies
