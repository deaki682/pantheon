# /midas-ghost — paper-only convergence shadow

Ghost Midas runs the convergence scan but **places no orders and touches
no real sleeve**. It opens a paper position for *every* stage-2 finalist
it can price — not just the single winner — marks the book to market,
and grades each one's 5-day return. Short horizons mean useful answers
in weeks, not months.

**The 2026-07-04 A/B race:** since the convergence multiplier was
flattened out of the live formula (operator directive; see the rule-
change record in midas.md), every finalist carries both `score` (live,
max-of-timely) and `score_legacy` (old convergence formula), and
`finalists_to_candidates` flags each week's `live_pick` and
`legacy_pick`. The report's `signal_lift` grades those two flags head-
to-head — the multiplier earns its way back only if legacy picks beat
live picks over a real sample (own prereg before any reversal).

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

**This ghost outlives the live god.** Midas's live sleeve was retired on
2026-07-04 (capital reallocated to Proteus, operator directive), but this
A/B race keeps running on its own daily cadence — mark the run with
`oracle.calendar.mark_run("cache/ghost_midas_cadence.json", "session")`
and persist that cadence file too (Zeus gates on it).

**Death clock (operator directive, 2026-07-04).** This program runs to
the ≥20-graded-weeks checkpoint and NOT ONE WEEK further. When the
ledger holds 20 graded weekly `live_pick`-vs-`legacy_pick` head-to-heads,
run the pre-registered comparison ONCE:
- If legacy picks beat live picks per that prereg's frozen criteria,
  the reversal case goes to the operator (with the numbers, not a
  recommendation to un-retire).
- Otherwise the ENTIRE program retires permanently — `/midas-scan`,
  `/midas-ghost`, the weekly A/B, all of it. Write the ledger row,
  persist the final report, and remove both commands.
No extensions, no "one more season", no widening the question after
seeing the data. The scan exists only to feed this race; when the race
ends, so does the scan.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Restore the ledger.** `shared.ghost.load_ledger("cache/ghost_midas_ledger.json")`.

2. **Open paper positions for every finalist.** Load the most recent stage-2
   finalists from `cache/midas_dossiers.json` (the dossiers include both
   disqualified and non-disqualified names). **Since Midas's live retirement
   (2026-07-04) no new dossiers are built** — fall back to the finalists in
   `cache/midas_scan.json` (the weekend `/midas-scan` output; the
   `disqualified`-lift channel simply stops accruing new data). If neither
   exists, run stages 1-2 of the `/midas` scan to produce finalists. Fetch a quote per symbol.
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
