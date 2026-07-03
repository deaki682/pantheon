# Pre-registration: reaction-direction gate replay (Achilles/PEAD)

Committed 2026-07-03, before any results exist. Same one-shot terms as
docs/oracle_prereg_cluster_replay.md.

## Question

Achilles' entry gate says the drift follows the REACTION, not the EPS
headline: only go long an earnings event the market rewarded; never buy a
"sold" report. That gate was designed from theory (the DAKT lesson) and
has never been tested on history. This replay asks: after an earnings
8-K, does the market's day-one verdict predict the next five days?

Note what this does and does not test: historical analyst estimates are
not reconstructable, so beat-vs-miss conditioning is out of scope. The
REACTION side of his gate — the part that actually gates entries — is
fully testable from filings + bars.

## Population (FROZEN)

- Every 8-K carrying Item 2.02 (results of operations) filed 2025-01-02
  .. 2026-05-31, cataloged from each issuer's EDGAR submissions record
  (items field), across the full company_tickers universe.
- Exclusions: none at catalog time. (Small/mid slice — his actual pond —
  reported alongside all-cap at grading.)

## Sampling (FROZEN)

Grading needs per-event price history through a rate-limited broker API,
so the graded set is a RANDOM SAMPLE of the population: 600 events drawn
with Python's random.Random(20260703).sample(). Seed fixed here, before
the catalog exists. No redraws; if a sampled event is unpriceable it is
reported as such, not replaced.

## Event mechanics (FROZEN)

- Reaction day: the first trading session AFTER the 8-K filing date
  (earnings 8-Ks overwhelmingly file the day of an after-close release;
  where a company releases pre-market and files same-day this lags one
  session — a disclosed approximation that only blurs, never flatters).
- Reaction return: reaction-day close vs prior session close.
- **Rewarded**: reaction ≥ +3%. **Sold**: ≤ −3%. Between: excluded
  (his gate doesn't trade lukewarm reactions).
- Entry: next session's OPEN after the reaction day (his real entry
  timing). Hold 5 trading days; exit at the 5th close. No stop modeled
  (his −8% stop would only improve the sold-group's numbers; omitting it
  is conservative for the gate hypothesis). Excess return vs IWM over
  the identical window.

## Validation / refutation (FROZEN)

- **Validated**: rewarded-group mean excess > 0 AND
  (rewarded − sold) spread > 0 with t ≥ 2 on event-level returns.
- **Refuted**: spread ≤ 0, or rewarded-group excess ≤ 0, with n ≥ 150
  graded rewarded events.
- **Inconclusive**: anything else. One shot, no re-cuts.

## What this is NOT

- Not a live-rule change; his gates run as written this season either way.
- Not a test of his scoring curve, liquidity filters, or basket sizing —
  the gate is the load-bearing wall; it goes first.
