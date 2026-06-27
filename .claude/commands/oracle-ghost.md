# /oracle-ghost — paper-only learning shadow

Ghost Oracle runs Oracle's brain (screen + dossiers) but **places no orders and
touches no real sleeve**. It opens a paper position for *every* candidate it can
price — no concentration, no caps, no min-ticket — and grades each one's forward
return at its horizon. The point is **data, not returns**: enough graded outcomes
to measure whether the lenses and conviction actually predict returns, years
before the real (8-name) Oracle ever could.

State lives in its own namespace so it can never corrupt the real book:
`cache/ghost_oracle_ledger.json`, persisted under god name `ghost_oracle`.

## Steps

1. **Restore the ghost ledger.** `oracle.ghost.load_ledger("cache/ghost_oracle_ledger.json")`.

2. **Open new paper positions (breadth, not selection).**
   - From the screen: read `cache/oracle_screen.json` `top` rows, fetch a current
     quote per symbol (Robinhood `get_equity_quotes`), and
     `oracle.ghost.screen_rows_to_candidates(rows, price_lookup)`. Features carry
     the lens flags, so lens lift is measurable.
   - From dossiers (optional): `oracle.ghost.dossiers_to_candidates(dossiers)` —
     features carry `conviction`, so conviction calibration is measurable.
   - `oracle.ghost.open_entries(candidates, existing=ledger, today=…)` and extend
     the ledger. Same-day re-opens are de-duped automatically.
   - **Liquidity:** only open names you could realistically trade (a price/volume
     floor). Microcap paper returns are fantasy and will distort the stats.

3. **Grade matured positions.** `oracle.ghost.grade_entries(ledger, price_lookup,
   today=…)` — fetch a current quote for each ungraded entry whose horizon has
   elapsed. Names that can't be priced (delisted/halted) are graded as a loss
   (survivorship guard), not dropped.

4. **Report.** `oracle.ghost.calibration_report(ledger)` →
   - overall mean return + hit rate (`n` = sample size — the thing that was missing)
   - **per-lens lift**: mean forward return when each lens fired vs not. This is
     how you *empirically* recalibrate the screen weights instead of guessing.
   - **conviction tiers + monotonicity**: does high-conviction actually outperform?
   Write the report to `cache/ghost_oracle_report.json`.

5. **Persist.** `oracle.ghost.save_ledger(...)`, then
   `pantheon.persist("ghost_oracle", {"cache/ghost_oracle_ledger.json": …,
   "cache/ghost_oracle_report.json": …}, branch="claude/live")`.

## Cadence

- **Open** on every fresh screen (so each screen's survivors become labeled samples).
- **Grade** on a regular pass (daily/weekly); horizons mature on their own clock.

## Hard rules

- NEVER place a broker order. NEVER read or write the real `oracle_*` sleeve/ledger.
- Feed what Ghost learns (lens lift, conviction calibration) *back* into the real
  Oracle's weights only as evidence accumulates — don't overfit a small `n`.
