# Results — `delphi_ruleset_fullwindow` (backlog #11)

> **ERRATUM (2026-07-04, same day — operator-ordered accuracy audit).**
> The primary cell did NOT implement "her exact frozen live ruleset" as
> this doc and the prereg claimed. In Delphi's real code
> (`delphi/signals.py::rank_by_momentum`), the 20-day MA is an ENTRY
> FILTER inside the ranking — only names above their MA are ever
> ranked, and holdings below it drop out of the picks at the next
> pass. The cell simulated here ranked ALL names (no MA entry filter)
> and bolted on a standalone DAILY MA stop with a 5-day cooldown — so
> it repeatedly bought below-MA names her rules would never enter and
> then stopped out of them. The real system also carries a 20%
> rebalance band and cooldown-on-any-sell (unmodeled here), and live
> Delphi now evaluates DAILY (2026-07-04 cadence rule), not weekly.
> **What remains valid:** every number below, as a measurement of the
> variant actually simulated; the benchmark and SPY legs; the no-exit
> momentum cell (gauntlet-consistent). **What is retracted:** the
> claim that this tested her ruleset, and the "MA exit is the saboteur
> of HER design" attribution — that measured a strawman. The faithful
> re-test is `delphi_ruleset_faithful`
> (docs/lab_prereg_delphi_ruleset_faithful.md); the registry verdict
> stands for the mis-specified variant this slug actually froze.

- **Prereg:** [docs/lab_prereg_delphi_ruleset_fullwindow.md](lab_prereg_delphi_ruleset_fullwindow.md)
  (committed 2026-07-04 before any data pull for this study)
- **Run:** 2026-07-04, `run_delphi_fullwindow.py` (universes → bars →
  cells), engine `shared/gauntlet.py` with `ExitRules` daily exits,
  `signal_lag=1`, total-return marking
- **Data:** 110 quarterly PIT top-119 universes (Sharadar DAILY
  marketcap, 1999-03-31..2026-06-30) → 419 final tickers, 2.06M SEP
  bars 1998-12..2026-06 (delisted included, 0 members missing, 0
  price-return-only symbols), SPY total return from SFP
- **Registry:** `delphi_ruleset_fullwindow` → **refuted** (terminal),
  `hypotheses_ever` 93→96 (+1 slug, +2 ablation cells, gauntlet_v1
  counting precedent)

## Verdict

**REFUTED** per the frozen criterion (primary-cell excess CAGR vs the
EW top-119 benchmark ≤ 0). Delphi's exact live ruleset, run honestly
over 27 years, lost to everything the prereg measured it against:

| cell | CAGR | Sharpe | maxDD | excess vs EW-119 | IR |
|---|---|---|---|---|---|
| **delphi_live** (primary) | **1.08%** | 0.15 [CI −0.21, 0.52] | −76.7% | **−6.86%/yr** | −0.43 |
| delphi_no_exit (ablation) | 6.92% | 0.40 | −76.8% | −1.01%/yr | −0.00 |
| delphi_monthly (ablation) | −0.61% | 0.01 | −77.2% | −8.54%/yr | −0.52 |
| bench_ew (EW top-119) | 7.94% | 0.49 | −55.1% | — | — |
| delphi_live @2× slippage | −0.93% | 0.02 | −82.1% | −8.86%/yr | −0.54 |

SPY total return over the same window: 8.82% CAGR; primary cell excess
vs SPY: **−7.60%/yr**. Both halves of the SUPPORTED bar fail; the
REFUTED bar (≤0 vs EW) is met with 6.9 points to spare.

## The headline finding: the MA exit is the saboteur, not the savior

The runbook's design rationale credited the 20-day-MA exit as "what
made the backtest work." The ablation measures the opposite at full
window: the exit **cost ~5.8pp/yr** (1.08% with it, 6.92% without).
Per-exit-reason round trips tell the mechanism:

| exit reason | n | win rate | mean return |
|---|---|---|---|
| ma_exit | 4,552 | 32% | −0.52% |
| rebalance (ranking rotation) | 2,517 | 81% | +7.9% |

Four and a half thousand whipsaws: sell on a dip through the MA,
cool down five days, rebuy the same momentum name higher, repeat.
Turnover 20×/yr, cost drag ~200bps/yr at just 5bps slippage — and the
exit bought NO book-level protection (maxDD −76.7% with the exit vs
−76.8% without; the benchmark's was −55.1%). At 2× slippage the
ruleset is a money-losing machine (−0.93% CAGR).

The no-exit ablation is also the gauntlet_v1 reconciliation: exit-less
weekly top-10 momentum earns 6.92% but still loses to plain equal
weight (7.94%) — consistent with the factory's 48 dead momentum cells.
There was never a contradiction between gauntlet_v1 and #4; there was
a hot half-decade.

## Rules vs era: answered

Per-regime table for the primary cell (prereg-frozen boundaries):

| regime | CAGR | Sharpe |
|---|---|---|
| 1999–2002 (dot-com bust) | −16.47% | −0.82 |
| 2003–2007 (bull) | −0.65% | 0.01 |
| 2008–2012 (GFC + recovery) | −5.87% | −0.33 |
| 2013–2019 (bull) | +5.66% | 0.61 |
| 2020–2021-05 (covid/meme) | +29.36% | 1.40 |
| 2021-06–2026-06 (the #4 window) | +12.18% | 0.72 |

Her edge is her era. The #4 replay's +56.8pp window (2021–2026) is the
second-best regime in 27 years; every regime before 2013 lost money.
The 2000–2015 graveyard sub-window the prereg called out in advance:
negative throughout.

## Coverage / survivorship disclosure (mandatory)

- 110/110 quarters built; union 419 final tickers; **0 missing bars, 0
  price-return-only symbols** (full closeadj coverage).
- Boundary audit (self-auditing build): the only above-floor
  exclusions across all 110 quarters were **25 distinct ADR/Canadian
  issuers** (UBS, TM, SHEL, SPOT, SHOP, MELI, BUD, ARM, TTE, …),
  every one verified against TICKERS categories — excluded BY DESIGN
  per the prereg's US-common-only rule (inherited from #4), not a
  coverage hole. Full list in `docs/data/delphi_fullwindow/`.
- Ticker resolution: layered as-traded→final resolver (the first build
  wrongly dropped JPM/BAC/T in 2020 to preferred-series pollution —
  caught by the boundary audit, fixed, rebuilt; also handles dead-
  holder suffixes JPM1/T1 and the spinoff-recycled AA case).
- Capacity: p90 fill participation ~4e-6 of ADV at $10k — capacity is
  a non-issue at house scale, reported per prereg anyway.
- Methodological note: the prereg froze DAILY MA-exit evaluation; live
  Delphi evaluates at her run cadence. The ablations bracket every
  intermediate cadence — daily-exit (1.08%) and never-exit (6.92%)
  BOTH fail the benchmark bar, so the verdict does not hinge on it.

## Consequences (pre-committed in the prereg)

REFUTED → **operator retire-or-demote decision with the numbers; her
live book's fate follows the Midas precedent unless the operator
explicitly overrides in writing.** This study validates history, not
live skill — but the historical claim her live deployment rested on
is now measured false on its own terms: the +85% was real, the alpha
was a broken benchmark (#4), and the ruleset's full-window record is
1.08%/yr against an 7.94% do-nothing benchmark. One dataset, one
decision, once — no re-cuts.

Per-cell artifacts: `docs/data/delphi_fullwindow/` (results.json,
primary + benchmark curves, universes with exclusion log).
