# /midas-ghost — paper-only convergence shadow

Ghost Midas runs the convergence scan but **places no orders and touches
no real sleeve**. It opens a paper position for *every* stage-2 finalist
it can price — not just the single winner — marks the book to market,
and grades each one's 5-day return. Short horizons mean useful answers
in weeks, not months.

The payoff is signal-convergence validation:
  - **convergence_terciles** — do multi-signal names outperform single-signal
    names? This is the core thesis test. If it's flat or inverted, the
    convergence multiplier is wrong.
  - **score_terciles** — is the timing-weighted convergence score monotonic
    in forward return? Tests the full scoring formula end-to-end.
  - **timing_weighted_terciles** — do timing-weighted strengths predict better
    than raw counts? Validates the timing floor change.
  - **signal_lift** — per-channel boolean lift. Which signals actually predict
    5-day pops? Does insider_cluster help? Does activist_13d hurt?
  - **disqualified lift** — do LLM disqualifications filter losers or kill
    winners?

State: `cache/ghost_midas_ledger.json` + `cache/ghost_midas_curve.json`,
persisted under god name `ghost_midas`. Engine is `shared.ghost`; Midas
bits in `midas.ghost`.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Restore the ledger.** `shared.ghost.load_ledger("cache/ghost_midas_ledger.json")`.

2. **Open paper positions for every finalist.** Load the most recent stage-2
   finalists from `cache/midas_dossiers.json` (the dossiers include both
   disqualified and non-disqualified names). If no dossiers exist, run stages
   1-2 of the `/midas` scan to produce finalists. Fetch a quote per symbol.
   Pass ALL finalists to `midas.ghost.finalists_to_candidates(finalists,
   price_lookup)` — this opens every name including disqualified ones so the
   report can test whether disqualification helps. Then
   `shared.ghost.open_entries(candidates, existing, today=today, skip_open=True)`.

3. **Mark to market.** `shared.ghost.mark_to_market(ledger, price_lookup)` +
   `append_equity_point(curve, today, snapshot, benchmark={"SPY": r})`; save.

4. **Grade matured positions.** `shared.ghost.grade_entries(ledger,
   price_lookup, today=…)`. 5-day horizon means trades grade within a week.

5. **Report.** `midas.ghost.convergence_report(ledger)` →
   - **`convergence_terciles`**: THE test. Do 3-signal names beat 1-signal
     names? If not monotonic with sufficient n, the convergence thesis needs
     revisiting.
   - **`score_terciles`**: is the full scoring formula predictive?
   - **`timing_weighted_terciles`**: do timing weights improve prediction?
   - **`signal_lift`**: per-channel boolean — which signals fire on winners?
   - **`disqualified` lift**: does the LLM veto gate add value?
   Write to `cache/ghost_midas_report.json`.

6. **Persist.** `shared.ghost.save_ledger(...)`, then
   `pantheon.persist("ghost_midas", {…ledger, curve, report…}, branch="claude/live")`.

## Hard rules

- NEVER place a broker order. NEVER touch the real `midas_*` sleeve/ledger.
- Open ALL finalists including disqualified ones — the disqualified control
  group is how you test whether the LLM veto gate works.
- Tercile monotonicity is evidence, not proof, until n is large (30+).
