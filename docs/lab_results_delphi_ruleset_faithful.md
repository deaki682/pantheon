# Results — `delphi_ruleset_faithful` (the #11 correction study)

- **Prereg:** [docs/lab_prereg_delphi_ruleset_faithful.md](lab_prereg_delphi_ruleset_faithful.md)
  (committed 2026-07-04 before any faithful cell was computed)
- **Run:** 2026-07-04, `run_delphi_fullwindow.py faithful`, engine
  `shared/gauntlet.py` with `rebalance_band`/`sell_cooldown_days`
  (added same day, tested), selection mirroring
  `delphi/signals.py::rank_by_momentum` line for line
- **Data:** identical panel to #11 (110 PIT top-119 universes, 419
  final tickers, 2.06M bars, SPY TR) — erratum-correction reuse,
  disclosed
- **Registry:** `delphi_ruleset_faithful` → **refuted** (terminal),
  `hypotheses_ever` 96→98

## Verdict

**REFUTED — and harder than the mis-specified #11 variant.** Delphi's
ACTUAL semantics (20-day MA as entry filter inside the ranking, 20%
band, cooldown-on-any-sell), full window, net of costs:

| cell | CAGR | Sharpe | maxDD | excess vs EW-119 | IR |
|---|---|---|---|---|---|
| **faithful_daily** (primary; current live cadence) | **−1.42%** | 0.01 [CI −0.35, 0.39] | −90.5% | **−9.36%/yr** | −0.58 |
| faithful_weekly (original claim's cadence) | 0.74% | 0.14 | −91.9% | −7.20%/yr | −0.41 |
| faithful_daily @2× slippage | −5.04% | −0.20 | −94.2% | −12.98%/yr | −0.81 |
| bench_ew (EW top-119) | 7.94% | 0.49 | −55.1% | — | — |

Excess vs SPY (primary): **−10.10%/yr**.

## Why her true design churns even harder

The MA-as-entry-filter looked like the defensible half of the design;
measured, it is the churn engine. Names oscillate around their 20-day
MA, flickering in and out of the ELIGIBLE set — and a name that drops
out is a full dropout exit, which the 20% band cannot damp (the band
gates trims, not exits, exactly as in her code). Result on the daily
cell: **10,971 round trips, median holding period 3 trading days,
37.4×/yr turnover, ~374bps/yr cost drag** — worse than the strawman's
20×/yr. Weekly evaluation softens it (18.8×/yr, 13-day median hold)
and still loses by 7.2pp/yr. Neither cadence bought crash protection:
max drawdowns of −90.5% and −91.9% vs the benchmark's −55.1%.

## The cross-study reconciliation that closes the case

`faithful_weekly`'s 2021-06→2026-06 segment: **+18.89%/yr**. The #4
replay's Run B on her own code, same window: +143.5% total = **+19.15%/yr**
implied. Two independent implementations agree within 0.3pp/yr — the
faithful simulation is validated against her own code's output, the
2021–26 result was real, and it is the outlier:

| regime | faithful_daily CAGR | faithful_weekly CAGR |
|---|---|---|
| 1999–2002 | −25.72% | −26.05% |
| 2003–2007 | −1.25% | +0.87% |
| 2008–2012 | −11.15% | −10.83% |
| 2013–2019 | +6.37% | +10.23% |
| 2020–2021-05 | +27.19% | +27.46% |
| 2021-06–2026-06 | +13.59% | +18.89% |

## Coverage / disclosures

Identical to #11 (same panel): 0 missing members, 0 price-return-only
symbols, self-audited universe boundary (25 by-design ADR/Canadian
exclusions), layered ticker resolution. Look-ahead is STRICTER than
live: `signal_lag=1`, whereas her live code ranks and trades same-day
— i.e., the live system enjoys a small lookahead this study refuses,
so if anything these numbers flatter her.

## Consequences

This verdict REPLACES #11's as the operative full-window answer on
Delphi's design (per the correction prereg). The family score across
both studies: **five cells tested, five refuted** — her rules at two
cadences, her rules without the exit, the strawman variant, and the
monthly variant, all losing to their own universe's equal weight.
The retire-or-demote question REOPENS on the operator's desk with
clean evidence this time; the operator's standing written override
("don't freeze or change her yet") remains in force until they act.
One dataset, one decision, once: this panel is SPENT for the Delphi
ruleset family — any future momentum idea is a new mechanism, a new
slug, and fresh data.
