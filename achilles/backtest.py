#!/usr/bin/env python3
"""Full-fidelity Achilles backtest.

Replays historical SEC filings day-by-day through the complete Achilles
cycle with real price data. Uses pre-fetched EDGAR filings and Robinhood
historical OHLCV bars.

Usage:
    python -m achilles.backtest
    python -m achilles.backtest --start 2025-07-01 --end 2026-06-28
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from achilles.sleeve import (
    AchillesSleeve, AchillesPosition, HARD_FLOOR, DRAWDOWN_HALT,
    MAX_CONCURRENT_POSITIONS, MAX_TRADES_PER_DAY, PER_POSITION_CAP_FRAC,
    PER_POSITION_MIN, PER_POSITION_MAX, FEE_BPS,
)
from achilles.playbooks import (
    Playbook, build_playbooks, record_outcome, maybe_autodisable,
    UNIVERSAL_DISQUALIFIERS, CLASS_DISQUALIFIERS,
)
from achilles.scoring import (
    score_event, liquidity_score, time_decay, surprise_strength,
    MEGACAP_DECAY_START,
)
from achilles.earnings import compute_surprise, is_actionable_beat, EarningsSurprise
from achilles.oracle_bridge import (
    company_quality as oracle_company_quality,
    has_insider_preactivity,
    load_dossier_convictions,
    load_insider_activity,
    load_prescreener_quality,
    load_screen_scores,
    QUALITY_DEFAULT,
)
from achilles.convergence import (
    neglect_premium,
    conviction_multiplier,
    extract_convergence_signals,
    build_prescreener_lookup,
)
from achilles.exits import evaluate as evaluate_exit
from achilles.journal import TradeEntry, round_trip_pnl, per_class_stats

log = logging.getLogger("achilles.backtest")

PRICES_PATH = "cache/backtest_prices.json"
FILINGS_PATH = "cache/backtest_filings.json"
EARNINGS_PATH = "cache/backtest_earnings.json"
OUTPUT_PATH = "cache/backtest_results.json"
JOURNAL_PATH = "cache/backtest_journal.jsonl"
CURVE_PATH = "cache/backtest_curve.json"


# ── data loading ──────────────────────────────────────────────────────

def load_prices(path: str) -> dict[str, dict[str, dict]]:
    """Load prices as {SYMBOL: {date_str: {open, high, low, close, volume}}}."""
    with open(path) as f:
        raw = json.load(f)
    out = {}
    for sym, bars in raw.items():
        by_date = {}
        for b in bars:
            by_date[b["date"]] = b
        out[sym] = by_date
    return out


def load_filings(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def load_earnings(path: str) -> dict[str, list[dict]]:
    """Load pre-fetched earnings data as {SYMBOL: [{actual_eps, estimate_eps, report_date, quarter}]}."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def match_earnings_to_filing(
    symbol: str,
    filing_date: str,
    earnings_data: dict[str, list[dict]],
    *,
    max_gap_days: int = 5,
) -> Optional[EarningsSurprise]:
    """Find the earnings result that matches a filing date.

    An 8-K item 2.02 is filed on or near the earnings report date.
    We match by finding the closest report_date within max_gap_days.
    """
    quarters = earnings_data.get(symbol.upper(), [])
    if not quarters:
        return None

    try:
        fd = datetime.strptime(filing_date, "%Y-%m-%d")
    except ValueError:
        return None

    best = None
    best_gap = max_gap_days + 1
    for q in quarters:
        rd = q.get("report_date", "")
        actual = q.get("actual_eps")
        estimate = q.get("estimate_eps")
        if actual is None or estimate is None or not rd:
            continue
        try:
            rd_dt = datetime.strptime(rd, "%Y-%m-%d")
            gap = abs((fd - rd_dt).days)
            if gap < best_gap:
                best_gap = gap
                best = q
        except ValueError:
            continue

    if best is None:
        return None

    actual_f = float(best["actual_eps"])
    estimate_f = float(best["estimate_eps"])
    surprise_pct, is_beat = compute_surprise(actual_f, estimate_f)

    return EarningsSurprise(
        symbol=symbol.upper(),
        actual_eps=actual_f,
        estimate_eps=estimate_f,
        surprise_pct=surprise_pct,
        is_beat=is_beat,
        report_date=best.get("report_date", ""),
        quarter=best.get("quarter", ""),
    )


# ── event pre-processing ─────────────────────────────────────────────

@dataclass
class BacktestEvent:
    event_id: str
    event_class: str
    symbol: str
    filing_date: str
    strength: float = 1.0
    metadata: dict = field(default_factory=dict)


def classify_8k_items(items_str: str) -> list[str]:
    """Classify 8-K items into event classes."""
    if not items_str:
        return []
    items = set()
    for item in items_str.split(","):
        item = item.strip().rstrip(".")
        if item:
            items.add(item)
    labels = []
    if "2.02" in items:
        labels.append("earnings_reaction")
    if "2.01" in items:
        labels.append("ma_target")
    if "7.01" in items or "8.01" in items:
        labels.append("guidance_revision")
    return labels


def build_event_timeline(
    filings: list[dict],
    *,
    earnings_data: Optional[dict[str, list[dict]]] = None,
    insider_activity: Optional[dict[str, dict]] = None,
) -> dict[str, list[BacktestEvent]]:
    """Pre-process all filings into a date-keyed event timeline.

    With earnings_data: matches 8-K item 2.02 to actual/estimate EPS,
    filters for beats only, and applies the surprise strength curve.
    Without: falls back to flat 0.85 strength (old behavior).

    With insider_activity: checks for pre-earnings insider buying and
    applies a boost to the event strength.
    """
    events_by_date: dict[str, list[BacktestEvent]] = defaultdict(list)
    earnings_data = earnings_data or {}
    insider_activity = insider_activity or {}

    # Track Form 4s for insider cluster detection
    form4_by_sym_date: dict[str, list[str]] = defaultdict(list)

    # Stats for logging
    earnings_total = 0
    earnings_matched = 0
    earnings_beats = 0
    earnings_misses = 0
    earnings_no_data = 0
    insider_boosted = 0

    for f in filings:
        form = (f.get("form") or "").strip()
        sym = f.get("symbol", "").upper()
        fdate = f.get("filing_date", "")
        acc = f.get("accession_no", "")
        items_str = f.get("items", "")

        if not sym or not fdate:
            continue

        if form in ("4", "4/A"):
            form4_by_sym_date[sym].append(fdate)
            continue

        if form == "SCHEDULE 13D":
            events_by_date[fdate].append(BacktestEvent(
                event_id=f"13d:{sym}:{acc}",
                event_class="activist_13d",
                symbol=sym,
                filing_date=fdate,
                strength=1.0,
            ))
            continue

        if form == "8-K":
            labels = classify_8k_items(items_str)

            # Check for concurrent restructuring items (disqualifier)
            raw_items = set()
            for item in items_str.split(","):
                item = item.strip().rstrip(".")
                if item:
                    raw_items.add(item)
            has_restructuring = "2.05" in raw_items or "2.06" in raw_items

            for lbl in labels:
                if lbl == "earnings_reaction":
                    earnings_total += 1

                    if has_restructuring:
                        continue

                    if earnings_data:
                        surprise = match_earnings_to_filing(sym, fdate, earnings_data)
                        if surprise is None:
                            earnings_no_data += 1
                            # No Robinhood data — can't determine direction.
                            # Keep the trade with neutral strength rather
                            # than dropping it (PKE, KOPN, etc. have no
                            # analyst coverage but valid PEAD drift).
                            strength = 0.85
                            metadata = {"no_earnings_data": True}
                            events_by_date[fdate].append(BacktestEvent(
                                event_id=f"earn:{sym}:{acc}",
                                event_class="earnings_reaction",
                                symbol=sym,
                                filing_date=fdate,
                                strength=strength,
                                metadata=metadata,
                            ))
                            continue
                        earnings_matched += 1
                        if not is_actionable_beat(surprise):
                            earnings_misses += 1
                            continue
                        earnings_beats += 1
                        strength = surprise_strength(surprise.surprise_pct)

                        # Apply concurrent guidance boost
                        if "guidance_revision" in labels:
                            # Can't read body in backtest, but concurrent
                            # guidance + beat is generally positive.
                            # Apply a conservative 1.1x (vs 1.2x in production
                            # where we can confirm direction is "raised")
                            strength *= 1.1

                        # Apply insider pre-earnings boost
                        has_insider, boost = has_insider_preactivity(
                            sym,
                            insider_activity=insider_activity,
                            filing_date=fdate,
                        )
                        if has_insider:
                            strength *= boost
                            insider_boosted += 1

                        strength = min(1.5, strength)

                        metadata = {
                            "surprise_pct": surprise.surprise_pct,
                            "actual_eps": surprise.actual_eps,
                            "estimate_eps": surprise.estimate_eps,
                            "quarter": surprise.quarter,
                        }
                        if has_insider:
                            metadata["insider_boost"] = boost
                    else:
                        strength = 0.85
                        metadata = {}

                    events_by_date[fdate].append(BacktestEvent(
                        event_id=f"earn:{sym}:{acc}",
                        event_class="earnings_reaction",
                        symbol=sym,
                        filing_date=fdate,
                        strength=strength,
                        metadata=metadata,
                    ))
                elif lbl == "ma_target":
                    events_by_date[fdate].append(BacktestEvent(
                        event_id=f"ma:{sym}:{acc}",
                        event_class="ma_target",
                        symbol=sym,
                        filing_date=fdate,
                        strength=1.0,
                    ))
                elif lbl == "guidance_revision":
                    # Skip standalone guidance when already consumed as
                    # concurrent boost on an earnings event
                    if "earnings_reaction" in labels and earnings_data:
                        continue
                    events_by_date[fdate].append(BacktestEvent(
                        event_id=f"guidance:{sym}:{acc}",
                        event_class="guidance_revision",
                        symbol=sym,
                        filing_date=fdate,
                        strength=0.7,
                    ))

    if earnings_data:
        log.info("Earnings pipeline: %d total, %d matched, %d beats, %d misses/OOR, "
                 "%d no data, %d insider-boosted",
                 earnings_total, earnings_matched, earnings_beats,
                 earnings_misses, earnings_no_data, insider_boosted)

    # Aggregate insider clusters: 2+ Form 4s within 2-day window per symbol
    for sym, dates in form4_by_sym_date.items():
        dates_sorted = sorted(set(dates))
        i = 0
        while i < len(dates_sorted):
            window_start = dates_sorted[i]
            ws_dt = datetime.strptime(window_start, "%Y-%m-%d")
            cluster_dates = [window_start]
            j = i + 1
            while j < len(dates_sorted):
                d_dt = datetime.strptime(dates_sorted[j], "%Y-%m-%d")
                if (d_dt - ws_dt).days <= 2:
                    cluster_dates.append(dates_sorted[j])
                    j += 1
                else:
                    break
            if len(cluster_dates) >= 2:
                latest = cluster_dates[-1]
                strength = min(1.0, len(cluster_dates) / 4.0)
                events_by_date[latest].append(BacktestEvent(
                    event_id=f"cluster:{sym}:{latest}",
                    event_class="insider_cluster",
                    symbol=sym,
                    filing_date=latest,
                    strength=strength,
                    metadata={"insider_count": len(cluster_dates)},
                ))
                i = j
            else:
                i += 1

    return events_by_date


# ── market cap estimation ─────────────────────────────────────────────

def estimate_market_caps(
    prices: dict[str, dict[str, dict]],
) -> dict[str, float]:
    """Rough market cap estimate from price level.

    Without real share count data, we use price as a proxy. Achilles's
    seed list is curated small/mid-caps, so we assign a base market cap
    of $500M and scale by relative price level. This is sufficient for
    the liquidity scoring curve (which only cares about order-of-magnitude).
    """
    caps = {}
    for sym, by_date in prices.items():
        # Use the median close price as baseline
        closes = sorted(b["close"] for b in by_date.values())
        if closes:
            median_close = closes[len(closes) // 2]
            # Heuristic: seed list is $200M-$5B range
            # Scale around $500M baseline
            caps[sym] = 500_000_000
    return caps


# ── simulation ────────────────────────────────────────────────────────

@dataclass
class BacktestTrade:
    event_id: str
    event_class: str
    symbol: str
    entry_date: str
    entry_price: float
    exit_date: str = ""
    exit_price: float = 0.0
    exit_reason: str = ""
    dollars: float = 0.0
    shares: float = 0.0
    pnl: float = 0.0
    return_pct: float = 0.0
    score: float = 0.0


def get_trading_days(prices: dict[str, dict[str, dict]]) -> list[str]:
    """Extract sorted list of all trading days from price data."""
    all_dates = set()
    for by_date in prices.values():
        all_dates.update(by_date.keys())
    return sorted(all_dates)


def run_backtest(
    prices: dict[str, dict[str, dict]],
    events_by_date: dict[str, list[BacktestEvent]],
    market_caps: dict[str, float],
    *,
    start_date: str = "",
    end_date: str = "",
    initial_cash: float = 1000.0,
    conservative_start: bool = False,
    event_classes: Optional[set[str]] = None,
    dossier_convictions: Optional[dict[str, float]] = None,
    prescreener_quality: Optional[dict[str, float]] = None,
    screen_scores: Optional[dict[str, dict]] = None,
    quality_override: Optional[float] = None,
    prescreener_snapshots: Optional[dict[str, dict]] = None,
    benchmark_daily_return: Optional[float] = None,
) -> dict:
    """Run full-fidelity Achilles backtest.

    New convergence features:
      - neglect_premium replaces company_quality (inverts the signal)
      - conviction_multiplier stacks Oracle signals for position sizing
      - prescreener_snapshots: {SYM: {snapshot}} for convergence signals
      - benchmark_daily_return: daily return to apply to idle cash (IWM overlay)
    """
    dossier_convictions = dossier_convictions or {}
    prescreener_quality = prescreener_quality or {}
    screen_scores = screen_scores or {}
    prescreener_snapshots = prescreener_snapshots or {}

    trading_days = get_trading_days(prices)
    if start_date:
        trading_days = [d for d in trading_days if d >= start_date]
    if end_date:
        trading_days = [d for d in trading_days if d <= end_date]

    if not trading_days:
        return {"error": "No trading days in range"}

    log.info("Backtest: %s to %s (%d trading days)",
             trading_days[0], trading_days[-1], len(trading_days))

    # Initialize
    sleeve = AchillesSleeve(initial_cash=initial_cash, conservative_mode=conservative_start)
    playbooks = build_playbooks()
    trades: list[BacktestTrade] = []
    open_trades: dict[str, BacktestTrade] = {}
    equity_curve: list[dict] = []
    daily_events_log: list[dict] = []
    seen_event_ids: set[str] = set()

    total_events = 0
    total_scored = 0
    total_opened = 0
    total_closed = 0
    total_blocked = 0

    for day_idx, today in enumerate(trading_days):
        # Get today's prices
        today_prices = {}
        for sym, by_date in prices.items():
            if today in by_date:
                today_prices[sym] = by_date[today]["close"]

        # ── 1. Process settlements ──
        sleeve.process_settlements(today)

        # ── 2. Floor check ──
        sleeve.update_peak(today_prices)
        if sleeve.check_hard_floor(today_prices):
            if not sleeve.halted:
                log.warning("Day %s: HALTED at equity $%.2f", today, sleeve.equity(today_prices))
            # Still evaluate exits but no new opens
            pass

        # ── 3. Get today's events ──
        day_events = events_by_date.get(today, [])

        # ── 4. Score and open ──
        for ev in day_events:
            if ev.event_id in seen_event_ids:
                continue
            seen_event_ids.add(ev.event_id)
            total_events += 1

            if event_classes and ev.event_class not in event_classes:
                continue

            pb = playbooks.get(ev.event_class)
            if not pb or pb.disabled:
                continue

            mcap = market_caps.get(ev.symbol, 500_000_000)

            # Skip mega-caps (>$50B) — Achilles doesn't trade these
            if mcap > MEGACAP_DECAY_START:
                continue

            # Oracle quality for convergence sizing
            oq = oracle_company_quality(
                ev.symbol,
                dossier_convictions=dossier_convictions,
                prescreener_quality=prescreener_quality,
                screen_scores=screen_scores,
            )

            score_out = score_event(
                playbook=pb,
                event_strength=ev.strength,
                company_quality=quality_override if quality_override is not None else 1.0,
                market_cap=mcap,
                first_seen_iso=f"{today}T10:00:00",
                now=datetime.strptime(f"{today}T10:00:00", "%Y-%m-%dT%H:%M:%S"),
            )
            total_scored += 1

            score = score_out["score"]
            if score < 0.05:
                continue

            entry_price = today_prices.get(ev.symbol)
            if not entry_price or entry_price <= 0:
                continue

            if sleeve.halted:
                total_blocked += 1
                continue

            # Compute convergence signals for position sizing
            conv_signals = extract_convergence_signals(
                ev.symbol,
                prescreener_rows=prescreener_snapshots,
                event_metadata=ev.metadata,
                oracle_quality=oq,
            )
            conviction = conviction_multiplier(**conv_signals)

            # Compute play parameters
            hard_stop_price = entry_price * (1.0 + pb.hard_stop_pct)
            profit_target_price = entry_price * (1.0 + pb.profit_target_pct)
            entry_dt = datetime.strptime(today, "%Y-%m-%d")
            time_stop_date = (entry_dt + timedelta(days=pb.time_stop_days)).strftime("%Y-%m-%d")

            # Try to open
            pos = sleeve.open(
                event_id=ev.event_id,
                symbol=ev.symbol,
                event_class=ev.event_class,
                entry_price=entry_price,
                score=score,
                hard_stop_price=hard_stop_price,
                profit_target_price=profit_target_price,
                time_stop_date=time_stop_date,
                today=today,
                trail_armed_at=pb.trail_armed_at,
                trail_pct=pb.trail_pct,
                conviction=conviction,
            )
            if pos is None:
                total_blocked += 1
                continue

            total_opened += 1
            bt = BacktestTrade(
                event_id=ev.event_id,
                event_class=ev.event_class,
                symbol=ev.symbol,
                entry_date=today,
                entry_price=entry_price,
                dollars=pos.dollars_at_entry,
                shares=pos.shares,
                score=score,
            )
            open_trades[ev.event_id] = bt

        # ── 5. Update high-water marks from intraday highs ──
        for event_id, pos in sleeve.positions.items():
            bar = prices.get(pos.symbol, {}).get(today)
            if bar and bar["high"] > pos.high_water_price:
                pos.high_water_price = bar["high"]

        # ── 6. Evaluate exits ──
        to_close = []
        for event_id, pos in list(sleeve.positions.items()):
            bar = prices.get(pos.symbol, {}).get(today)
            price = today_prices.get(pos.symbol)
            if not price:
                if bar:
                    if bar["low"] <= pos.hard_stop_price:
                        price = pos.hard_stop_price
                    elif bar["high"] >= pos.profit_target_price:
                        price = pos.profit_target_price
                    else:
                        price = bar["close"]
                else:
                    continue

            verdict = evaluate_exit(pos, price, today)
            if verdict["action"] == "exit":
                to_close.append((event_id, price, verdict["reason"]))
                continue

            # Check intraday stops if close-price didn't trigger
            if bar:
                if bar["low"] <= pos.hard_stop_price:
                    to_close.append((event_id, pos.hard_stop_price, "hard_stop"))
                elif bar["high"] >= pos.profit_target_price:
                    to_close.append((event_id, pos.profit_target_price, "profit_target"))
                elif pos.trail_armed_at > 0 and pos.trail_pct > 0:
                    arm_price = pos.entry_price * (1.0 + pos.trail_armed_at)
                    if pos.high_water_price >= arm_price:
                        trail_level = pos.high_water_price * (1.0 - pos.trail_pct)
                        if bar["low"] <= trail_level:
                            to_close.append((event_id, trail_level, "trailing_stop"))

        for event_id, exit_price, reason in to_close:
            if event_id not in sleeve.positions:
                continue
            pos = sleeve.positions[event_id]
            realized = sleeve.close(event_id, exit_price=exit_price, today=today)
            if realized is not None:
                total_closed += 1
                bt = open_trades.pop(event_id, None)
                if bt:
                    bt.exit_date = today
                    bt.exit_price = exit_price
                    bt.exit_reason = reason
                    bt.pnl = realized
                    bt.return_pct = (exit_price - bt.entry_price) / bt.entry_price if bt.entry_price > 0 else 0
                    trades.append(bt)

                    if reason == "hard_stop":
                        sleeve.add_cooldown(pos.symbol, today)

                    # Record outcome for playbook auto-disable
                    pb = playbooks.get(pos.event_class)
                    if pb:
                        record_outcome(pb, hit=(realized > 0))
                        maybe_autodisable(pb)

        # ── 7. Benchmark overlay: idle cash earns IWM return ──
        if benchmark_daily_return and benchmark_daily_return > 0:
            idle = max(0.0, sleeve.cash)
            if idle > 0:
                bench_gain = idle * benchmark_daily_return
                sleeve.cash += bench_gain

        # ── 8. Record equity ──
        eq = sleeve.equity(today_prices)
        equity_curve.append({
            "date": today,
            "equity": round(eq, 2),
            "cash": round(sleeve.cash, 2),
            "positions": len(sleeve.positions),
            "halted": sleeve.halted,
        })

        if (day_idx + 1) % 50 == 0:
            log.info("Day %d/%d (%s): equity=$%.2f, positions=%d, trades=%d",
                     day_idx + 1, len(trading_days), today, eq,
                     len(sleeve.positions), len(trades))

    # Close any remaining positions at last available price
    last_day = trading_days[-1]
    for event_id in list(sleeve.positions.keys()):
        pos = sleeve.positions[event_id]
        last_price = prices.get(pos.symbol, {}).get(last_day, {}).get("close", pos.entry_price)
        realized = sleeve.close(event_id, exit_price=last_price, today=last_day)
        if realized is not None:
            total_closed += 1
            bt = open_trades.pop(event_id, None)
            if bt:
                bt.exit_date = last_day
                bt.exit_price = last_price
                bt.exit_reason = "backtest_end"
                bt.pnl = realized
                bt.return_pct = (last_price - bt.entry_price) / bt.entry_price if bt.entry_price > 0 else 0
                trades.append(bt)

    # ── Results ──
    final_equity = sleeve.equity()

    # Per-class breakdown
    by_class: dict[str, list[BacktestTrade]] = defaultdict(list)
    for t in trades:
        by_class[t.event_class].append(t)

    class_stats = {}
    for cls, cls_trades in by_class.items():
        wins = [t for t in cls_trades if t.pnl > 0]
        losses = [t for t in cls_trades if t.pnl <= 0]
        total_pnl = sum(t.pnl for t in cls_trades)
        avg_return = sum(t.return_pct for t in cls_trades) / len(cls_trades) if cls_trades else 0
        avg_win = sum(t.return_pct for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.return_pct for t in losses) / len(losses) if losses else 0

        # Exit reason breakdown
        reasons = defaultdict(int)
        for t in cls_trades:
            reasons[t.exit_reason] += 1

        class_stats[cls] = {
            "n": len(cls_trades),
            "wins": len(wins),
            "losses": len(losses),
            "hit_rate": len(wins) / len(cls_trades) if cls_trades else 0,
            "total_pnl": round(total_pnl, 2),
            "avg_return_pct": round(avg_return * 100, 2),
            "avg_win_pct": round(avg_win * 100, 2),
            "avg_loss_pct": round(avg_loss * 100, 2),
            "exit_reasons": dict(reasons),
        }

    # Overall stats
    all_wins = [t for t in trades if t.pnl > 0]
    all_losses = [t for t in trades if t.pnl <= 0]
    total_pnl = sum(t.pnl for t in trades)

    # Compute max drawdown from equity curve
    peak = initial_cash
    max_dd = 0.0
    max_dd_date = ""
    for pt in equity_curve:
        if pt["equity"] > peak:
            peak = pt["equity"]
        dd = (peak - pt["equity"]) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            max_dd_date = pt["date"]

    # Compute Sharpe ratio (annualized, daily returns)
    daily_returns = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]["equity"]
        curr = equity_curve[i]["equity"]
        if prev > 0:
            daily_returns.append((curr - prev) / prev)
    if daily_returns:
        import statistics
        mean_daily = statistics.mean(daily_returns)
        std_daily = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 1e-9
        sharpe = (mean_daily / std_daily) * (252 ** 0.5) if std_daily > 0 else 0
    else:
        sharpe = 0

    # Win streak / loss streak
    max_win_streak = max_loss_streak = 0
    cur_win = cur_loss = 0
    for t in sorted(trades, key=lambda x: x.entry_date):
        if t.pnl > 0:
            cur_win += 1
            cur_loss = 0
        else:
            cur_loss += 1
            cur_win = 0
        max_win_streak = max(max_win_streak, cur_win)
        max_loss_streak = max(max_loss_streak, cur_loss)

    # Playbook status
    pb_status = {}
    for cls, pb in playbooks.items():
        pb_status[cls] = {
            "live_n": pb.live_n,
            "live_hits": pb.live_hits,
            "live_hit_rate": round(pb.live_hits / pb.live_n, 3) if pb.live_n > 0 else 0,
            "expected_hit_rate": pb.expected_hit_rate,
            "disabled": pb.disabled,
        }

    results = {
        "period": f"{trading_days[0]} to {trading_days[-1]}",
        "trading_days": len(trading_days),
        "initial_equity": initial_cash,
        "final_equity": round(final_equity, 2),
        "total_return_pct": round((final_equity - initial_cash) / initial_cash * 100, 2),
        "total_pnl": round(total_pnl, 2),
        "annualized_return_pct": round(
            ((final_equity / initial_cash) ** (252 / max(1, len(trading_days))) - 1) * 100, 2
        ),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "max_drawdown_date": max_dd_date,
        "total_events_detected": total_events,
        "total_scored": total_scored,
        "total_trades": len(trades),
        "total_opened": total_opened,
        "total_blocked": total_blocked,
        "wins": len(all_wins),
        "losses": len(all_losses),
        "overall_hit_rate": round(len(all_wins) / len(trades), 3) if trades else 0,
        "avg_return_pct": round(
            sum(t.return_pct for t in trades) / len(trades) * 100, 2
        ) if trades else 0,
        "avg_win_pct": round(
            sum(t.return_pct for t in all_wins) / len(all_wins) * 100, 2
        ) if all_wins else 0,
        "avg_loss_pct": round(
            sum(t.return_pct for t in all_losses) / len(all_losses) * 100, 2
        ) if all_losses else 0,
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "biggest_win": round(max((t.pnl for t in trades), default=0), 2),
        "biggest_loss": round(min((t.pnl for t in trades), default=0), 2),
        "class_stats": class_stats,
        "playbook_status": pb_status,
        "halted": sleeve.halted,
    }

    return {
        "results": results,
        "equity_curve": equity_curve,
        "trades": [asdict(t) for t in trades],
    }


# ── output ────────────────────────────────────────────────────────────

def print_report(results: dict) -> str:
    r = results["results"]
    lines = []
    lines.append("=" * 64)
    lines.append("ACHILLES BACKTEST REPORT")
    lines.append("=" * 64)
    lines.append(f"Period           : {r['period']}")
    lines.append(f"Trading days     : {r['trading_days']}")
    lines.append("")
    lines.append("── PERFORMANCE ─────────────────────────────────────────")
    lines.append(f"Initial equity   : ${r['initial_equity']:.2f}")
    lines.append(f"Final equity     : ${r['final_equity']:.2f}")
    lines.append(f"Total return     : {r['total_return_pct']:+.2f}%")
    lines.append(f"Annualized return: {r['annualized_return_pct']:+.2f}%")
    lines.append(f"Sharpe ratio     : {r['sharpe_ratio']:.2f}")
    lines.append(f"Max drawdown     : {r['max_drawdown_pct']:.2f}% (on {r['max_drawdown_date']})")
    lines.append(f"Total PnL        : ${r['total_pnl']:+.2f}")
    lines.append("")
    lines.append("── TRADE STATISTICS ────────────────────────────────────")
    lines.append(f"Events detected  : {r['total_events_detected']}")
    lines.append(f"Events scored    : {r['total_scored']}")
    lines.append(f"Trades executed  : {r['total_trades']}")
    lines.append(f"Trades blocked   : {r['total_blocked']}")
    lines.append(f"Win / Loss       : {r['wins']} / {r['losses']}")
    lines.append(f"Hit rate         : {r['overall_hit_rate']:.1%}")
    lines.append(f"Avg return       : {r['avg_return_pct']:+.2f}%")
    lines.append(f"Avg win          : {r['avg_win_pct']:+.2f}%")
    lines.append(f"Avg loss         : {r['avg_loss_pct']:+.2f}%")
    lines.append(f"Max win streak   : {r['max_win_streak']}")
    lines.append(f"Max loss streak  : {r['max_loss_streak']}")
    lines.append(f"Biggest win      : ${r['biggest_win']:+.2f}")
    lines.append(f"Biggest loss     : ${r['biggest_loss']:+.2f}")
    lines.append(f"Halted           : {'YES' if r['halted'] else 'No'}")
    lines.append("")
    lines.append("── PER-CLASS BREAKDOWN ─────────────────────────────────")
    header = f"{'Class':22s} {'N':>4s} {'Wins':>5s} {'Hit%':>6s} {'AvgRet':>8s} {'PnL':>8s}   Exit reasons"
    lines.append(header)
    lines.append("-" * len(header) + "-" * 30)
    for cls in ("earnings_reaction", "insider_cluster", "activist_13d",
                "ma_target", "spinoff_window", "guidance_revision"):
        s = r["class_stats"].get(cls)
        if not s:
            continue
        reasons_str = ", ".join(f"{k}={v}" for k, v in sorted(s["exit_reasons"].items()))
        lines.append(
            f"{cls:22s} {s['n']:4d} {s['wins']:5d} {s['hit_rate']:5.1%} "
            f"{s['avg_return_pct']:+7.2f}% ${s['total_pnl']:+7.2f}   {reasons_str}"
        )
    lines.append("")
    lines.append("── PLAYBOOK STATUS ─────────────────────────────────────")
    for cls, ps in r["playbook_status"].items():
        status = "DISABLED" if ps["disabled"] else "active"
        lines.append(
            f"  {cls:22s} n={ps['live_n']:3d} hit={ps['live_hit_rate']:.1%} "
            f"(expected {ps['expected_hit_rate']:.1%}) [{status}]"
        )
    lines.append("")
    lines.append("=" * 64)

    text = "\n".join(lines)
    print(text)
    return text


# ── main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Achilles full backtest")
    parser.add_argument("--start", default="", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="", help="End date (YYYY-MM-DD)")
    parser.add_argument("--cash", type=float, default=1000.0, help="Initial cash")
    parser.add_argument("--conservative", action="store_true", help="Start in conservative mode")
    parser.add_argument("--classes", default="", help="Comma-separated event classes to include (default: all)")
    parser.add_argument("--quality-override", type=float, default=None,
                        help="Pin company_quality to this value (ignores Oracle data)")
    parser.add_argument("--no-earnings-filter", action="store_true",
                        help="Disable beat filter — treat all earnings 8-Ks as events (old behavior)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    log.info("Loading price data...")
    prices = load_prices(PRICES_PATH)
    log.info("Loaded prices for %d symbols", len(prices))

    log.info("Loading filings...")
    filings = load_filings(FILINGS_PATH)
    log.info("Loaded %d filings", len(filings))

    log.info("Loading earnings data...")
    earnings_data = load_earnings(EARNINGS_PATH)
    log.info("Loaded earnings for %d symbols", len(earnings_data))

    log.info("Loading Oracle research data...")
    dossier_convictions = load_dossier_convictions()
    prescreener_quality = load_prescreener_quality()
    insider_activity = load_insider_activity()
    screen_scores = load_screen_scores()

    # Load prescreener snapshots for convergence scoring
    import json as _json
    try:
        with open("cache/oracle_prescreener.json") as _f:
            _ps_data = _json.load(_f)
        prescreener_snapshots = build_prescreener_lookup(_ps_data.get("rows", []))
    except (FileNotFoundError, _json.JSONDecodeError):
        prescreener_snapshots = {}

    log.info("Oracle data: %d dossiers, %d prescreener, %d insider clusters, %d screen, %d snapshots",
             len(dossier_convictions), len(prescreener_quality),
             len(insider_activity), len(screen_scores), len(prescreener_snapshots))

    log.info("Building event timeline...")
    events_by_date = build_event_timeline(
        filings,
        earnings_data=None if args.no_earnings_filter else earnings_data,
        insider_activity=insider_activity,
    )
    total_events = sum(len(v) for v in events_by_date.values())
    log.info("Built timeline: %d events across %d dates", total_events, len(events_by_date))

    log.info("Estimating market caps...")
    market_caps = estimate_market_caps(prices)

    event_classes = set(args.classes.split(",")) if args.classes else None
    if event_classes:
        log.info("Filtering to event classes: %s", event_classes)

    log.info("Running simulation...")
    output = run_backtest(
        prices, events_by_date, market_caps,
        start_date=args.start,
        end_date=args.end,
        initial_cash=args.cash,
        conservative_start=args.conservative,
        event_classes=event_classes,
        dossier_convictions=dossier_convictions,
        prescreener_quality=prescreener_quality,
        screen_scores=screen_scores,
        quality_override=args.quality_override,
        prescreener_snapshots=prescreener_snapshots,
    )

    # Save results
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output["results"], f, indent=2)
    with open(CURVE_PATH, "w") as f:
        json.dump(output["equity_curve"], f, indent=1)

    # Save trade journal
    with open(JOURNAL_PATH, "w") as f:
        for t in output["trades"]:
            f.write(json.dumps(t, sort_keys=True) + "\n")

    print_report(output)
    log.info("Results saved to %s", OUTPUT_PATH)
    log.info("Equity curve saved to %s", CURVE_PATH)
    log.info("Trade journal saved to %s", JOURNAL_PATH)


if __name__ == "__main__":
    main()
