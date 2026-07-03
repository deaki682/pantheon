# Pre-registration: blinded reader-accuracy study (the load-bearing wall)

Committed 2026-07-04 (small hours), before any anonymized document or
read exists.

## Question

Every mechanical buy-trigger tested this weekend measured ≈ zero or
negative alone; the entire program now rests on the claim that the
READING adds selection value. Judge consistency is measured (probe);
judge ACCURACY against resolved outcomes is not. This study asks: on
spinoffs whose outcomes are now known, does the production reading
pipeline's condemnation separate the disasters from the rest?

## The contamination problem, confronted first

The reader may recognize resolved names from training data (a model
that knows LYLT went bankrupt can fake discrimination). Defenses, all
FROZEN:

1. **Anonymization pipeline**: each specimen's document set has
   tickers, company/parent/subsidiary names, officer/director names,
   exchange names, cities, and absolute dates masked (entities →
   consistent placeholders like SPINCO/PARENT/CEO-1; dates → T+offset
   form). Dollar figures, ratios, and structural facts stay.
2. **De-anonymization gate**: before any judgment, a separate agent
   (same model class) is shown the anonymized set and asked to name
   the company, with incentive-to-guess framing. A correct or
   near-correct identification marks the specimen CONTAMINATED.
   Results are reported for the clean set as primary, contaminated
   set alongside — if the clean set is under 20 specimens, the study
   reports insufficient-clean-n rather than borrowing.
3. **No market data in documents**: nothing post-distribution enters
   the document set (filings up to and including the first 10-Q only,
   matching what live Nemesis reads in-window).

## Population (FROZEN)

The 48 triggered events of the 2021–24 ocean extension (resolved:
net returns and excess vs SPY already computed under frozen exits) —
minus any specimen whose documents cannot be fetched. Every exclusion
named.

## Procedure (FROZEN)

- Production deep-read standard per specimen on the ANONYMIZED set:
  section extraction → judge → two adversarial refuters → 3-judge
  median if boundary (the live pipeline as of 2026-07-03, including
  the panel rule).
- Output per specimen: verdict, incentive_alignment,
  garbage_barge_risk → condemned = avoid OR garbage > 0.6 (the live
  veto, unchanged).
- Readers and judges see ONLY anonymized documents. No web, no EDGAR.

## Validation / refutation (FROZEN)

On the CLEAN (uncontaminated) specimens:

- **Validated**: condemned-group mean excess < non-condemned mean
  excess, spread ≥ 15 percentage points, t ≥ 1.5 (n will be small;
  the effect must be LARGE to matter — a veto that needs n=500 to
  detect is not paying for its tokens), AND the condemned group
  contains at least one of the two worst realized outcomes.
- **Refuted**: condemned group performs equal or better than
  non-condemned (spread ≤ 0) with ≥ 8 condemned specimens.
- **Inconclusive**: anything else — including insufficient clean n.

## Consequences

- Validated → the veto keeps its live role with measured backing;
  the 20-grade live checkpoint remains the binding test.
- Refuted → OPERATOR DECISION with a recommendation to suspend the
  veto leg (revert to buy-all ghost + own-picks only) — reading costs
  real money and must not keep a job it measurably cannot do.
- Either way: nothing changes without the operator seeing this doc's
  results first.
