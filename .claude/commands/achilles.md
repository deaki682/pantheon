# /achilles — full Achilles pass

Event-driven, short-horizon. Runs frequently (multiple times per day).
12 steps.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Safety check.** Refuse if `KILL_SWITCH` exists. Liquidate all event positions if so.

2. **Restore.** Load `cache/achilles_sleeve.json`. If absent, create an `AchillesSleeve(initial_cash=1000)`.

3. **Floor check.** `sleeve.check_hard_floor()`. If True, do not open new positions. Continue to exits but no opens.

4. **Process settlements.**

5. **Restore cursor.** `achilles.cursor.load("cache/achilles_cursor.json")`.

6. **Build watchlist.** `achilles.watchlist.build_watchlist(...)` reading from Oracle screen caches (`cache/oracle_activist_13d.json`, `cache/oracle_insider_clusters.json`, `cache/oracle_smart_money.json`, `cache/oracle_screen.json`, `cache/oracle_prescreener.json`). Cap at 800.

7. **Poll EDGAR.** For each watchlist symbol, fetch submissions. Filter via `cursor.filter_new` (strict greater-than). Register batch via `cursor.register_events` to advance cursor + dedup.

8. **Classify and refine.** For each new filing:
   - `achilles.classify.classify_filing` -> labels.
   - For guidance/spinoff: read body via `shared.edgar.fetch_body` and refine via `achilles.events.refine_guidance` / `refine_spinoff`.
   - Form 4s get aggregated across symbol-window via `achilles.events.aggregate_insider_clusters`.

9. **Score each event.** Use the matching playbook from `achilles.playbooks.build_playbooks()`. Compute company_quality (from Oracle's prescreener cache or fundamentals), market_cap (from broker fundamentals), first_seen_iso (when Achilles first observed the event). `achilles.scoring.score_event(...)`.

10. **Write brief and (maybe) open.** For each event with score >= 0.05:
    - `achilles.brief.build_play(playbook, entry_price, today, entry_dollars=sleeve.position_dollars(score))`.
    - `make_brief(...)`. Validate via `brief_check.validate_brief`.
    - `plan_open(...)`. If non-None, place market order via Robinhood, append to `cache/achilles_ledger.jsonl`, record open via `journal.append`.

11. **Exits.** `plan_exits(sleeve, quotes, today)`. Place sell market orders for any triggered. Record close in journal. Update `playbooks` attribution (`record_outcome`, `maybe_autodisable`).

12. **Persist.** Save sleeve + cursor + curve. `pantheon.persist("achilles", ...)`.

## Halt path

Sticky $600 floor or 40% drawdown -> permanent halt. Only `sleeve.manual_reset()` can clear (operator-only).
