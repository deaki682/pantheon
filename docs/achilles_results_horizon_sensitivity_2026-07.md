# Results: PEAD hold-horizon sensitivity (5 vs 10 vs 20 trading days)

Graded 2026-07-04 per the frozen terms of
`docs/achilles_prereg_horizon_sensitivity.md`. Backlog item #8. One
shot, no re-cuts. Per-event data:
`docs/data_achilles_horizon_sensitivity_2026-07.json` (h10/h20 added to
the frozen 293-event reaction-gate population) plus current market caps
used for the neglect cut (`achilles_market_caps.json`, not committed —
ephemeral lookup, values quoted below).

## Method verification

Before scaling to all 293 events, RICK (entry 2025-01-13) and CMTL
(entry 2025-01-15) were recomputed from raw bars and matched the
frozen `ret5`/`excess` values byte-for-byte (RICK −2.39%/−7.50%, CMTL
−10.25%/−11.51%), confirming the entry-OPEN, Nth-session-CLOSE
convention before any new number was trusted.

One data-quality wrinkle, disclosed: 7 thinly-traded symbols (ATROB,
APTOF, ECTM, OWLTW, DRMAW, SQFTW, IMO) returned interpolated
(zero-volume gap-fill) bars somewhere in their window; these were
excluded from each symbol's own trading-session count before finding
the 10th/20th session, per the historicals tool's own guidance that
interpolated bars "carry no new info." This changed the session count
for 4 events (ATROB, OWLTW, ECTM, APTOF, all May 2025 entries) — using
the raw, uncorrected bars would have overstated how many real trading
sessions had elapsed for these names.

Coverage: 0/293 not-elapsed, 0/293 unpriceable at either horizon (all
280 unique symbols returned price data — better coverage than the
original 5-day study's population, which is the same symbols by
construction).

## Headline: no drift at 10 or 20 trading days either

| Horizon | Rewarded n/mean/t | Sold n/mean/t | Spread | Spread t |
|---|---|---|---|---|
| 5d (frozen) | 137 / −0.60% / −0.96 | 156 / −1.60% / −2.27 | +1.00% | 1.07 |
| 10d | 137 / −0.39% / −0.45 | 156 / −1.29% / −1.31 | +0.90% | 0.68 |
| 20d | 137 / −0.76% / −0.59 | 156 / −1.05% / −0.65 | +0.29% | 0.14 |

Neither the rewarded-group excess nor the rewarded−sold spread reaches
t ≥ 1.5 at 10 or 20 trading days — the pre-registered "no drift at any
horizon tested" outcome. If anything, the spread **shrinks** as the
hold lengthens (1.07 → 0.68 → 0.14 t), the opposite of what a
lengthening-drift story would predict. The sold-group's real avoidance
signal (t −2.27 at 5 days) also decays with hold length (−1.31, then
−0.65) — the loss is front-loaded in the first few days, not a slow
bleed that a longer hold would dodge or that a short would want to
ride.

## Neglected-name cut (exploratory, current-cap proxy — 276/280 symbols resolved; ASNS and 3 warrant tickers had no cap data)

| Bucket (n symbols) | Horizon | Rewarded n/mean/t | Sold n/mean/t | Spread | Spread t |
|---|---|---|---|---|---|
| Small <$2B (170) | 10d | 72 / −1.04% / −0.80 | 107 / −2.57% / −2.09 | +1.54% | 0.86 |
| Small <$2B (170) | 20d | 72 / −2.11% / −1.29 | 107 / −1.66% / −0.81 | −0.46% | −0.17 |
| Mid $2-10B (69) | 10d | 36 / +0.19% / 0.11 | 36 / +3.09% / 1.61 | −2.90% | −1.12 |
| Mid $2-10B (69) | 20d | 36 / +1.30% / 0.37 | 36 / +3.69% / 1.37 | −2.39% | −0.54 |
| Large >$10B (37) | 10d | 28 / +1.30% / 1.07 | 10 / −1.31% / −0.58 | +2.61% | 1.02 |
| Large >$10B (37) | 20d | 28 / +0.35% / 0.28 | 10 / −0.57% / −0.18 | +0.91% | 0.27 |

The small-cap tercile — the subset PEAD theory predicts should show
the strongest, longest-running drift — shows no such thing: its spread
is directionally positive at 10 days (t 0.86) but flips negative at 20
days (t −0.17). No bucket at either horizon clears the pre-registered
t ≥ 2 bar, and no bucket's direction is stable across the two extended
horizons. The neglected-name hypothesis is not rescued by this cut.

## Verdict

**No drift.** The 5-trading-day hold is not cutting the signal short —
extending to 10 or 20 trading days finds progressively LESS structure,
not more, both in the full population and in the small-cap subset
theory says should show it most. Combined with the frozen 5-day result
(real avoidance signal, no real buy signal), the honest read is that
PEAD's reward-side drift, if it exists at all in this population, does
not survive past the first few sessions — consistent with the original
study's finding that the sold-side penalty is front-loaded and real
while the reward side never clears significance at any hold tested.

## Consequences

1. **Achilles keeps her 5-day hold.** No horizon change is warranted —
   longer holds only add unrewarded holding-period risk (the sold-group
   penalty actually shrinks the longer you hold a name that already
   sold off, meaning a longer hold does not even improve the avoidance
   side).
2. Backlog #8 struck. Backlog #3 (sold-report ban replication, fall
   season forward test) remains the standing test of Achilles' one
   validated rule; nothing here changes its priority or design.
3. No live-rule change beyond what's stated above (none — the 5-day
   hold was already the live rule).
