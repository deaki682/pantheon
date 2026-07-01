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

from .scoring import STALENESS_PCT

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


# ------- reaction-bar freshness (earnings / guidance) -------
#
# Earnings and guidance signals arrive with a calendar `report_date`, but the
# calendar routinely lags the tape: the real gap-and-volume reaction can be
# several trading days earlier than the reported date (observed on DAKT, PRGS).
# The PEAD drift window Midas trades is only ~1-5 trading days, so a reaction
# that already happened a week ago is a dead signal even though the beat is
# "recent" by the calendar. We therefore locate the actual reaction bar on the
# price/volume tape and gate freshness off THAT, not off report_date.

REACTION_MIN_GAP = 0.04     # a bar must move >= 4% vs the prior close to count
REACTION_VOL_RATIO = 1.5    # ...on >= 1.5x its trailing volume (when available)
REACTION_LOOKBACK = 15      # search the most recent ~3 weeks of bars
REACTION_VOL_BASELINE = 20  # trailing bars for the volume baseline

# A reaction older than this many trading days at SCAN time is stale. The scan
# runs on the weekend and entry is the following Monday, so a reaction already
# 3 trading days old at scan will be ~4-5 days old at entry — the tail end of
# the drift window. Beyond that the move is spent.
MAX_REACTION_AGE_DAYS = 3


def _bar_close(bar: dict) -> Optional[float]:
    for k in ("close_price", "close", "close_pric", "adjusted_close"):
        if bar.get(k) not in (None, ""):
            try:
                return float(bar[k])
            except (TypeError, ValueError):
                return None
    return None


def _bar_volume(bar: dict) -> float:
    try:
        return float(bar.get("volume", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _bar_date(bar: dict) -> str:
    for k in ("begins_at", "date", "begin_at"):
        if bar.get(k):
            return str(bar[k])[:10]
    return ""


def _latest_close(bars: list[dict]) -> Optional[float]:
    for b in reversed(bars):
        c = _bar_close(b)
        if c is not None and c > 0:
            return c
    return None


def find_reaction_bar(
    bars: list[dict],
    *,
    lookback: int = REACTION_LOOKBACK,
    min_gap: float = REACTION_MIN_GAP,
    vol_ratio: float = REACTION_VOL_RATIO,
    baseline: int = REACTION_VOL_BASELINE,
) -> Optional[dict]:
    """Locate the actual catalyst bar on the tape — the recent day with the
    largest abnormal price move on elevated volume — instead of trusting the
    reported calendar date.

    bars: daily bars, oldest first (Robinhood get_equity_historicals shape).
    Returns {index, date, pre_price, reaction_price, gap, vol_ratio, age_days}
    for the most significant qualifying bar, or None if the tape shows no clear
    reaction (e.g. an undigested beat that hasn't moved yet — deliberately NOT
    treated as stale).

    age_days = trading days between the reaction bar and the latest bar.
    """
    if not bars:
        return None
    valid = [(_bar_close(b), _bar_volume(b), _bar_date(b)) for b in bars]
    valid = [(c, v, d) for (c, v, d) in valid if c is not None and c > 0]
    if len(valid) < 2:
        return None

    last = len(valid) - 1
    start = max(1, len(valid) - lookback)
    best = None
    best_score = 0.0
    for i in range(start, len(valid)):
        close_i, vol_i, date_i = valid[i]
        prev_close = valid[i - 1][0]
        if prev_close <= 0:
            continue
        gap = (close_i - prev_close) / prev_close
        if abs(gap) < min_gap:
            continue
        base_slice = [v for (_, v, _) in valid[max(0, i - baseline):i]]
        avg_base = sum(base_slice) / len(base_slice) if base_slice else 0.0
        ratio = (vol_i / avg_base) if avg_base > 0 else float("inf")
        # Require elevated volume when we have a baseline to judge it against.
        if avg_base > 0 and ratio < vol_ratio:
            continue
        score = abs(gap) * (ratio if ratio != float("inf") else vol_ratio)
        if score > best_score:
            best_score = score
            best = {
                "index": i,
                "date": date_i,
                "pre_price": round(prev_close, 4),
                "reaction_price": round(close_i, 4),
                "gap": round(gap, 4),
                "vol_ratio": (round(ratio, 2) if ratio != float("inf") else None),
                "age_days": last - i,
            }
    return best


def filter_stale_earnings_signals(
    earnings_surprise: Optional[dict],
    guidance_raised: Optional[set],
    historicals: dict[str, list[dict]],
    *,
    max_age_days: int = MAX_REACTION_AGE_DAYS,
) -> tuple[dict, set, dict[str, str]]:
    """Drop earnings-beat / guidance-raised signals whose actual reaction bar
    has already aged out of the drift window.

    The insider-cluster staleness gate in `stage1_sieve` never covered these
    two channels, so a fully-resolved, week-old pop passed the sieve looking
    identical to a fresh one. This closes that gap using the real reaction bar
    from the tape rather than the calendar `report_date`.

    A name whose tape shows NO clear reaction is KEPT — that's an undigested
    beat (the ideal pre-drift setup), not a stale one.

    Two complementary gates fire off the reaction bar:
      - age gate: the reaction is older than `max_age_days` trading days, so
        the drift window has closed (catches a faded, week-old pop).
      - move gate: the price has already run more than `STALENESS_PCT` past the
        pre-reaction price, so the catalyst is priced in (catches a big gap
        that's still recent but already spent) — this is the insider-cluster
        gate's exact mechanism, extended to earnings/guidance.

    Returns (fresh_earnings_surprise, fresh_guidance_raised, dropped) where
    `dropped` maps symbol -> reason for logging.
    """
    dropped: dict[str, str] = {}

    def _fresh(sym: str) -> bool:
        bars = historicals.get(sym) or historicals.get(sym.upper())
        if not bars:
            return True  # no tape to judge — don't over-filter
        rb = find_reaction_bar(bars)
        if rb is None:
            return True  # no reaction yet — undigested beat, keep it
        if rb["age_days"] > max_age_days:
            dropped[sym] = f"reaction {rb['age_days']}d old ({rb['date']}), drift window closed"
            return False
        latest = _latest_close(bars)
        pre = rb["pre_price"]
        if latest and pre > 0 and abs(latest - pre) / pre > STALENESS_PCT:
            moved = round(100 * abs(latest - pre) / pre)
            dropped[sym] = f"price already moved {moved}% since reaction {rb['date']}, catalyst priced in"
            return False
        return True

    fresh_earnings = {
        sym: data for sym, data in (earnings_surprise or {}).items() if _fresh(sym)
    }
    fresh_guidance = {sym for sym in (guidance_raised or set()) if _fresh(sym)}
    return fresh_earnings, fresh_guidance, dropped


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
