# Prereg — `gauntlet_v4_composite` (the Delphi-replacement capstone)

- **Sponsor:** operator (overnight directive: Delphi-replacement watch)
- **Committed:** 2026-07-04, BEFORE any composite holding is computed.
  Reuses cached SF1 signals (v2), DAILY price-to-sales (v3), the v1 PIT
  universes, and SEP bars — all already pulled; the composite RANKING
  and its outcomes have never been computed.

## Question

Do the three families that showed life in v2/v3 — net-issuance-low
(SUPPORTED), gross-profitability-high (SUPPORTED), price-to-sales-low
(inconclusive-alive) — combine into a rank-composite that beats each
alone and beats the EW benchmark two-regime + 2× + cliff? JKP (2023)
find composite factors the most robust form; a robust LARGE-bucket
composite is the strongest Delphi-replacement candidate (Lens A).

## The composite (frozen)

At each quarterly rebalance, within each bucket, each member is
percentile-ranked in all three signals it has data for (net-issuance
ascending=better, gross-profitability descending=better, price-to-sales
ascending=better); composite score = MEAN of available percentile ranks
(a name needs ≥2 of 3 signals to be scored — disclosed coverage rule).
Long the top-N by composite score, equal weight, next-day-close exec.

## Grid (n_trials = 4, FROZEN)

`composite` × {LARGE, SMALL} × {N25, N50} = 4 cells. The individual
three families are re-run in the SAME harness as REFERENCE (not counted
as new trials — already recorded in v2/v3), so the composite's lift
over each is apples-to-apples.

## Machinery, benchmarks, verdict (frozen — identical to v2/v3)

In-sample 2000-07..2015-12, holdout 2016-01..2025-12 touched once;
per-bucket costs + total-return marking + signal_lag next-day exec;
in-sample DSR≥0.95 (n_trials=4, cross-sectional variance) AND > bucket
EW scalar; holdout beats bucket EW scalar; 2× rerun; cliff
(parameter-neighbor must also survive). A full survivor earns a paper
forward test AND — if LARGE — is flagged an explicit Delphi-replacement
candidate for the operator. Counter +4 (133→137).

## Bias checklist (at record)

Same panel/PIT/cost disclosures as v2/v3; the ONE new degree of freedom
is the composite weighting (equal-mean of ranks) — frozen here as
equal, NOT tuned; any weight optimization would be a new prereg. The
composite reuses spent panels, disclosed: this buys the "does combining
help" decision once, and the fresh-data forward test remains the
arbiter for all of it.
