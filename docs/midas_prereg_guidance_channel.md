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

## Correction addendum 2 (2026-07-04, committed BEFORE recomputing)

The original pass classified the PRIMARY document per the frozen spec —
faithfully measuring what production trades — and returned 0 raised in
900 because 7.01/8.01 primary docs are cover shells; the guidance text
lives in the press-release exhibit (verified on a sampled filing). That
verdict stands as recorded: the PRODUCTION channel is near-inert.

This addendum pre-registers the HYPOTHETICAL-channel question: does
guidance direction classified from EXHIBIT text carry 5-day edge? This
is what decides whether the live channel should be fixed to read
exhibits or retired.

- **Same seeded 900 events.** For each, fetch the accession's exhibit
  documents (ex-99*/press-release; largest non-primary HTML fallback)
  and run the production `guidance_direction` regex on the exhibit
  text. No new sampling.
- **Grading:** every raised/lowered/reaffirmed event graded in full
  (entry next session's open after filing date, 5 trading days, excess
  vs IWM — identical mechanics to the original). The "none" comparison
  group is graded from a seeded random subsample of 200
  (`random.Random(20260705).sample`) to bound the bar-fetch load —
  seed fixed here, before classification runs.
- **Same thresholds as the original prereg**: validated iff raised
  mean > 0 AND (raised − none) spread > 0 with t ≥ 2; refuted iff
  raised ≤ 0 or spread ≤ 0 with ≥ 100 graded raised events; else
  inconclusive. One shot on this addendum; no further re-cuts.
- **Pre-stated consequence:** validated → a prereg'd code change to
  read exhibits in the live path becomes eligible; refuted → recommend
  RETIRING the guidance channel (weight 0) as dead weight;
  inconclusive → channel stays as-is (near-inert) and the question
  waits for live grades.
