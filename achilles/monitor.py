#!/usr/bin/env python3
"""Achilles constant monitor — standalone event-driven trading loop.

Polls EDGAR for new SEC filings, classifies events, scores through the
multiplicative pipeline, and either logs (dry-run) or places orders (live).

Usage:
    python -m achilles.monitor                         # single cycle
    python -m achilles.monitor --loop                  # every 30 min
    python -m achilles.monitor --loop --interval 900   # every 15 min
    ACHILLES_LIVE=true python -m achilles.monitor      # live mode
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, date, timedelta
from typing import Optional

from shared import broker
from shared.edgar import (
    fetch_body, fetch_company_tickers, fetch_submissions,
    parse_submissions_recent,
)
from shared.guards import kill_switch_active, is_live, append_order, OrderRecord
from shared.insiders import parse_form4

from . import cursor as cursor_mod
from .classify import classify_filing
from .earnings import fetch_earnings_surprise, is_actionable_beat
from .events import aggregate_insider_clusters, build_event_for_filing
from .execution import plan_exits, plan_open
from .brief import build_play, make_brief
from .journal import TradeEntry, append as journal_append
from .oracle_bridge import (
    company_quality as oracle_company_quality,
    has_insider_preactivity,
    load_dossier_convictions,
    load_insider_activity,
    load_prescreener_quality,
    load_screen_scores,
)
from .playbooks import build_playbooks
from .scoring import score_event
from .sleeve import AchillesSleeve
from .watchlist import build_watchlist

log = logging.getLogger("achilles.monitor")

# ── paths ──────────────────────────────────────────────────────────────
SLEEVE_PATH = "cache/achilles_sleeve.json"
CURSOR_PATH = "cache/achilles_cursor.json"
CURVE_PATH = "cache/achilles_curve.json"
JOURNAL_PATH = "cache/achilles_journal.jsonl"
QUOTES_PATH = "cache/achilles_quotes.json"

LEDGER_PATH = "cache/achilles_ledger.jsonl"

ACTIVIST_PATH = "cache/oracle_activist_13d.json"
INSIDER_PATH = "cache/oracle_insider_clusters.json"
SMART_MONEY_PATH = "cache/oracle_smart_money.json"
SCREEN_PATH = "cache/oracle_screen.json"
PRESCREENER_PATH = "cache/oracle_prescreener.json"

DEFAULT_INTERVAL = 1800  # 30 minutes
POLL_CAP = 250  # max symbols to poll per cycle (SEC rate-limit budget)


# ── helpers ────────────────────────────────────────────────────────────

def _load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _symbols_from_cache(path):
    data = _load_json(path, [])
    if isinstance(data, list):
        return [
            d.get("symbol", d.get("ticker", ""))
            for d in data if isinstance(d, dict)
        ]
    if isinstance(data, dict):
        return list(data.keys())
    return []


def _load_quotes():
    data = _load_json(QUOTES_PATH, {})
    return {k.upper(): float(v) for k, v in data.items() if v}


def _save_quotes(quotes: dict[str, float]):
    os.makedirs(os.path.dirname(QUOTES_PATH) or ".", exist_ok=True)
    with open(QUOTES_PATH, "w") as f:
        json.dump(quotes, f, indent=2, sort_keys=True)


def _load_market_caps():
    data = _load_json(PRESCREENER_PATH, {})
    caps = {}
    if isinstance(data, dict):
        for sym, info in data.items():
            if isinstance(info, dict) and "market_cap" in info:
                try:
                    caps[sym.upper()] = float(info["market_cap"])
                except (TypeError, ValueError):
                    pass
    return caps


def _append_curve(today: str, equity: float):
    curve = _load_json(CURVE_PATH, [])
    curve.append({
        "date": today,
        "equity": equity,
        "timestamp": datetime.utcnow().isoformat(),
    })
    os.makedirs(os.path.dirname(CURVE_PATH) or ".", exist_ok=True)
    with open(CURVE_PATH, "w") as f:
        json.dump(curve, f, indent=2)


def _build_cik_map(symbols: list[str]) -> dict[str, str]:
    try:
        tickers = fetch_company_tickers()
        return {s: tickers[s] for s in symbols if s in tickers}
    except Exception as exc:
        log.warning("CIK lookup failed: %s", exc)
        return {}


def _is_market_hours() -> bool:
    """True if current UTC time is within US market-adjacent hours (12-22 UTC)."""
    h = datetime.utcnow().hour
    wd = datetime.utcnow().weekday()
    return wd < 5 and 12 <= h < 22


# ── cycle ──────────────────────────────────────────────────────────────

class CycleResult:
    def __init__(self):
        self.events_detected: list = []
        self.scores: list[dict] = []
        self.opens_planned: list[dict] = []
        self.exits_planned: list[dict] = []
        self.errors: list[str] = []
        self.filings_scanned: int = 0
        self.new_filings: int = 0


def run_cycle(*, dry_run: bool = True, max_poll: int = POLL_CAP) -> CycleResult:
    """One complete Achilles 12-step cycle."""
    result = CycleResult()
    today = date.today().isoformat()
    now_iso = datetime.utcnow().isoformat()

    # ── 1. Safety ──
    if kill_switch_active():
        log.critical("KILL_SWITCH active — aborting")
        result.errors.append("KILL_SWITCH")
        return result

    # ── 2. Restore sleeve ──
    try:
        sleeve = AchillesSleeve.load(SLEEVE_PATH)
    except FileNotFoundError:
        sleeve = AchillesSleeve(initial_cash=1000.0, conservative_mode=False)
    log.info("Sleeve: $%.2f cash, %d positions, $%.2f equity",
             sleeve.cash, len(sleeve.positions), sleeve.equity())

    # ── 3. Floor check ──
    if sleeve.check_hard_floor():
        log.warning("HALTED — below hard floor / drawdown limit")

    # ── 4. Settlements ──
    sleeve.process_settlements(today)

    # ── 5. Cursor ──
    try:
        cursor = cursor_mod.load(CURSOR_PATH)
    except FileNotFoundError:
        cursor = cursor_mod.Cursor()
    log.info("Cursor: date=%s, %d seen accessions", cursor.cursor_date, len(cursor.seen))

    # ── 6. Watchlist ──
    watchlist = build_watchlist(
        activist_13d=_symbols_from_cache(ACTIVIST_PATH),
        insider_clusters=_symbols_from_cache(INSIDER_PATH),
        smart_money=_symbols_from_cache(SMART_MONEY_PATH),
        broad_screen=_symbols_from_cache(SCREEN_PATH),
    )
    poll_list = watchlist[:max_poll]
    log.info("Watchlist: %d symbols, polling top %d", len(watchlist), len(poll_list))

    # ── 7. Poll EDGAR ──
    cik_map = _build_cik_map(poll_list)
    log.info("CIK resolved: %d / %d", len(cik_map), len(poll_list))

    all_filings = []
    poll_errors = 0
    for i, sym in enumerate(poll_list):
        cik = cik_map.get(sym)
        if not cik:
            continue
        try:
            payload = fetch_submissions(cik)
            filings = parse_submissions_recent(payload, symbol=sym)
            all_filings.extend(filings)
        except Exception as exc:
            poll_errors += 1
            if poll_errors <= 5:
                log.debug("Poll %s failed: %s", sym, exc)
        if (i + 1) % 50 == 0:
            log.info("  polled %d / %d symbols...", i + 1, len(poll_list))

    result.filings_scanned = len(all_filings)
    new_filings = cursor_mod.filter_new(cursor, all_filings)
    new_filings = cursor_mod.register_events(cursor, new_filings)
    result.new_filings = len(new_filings)
    log.info("Filings: %d scanned, %d new (cursor advanced to %s)",
             len(all_filings), len(new_filings), cursor.cursor_date)

    # ── 8. Classify & refine ──
    playbooks = build_playbooks()
    events = []
    form4_txns = []

    # Load Oracle research data for quality scoring and insider cross-reference
    dossier_convictions = load_dossier_convictions()
    prescreener_quality = load_prescreener_quality()
    oracle_insider_activity = load_insider_activity()
    screen_scores = load_screen_scores()
    log.info("Oracle data: %d dossiers, %d prescreener, %d insider clusters, %d screen",
             len(dossier_convictions), len(prescreener_quality),
             len(oracle_insider_activity), len(screen_scores))

    for filing in new_filings:
        try:
            if filing.form.strip() in ("4", "4/A"):
                try:
                    body = fetch_body(filing)
                    txns = parse_form4(body, accession_no=filing.accession_no)
                    form4_txns.extend(txns)
                except Exception:
                    pass
                continue

            labels = classify_filing(filing)
            needs_body = any(
                l in ("guidance_revision", "spinoff_window_candidate", "earnings_reaction")
                for l in labels
            )
            body_text = ""
            if needs_body:
                try:
                    body_text = fetch_body(filing)
                except Exception:
                    pass

            # For earnings 8-Ks: fetch actual surprise data from broker
            earnings_surprise = None
            surprise_pct = None
            insider_boost = 1.0

            if "earnings_reaction" in labels:
                sym = (filing.symbol or "").upper()
                if sym:
                    earnings_surprise = fetch_earnings_surprise(sym)
                    if earnings_surprise:
                        if not is_actionable_beat(earnings_surprise):
                            log.info("  %-6s earnings: %s (surprise=%.1f%%) — skipping",
                                     sym,
                                     "miss" if not earnings_surprise.is_beat else "out of range",
                                     earnings_surprise.surprise_pct)
                            # Still process non-earnings labels from same filing
                            labels = [l for l in labels if l != "earnings_reaction"]
                            if not labels:
                                continue
                        else:
                            surprise_pct = earnings_surprise.surprise_pct
                            log.info("  %-6s earnings BEAT: %.1f%% surprise (actual=%.2f est=%.2f)",
                                     sym, surprise_pct,
                                     earnings_surprise.actual_eps,
                                     earnings_surprise.estimate_eps)

                    # Pre-earnings insider cross-reference
                    has_insider, boost = has_insider_preactivity(
                        sym,
                        insider_activity=oracle_insider_activity,
                        filing_date=filing.filing_date,
                    )
                    if has_insider:
                        insider_boost = boost
                        log.info("  %-6s insider pre-activity detected: boost=%.2f", sym, boost)

            filing_events = build_event_for_filing(
                filing, body_text=body_text, today=today,
                surprise_pct=surprise_pct,
                earnings_surprise=earnings_surprise,
                insider_boost=insider_boost,
            )
            events.extend(filing_events)
        except Exception as exc:
            log.warning("Classify failed for %s: %s", filing.accession_no, exc)

    if form4_txns:
        clusters = aggregate_insider_clusters(form4_txns)
        events.extend(clusters)
        log.info("Form 4: %d txns → %d clusters", len(form4_txns), len(clusters))

    result.events_detected = events
    if events:
        log.info("Events detected: %d", len(events))
        for ev in events:
            log.info("  %-20s %-6s strength=%.2f", ev.event_class, ev.symbol, ev.strength)

    # ── 9. Score ──
    # Fetch fresh quotes from broker if available, merge with cache
    quotes = _load_quotes()
    need_quotes = set()
    for ev in events:
        need_quotes.add(ev.symbol)
    for pos in sleeve.positions.values():
        need_quotes.add(pos.symbol)
    if need_quotes:
        live_quotes = broker.get_quotes(sorted(need_quotes))
        if live_quotes:
            quotes.update(live_quotes)
            _save_quotes(quotes)
            log.info("Broker quotes: %d fresh prices", len(live_quotes))

    market_caps = _load_market_caps()
    if need_quotes - set(market_caps):
        live_caps = broker.get_market_caps(sorted(need_quotes - set(market_caps)))
        if live_caps:
            market_caps.update(live_caps)
            log.info("Broker fundamentals: %d market caps", len(live_caps))

    scored_briefs = []

    for ev in events:
        pb = playbooks.get(ev.event_class)
        if not pb or pb.disabled:
            continue

        mcap = market_caps.get(ev.symbol, 500_000_000)
        if ev.event_class == "earnings_reaction":
            cq = 1.0
        else:
            cq = oracle_company_quality(
                ev.symbol,
                dossier_convictions=dossier_convictions,
                prescreener_quality=prescreener_quality,
                screen_scores=screen_scores,
            )
        score_out = score_event(
            playbook=pb,
            event_strength=ev.strength,
            company_quality=cq,
            market_cap=mcap,
            first_seen_iso=now_iso,
            disqualifier_flags=ev.metadata.get("disqualifiers", []),
        )
        result.scores.append({
            "symbol": ev.symbol,
            "event_class": ev.event_class,
            "score": score_out["score"],
            "components": score_out["components"],
        })

        if score_out["score"] < 0.05:
            continue

        entry_price = quotes.get(ev.symbol)
        if not entry_price or entry_price <= 0:
            log.info("  %-6s score=%.3f — awaiting quote", ev.symbol, score_out["score"])
            continue

        play = build_play(
            pb, entry_price, today,
            sleeve.position_dollars(score_out["score"]),
        )
        brief = make_brief(
            event_id=ev.event_id,
            event_class=ev.event_class,
            symbol=ev.symbol,
            score=score_out["score"],
            play=play,
        )
        scored_briefs.append((brief, entry_price, ev))

    # ── 10. Open ──
    for brief, entry_price, ev in scored_briefs:
        plan = plan_open(sleeve, brief, today=today, current_price=entry_price)
        if plan is None:
            continue

        result.opens_planned.append(plan)

        if dry_run:
            log.info("DRY-RUN BUY  %-6s $%.0f @ $%.2f  %s  score=%.3f",
                     plan["symbol"], plan["dollars"], plan["entry_price"],
                     plan["event_class"], plan["score"])
        else:
            order_result = broker.buy_fractional(plan["symbol"], plan["dollars"])
            if not order_result or not order_result.get("id"):
                log.error("Broker order failed for %s — skipping", plan["symbol"])
                continue
            append_order(LEDGER_PATH, OrderRecord(
                order_id=order_result["id"], symbol=plan["symbol"],
                side="buy", dollars=plan["dollars"], date=today,
            ))
            pos = sleeve.open(
                event_id=plan["event_id"], symbol=plan["symbol"],
                event_class=plan["event_class"], entry_price=plan["entry_price"],
                score=plan["score"], hard_stop_price=plan["hard_stop_price"],
                profit_target_price=plan["profit_target_price"],
                time_stop_date=plan["time_stop_date"], today=today,
            )
            if pos:
                journal_append(JOURNAL_PATH, TradeEntry(
                    timestamp=now_iso, event_id=plan["event_id"],
                    event_class=plan["event_class"], symbol=plan["symbol"],
                    action="open", price=plan["entry_price"],
                    shares=pos.shares, dollars=plan["dollars"],
                ))
                log.info("OPENED %-6s %.1f sh @ $%.2f (order %s)",
                         plan["symbol"], pos.shares, plan["entry_price"], order_result["id"])

    # ── 11. Exits ──
    if sleeve.positions:
        exit_plans = plan_exits(sleeve, quotes, today)
        result.exits_planned = exit_plans
        for ep in exit_plans:
            if dry_run:
                log.info("DRY-RUN SELL %-6s reason=%s @ $%.2f",
                         ep["symbol"], ep["reason"], ep["exit_price"])
            else:
                order_result = broker.sell_fractional(ep["symbol"], ep["shares"])
                if not order_result or not order_result.get("id"):
                    log.error("Broker sell failed for %s — skipping", ep["symbol"])
                    continue
                append_order(LEDGER_PATH, OrderRecord(
                    order_id=order_result["id"], symbol=ep["symbol"],
                    side="sell", dollars=ep["shares"] * ep["exit_price"], date=today,
                ))
                realized = sleeve.close(ep["event_id"], exit_price=ep["exit_price"], today=today)
                if realized is not None:
                    journal_append(JOURNAL_PATH, TradeEntry(
                        timestamp=now_iso, event_id=ep["event_id"],
                        event_class="", symbol=ep["symbol"],
                        action="close", price=ep["exit_price"],
                        shares=ep["shares"],
                        dollars=ep["shares"] * ep["exit_price"],
                        reason=ep["reason"], pnl=realized,
                    ))
                    log.info("CLOSED %-6s pnl=$%.2f reason=%s (order %s)",
                             ep["symbol"], realized, ep["reason"], order_result["id"])

    # ── 12. Persist ──
    sleeve.save(SLEEVE_PATH)
    cursor_mod.save(CURSOR_PATH, cursor)
    _append_curve(today, sleeve.equity())
    log.info("Persisted. Equity=$%.2f", sleeve.equity())

    return result


# ── output ─────────────────────────────────────────────────────────────

def print_summary(r: CycleResult) -> str:
    lines = []
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"{'=' * 56}")
    lines.append(f"ACHILLES CYCLE — {ts}")
    lines.append(f"{'=' * 56}")
    lines.append(f"Filings scanned : {r.filings_scanned}")
    lines.append(f"New filings     : {r.new_filings}")
    lines.append(f"Events detected : {len(r.events_detected)}")

    if r.events_detected:
        by_cls: dict[str, int] = {}
        for ev in r.events_detected:
            by_cls[ev.event_class] = by_cls.get(ev.event_class, 0) + 1
        for cls, n in sorted(by_cls.items()):
            lines.append(f"  {cls}: {n}")

    if r.scores:
        lines.append(f"Scored          : {len(r.scores)}")
        top = sorted(r.scores, key=lambda x: -x["score"])[:5]
        for s in top:
            lines.append(f"  {s['event_class']:20s} {s['symbol']:6s} {s['score']:.3f}")

    if r.opens_planned:
        lines.append(f"Opens planned   : {len(r.opens_planned)}")
        for o in r.opens_planned:
            lines.append(f"  BUY  {o['symbol']:6s} ${o['dollars']:.0f} @ ${o['entry_price']:.2f}")

    if r.exits_planned:
        lines.append(f"Exits planned   : {len(r.exits_planned)}")
        for e in r.exits_planned:
            lines.append(f"  SELL {e['symbol']:6s} {e['reason']}")

    if r.errors:
        lines.append(f"Errors          : {', '.join(r.errors)}")

    lines.append(f"{'=' * 56}")
    text = "\n".join(lines)
    print(text)
    return text


# ── main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Achilles constant monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--loop", action="store_true",
                        help="Run continuously on an interval")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Seconds between cycles (default {DEFAULT_INTERVAL})")
    parser.add_argument("--max-poll", type=int, default=POLL_CAP,
                        help=f"Max symbols to poll per cycle (default {POLL_CAP})")
    parser.add_argument("--market-hours-only", action="store_true",
                        help="Skip cycles outside US market hours (12-22 UTC)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-5s %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    dry_run = not is_live("achilles")
    mode = "LIVE" if not dry_run else "DRY-RUN"
    log.info("Achilles monitor — %s — interval %ds", mode, args.interval)

    if broker.login():
        log.info("Broker connected — live quotes enabled")
    else:
        log.info("Broker unavailable — using cached quotes only")

    running = True

    def _stop(sig, _frame):
        nonlocal running
        log.info("Signal %d received, stopping after this cycle", sig)
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    while running:
        if args.market_hours_only and not _is_market_hours():
            log.info("Outside market hours, sleeping %ds", args.interval)
        else:
            try:
                r = run_cycle(dry_run=dry_run, max_poll=args.max_poll)
                print_summary(r)
            except Exception:
                log.exception("Cycle failed")

        if not args.loop:
            break

        for _ in range(args.interval):
            if not running:
                break
            time.sleep(1)

    broker.logout()
    log.info("Monitor stopped")


if __name__ == "__main__":
    main()
