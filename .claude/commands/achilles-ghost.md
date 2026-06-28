# /achilles-ghost — paper-only event-study shadow

Ghost Achilles runs Achilles's event detection but **places no orders and touches
no real sleeve**. It opens a paper position on *every* classified event it can
price — not just the few the $1k sleeve can afford — marks the book to market,
and grades each one's short-horizon drift. Short horizons (~10 days) mean useful
answers in weeks, not years.

The payoff is comprehensive signal validation:
  - **per-event-class drift** — replaces the literature-seeded priors in
    `playbooks.py` with measured numbers. This is how the 5 disabled playbooks
    get turned on.
  - **neglect terciles** — validates the core PEAD thesis (do neglected names
    drift more?)
  - **surprise/conviction/liquidity terciles** — validates each axis of the
    multiplicative scoring formula
  - **compound signal lift** — do insider pre-activity and concurrent guidance
    boosts actually predict higher drift?
  - **disqualifier lift** — do disqualifiers filter losers or kill winners?

State lives in its own namespace: `cache/ghost_achilles_ledger.json` +
`cache/ghost_achilles_curve.json`, persisted under god name `ghost_achilles`.
Engine is `shared.ghost`; Achilles-specific bits are in `achilles.ghost`.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Restore the ledger.** `shared.ghost.load_ledger("cache/ghost_achilles_ledger.json")`.

2. **Open paper positions for every event.** From the day's classified briefs
   (the same ones Achilles produces), **enrich each brief with convergence signals**
   before passing to the ghost adapter:
   - `neglect`: `achilles.convergence.neglect_premium(oracle_quality)` — the core
     thesis factor. Must be on every brief so tercile analysis can validate it.
   - `surprise_pct`: from `achilles.earnings.fetch_earnings_surprise` — drives the
     surprise strength curve.
   - `insider_preactivity`: from `achilles.oracle_bridge.has_insider_preactivity` —
     compound signal.
   - `concurrent_guidance`: from the LLM filing analysis — compound signal.
   - `conviction`: from `achilles.convergence.conviction_multiplier` — sizing factor.
   - `liquidity`: from `achilles.scoring.liquidity_score(market_cap)` — market cap
     edge curve.

   Then `achilles.ghost.briefs_to_candidates(briefs, price_lookup)` — this opens
   EVERY event, **including disqualified ones**, so the report can test whether the
   disqualifiers actually filter losers. Then `shared.ghost.open_entries(...)`.
   Restrict to liquid names — illiquid event paper-fills are fiction.

3. **Mark to market.** `shared.ghost.mark_to_market(ledger, price_lookup)` +
   `append_equity_point(curve, today, snapshot, benchmark={"SPY": r})`; save the curve.

4. **Grade matured positions.** `shared.ghost.grade_entries(ledger, price_lookup,
   today=…)` — short horizons mature fast. Unpriceable names grade as a loss.

5. **Report.** `achilles.ghost.drift_report(ledger)` →
   - **`class_drift[event_class]`**: the empirical mean drift per class — the
     number the playbooks currently *guess*. Feed this back to recalibrate the
     per-class priors (Bayesian-shrink toward the prior until `n` is large).
     This is the gating data for enabling the 5 disabled playbooks.
   - **`lens_lift`**: boolean signals —
     - `disqualified`: did disqualified events actually underperform?
     - `insider_preactivity`: did pre-earnings insider buying predict drift?
     - `concurrent_guidance`: did simultaneous guidance raises amplify drift?
   - **`neglect_terciles`**: core thesis test. Do high-neglect names drift more
     than low-neglect names? If this isn't monotonic, the neglect premium is wrong.
   - **`surprise_terciles`**: is the piecewise surprise strength curve correct?
     Do larger surprises actually produce more drift?
   - **`conviction_terciles`**: does higher conviction → higher returns? If yes,
     the sizing multiplier is earning its keep.
   - **`score_terciles`**: is the multiplicative score monotonic in forward return?
     This tests the whole scoring formula end-to-end.
   - **`liquidity_terciles`**: does the market cap edge curve correctly weight?
     Is the mega-cap decay helping or hurting?
   Write to `cache/ghost_achilles_report.json`.

6. **Persist.** `shared.ghost.save_ledger(...)`, then
   `pantheon.persist("ghost_achilles", {…ledger, curve, report…}, branch="claude/live")`.

## Hard rules

- NEVER place a broker order. NEVER touch the real `achilles_*` sleeve/ledger.
- Recalibrate playbook drifts from measured `class_drift` only as `n` grows —
  don't overfit a handful of events.
- The neglect tercile is the single most important output. If it's flat or
  inverted, the core thesis needs revisiting before going live with real money.
