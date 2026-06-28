# /achilles-ghost — paper-only event-study shadow

Ghost Achilles runs Achilles's event detection but **places no orders and touches
no real sleeve**. It opens a paper position on *every* classified event it can
price — not just the few the $1k sleeve can afford — marks the book to market,
and grades each one's short-horizon drift. The payoff is the **measured per-event-
class drift**, which replaces the literature-seeded priors in `playbooks.py` with
real numbers. Short horizons (~10 days) mean useful answers in weeks.

State lives in its own namespace: `cache/ghost_achilles_ledger.json` +
`cache/ghost_achilles_curve.json`, persisted under god name `ghost_achilles`.
Engine is `shared.ghost`; Achilles-specific bits are in `achilles.ghost`.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Restore the ledger.** `shared.ghost.load_ledger("cache/ghost_achilles_ledger.json")`.

2. **Open paper positions for every event.** From the day's classified briefs
   (the same ones Achilles produces), fetch a quote per symbol and
   `achilles.ghost.briefs_to_candidates(briefs, price_lookup)` — this opens EVERY
   event, **including disqualified ones**, so the report can test whether the
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
   - **`lens_lift["disqualified"]`**: did disqualified events actually underperform?
   Write to `cache/ghost_achilles_report.json`.

6. **Persist.** `shared.ghost.save_ledger(...)`, then
   `pantheon.persist("ghost_achilles", {…ledger, curve, report…}, branch="claude/live")`.

## Hard rules

- NEVER place a broker order. NEVER touch the real `achilles_*` sleeve/ledger.
- Recalibrate playbook drifts from measured `class_drift` only as `n` grows —
  don't overfit a handful of events.
