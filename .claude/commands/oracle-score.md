# /oracle-score — score and trade from existing dossiers

Runs steps 7–12 of `/oracle` only — assumes dossiers are already fresh.

## Steps

1. Restore sleeve from `cache/oracle_sleeve.json`.
2. Load dossiers from `cache/oracle_dossiers.json`. Refresh `current_price` for each via Robinhood quotes.
3. Rescore via `oracle.research.rescore_dossier`.
4. Apply rotation rules (`oracle.positioning.rotation_decision`) — incumbent stays unless challenger >= 1.25x score.
5. `size_book` -> `plan_orders` -> place orders via broker, log to ledger.
6. Journal each decision.
7. Apply thesis-anchored exit checks via `oracle.exits.exit_signal`.
8. Persist.

DO NOT do net-new research here — only the scoring/trading path.
