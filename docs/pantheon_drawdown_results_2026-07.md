# Results: Pantheon correlated-drawdown study

Run 2026-07-03 per the frozen terms of
`docs/pantheon_prereg_correlated_drawdown.md`. Data:
`scratchpad drawdown_study_results.json` (session archive).

## Data-integrity note, first

The broker's pre-2010 weekly history is internally inconsistent (IWM
prints 129 in Dec-2004 and 83 in Jun-2007 with no crash between; a
half-price bar in Jun-2000). Episodes are therefore measured 2010→now
only, and the GFC-scale case is a labeled SYNTHETIC scenario (−60%
benchmark over 18 months), not a data claim.

## Measured inputs

Event-level betas from this weekend's graded reference classes:

| God | β | vs | Residual sd (event horizon) | Basis |
|---|---|---|---|---|
| Oracle | 1.00 | IWM | 0.61 (6mo) | 612 cluster events |
| Achilles | 1.40 | IWM | 0.08 (5d) | 293 reaction events |
| Midas (proxy) | 1.12 | IWM | 0.11 (5d) | 892 cluster 5d events |
| Nemesis | 1.37 | SPY | 0.28 (~150d) | 48 ocean events |
| Delphi | 1.00 | MTUM (γ=0.67 to IWM) | 0.017/wk | MTUM weekly overlap |

Confirmed structurally: all five books are high-beta long equity; in a
small-cap selloff they draw down together. IWM episodes ≥20% since
2010: 2011 (−26%), 2015-16 (−24%), 2018-2020 (−41%), 2021-23 (−33%),
2024-25 (−25%).

## Stress results (10K Monte Carlo paths, per-god 40% halts modeled in ALL arms)

Combined-book max drawdown:

| Scenario | C: status quo | A: book-halt @−25% | B: A + half-liquidate @−35% |
|---|---|---|---|
| Worst measured (2018→2020, IWM −41%) | p50 −38%, P(>50%)=1.6% | p50 −34%, P(>50%)=0 | ~same as A |
| Synthetic −60% (GFC-scale) | p50 −52%, P(>50%)=65% | p50 −46%, P(>50%)=22% | ~same as A |

False-trigger test: **47% of full-history simulated paths breach −25%
book drawdown OUTSIDE any ≥20% benchmark episode** — the combined book
is volatile enough (Midas is a single name at ~1.1β; Oracle's pond has
61% six-month idio dispersion) that a −25% book halt fires routinely on
god-specific noise, versus the frozen budget of <5%.

## Verdict (frozen criterion applied)

- Status quo C PASSES on the worst measured episode (P(dd>50%) = 1.6%
  < 10%) with zero false triggers by construction.
- A and B FAIL the false-trigger budget catastrophically (47% ≫ 5%).
- **Recommendation, per the pre-stated rule: NO new portfolio breaker.**
  The per-god 40% halts are doing real work (without them the synthetic
  scenario ran to −74% median) and are correctly scaled to each god's
  own volatility, which a book-level trigger is not.

## The finding that matters anyway

In a GFC-scale event, this portfolio loses ~half, breaker or no
breaker. That is not a defect a trigger can fix — it is what being
five concentrated long-equity books IS. The protective stack that
exists (per-god halts, Midas weekly stop, Nemesis −40%, Achilles
off-season cash, kill switch) is roughly right-sized; the only real
lever on tail loss is the total capital allocated to Pantheon, which
is an operator decision, not a god rule. Stated here so the correlated
month, when it comes, is met as expected weather rather than surprise.
