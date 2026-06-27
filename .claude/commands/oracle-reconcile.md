# /oracle-reconcile — broker fill reconcile

Reconcile each god's sleeve against the broker's filled orders since the
last reconcile. Works across all three gods.

## Steps

For each god in (oracle, delphi, achilles):

1. Restore the sleeve from its JSON cache.
2. Read this god's order ledger (`cache/<god>_ledger.jsonl`).
3. Fetch broker orders via Robinhood MCP `get_equity_orders` for account 563854249, filtering to recent state.
4. Filter broker orders to ones in our ledger via `shared.guards.filter_orders_by_ledger`. **CRITICAL**: empty ledger -> empty result; never claim broker orders that aren't ours.
5. For each newly-filled order:
   - If the corresponding sleeve action isn't already reflected, apply it (buy/sell with the actual filled price + shares).
   - Achilles uses event_id keys; map from order via the metadata stored in the ledger.
6. Save each updated sleeve.
7. Persist via `pantheon.persist(god, ...)`.

## Idempotency

If a fill is already reconciled (the sleeve already has the position at the
filled price), skip it. The ledger should track `reconciled` state.
