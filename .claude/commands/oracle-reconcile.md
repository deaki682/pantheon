# /oracle-reconcile — broker fill reconcile

Reconcile each god's sleeve against the broker's filled orders since the
last reconcile. Works across all three gods.

## CRITICAL RULE: The sleeve is authoritative

The sleeve is the single source of truth for what each god owns. The broker
account contains many positions the gods did NOT place (pre-existing manual
trades, positions from a prior system). **NEVER** add a position to a sleeve
just because the broker holds it. Only the ledger can prove a god placed an
order.

**If the ledger is empty, reconcile is a NO-OP.** Do not look at broker
positions, do not try to match them, do not add them to any sleeve. Return
immediately. An empty ledger means this god has placed zero orders — full stop.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

For each god in (oracle, delphi, achilles):

1. Restore the sleeve from its JSON cache.
2. Read this god's order ledger (`cache/<god>_ledger.jsonl`).
3. **If the ledger is empty, skip this god entirely.** Do not fetch broker orders. Do not touch the sleeve. Move to the next god.
4. Fetch broker orders via Robinhood MCP `get_equity_orders` for account 563854249, filtering to recent state.
5. Filter broker orders to ones in our ledger via `shared.guards.filter_orders_by_ledger`. This returns ONLY orders whose order_id appears in the ledger. If no matches, skip.
6. For each newly-filled order:
   - If the corresponding sleeve action isn't already reflected, apply it (buy/sell with the actual filled price + shares).
   - Achilles uses event_id keys; map from order via the metadata stored in the ledger.
7. Save each updated sleeve.
8. Persist via `pantheon.persist(god, ...)`.

## Idempotency

If a fill is already reconciled (the sleeve already has the position at the
filled price), skip it. The ledger should track `reconciled` state.

## What reconcile must NEVER do

- Add broker positions to a sleeve without a matching ledger entry
- Treat broker positions as belonging to a god just because the symbol exists in the broker
- "Discover" or "sync" positions from the broker into sleeves — only CONFIRM fills for orders the god placed via the ledger
