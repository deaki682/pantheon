# Results — `gauntlet_v2_fundamentals` — SUPPORTED (first in house history)

- **Prereg:** [docs/lab_prereg_gauntlet_v2_fundamentals.md](lab_prereg_gauntlet_v2_fundamentals.md)
- **Run:** 2026-07-04, `run_gauntlet_v2_pull.py` + `run_gauntlet_v2_screen.py`
- **Data:** SF1 ARQ (673k filing-dated rows, 1996-2025), gauntlet_v1
  PIT universes, SEP delisted-inclusive bars both windows
- **Registry:** `gauntlet_v2_fundamentals` → **supported → forward_testing**;
  `hypotheses_ever` 133

## Verdict: SUPPORTED — two parameter-robust families cleared the FULL gauntlet

The full gauntlet = in-sample DSR ≥ 0.95 (n_trials=20) + beat in-sample
EW benchmark + beat holdout EW benchmark (2016-2025, touched once) +
survive 2× slippage + a surviving parameter-neighbor (non-isolated).

| family | cells | in-sample CAGR (bench) | holdout@2× CAGR (bench) | excess/yr |
|---|---|---|---|---|
| **net-issuance-low LARGE** | N25, N50 | +9.1/9.3% (5.5%) | +15.1/14.3% (11.4%) | **+2.9 to +3.7%** |
| **gross-profitability N50** | LARGE, SMALL | +9.1/7.9% | +11.7/11.6% (11.4/9.5%) | +0.3 to +2.1% |

Both beat their equal-weight universe benchmark in BOTH regimes at 2×
cost — the property v1's low-vol survivors lacked (they died in the
bull holdout). This two-regime out-of-sample survival is the finding.

**net-issuance-low** = each quarter, long the 50 top-500 names with the
lowest trailing-4-quarter change in weighted shares outstanding (the
buyback side), equal weight, next-day-close execution. **gross-
profitability** = the 50 highest gross-profit/assets.

## What the gauntlet KILLED (the discipline worked)

- **accruals** — dead in every cell (in-sample CAGR −1.7% to +2.1%).
- **price-to-book (v3)** — failed in-sample, exactly as the modern
  literature predicts (B/M is the weakest value multiple post-2000).
- **thin holdout passers** — roa_high N50 SMALL (+9.51 vs 9.50) and
  gross_prof N25 SMALL died at 2× cost. Cost stress did real work.
- **asset-growth-low N50 LARGE** — cleared every statistical bar
  including 2× (+14.1% vs 11.4%) but was EXCLUDED as an isolated peak:
  no other asset-growth cell survived, so per the frozen cliff rule it
  is treated as noise. The single most important discipline moment of
  the night — a +14% cell voluntarily discarded.

## The DSR bug (caught before any verdict)

The first screen pass reported DSR=0.000 for all 20 cells (an apparent
universal refutation) because `deflated_sharpe_ratio` was called
without the cross-sectional `variance_of_sr`, defaulting to 1.0 (an
absurd ~1.9 annualized-Sharpe bar). Fixed to v1's convention
(variance_of_sr = cross-sectional Sharpe variance = 0.0337) before any
verdict was recorded; both passes are on record. Without the audit,
two real families would have been buried as noise.

## CAVEATS — front and center (what "supported" does NOT mean)

Supported means: **earned a paper forward test.** NOT live money. NOT
validated. Specifically:

1. **Famous anomalies.** Net issuance and profitability are in every
   factor fund. McLean-Pontiff measured ~58% post-publication decay —
   historical survival is NOT live harvestability.
2. **Multiple testing.** House counter 133 → ~6-7 false positives
   expected at 5%. The two-regime + 2× survival is why these clear the
   bar to forward-test, but only FRESH post-2026 graded quarters can
   separate real from lucky.
3. **Equal-weight small book frame.** These are equal-weighted; net
   issuance is famously fragile to value-weighting — though it survived
   here in LARGE-cap (top-500) equal weight, not microcaps, which is a
   point of genuine interest for a tiny book.

## The forward test (now live, paper)

`start_forward_test` fired for `gauntlet_v2_fundamentals`. The two
families accrue graded paper quarters on fresh data; validation needs
≥20 graded quarters with positive shrunk excess. Nothing goes near live
money before that.

## Operator lenses

- **Lens A (Delphi replacement):** net-issuance-low LARGE is the first
  mechanical large-cap strategy the house has measured beating its
  benchmark out-of-sample. It is a genuine drop-in candidate for
  Delphi's refuted seat — same universe scale, mechanical, quarterly.
  Pending its forward test.
- **Lens B (LLM integration):** the indicated construction is a
  COMPOSITE of the three live families (net-issuance + profitability +
  value) with an LLM "why-cheap/why-buying-back" quality read on the
  shortlist — the textbook mechanical-filter-plus-reading shape. New
  prereg required.
