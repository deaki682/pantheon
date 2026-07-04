# Results — `gauntlet_v4_composite` — REFUTED (a useful negative)

- **Prereg:** [docs/lab_prereg_gauntlet_v4_composite.md](lab_prereg_gauntlet_v4_composite.md)
- **Run:** 2026-07-04, `run_gauntlet_v4.py`
- **Registry:** `gauntlet_v4_composite` → **refuted**; `hypotheses_ever` 137

## Verdict: REFUTED — naive compositing destroys the edge

| cell | in-sample CAGR | bench | DSR |
|---|---|---|---|
| composite LARGE N25 | −6.71% | 5.51% | 0.000 |
| composite LARGE N50 | −2.60% | 5.51% | 0.002 |
| composite SMALL N25 | −9.36% | 6.79% | 0.000 |
| composite SMALL N50 | −6.80% | 6.79% | 0.000 |

Each ingredient earns **+8 to +9% alone**; the equal-rank composite of
all three is **negative**. Zero cells cleared the in-sample screen, so
none reached the holdout.

## Why (verified, not a bug)

The composite's top names rank high (0.5–0.98) on all three signals —
direction is correct, no ranking bug. The mechanism is real: **averaging
percentile ranks selects names that are moderately-good-at-everything
and extreme-at-nothing, discarding the tail where each factor's alpha
concentrates.** Net-issuance's edge is in *deep* buybacks, not moderate
ones; profitability's is in the *highest* margins. A mean-rank composite
never holds the extreme of any factor. This is the classic failure of
naive multi-factor rank-averaging — measured here rather than assumed.

## Delphi-replacement conclusion (Lens A)

Naive compositing does **not** beat net-issuance-low LARGE alone. The
standalone factor remains the Delphi-replacement candidate to
forward-test. A **tail-preserving** construction (intersect the tails,
or factor-weight rather than rank-average) is the indicated follow-up —
a new prereg. This closes the naive-composite question.
