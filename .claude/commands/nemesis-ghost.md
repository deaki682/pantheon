# /nemesis-ghost — paper-only contrarian shadow (fade vs flow, head-to-head)

Nemesis buys what the market just punished. She has **no sleeve, no ledger,
and places no orders** — she exists only as this ghost until a leg proves
itself in the current regime. Two legs run head-to-head every trigger week:

- **FADE** — liquid names that crashed on NO news. Price moves without news
  revert; price moves with news drift. The no-news conditioning IS the edge.
- **DESTINATION** — the receiver sectors the conditional rotation matrix
  predicts (computed from history via `nemesis.rotation`, never assumed).

Plus the control that keeps it honest: **news-driven crashes are opened on
purpose** — they should FAIL to bounce, and that failure validates the filter.

State: `cache/ghost_nemesis_ledger.json` + `_curve.json` + `_report.json` +
`cache/nemesis_matrix.json`, persisted under god name `ghost_nemesis`.
Engine is `shared.ghost`; Nemesis bits in `nemesis.detect` / `nemesis.rotation`
/ `nemesis.ghost`.

## Steps

0. **Hydrate.** `pantheon.hydrate()`.

1. **Restore the ledger.** `nemesis.ghost.load_ledger("cache/ghost_nemesis_ledger.json")`.

2. **Detect today's crashes (liquid universe only).** Fetch ~70 daily closes
   for `delphi.signals.UNIVERSE` (the 118 liquid large-caps — reversal in
   illiquid names is uncapturable after costs). Then
   `nemesis.detect.detect_crashes(universe_prices, sectors=<symbol->sector map>)`
   — flags names down ≥4% AND ≥2σ vs their own trailing vol, and tags
   sector cascades (3+ same-sector crashers = flow, not story).
   If no crashes today, skip to step 6 — mark/grade the open book and exit.

3. **News-check each crash (the conditioning).** For each crashed name:
   - `get_earnings_results`: did it report within the last ~3 trading days?
   - EDGAR: any 8-K in the same window (guidance, M&A, investigation)?
   Set `news_driven=True/False` accordingly. If the check can't be completed,
   leave `news_driven=None` — it's tagged `news_checked=False`, never silently
   treated as clean.

4. **Compute destinations (only on sector-cascade days).** When a cascade or a
   trigger-ETF crash day is detected: fetch ~2 years of daily closes for the
   sector ETFs (XLK XLY IWM XLI XLF XLB XLE XLV XLP XLU),
   `nemesis.rotation.conditional_matrix(etf_closes, trigger_sym=<crashed sector's ETF>)`,
   then `predicted_destinations(matrix)` (quality-floored: ≥10 events, ≥60%
   hit, ≥+0.2pp excess; excludes the trigger itself — its bounce belongs to
   the fade leg). Save the matrix to `cache/nemesis_matrix.json`.

5. **Open both legs.**
   - `nemesis.ghost.crashes_to_ghost(crashes, price_lookup)` — ALL crashes,
     news-driven included (the control group).
   - `nemesis.ghost.destinations_to_ghost(destinations, price_lookup)`.
   - `open_entries(..., today=…, skip_open=False)` — each crash event is an
     independent sample; same-day dupes are de-duped by the engine.

6. **Mark, grade.** `mark_to_market` + `append_equity_point(curve, …,
   benchmark={"SPY": r})`; `grade_entries(..., today=…)` at the 7-day horizon.
   Unpriceable names grade as a loss.

7. **Report.** `nemesis.ghost.nemesis_report(ledger)` →
   - **`leg_returns`** — THE head-to-head: fade vs destination mean return.
     This answers "target who's losing, or where the money's going?"
   - **`signal_lift.news_driven`** — the validation check: a clearly NEGATIVE
     lift (news crashes bleed) proves the no-news filter; a flat one kills it.
   - **`signal_lift.sector_cascade`** — do flow crashes revert harder than
     idiosyncratic ones?
   - **`zscore_terciles`** — does a more violent crash bounce harder?
   - **`predicted_excess_terciles`** — did the matrix's ranking mean anything?
   Write to `cache/ghost_nemesis_report.json`.

8. **Persist.** `save_ledger(...)`, then `pantheon.persist("ghost_nemesis",
   {…ledger, curve, report, matrix…}, branch="claude/live")`.

## Cadence

Daily after the close (or via Zeus on weekdays). Crash days are episodic —
most runs will only mark/grade. That's correct behavior, not a wasted run.

## Hard rules

- NEVER place a broker order. There is NO live Nemesis sleeve — capital is a
  conversation that starts only after a leg survives a real graded sample.
- Open news-driven crashes too. Without the control group the no-news filter
  is a belief.
- The rotation matrix is regime-conditional (2024-26 was a buy-the-dip era).
  Re-estimate it fresh at each use; never hardcode destinations.
- Sub-1pp edges die to costs — if a leg validates, the live design must
  confront spreads before any sleeve exists.
