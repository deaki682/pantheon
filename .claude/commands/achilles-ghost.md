# /achilles-ghost — paper-only PEAD-basket shadow

Ghost Achilles shadows the CURRENT Achilles strategy (diversified basket of
market-rewarded earnings beats) but **places no orders and touches no real
sleeve**. It opens a paper position on *every* actionable beat — rewarded,
sold, and unconfirmed alike — because the names the live strategy refuses to
buy are the control groups that prove whether each gate earns its place.

The one question this ghost exists to answer: **is the reaction-direction gate
real?** If sold beats drift up as well as rewarded ones, the gate costs money.
If they bleed, it saves it. That's the `rewarded` row of `signal_lift`.

State: `cache/ghost_achilles_ledger.json` + `_curve.json` + `_report.json`,
persisted under god name `ghost_achilles`. Engine is `shared.ghost`; Achilles
bits in `achilles.ghost`. New entries are tagged `source="pead"`; entries from
the retired event-study ghost remain in the ledger but are filtered out of the
report.

## Steps

0. **Hydrate.** `pantheon.hydrate()`.

1. **Season note.** Run during earnings windows (`achilles.season`) when beats
   exist; off-season runs still mark/grade the open book — never skip those.

2. **Restore the ledger.** `achilles.ghost.load_ledger("cache/ghost_achilles_ledger.json")`.

3. **Gather ALL actionable beats (not just the basket).** Same discovery the
   live `/achilles` uses, minus the gates:
   - `get_earnings_calendar(start_date=today, days=-5)` → recent reporters;
     `get_earnings_results` per name → `compute_surprise`; keep
     `is_actionable_beat` (3–500% surprise).
   - Historicals per name → `reaction_return(pre_report_close, post_report_close)`
     → attach `reaction_pct` (leave None when unconfirmable — that's a tag, not
     a reject here).
   - Attach confirming signals (revenue beat, guidance, short float) and
     `market_cap` where available. Build `BeatCandidate`s.
   - Also run the live selection (`rank_beats(candidates, top_n=12)`) and keep
     its symbols as `basket_selected` — the end-to-end selection test.

4. **Open paper positions on everything.**
   `achilles.ghost.beats_to_candidates(all_beats, price_lookup, basket_selected=<symbols>)`
   then `achilles.ghost.open_entries(..., today=…)`. Sold beats are opened LONG
   deliberately — they're the gate's control group. `skip_open=False`: each
   week's beats are independent samples.

5. **Mark to market.** `mark_to_market(ledger, price_lookup)` +
   `append_equity_point(curve, today, snapshot, benchmark={"SPY": r})`.

6. **Grade matured positions.** `grade_entries(ledger, price_lookup, today=…)`
   — 7-calendar-day horizon (≈ the 5-trading-day live hold). Unpriceable names
   grade as a loss (survivorship guard).

7. **Report.** `achilles.ghost.pead_report(ledger)` →
   - **`signal_lift.rewarded`** — the reaction-direction gate's measured value.
     THE number to watch.
   - **`signal_lift.basket_selected`** — do the picks beat rewarded-but-passed-over?
   - **`reaction_terciles`** — bigger reaction → bigger drift? (directional thesis)
   - **`surprise_terciles`** — surprise magnitude curve check.
   - **`cap_terciles`** — neglect thesis: healthy reading is LOW cap above high
     (inverse monotonicity — the `monotonic` flag will read False when the
     thesis is working; read the tercile means, not the flag).
   Write to `cache/ghost_achilles_report.json`.

8. **Persist.** `save_ledger(...)`, then
   `pantheon.persist("ghost_achilles", {…ledger, curve, report…}, branch="claude/live")`.

## Hard rules

- NEVER place a broker order. NEVER touch the real `achilles_*` sleeve/ledger.
- Open sold and unconfirmed beats too — without the control groups, the gate
  can never be validated, only believed.
- Feed conclusions back into the live strategy only as graded `n` grows; a
  couple of weeks of earnings-season data is suggestive, not proof.
