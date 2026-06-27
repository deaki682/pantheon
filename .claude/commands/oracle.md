# /oracle — full Oracle pass

Run Oracle's complete cycle: restore state, research, score, execute, journal,
attribute, allocate capital, persist. 12 steps. Fail-safe — if any step
breaks, skip the cycle and open a PR; never silently patch the codebase.

## Steps

1. **Safety check.** Run `python -c "from shared.guards import kill_switch_active; assert not kill_switch_active(), 'KILL_SWITCH present — liquidate'"`. If a `KILL_SWITCH` file exists, liquidate all positions via the broker and stop.

2. **Restore state.** Read `cache/oracle_sleeve.json`. If absent, call `/oracle-setup` first.

3. **Process settlements.** Advance `sleeve.process_settlements(today)`; today is UTC date.

4. **Broker reconcile.** Call `/oracle-reconcile` to sync any pending fills since last run.

5. **Should we research?** Use `oracle.calendar.should_run(cache/oracle_cadence.json, "research", interval_days=3)`. If False, skip to step 7.

6. **Research pass.** For 8–15 candidates from the screen cache (`cache/oracle_screen.json`), build dossiers via `oracle.research.make_dossier`. Each dossier MUST validate. Persist to `cache/oracle_dossiers.json`. Cite SEC filings on every dossier.

7. **Rescore and rank.** Walk every dossier; refresh `current_price` via broker quotes; rescore; sort by `derived.potential_score`.

8. **Size positions.** `oracle.positioning.size_book(scored, equity=sleeve.equity(marks))`. Apply per-name 15%, per-sector 35%, 10% cash floor, $50 min ticket.

9. **Plan and place orders.** `oracle.execution.plan_orders(sleeve, targets, prices)`. For each order, check the ledger (`shared.guards.already_placed_today`). Place fractional-share market orders via Robinhood MCP. Append each order to `cache/oracle_ledger.jsonl`.

10. **Journal decisions.** Every buy/sell/hold/avoid gets a `JournalEntry` via `oracle.journal.append`. Grade any prior entries whose horizon has elapsed using actual prices.

11. **Attribute and allocate.** Compute factor regression vs MTUM/QUAL/IWM/VTV with `oracle.attribution.factor_regression`. Update target capital with `oracle.capital.compute_allocation`. Inject/withdraw cash to match.

12. **Persist.** Save `cache/oracle_sleeve.json`, append to `cache/oracle_curve.json` (equity timestamp), then call `pantheon.persist("oracle", files, branch="claude/live")`.

## Halt conditions

- Circuit breaker hit (`sleeve.check_circuit_breakers` returns "halt"). Set `sleeve.halted = True`, stop opening, exit positions if appropriate.
- Code-level error: catch, log to `cache/oracle_errors.jsonl`, OPEN A PR. Do not auto-patch.
