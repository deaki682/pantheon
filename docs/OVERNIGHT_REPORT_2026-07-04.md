# Overnight sweep report — 2026-07-04

Operator directive: "deep research on every perceivable alpha strategy,
run them through the tests" + watch for Delphi replacements and
LLM-integration candidates.

## Headline

**The house has its first SUPPORTED strategies** — and they are on
paper forward tests, not live money. After ~150 mechanical cells tested
across the house's history (all price families dead), the fundamentals
sweep found two families that beat their equal-weight benchmark in BOTH
an in-sample (2000-2015) and a held-out (2016-2025) regime, at 2× cost,
with parameter robustness:

1. **Net-issuance-low, LARGE cap** (buyback tilt) — holdout +14-15%/yr
   vs 11.4% benchmark. **The leading Delphi-replacement candidate.**
2. **Gross-profitability, N50** (quality) — holdout +11.6-11.7%/yr,
   bucket-robust.

Both now accrue graded paper quarters; validation needs ≥20 on fresh
post-2026 data. Nothing is live.

## What ran (all preregistered before data)

| study | cells | verdict | counter |
|---|---|---|---|
| gauntlet_v2_fundamentals | 20 | **SUPPORTED → forward-testing** | +20 |
| gauntlet_v3_value | 8 | inconclusive (value alive, not robust) | +8 |
| gauntlet_v4_composite | 4 | REFUTED (naive rank-averaging dilutes tail alpha) | +4 |
| alpha_map | — | enumeration of 15 families | — |

Counter: 105 → 137. Every cell paid for in advance; DSR deflated at the
grid size.

## Three defects caught before any verdict (the audit reflex)

1. **DSR variance_of_sr bug** — v2/v3 screens defaulted to 1.0, forcing
   DSR=0.000 for all 28 cells (apparent universal refutation). Fixed to
   v1's cross-sectional convention; resurrected two real families.
2. **SF1 early-years coverage starvation** — first-snapshot coverage
   3.2%; fixed with a 1996-1998 supplement (→73%).
3. **(earlier tonight) event_car M&A attrition** — carry-at-cash-out.

## Honest coverage accounting

"Every perceivable alpha strategy" is infinite; the factor zoo (~400
anomalies) collapses to ~15 families (docs/alpha_map.md). Covered
tonight: the fundamentals families (7-10, TESTED) and value (11,
TESTED). Already dead: all price families (momentum/reversal/low-vol/
trend, 1-6). Live with gods: spinoffs (17), quiet clusters (16), PEAD
(Achilles). Refuted earlier tonight: the tender family (15, 4 cells).
**NOT covered — the honest gaps:** forced flows / index reconstitution
(14) — the highest-prior UNTESTED family, needs an event-feed build;
cross-asset/carry/vol (19-20) — out of the long-only-no-options mandate.

## The two operator lenses

- **Lens A (Delphi replacement):** ANSWERED with a candidate —
  net-issuance-low LARGE, the first mechanical large-cap OOS-benchmark-
  beater. Pending its forward test, it is a genuine drop-in for Delphi's
  refuted seat. Low-vol LARGE remains a defensible lower-drawdown core
  (not alpha).
- **Lens B (LLM integration):** two shapes surfaced — (1) an LLM
  value-trap / buyback-quality read on the mechanical fundamentals
  shortlist (the surviving families are the filter, the LLM discriminates
  the traps); (2) the forced-flow event feed (highest-prior untested,
  reading-shaped). Both are new preregs.

## Recommended next (each a NEW prereg, operator's call)

1. **gauntlet_v4 composite** — combine the three surviving fundamental
   families (net-issuance + profitability + price-to-sales), LARGE; the
   most-robust factor form and a direct Delphi replacement.
2. **Let the v2 forward tests accrue** — the real arbiter; no live money
   until ≥20 graded fresh-data quarters.
3. **Forced-flow catalog build** — the last high-prior untested family.

## Discipline note

Testing this many strategies is exactly what the counter + DSR + holdout
+ forward-test machinery exists to keep honest. The two-regime
out-of-sample survival at 2× cost is why these are credible enough to
forward-test — but "supported" is a licence to spend PAPER, and the
famous-anomaly decay literature means the fresh-data forward test is the
only thing that will separate a real edge from a historical ghost.
