# /oracle — full Oracle pass

Run Oracle's complete cycle: restore state, research, score, execute, journal,
attribute, allocate capital, persist. 12 steps. Fail-safe — if any step
breaks, skip the cycle and open a PR; never silently patch the codebase.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Safety check.** Run `python -c "from shared.guards import kill_switch_active; assert not kill_switch_active(), 'KILL_SWITCH present — liquidate'"`. If a `KILL_SWITCH` file exists, liquidate all positions via the broker and stop. Then check `shared.guards.is_live("oracle")` — if `ORACLE_LIVE` env var is not exactly `"true"`, run in **paper mode**: compute everything normally but **do not place broker orders** in step 9. Log the planned orders to the decision log so they can be reviewed. Print "PAPER MODE — no orders placed" prominently.

2. **Restore state.** Read `cache/oracle_sleeve.json`. If absent, call `/oracle-setup` first.

3. **Process settlements.** Advance `sleeve.process_settlements(today)`; today is UTC date.

4. **Broker reconcile.** Call `/oracle-reconcile` to sync any pending fills since last run. **NOTE:** If the ledger (`cache/oracle_ledger.jsonl`) is empty, reconcile is a no-op — do not add broker positions to the sleeve. The broker holds many pre-existing positions that are NOT Oracle's. Only ledger-tracked orders belong to Oracle.

5. **Should we research?** Use `oracle.calendar.should_run(cache/oracle_cadence.json, "research", interval_days=3)`. If False, skip to step 7.

6. **Research pass.** First, refresh stale dossiers: run `oracle.research.check_staleness(dossiers)` and re-research any flagged name from scratch (older than 14 days or price drifted >20% from scenario anchor). Then, pick new candidates deterministically: call `oracle.screener.pick_candidates("cache/oracle_screen.json", "cache/oracle_dossiers.json", n=40)` — this returns the top undossiered names from the screen sorted by composite score. Do NOT hand-pick — use the list it returns, in order. Research **wider** than the ~8 you'll hold so the dossier scoring, not the screen, selects the book. Build dossiers via `oracle.research.make_dossier`. Build each one **balanced** (see `/oracle-research`): the screen surfaces names insiders are *buying*, which includes both bargains and falling knives. Verify recent price action against **current** sources (not memory) — for any name down >30% from its 52-week high, fetch `high_52w` and supply a `decline_explanation` (the falling-knife gate rejects an *unexplained* big-decliner by design; an explained, priced-in decline is a valid buy). State both the bull and bear case, then judge the deciding question — *is the bad news already priced in?* — and set scenarios to your honest, un-tilted estimate. Each dossier MUST validate. Persist to `cache/oracle_dossiers.json`. Cite SEC filings on every dossier. **Market data verification:** For each dossier, fetch the current price from `get_equity_quotes` and `high_52_weeks` from `get_equity_fundamentals`, then pass both as `broker_price=` and `broker_high_52w=` to `make_dossier`. The validator cross-checks these against LLM-supplied values and rejects on >5% divergence.

7. **Rescore and rank.** Walk every dossier; refresh `current_price` via broker quotes; rescore; sort by `derived.potential_score`.

8. **Size positions.** Pass *all* scored dossiers to `oracle.positioning.size_book(scored, equity=sleeve.equity(marks))` — it ranks by conviction, **selects the best ~8** (`MAX_POSITIONS`), and **equal-weights** them. Caps: per-name 25%, per-sector 35%, 10% cash floor, $50 min ticket. (Conviction-weighting is opt-in via `weighting="conviction"` — only graduate to it once `oracle.learning.calibration_stats` shows high-conviction calls actually outperform.)

9. **Plan and place orders.** First, fetch the broker's actual equity positions, then filter through `shared.guards.filter_broker_to_gods(broker_positions)` to strip out pre-existing personal positions. Also fetch recent broker orders via `get_equity_orders` and compute `shared.guards.pending_shares_from_orders(broker_orders)` to account for queued orders awaiting fill. Pass both to `shared.guards.pre_trade_check(filtered, pending_orders=pending)`. If any symbol's shares are out of sync, **halt trading and run `/oracle-reconcile`** before proceeding. Then `oracle.execution.plan_orders(sleeve, targets, prices)`. For each order, check the ledger (`shared.guards.already_placed_today`). Place fractional-share market orders via Robinhood MCP. Append each order to `cache/oracle_ledger.jsonl`.

10. **Journal decisions.** Every buy/sell/hold/avoid gets a `JournalEntry` via `oracle.journal.append`. Grade any prior entries whose horizon has elapsed using actual prices.

11. **Attribute and allocate.** Fetch daily historicals for the 4 factor ETFs (MTUM, QUAL, IWM, VTV) via `get_equity_historicals` with `interval="day"` covering the equity curve's date range. Then call `oracle.attribution.compute_factor_attribution(equity_curve, factor_historicals)` — it aligns dates, computes returns, and runs the OLS regression end-to-end. If the result has `skipped=True`, log the reason and use defaults (alpha=0, alpha_t=0). Pass the result to `oracle.capital.compute_allocation`. Inject/withdraw cash to match.

12. **Persist.** Save `cache/oracle_sleeve.json`, append to `cache/oracle_curve.json` (equity timestamp), then call `pantheon.persist("oracle", files, branch="claude/live")`.

## Halt conditions

- Circuit breaker hit (`sleeve.check_circuit_breakers` returns "halt"). Set `sleeve.halted = True`, stop opening, exit positions if appropriate.
- Code-level error: catch, log to `cache/oracle_errors.jsonl`, OPEN A PR. Do not auto-patch.
