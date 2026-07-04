# /oracle — full Oracle pass (cohort model)

Run Oracle's complete cycle: restore state, load cohort, research, check
thesis-breaks, execute, journal, attribute, allocate capital, persist.
Fail-safe — if any step breaks, skip the cycle and open a PR; never
silently patch the codebase.

Oracle uses a **batch-and-hold cohort model**: positions are selected once
per cohort (~12-month horizon) and held until review. During the hold
period, exits happen ONLY on thesis-break conditions — never on rank drift
or dossier score freshness.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Safety check.** Run `python -c "from shared.guards import kill_switch_active; assert not kill_switch_active(), 'KILL_SWITCH present — liquidate'"`. If a `KILL_SWITCH` file exists, liquidate all positions via the broker and stop. Then check `shared.guards.is_live("oracle")` — if `ORACLE_LIVE` env var is not exactly `"true"`, run in **paper mode**: compute everything normally but **do not place broker orders** in step 10. Log the planned orders to the decision log so they can be reviewed. Print "PAPER MODE — no orders placed" prominently.

2. **Restore state.** Read `cache/oracle_sleeve.json`. If absent, call `/oracle-setup` first.

3. **Load cohort.** `oracle.cohort.load_cohort("cache/oracle_cohort.json")`. If None, this is the first run or post-review — a new cohort will be created in step 9.

4. **Process settlements.** Advance `sleeve.process_settlements(today)`; today is UTC date.

5. **Broker reconcile.** Call `/oracle-reconcile` to sync any pending fills since last run. **NOTE:** If the ledger (`cache/oracle_ledger.jsonl`) is empty, reconcile is a no-op — do not add broker positions to the sleeve. The broker holds many pre-existing positions that are NOT Oracle's. Only ledger-tracked orders belong to Oracle.

6. **Should we research?** TWO gates, both must pass (pool floor added 2026-07-04, operator directive — the pool sits at 93 against a 60–80 target; research machinery is frozen at current size until cohort-1 produces graded calls):
   - (a) `oracle.calendar.should_run(cache/oracle_cadence.json, "research", interval_days=3)`, AND
   - (b) the dossier pool has decayed below **70** live dossiers (count `cache/oracle_dossiers.json`; stale/dropped dossiers don't count toward the floor).
   If either gate fails, skip to step 8. Research keeps the dossier pool fresh for the NEXT cohort — it does NOT trigger position changes in the current cohort.

7. **Research pass.** Same as before — refresh stale dossiers, pick new candidates via `oracle.screener.pick_candidates`, build balanced dossiers via `oracle.research.make_dossier`. The goal is to accumulate 60–100 dossiers across passes so the next cohort selection has real choice. Persist to `cache/oracle_dossiers.json`. **Market data verification:** For each dossier, fetch the current price from `get_equity_quotes` and `high_52_weeks` from `get_equity_fundamentals`, then pass both as `broker_price=` and `broker_high_52w=` to `make_dossier`.

8. **Rescore (calibration only).** Walk every dossier; refresh `current_price` via broker quotes; rescore. This is for calibration and learning — rescoring does NOT drive trading decisions during a cohort hold period.

9. **Cohort logic.** Three branches:

   **A. No active cohort (first run or post-review):** Create a new cohort.
   - **Deep verification of the finalists (mandatory — added 2026-07-03).**
     A cohort locks ~8 names for a YEAR; the selection moment is where
     Oracle's entire annual risk concentrates, so it gets the deep-read
     standard (the pattern proven on Nemesis). Take the top ~15 dossiers
     by conviction and, for each: dispatch extraction subagents to
     re-verify the dossier's load-bearing claims against CURRENT filings
     and prices (the thesis was written weeks ago — has a 10-Q since
     contradicted it?), then one adversarial refuter attacking the
     deciding judgment — *is the bad news actually priced in?* — and the
     scenario probabilities. Fold non-flipping corrections in via
     `oracle.research.update_scenarios(d, new_scenarios, current_price=…)`;
     a refuted dossier is rescored (and may drop out of the top 8) BEFORE
     selection, never patched afterward.
   - **3-draw median conviction for boundary names (mandatory since
     2026-07-04).** Per the decision-consistency sweep
     (docs/pantheon_decision_consistency_results_2026-07.md): conviction
     re-scored blind from stored narrative alone flipped the actual
     top-5 selection on 2 of 5 independent draws — conviction is the
     mechanical input to `size_book`'s ranking, so this instability is
     load-bearing, not cosmetic. For any name within the bottom 2 slots
     of the cut line (i.e. whose inclusion/exclusion decides the
     cohort), get 2 additional independent conviction re-scores from the
     SAME dossier narrative (un-anchored) and take the median of the 3
     before the cut is final. Names far from the cut line do not need
     this — the finding was about boundary noise, not universal
     unreliability. Only then:
   - `oracle.positioning.size_book(scored, equity=sleeve.equity(marks))` → targets
   - `oracle.execution.plan_orders(sleeve, targets, prices)` → initial buy orders
   - `oracle.cohort.create_cohort(cohort_id, selected_dossiers, prices, inception_date=today, review_date=today+365)` → save to `cache/oracle_cohort.json`
   - Tag each sleeve position with `pos.cohort_id = cohort.cohort_id`

   **B. Active cohort, not at review date:** Check thesis-breaks, then top up.
   - For each symbol in `cohort.active_symbols()`:
     - Fetch current price
     - `oracle.cohort.check_thesis_break(sym, cohort, current_price=px, dossier=d)` — also pass `insider_reversal`, `fraud_flag`, `going_concern_flag`, `thesis_exhausted` if detected during research
     - **Refute before you sell (mandatory — added 2026-07-03).** A
       thesis-break sell ends a 12-month position early; the known
       failure mode is panic-selling a headline. If the returned break is
       judgment-based (`fraud`, `going_concern`, `insider_reversal`,
       `thesis_exhausted`, `thesis_break`): dispatch ONE adversarial
       subagent to argue AGAINST the break — is the "fraud" an
       unconfirmed short report? Is the going-concern language actually
       in the filing or only in a news paraphrase? Is the insider selling
       10b5-1-scheduled rather than discretionary? Sell only if the break
       case survives the attack, and journal the refuter's argument
       either way. The `drawdown` break (≥40% from entry) is ARITHMETIC —
       it executes immediately, no debate; discipline rules there.
     - If thesis-break returned (and survived refutation where required): `oracle.cohort.record_exit(cohort, sym, exit_price=px, exit_date=today, exit_reason=reason)`; remove from `cohort_holds`
   - `cohort_holds = set(cohort.active_symbols())`
   - **Top up idle cash.** If `sleeve.cash > CASH_FLOOR * sleeve.equity(marks) + MIN_TICKET`, there's deployable excess cash (e.g. from a capital injection). Recompute equal-weight targets across the active cohort positions using the current equity, then run `oracle.execution.plan_orders(sleeve, targets, prices, cohort_holds=cohort_holds)` → generates buy orders to bring underweight positions up to target. No new names — only existing cohort symbols get topped up. No mid-cohort replacements — freed thesis-break slots stay as cash.
   - If no excess cash: `oracle.execution.plan_orders(sleeve, targets={}, prices, cohort_holds=cohort_holds)` → only thesis-break exits generate sell orders

   **C. Active cohort at review date** (`oracle.cohort.should_review(cohort, today)`):
   - `oracle.cohort.grade_cohort(cohort, final_prices)` → grade all 8 calls
   - Convert graded results to `JournalEntry` records for the calibration dataset
   - Save closed cohort to `cache/oracle_cohort_history.jsonl`
   - Fall through to branch A to create the next cohort

10. **Pre-trade check and place orders.** Fetch broker equity positions, filter through `shared.guards.filter_broker_to_gods(broker_positions)`. Fetch recent broker orders, compute `shared.guards.pending_shares_from_orders(broker_orders)`. Run `shared.guards.pre_trade_check(filtered, pending_orders=pending)`. If any symbol is out of sync, halt and run `/oracle-reconcile`. Place fractional-share market orders via Robinhood MCP. Append each order to `cache/oracle_ledger.jsonl`.

11. **Journal decisions.** Every buy/sell/hold/avoid gets a `JournalEntry` via `oracle.journal.append`. Grade any prior entries whose horizon has elapsed using actual prices.

12. **Attribute and allocate.** Fetch daily historicals for the 4 factor ETFs (MTUM, QUAL, IWM, VTV) via `get_equity_historicals`. Run `oracle.attribution.compute_factor_attribution(equity_curve, factor_historicals)`. Pass to `oracle.capital.compute_allocation`. Inject/withdraw cash to match.

13. **Persist.** Save `cache/oracle_sleeve.json`, `cache/oracle_cohort.json`, append to `cache/oracle_curve.json` (equity timestamp), then call `pantheon.persist("oracle", files, branch="claude/live")`.

## Thesis-break conditions (the only permitted exits during hold)

1. **fraud** — SEC investigation or fraud allegation filed
2. **going_concern** — bankruptcy filing or going-concern disclosure
3. **insider_reversal** — the same insiders who accumulated begin net-selling
4. **drawdown** — position loss >= 40% from entry price
5. **thesis_exhausted** — original catalyst resolved without price response
6. **thesis_break** — moat AND quality ratings both collapsed below 0.2

## Prohibited exits during hold

- "A new dossier scored higher"
- "The sector is out of favor this month"
- "The position is flat after 60 days"
- Rank drift of any kind

## Halt conditions

- Circuit breaker hit (`sleeve.check_circuit_breakers` returns "halt"). Set `sleeve.halted = True`, stop opening, exit positions if appropriate.
- Code-level error: catch, log to `cache/oracle_errors.jsonl`, OPEN A PR. Do not auto-patch.
