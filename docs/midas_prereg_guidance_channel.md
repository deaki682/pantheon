# Pre-registration: guidance-channel replay (Midas)

Committed 2026-07-03 (late night), before any catalog or results exist.
Same one-shot terms as the Oracle and Achilles replays.

## Question

Midas scores "guidance raised" as a binary signal channel
(`shared.edgar.guidance_direction` over Item 7.01/8.01 8-Ks) worth 1.0
— pure folklore, never measured. After a company files an 8-K whose
text signals raised guidance, does the stock beat small-caps over
Midas's one-week horizon?

## Population (FROZEN)

- Every 8-K carrying Item 7.01 or 8.01 filed 2025-01-02..2026-05-31,
  cataloged from issuer submissions records (items field) across the
  full company_tickers universe. Accession numbers captured at catalog
  time so the filing text is fetchable.
- These items are the most common 8-K furnishings; the population will
  be large (tens of thousands). No exclusions at catalog time.

## Sampling (FROZEN)

- Text-classification and grading run on a RANDOM SAMPLE of 900 events,
  drawn with Python's random.Random(20260704).sample() over the catalog
  sorted by (filed, cik, accession). Seed fixed here, before the
  catalog exists. Unpriceable/unfetchable events reported, not replaced.

## Event mechanics (FROZEN)

- Classification: production `shared.edgar.guidance_direction` on the
  filing's primary document text → raised / lowered / none. The
  classifier is used AS-IS; this measures the channel Midas actually
  trades, not an idealized one.
- Entry: next session's OPEN after the filing date. Hold 5 trading
  days; exit at the 5th close. Excess vs IWM over the identical window.
  (Midas enters Mondays only in live trading; entering next-open here
  measures the signal, not his calendar — disclosed simplification.)
- Groups: raised vs none (the tradable contrast), lowered reported for
  symmetry.

## Validation / refutation (FROZEN)

- **Validated**: raised-group mean excess > 0 AND (raised − none)
  spread > 0 with t ≥ 2 on event-level returns.
- **Refuted**: raised-group excess ≤ 0 or spread ≤ 0 with ≥ 100 graded
  raised events.
- **Inconclusive**: anything else. One shot, no re-cuts.

## What this is NOT

- Not a live-rule change; Midas's channels run as written either way.
  A refuted channel's weight is a cohort-review question with its own
  prereg, not a weekend knob.
- Not a test of his convergence multipliers (still untested folklore —
  noted for later, again).
