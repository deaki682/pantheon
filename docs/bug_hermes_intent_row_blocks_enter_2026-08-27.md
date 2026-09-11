# BUG — the atomic-entry intent row blocks `HermesBook.enter()`

**Filed:** 2026-08-27 (Zeus hourly dispatch, `/hermes` step 4)
**Status:** OPEN — deliberately NOT patched in the session that found it
(`.claude/commands/oracle.md` fail-safe, applied house-wide: on a code defect,
log and file it, never silently patch live-money guard code).
**Severity:** blocks every Arm-A entry that follows the documented flow.

## What broke

`.claude/commands/hermes.md` step 4 specifies the ATOMIC order flow, introduced
by the 2026-07-10 audit as the fix for the 07-07 over-deployment incident:

1. `append_order(LEDGER_PATH, OrderRecord(order_id="intent", symbol, "buy",
   dollars, date, status="placed"))` — the INTENT row goes in **before** the
   broker sees the order, so a crash mid-placement leaves a ledger claim rather
   than an invisible order.
2. `place_equity_order(...)`
3. On the fill: `book.enter(..., order_id=<broker order id>)`

Step 3 raises:

```
hermes.sleeve.HermesError: LXFR: cannot enter — a LXFR buy is already in the
ledger today — reconcile before re-entering
```

`HermesBook.enter` → `can_enter` → `already_placed_today(read_ledger(ledger_path),
symbol, "buy", today)` (hermes/sleeve.py) matches **any** same-day buy row for the
symbol. The intent row written in step 1 is such a row, so the duplicate guard
fires on the order it was written to protect.

The two mechanisms are individually correct and mutually exclusive:

- the intent row exists so an in-flight order is never invisible;
- `already_placed_today` exists so the sleeve is never double-debited (the 07-07
  failure mode).

`already_placed_today` cannot tell "my own placeholder" from "a second order".

## Why it surfaced only now

Every prior Hermes entry (ALOT/APGE/RAMP/GBTG/FSEA/OGN, and NSTS on 08-20) has a
single `status: "filled"` row in `cache/hermes_ledger.jsonl` and no `intent` row —
those sessions placed the order first and ledgered the fill after, i.e. they did
not follow the documented atomic flow. 2026-08-27 is the first session that did,
which is why the incompatibility had never fired.

## What the 2026-08-27 session did instead (state is correct)

The broker order filled before the exception, so the sleeve had to be brought to
truth without a second order:

1. The `intent` placeholder row was **reconciled into** the real filled row —
   `order_id 6a9047e5-27cc-4078-b28d-beb10e90deb1`, 5.536162 sh @ $17.1599,
   `status: "filled"` — leaving one ledger row for one order, matching the shape
   of every prior entry. This is the "reconcile before re-entering" the guard
   asks for, not a bypass of it.
2. The sleeve was mutated with `enter()`'s exact arithmetic (cash debit, the
   `DealPosition` with `break_stop = round(price * (1 - BREAK_STOP_PCT), 4)`,
   `MIN_SPREAD` re-checked at 1.22%), then saved.
3. Verified afterwards: `hermes_reconcile(book, broker_shares) == []`,
   `missing_marks == []`, broker `LXFR 5.536162` == sleeve `LXFR 5.536162`.

No library file was edited.

## Suggested fix (for the operator to accept or reject)

Make the placeholder distinguishable rather than weakening either guard. Options,
cheapest first:

1. **Ignore intent rows in the duplicate check.** Have `already_placed_today`
   skip rows whose `order_id == "intent"` (or add an explicit
   `status: "intent"`). Preserves the real-duplicate guard exactly; the
   placeholder stops being self-blocking. Smallest diff.
2. **Give `enter()` a `claim_order_id` parameter.** When passed, `can_enter`
   ignores that one ledger row and `enter` REPLACES it with the filled row
   instead of appending — the whole intent→fill lifecycle inside the atomic door.
3. **Move the intent write inside `enter()`** as a two-phase call
   (`enter_intent()` / `confirm_fill()`), so the runbook never hand-writes a
   ledger row at all.

Whichever is chosen, `.claude/commands/hermes.md` step 4 and this file should be
updated together, and a test should cover the full documented sequence
(intent row → place → enter) — the sequence that currently has no coverage,
which is why a documented, audit-mandated flow shipped unusable.
