# /delphi-ghost — paper-only learning shadow

Ghost Delphi runs Delphi's sector/momentum screen but **places no orders and
touches no real sleeve**. It opens a paper position for *every* screened
candidate it can price, marks the book to market, and grades the forward return
over a momentum holding window (~90 days). The payoff is whether Delphi's signals
actually predict returns:

  - **per-sector return** — did the rotation pick the right sectors?
  - **momentum terciles** — does higher momentum -> higher forward return?
  - **score terciles** — is the composite `0.6*momentum + 0.4*quality` monotonic?

State: `cache/ghost_delphi_ledger.json` + `cache/ghost_delphi_curve.json`,
persisted under god name `ghost_delphi`. Engine is `shared.ghost`; Delphi bits in
`delphi.ghost`.

## Steps

1. **Restore the ledger.** `shared.ghost.load_ledger("cache/ghost_delphi_ledger.json")`.

2. **Open paper positions for every candidate.** Run Delphi's screen
   (`delphi.screener.screen_universe`), flatten the per-sector candidate lists,
   fetch a quote per symbol, and `delphi.ghost.candidates_to_ghost(cands,
   price_lookup)` (skips blocked names). Then `shared.ghost.open_entries(...)`.
   Keep to liquid names.

3. **Mark to market.** `shared.ghost.mark_to_market(ledger, price_lookup)` +
   `append_equity_point(curve, today, snapshot, benchmark={"SPY": r})`; save the curve.

4. **Grade matured positions.** `shared.ghost.grade_entries(ledger, price_lookup,
   today=…)`. Unpriceable names grade as a loss (survivorship guard).

5. **Report.** `delphi.ghost.signal_report(ledger)` → `sector_return`,
   `momentum_terciles`, `score_terciles` (each with a `monotonic` flag). Write to
   `cache/ghost_delphi_report.json`. If momentum terciles aren't monotonic on a
   real `n`, the core premise isn't holding — investigate before trusting it.

6. **Persist.** `shared.ghost.save_ledger(...)`, then
   `pantheon.persist("ghost_delphi", {…ledger, curve, report…}, branch="claude/live")`.

## Hard rules

- NEVER place a broker order. NEVER touch the real `delphi_*` sleeve/ledger.
- Treat tercile monotonicity as evidence, not proof, until `n` is large.
