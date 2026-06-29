# /oracle-score — score and trade from existing dossiers

Runs steps 7–12 of `/oracle` only — assumes dossiers are already fresh.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Safety check.** Run `python -c "from shared.guards import kill_switch_active; assert not kill_switch_active(), 'KILL_SWITCH present — liquidate'"`. If a `KILL_SWITCH` file exists, liquidate all positions via the broker and stop. Then check `shared.guards.is_live("oracle")` — if `ORACLE_LIVE` env var is not exactly `"true"`, run in **paper mode**: compute everything normally but **do not place broker orders** in step 6. Log the planned orders to the decision log so they can be reviewed. Print "PAPER MODE — no orders placed" prominently.
2. Restore sleeve from `cache/oracle_sleeve.json`.
3. Load dossiers from `cache/oracle_dossiers.json`. Refresh `current_price` for each via Robinhood quotes.
4. Rescore via `oracle.research.rescore_dossier`.
5. Apply rotation rules (`oracle.positioning.rotation_decision`) — incumbent stays unless challenger >= 1.25x score.
6. **Pre-trade sanity check.** Fetch the broker's actual equity positions, then filter through `shared.guards.filter_broker_to_gods(broker_positions)` to strip out pre-existing personal positions. Pass the filtered result to `shared.guards.pre_trade_check(filtered)`. If any symbol is out of sync, **halt trading and run `/oracle-reconcile`** before proceeding. Then `size_book` -> `plan_orders` -> place orders via broker, log to ledger.
7. Journal each decision.
8. Apply thesis-anchored exit checks via `oracle.exits.exit_signal`.
9. Persist.

DO NOT do net-new research here — only the scoring/trading path.
