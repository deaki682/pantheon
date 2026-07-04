# Lab Results — `cross_asset_trend` (macro ETF trend-following)

**Slug:** `cross_asset_trend` | **Date:** 2026-07-04 | **Sponsor:** operator | **Verdict: REFUTED**

Prereg: `docs/lab_prereg_cross_asset_trend.md` (committed before any ETF
bar was fetched). Engine: `shared/gauntlet.py` (reused as-is — fixed
universe, no point-in-time ranking needed).

## Why this was worth testing after Gauntlet's refutation

`gauntlet_v1` refuted 90 cross-sectional equity factors. This tests a
structurally different mechanism (persistent order flow from
non-forecasting hedgers/rebalancers, not analyst underreaction to a
specific company) on a different asset class (macro ETFs: rates,
credit, commodities, currencies, country equities) that no house study
had touched.

## An infrastructure bug found and fixed before any signal was computed

Pulling 2006–2026 daily bars for all 17 ETFs surfaced a real data
artifact: Robinhood's historicals endpoint pads dates before a symbol's
real listing with a **flat, constant-OHLC placeholder bar** instead of
returning `not_found`. Confirmed on SHY: 418 consecutive bars at
exactly $81.05 (open=high=low=close, volume=0) from the requested
2006-01-01 start, then a genuine jump (close $81.25, volume 2,442,400)
on 2007-08-31 — SHY's real data-start date in this feed. This is
distinct from a genuine low-volume day: EEM and FXI both show
volume=0 on many 2006 bars while their OHLC still moves realistically
day to day, confirming they were actually trading (their real Sharadar-
independent listing dates, April 2003 and October 2004, predate this
study's pull window entirely).

Left uncorrected, this would have fed 12+ months of fake zero-
volatility "trading days" into the 252-day and 200-day lookback windows
for the later-listed ETFs (HYG, DBA, DBB, UUP, FXY, SHY), corrupting
their earliest signals. Fixed mechanically — strip the leading run of
bars identical to the first bar's close — and verified against the
EEM/FXI counter-case before trusting it. Landed as a reusable house
utility: `shared.historicals.strip_preinception_padding()`. **Any
future study pulling Robinhood historicals for an instrument that might
post-date the pull's start should call this first.**

| Ticker | Real data-start (post-strip) | Padding stripped |
|---|---|---|
| TLT, IEF, GLD, FXE, EEM, EFA, FXI, EWZ | 2006-01-03 (pull start) | 0 days |
| LQD | 2006-01-04 | 1 day |
| USO | 2006-04-10 | 67 days |
| SLV | 2006-04-28 | 80 days |
| DBA, DBB | 2007-01-05 | 253 days |
| UUP | 2007-02-20 | 283 days |
| FXY | 2007-02-13 | 279 days |
| HYG | 2007-04-11 | 318 days |
| SHY | 2007-08-31 | 418 days |

## Population and design

Fixed 17-ETF universe (TLT, IEF, SHY, LQD, HYG, GLD, SLV, USO, DBA,
DBB, UUP, FXE, FXY, EEM, EFA, FXI, EWZ), one per rates/credit/
commodity/currency/country-equity slot, per the prereg. First month-end
where all 17 have ≥252 real trading days: **2008-08-29**. 215 monthly
rebalances run through 2026-06-30 (signal_lag=1, $10k notional, 3bps
slippage, $25 min ticket, 0% cash proxy).

Two cells: `abs_mom_252` (long assets with positive trailing 252-day
return, equal-weighted, rest cash) and `sma_200` (long assets trading
above their own 200-day SMA, same construction). Benchmark: equal-
weight buy-and-hold of the same 17 ETFs, monthly rebalanced, no filter.

## Result

| Metric | `abs_mom_252` | `sma_200` | Benchmark (EW buy-and-hold) |
|---|---|---|---|
| In-sample (2008-08..2017-12) CAGR | **−1.48%** | **1.21%** | 0.08% |
| In-sample Sharpe | −0.096 | 0.172 | 0.063 |
| In-sample DSR (n_trials=2) | **0.00** | **1.00** | — |
| Stage 1 (DSR≥0.95 AND beat benchmark) | **FAIL** | **PASS** | — |
| Holdout (2018-01..2026-06) CAGR | 0.87% | **1.28%** | **3.03%** |
| Holdout PSR (vs 0) | 1.00 | 1.00 | — |
| Stage 2 (PSR≥0.95 AND beat benchmark) | not run (failed stage 1) | **FAIL** | — |
| Holdout CAGR @ 2× slippage (6bps) | — | 1.11% | — |

**Factory-level mean excess** (mean IS CAGR gap vs benchmark, n=2):
**−0.24%/yr** (shrunk, n=2: **−0.02%/yr**) — near zero, honestly
reflecting one outright failure and one narrow near-miss rather than a
uniform result.

**Verdict vs the frozen pass bars**: `abs_mom_252` failed stage 1
outright (negative Sharpe, DSR=0, also lost to the benchmark
in-sample). `sma_200` cleared stage 1 cleanly (DSR=1.00, beat the
benchmark's anemic 0.08% IS CAGR by over a full point) and posted a
genuinely positive holdout Sharpe (PSR=1.00) — but its holdout CAGR
(1.28%) did not beat the benchmark's holdout CAGR (3.03%). **Zero
stage-2 passers — REFUTED.** Unchanged at 2× slippage.

## Reading the result

The pattern is the same one that killed Gauntlet's low-vol survivors:
a strategy that looks genuinely good on its own terms (positive
Sharpe, positive PSR) can still lose to a benchmark that simply had a
better decade. Here the mechanism is legible: the in-sample window
(2008–2017) was a stretch where the always-invested benchmark barely
made money (0.08%/yr) — bonds and commodities chopped sideways for
years post-GFC — so a trend filter that avoided the chop had obvious
room to add value. The holdout (2018–2026) contained real trend
regimes (2018 vol spike, COVID crash, 2022 bond bear) but ALSO a
powerful multi-year recovery that the always-invested benchmark
captured in full; `sma_200`'s periodic moves to cash captured only
part of that recovery. A defensive filter earns its keep by avoiding
drawdowns, not by winning bull markets outright — and this decade's
bull was strong enough that avoiding some of the drawdowns wasn't
worth missing some of the recovery, net of costs.

One disclosed conservative assumption cuts against the strategy here:
cash is modeled at a literal 0% return, not a T-bill rate. Real-world
T-bill yields were 4-5% for much of 2022–2024, meaning a real
implementation's holdout CAGR would have been somewhat higher than
1.28% during its cash periods — plausibly enough to close some but very
likely not all of the 1.75-point gap to the benchmark's 3.03%. This is
flagged as a real limitation of this specific test, not grounds to
overturn the verdict: the benchmark also holds no cash drag at all
(always 100% invested), so a T-bill credit narrows the gap without
being obviously large enough to flip a REFUTED verdict on its own.

## Bias checklist

Recorded in full in `cache/lab_registry.json`
(`strategies.cross_asset_trend.backtest.bias_checklist`, persisted to
`origin/claude/live`) via `shared.lab.record_backtest`. Summary above
covers survivorship (including the placeholder-padding bug and fix),
look-ahead (signal_lag=1), multiple testing (n_trials=2,
`hypotheses_ever` 92→93), overfitting (zero free parameters, canonical
lookback windows), regime (IS low-return chop vs. HO real-trend-plus-
strong-recovery), selection (fixed named universe, disclosed judgment
call), costs (3bps, 2× sensitivity unchanged), and small-n (215 monthly
rebalances, ~2,300 daily observations per leg).

## Decision

**REFUTED.** `shared.lab.record_backtest` recorded this as
`cross_asset_trend: refuted` — terminal for this slug. No forward test
follows (only a `supported` backtest earns the paper gate). This is a
different mechanism and asset class than `gauntlet_v1`, refuted for a
structurally similar reason (a simple long-only, no-leverage
implementation loses to a passive benchmark once the benchmark gets
credit for a strong recovery period) rather than the same reason —
worth noting as a second, independent data point that "beat a passive
benchmark net of costs" is a genuinely hard bar at this house's scale
and constraints, across two unrelated signal families now. The
`strip_preinception_padding` fix is the lasting asset from this study
and is available to every future Robinhood-historicals-based test.
