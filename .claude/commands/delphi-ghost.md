# /delphi-ghost — paper-only momentum shadow

Ghost Delphi shadows the CURRENT Delphi strategy (118-name universe, 65-day
momentum, top-10 book, 20-day-MA exit) but **places no orders and touches no
real sleeve**. It opens a paper position on the ENTIRE universe — including
names below their MA and names the ranking passed over — because the unbought
names are the control groups that make the strategy measurable instead of
merely believed.

Three questions it exists to answer:
  1. Does higher momentum predict higher forward return? (`momentum_terciles`)
  2. Does the 20-day-MA rule separate winners from losers? (`signal_lift.above_ma`
     — the trailing-stop premise; below-MA names are the control group)
  3. Does the top-10 selection (ranking + LLM vetoes) beat the above-MA names
     it passed over? (`signal_lift.selected`, `signal_lift.vetoed`)

State: `cache/ghost_delphi_ledger.json` + `_curve.json` + `_report.json`,
persisted under god name `ghost_delphi`. Engine is `shared.ghost`; Delphi bits
in `delphi.ghost`. Entries are tagged `source="momentum"`; the report filters
to that source.

## Steps

0. **Hydrate.** `pantheon.hydrate()`.

1. **Restore the ledger.** `delphi.ghost.load_ledger("cache/ghost_delphi_ledger.json")`.

2. **Open the full universe.** Reuse the price history the live `/delphi` run
   fetched (126+ daily closes for `delphi.signals.UNIVERSE` + overrides), then:
   `delphi.ghost.universe_to_ghost(universe_prices, selected=<current top-10 book>,
   vetoed=<this run's LLM vetoes>, reviewed=<the top-20 the LLM examined>)`
   and `open_entries(..., today=…, skip_open=True)`.
   - Do NOT feed it `rank_by_momentum` output — that's already MA-filtered and
     silently drops the control group. Full raw prices in.
   - `skip_open=True`: the universe is static week to week; re-opening the same
     ~118 names every run would bloat the ledger. A name re-opens only after
     its previous entry grades out at the 90-day horizon.

3. **Mark to market.** `mark_to_market(ledger, price_lookup)` +
   `append_equity_point(curve, today, snapshot, benchmark={"SPY": r})`.

4. **Grade matured positions.** `grade_entries(ledger, price_lookup, today=…)` —
   90-day horizon (a momentum holding window). Unpriceable names grade as a
   loss (survivorship guard).

5. **Report.** `delphi.ghost.signal_report(ledger)` →
   - **`momentum_terciles`** — the primary signal. If high-momentum names don't
     beat low-momentum names on a real `n`, the core premise isn't holding.
   - **`signal_lift.above_ma`** — the MA-exit premise, now actually measurable.
     If below-MA names perform no worse, the trailing stop is churn, not
     protection; if they bleed, it's earning its keep.
   - **`signal_lift.selected`** — the book vs the above-MA names it passed over.
   - **`signal_lift.vetoed`** — did LLM vetoes filter losers or kill winners?
     This is the calibration read for the veto budget in `/delphi`.
   Write to `cache/ghost_delphi_report.json`.

6. **Persist.** `save_ledger(...)`, then
   `pantheon.persist("ghost_delphi", {…ledger, curve, report…}, branch="claude/live")`.

## Hard rules

- NEVER place a broker order. NEVER touch the real `delphi_*` sleeve/ledger.
- Open below-MA and passed-over names too — without control groups the MA rule
  and the selection can only be believed, never validated.
- 90-day horizons mean verdicts accumulate slowly here; treat early lifts as
  evidence, not proof, and don't touch the live strategy off a small `n`.
