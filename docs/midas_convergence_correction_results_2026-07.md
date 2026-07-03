# Results: corrected convergence re-test (double-count fix)

Run 2026-07-04 per the correction addendum in
`docs/midas_prereg_convergence_test.md`. One-time bug-fix re-run;
original result stands, not retracted. Raw data:
`docs/data_midas_convergence_correction_2026-07.json`.

## What was corrected

`midas/scoring.py` counted `earnings_beat`, `guidance_raised`, and
`volume_anomaly` as three independent convergence signals even when a
single earnings report trips all three. The original convergence
test's own co-signal join had the identical defect (earnings-8K and
guidance-8K flags counted independently even when filed the same day
for the same issuer). **134 of 934 events had a same-day earnings +
guidance filing** — a real, common pattern (companies routinely update
guidance in the same release as an earnings beat), not an edge case.
Correcting for it reclassified **104 events'** co-signal group.

## Result: REFUTED again, under corrected counting

| Group | n (old, buggy) | n (new, corrected) | mean excess (new) | t |
|---|---|---|---|---|
| 0 co-signals | 306 | 306 | +1.13% | 1.75 |
| 1 co-signal | 369 | 473 | +0.02% | 0.04 |
| 2+ co-signals | 217 | 113 | +0.26% | 0.17 |

Spread (2+ minus 0): **−0.87%** (was −1.27% under the buggy count —
similar magnitude, same sign). Monotonicity fails either way (1-signal
group is the worst of the three, not in between 0 and 2). Applying the
frozen rule: spread ≤ 0 with n(1+2) = 586 ≥ 80 → **REFUTED**, meeting
the same threshold as the original result.

## Reading

The double-counting bug was real, material (11% of the population
reclassified), and worth fixing in the live scorer regardless — bad
code should not survive because the conclusion happened not to change.
But the CONVERGENCE THESIS ITSELF is now refuted under two
independently-computed countings, buggy and corrected. That is
meaningfully stronger evidence than either result alone: this isn't
"we mismeasured and got a fluke negative," it's "stacking informed-
money signals did not predict a 5-day pop, and fixing how we count the
stack doesn't change that." The convergence multiplier is not a
counting artifact away from working.

## Consequence

`midas/scoring.py`'s double-count bug is fixed (own commit, tested
against this week's live finalists — 7 of 10, including DAKT, the
actual live pick, had their convergence tier inflated by exactly this
defect: recorded count 2, corrected count 1). Whether the
`CONVERGENCE_MULTIPLIERS` weighting itself should be changed in
production — given it is now refuted under two independent countings
— is a live-strategy decision, not a bug fix, and is presented to the
operator separately rather than changed unilaterally here.
