# /delphi-ghost — paper-only learning shadow

Ghost Delphi runs Delphi's sector/momentum screen but **places no orders and
touches no real sleeve**. It opens a paper position for *every* screened
candidate it can price, marks the book to market, and grades the forward return
over a momentum holding window (~90 days). The payoff is whether Delphi's signals
actually predict returns:

  - **per-sector return** — did the rotation pick the right sectors?
  - **momentum terciles** — does higher momentum -> higher forward return?
  - **regime return** — did risk-off periods actually avoid losses?
  - **rotation lift** — do chosen-sector names outperform unchosen ones?

State: `cache/ghost_delphi_ledger.json` + `cache/ghost_delphi_curve.json`,
persisted under god name `ghost_delphi`. Engine is `shared.ghost`; Delphi bits in
`delphi.ghost`.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Restore the ledger.** `shared.ghost.load_ledger("cache/ghost_delphi_ledger.json")`.

2. **Open paper positions for every candidate.** Run Delphi's screen
   (`delphi.screener.screen_universe`), flatten the per-sector candidate lists,
   fetch a quote per symbol, and compute the rotation plan. Pass **all** candidates
   (not just chosen sectors) to `delphi.ghost.candidates_to_ghost(cands,
   price_lookup, regime=plan["regime"], chosen_sectors=plan["sectors"])` — this
   stamps each candidate with the current regime and whether its sector was chosen,
   so the report can test rotation accuracy. Skips blocked names.
   Then `shared.ghost.open_entries(...)`. Keep to liquid names.

3. **Mark to market.** `shared.ghost.mark_to_market(ledger, price_lookup)` +
   `append_equity_point(curve, today, snapshot, benchmark={"SPY": r})`; save the curve.

4. **Grade matured positions.** `shared.ghost.grade_entries(ledger, price_lookup,
   today=…)`. Unpriceable names grade as a loss (survivorship guard).

5. **Report.** `delphi.ghost.signal_report(ledger)` →
   - **`momentum_terciles`** — does higher momentum predict higher forward return?
     If not monotonic on a real `n`, the core premise isn't holding — investigate
     before trusting it.
   - **`sector_return`** — per-sector mean return. Which sectors generate alpha?
   - **`regime_return`** — per-regime mean return (risk_on/neutral/cautious/risk_off).
     If risk-off periods show positive returns, the regime filter is costing you
     money. If risk-off shows large negative returns, the filter is saving you.
   - **`rotation_lift`** — `chosen` boolean: do names in chosen sectors outperform
     names in unchosen sectors? This is the direct test of whether sector rotation
     adds value over buy-all.
   Write to `cache/ghost_delphi_report.json`.

6. **Persist.** `shared.ghost.save_ledger(...)`, then
   `pantheon.persist("ghost_delphi", {…ledger, curve, report…}, branch="claude/live")`.

## Hard rules

- NEVER place a broker order. NEVER touch the real `delphi_*` sleeve/ledger.
- Treat tercile monotonicity as evidence, not proof, until `n` is large.
- Open candidates from ALL sectors (not just chosen ones) so rotation accuracy
  is testable. The ghost buys unchosen sectors too — that's the control group.
