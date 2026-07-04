# Results — `momentum_trend_exit_largecap` (hypothesis #92)

- **Prereg:** [docs/lab_prereg_momentum_trend_exit_largecap.md](lab_prereg_momentum_trend_exit_largecap.md)
  (committed before the study's only new data pull)
- **Run:** 2026-07-04, `run_momentum_trend_exit.py` — one run, as
  frozen. Engine: `delphi.backtest.run_backtest` with the
  delisting-exit fix (commit `4816307`, committed before this run).
- **Coverage:** 84 quarter-end universes, 352-ticker union, **all 352
  loaded** (DAILY history keys to final Sharadar tickers; zero renames
  needed, zero members missing bars). Delisted members included
  through their final trading day.

## Verdict: REFUTED (terminal), decisively

| | net CAGR | total | Sharpe | maxDD | monthly excess vs SPY |
|---|---|---|---|---|---|
| **Strategy** (net of 5 bps/side) | **−4.38%** | **−60.8%** (gross −47.8%) | −0.06 | **−87.4%** | mean −0.843%/mo, **t = −3.91**, n = 251 |
| SPY buy-and-hold | +7.24% | +331.6% | — | — | — |
| EW-119 (same universe, quarterly, 5 bps) | +6.56% | — | 0.42 | −53.7% | — |

The mechanics that returned +143.5% (+56.8pp over SPY) in the
2021–2026 discovery window **destroyed 61% of capital** over the
21 pre-discovery years while the market compounded at 7.2% and the
strategy's own universe at 6.6% equal-weighted. Costs are irrelevant
to the verdict (12.9% of initial over 21 years): the strategy fails
by 380 points **gross**.

## Attribution (year-end equity, $10k start)

| span | strategy | context |
|---|---|---|
| 2000–2002 | **−66%** ($10,000 → $3,414) | Dot-com unwind: momentum = tech mega-caps; the MA exit did not save it — bear-rally whipsaws kept re-entering |
| 2003–2007 | **−7%** in a +80% bull | Pure whipsaw/churn bleed — the same signature as gauntlet_v1's 48 dead momentum cells |
| 2008–2009 | −48% cumulative | The classic momentum crash: crushed down, then in cash for the 2009 rebound |
| 2010–2019 | ≈ index at best | +6.9%/yr with SPY at +13%/yr |
| 2020–2021 | +51% | The ONLY strong span — the start of the mega-cap melt-up regime |

Reading: momentum + trend-exit on mega-caps is not persistent alpha
with crash protection; it is a **concentrated bet on sustained
mega-cap-led melt-ups**. The 2021–2026 discovery window was that
regime, top to bottom. Everywhere else in 26 years of data the form
ranges from index-lagging to catastrophic.

## What this settles for the house

1. The momentum family is now dead at house scale under THREE
   independent pre-registered attacks: 48 gauntlet cells (monthly,
   no exit), this weekly trend-exit form (the published cure), and —
   as regime context — low-vol's holdout failure. `refuted` is
   terminal; any future momentum variant needs a new slug, a fresh
   counter increment, and a mechanism that explains all of the above.
2. The Delphi PIT replay's +56.8pp stands as measured but must never
   be cited without this study beside it: same mechanics, adjacent
   window, opposite sign. Window selection IS the result.
3. Delphi's live strategy keeps running on its own gates (live graded
   calls), which are precisely the right instrument: her mechanics'
   backtest evidence is now regime-conditional in both directions,
   and only forward grades can settle what the current regime pays.
   Whether this study changes her disposition is an operator decision
   outside this study's scope.

## Consistency check on published work

The 2021–2026 PIT replay was re-run under the delisting-exit fix as
part of this study: results byte-identical (+85.61% / +143.51% /
−1.08pp / +56.82pp) — no held delistings priced through the old code
path in that window. The published results doc stands without
amendment.

## Bias checklist

All eight items recorded in the registry entry
(`cache/lab_registry.json`, slug `momentum_trend_exit_largecap`);
highlights: coverage complete (352/352), costs immaterial to verdict,
the same-day-signal convention shared with the citation under test
could only have flattered the refuted strategy, and n=251 monthly
observations at t = −3.91 is decisive, not underpowered.

## Artifacts

- `docs/data/momentum_trend_exit/mte_results.json` — full metrics
- `docs/data/momentum_trend_exit/mte_curve.json` — daily equity curve
