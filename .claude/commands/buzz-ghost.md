# /buzz-ghost — paper-only validation shadow for Buzz

Ghost Buzz runs Buzz's discovery + confirmation but **places no orders and
touches no real sleeve**. It opens a paper position on *every* accelerating
candidate — confirmed AND unconfirmed — marks the book to market, and grades
each at a 5-trading-day horizon. The payoff is the one thing convergence-Midas
never had: proof, from graded outcomes, of whether each layer earns its place.

State: `cache/ghost_buzz_ledger.json` + `cache/ghost_buzz_curve.json` +
`cache/ghost_buzz_report.json`, persisted under god name `ghost_buzz`. Engine is
`shared.ghost`; Buzz bits in `buzz.ghost`.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — restore `cache/` (own `ghost_buzz` namespace).

1. **Restore the ledger.** `buzz.ghost.load_ledger("cache/ghost_buzz_ledger.json")`.

2. **Open paper positions for every accelerating candidate.** Run Buzz's
   mechanical layer: fetch ApeWisdom → `buzz.acceleration.accelerating`, fetch
   market cap + historicals, `buzz.confirm.confirm`, `buzz.scanner.build_candidate`.
   Keep small/mid-cap names but do NOT drop unconfirmed ones — the ghost needs
   both to test the confirmation gate. Then:
   `buzz.ghost.candidates_to_ghost(candidates, price_lookup, recommended=<LLM picks>, insider_backed=<insider set>)`
   and `buzz.ghost.open_entries(...)`. Pass the LLM `recommended` set and the
   `insider_backed` set from the `/buzz` run if available — those flags are what
   make the LLM and insider layers testable. `skip_open=False` so repeated weekly
   entries are independent samples.

3. **Mark to market.** `buzz.ghost.mark_to_market(ledger, price_lookup)` +
   `append_equity_point(curve, today, snapshot, benchmark={"SPY": r})`; save the curve.

4. **Grade matured positions.** `buzz.ghost.grade_entries(ledger, price_lookup, today=…)`.
   Unpriceable names grade as a loss (survivorship guard).

5. **Report.** `buzz.ghost.buzz_report(ledger)` →
   - **`signal_lift`** — the heart of it. `confirmed` lift answers "does the
     price/volume gate beat raw acceleration?"; `llm_recommended` lift answers
     "do the LLM's picks beat the names it reviewed and passed on?";
     `insider_backed` lift answers "does insider corroboration help?". Keep the
     layers that lift; drop the ones that don't.
   - **`accel_terciles`** — does MORE acceleration predict MORE forward return?
     If it's not monotonic on a real `n`, the core premise is shaky.
   - **`volume_terciles`** — does confirming volume predict returns?
   Write to `cache/ghost_buzz_report.json`.

6. **Persist.** `buzz.ghost.save_ledger(...)`, then
   `pantheon.persist("ghost_buzz", {…ledger, curve, report…}, branch="claude/live")`.

## Hard rules

- NEVER place a broker order. NEVER touch any god's sleeve/ledger.
- Open candidates regardless of the confirmation gate — the unconfirmed names
  are the control group that proves whether confirmation adds lift.
- Treat every lift/tercile as evidence, not proof, until `n` is large. Buzz is
  the noisiest, most adversarial signal in the system — demand a real sample
  before believing any layer, and before anyone discusses promoting Buzz to real
  capital / the Midas name.

## Note on OWNERSHIP_PREFIXES
`ghost_buzz` must be registered in `shared.guards.OWNERSHIP_PREFIXES` (like
`ghost_midas`) for persistence to route correctly.
