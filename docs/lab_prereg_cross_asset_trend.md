# Prereg — `cross_asset_trend` (house lab, operator-commissioned 2026-07-04)

- **Slug:** `cross_asset_trend`
- **Sponsor:** operator
- **Date:** 2026-07-04 — committed BEFORE any ETF bar is fetched. The
  only prior touch of this universe is general domain knowledge of
  which tickers exist and roughly when they listed — no price, no
  return, no signal value of any kind has been computed for any of
  these instruments before this commit.

## Why this is a genuinely different test, not a 91st Gauntlet cell

`gauntlet_v1` (REFUTED, `docs/lab_results_gauntlet_v1.md`) tested only
**cross-sectional** signals on **individual US equities**: rank names
against each other on momentum/reversal/vol/size/neglect, hold the
top/bottom N. This study tests **absolute (time-series) trend** on
**macro asset-class ETFs** — rates, credit, commodities, currencies,
country equity indices. The mechanism is structurally different:
cross-sectional equity momentum's proposed source is slow information
diffusion about a SPECIFIC COMPANY; time-series trend's proposed source
(Moskowitz/Ooi/Pedersen 2012 and the "dual momentum" literature) is
persistent one-directional order flow from institutions that trade an
ASSET CLASS for reasons unrelated to return forecasting — a pension
de-risking into bonds on a fixed schedule, an airline programmatically
hedging fuel costs, a central bank managing a currency band, a
sovereign wealth fund rebalancing a commodity allocation. Gauntlet's
refutation of cross-sectional equity factors says nothing about whether
this different, non-refuted mechanism holds elsewhere. It also sits
squarely in Proteus's chartered universe ("the full ETF window onto
commodities/rates/currencies/countries/vol") that no house study has
touched yet.

## Mechanism, who loses, why underutilized (hypothesis fields)

- **Mechanism**: hedgers, sovereign/pension rebalancers, and
  policy-driven actors (central banks, government debt-management
  offices) trade rates/currencies/commodities on fixed schedules or
  policy mandates, not short-term return forecasts. This creates
  autocorrelated order flow that a simple trend/absolute-momentum rule
  can ride, distinct from the equity-specific "analyst underreaction"
  story Gauntlet's momentum cells relied on (and which failed at house
  scale/costs).
- **Who loses**: non-forecasting flow — a fuel hedger who buys oil
  futures/ETPs to lock a cost regardless of price view, a pension plan
  shifting to bonds on a glide-path schedule regardless of the rate
  outlook, a central bank defending a currency band. None of these
  actors are trying to win a forecasting game; the trend-follower is
  the counterparty who gets paid to accept the flow's direction.
- **Underutilized because**: retail/self-directed capital overwhelmingly
  concentrates on single-stock picking (as this house's own prior
  studies — Oracle, Midas, Gauntlet — all did); a simple absolute-trend
  overlay on ~17 liquid macro ETFs requires no stock-picking skill at
  all and is mechanically trivial to run, yet is rarely deployed by
  small accounts, who default to buy-and-hold or single-stock bets
  instead. The professional CTA/managed-futures space runs this at
  scale, but typically with leverage, shorting, and dozens of futures
  contracts unavailable to a long-only, no-leverage account — this
  study asks whether a STRIPPED-DOWN, long-only-or-cash, ETF-only
  version still captures any of that premium.
- **Falsifiable claim**: at least one of the two frozen signal variants
  below clears the deflated in-sample bar (DSR ≥ 0.95 at n_trials=2) AND
  beats the always-invested benchmark net CAGR, THEN clears the same
  bar on the untouched holdout. Zero passers at either stage refutes
  cross-asset trend-following in this stripped-down form.

## Population (FROZEN, fixed universe — no ranking, no PIT selection)

Unlike Gauntlet's point-in-time ranked universes, this is a FIXED,
named list of 17 liquid, long-history macro ETFs, one per asset-class
slot, chosen for category coverage and inception date (all listed by
~2007) — not screened or ranked by any performance criterion:

| Ticker | Asset class | Slot |
|---|---|---|
| TLT | Rates | 20+ year US Treasury |
| IEF | Rates | 7-10 year US Treasury |
| SHY | Rates | 1-3 year US Treasury |
| LQD | Credit | Investment-grade corporate |
| HYG | Credit | High-yield corporate |
| GLD | Commodity | Gold |
| SLV | Commodity | Silver |
| USO | Commodity | Crude oil |
| DBA | Commodity | Agriculture |
| DBB | Commodity | Base metals |
| UUP | Currency | US dollar (bullish basket) |
| FXE | Currency | Euro |
| FXY | Currency | Japanese yen |
| EEM | Country/region equity | Emerging markets |
| EFA | Country/region equity | Developed ex-US |
| FXI | Country/region equity | China large-cap |
| EWZ | Country/region equity | Brazil |

**Explicitly excluded, disclosed here before any data is touched**:
volatility-linked ETPs (VXX and similar). Their structural futures-roll
decay is a confound orthogonal to spot-price trend and would make any
result about this study's actual question (does trend in the
UNDERLYING asset persist) uninterpretable without a separate
roll-adjustment methodology this prereg does not attempt. A vol-carry
study is a legitimate SEPARATE hypothesis for a future slug, not folded
in here.

**No survivorship risk in this universe**: none of these 17 (the
benchmark uses the same 17) have delisted or been materially
restructured over the test window; this is disclosed as a design choice
(fixed, currently-live, liquid instruments), not evidence there is no
survivorship question in ETPs generally (e.g., leveraged/inverse ETPs
close far more often — out of scope here).

## Execution model (FROZEN)

- **Bars**: Robinhood daily OHLC (split-adjusted), per-symbol, fetched
  in ≤9-symbol batches via the house's `shared.historicals` plumbing.
- **Signal date** t = last trading day of each calendar month. **Signal
  lag = 1**: the selection rule sees bars only through the trading day
  BEFORE the execution day (engine's `signal_lag` feature, identical
  discipline to `gauntlet_v1`).
- **Execution date** = first trading day of the next month, at that
  day's close.
- **Per-asset eligibility**: an asset needs ≥252 trading days of prior
  bars to have a valid signal on a given date; assets without enough
  history are simply not eligible that month (same disclosed convention
  as `gauntlet_v1` §3.5 — no assumed inception dates baked into this
  prereg, the data itself decides eligibility mechanically).
- **First live rebalance**: the first month-end where ALL 17 assets are
  simultaneously eligible (reported exactly in the results doc — not
  assumed here).
- **Costs** (`shared.gauntlet.CostModel`): commission 0 bps, slippage 3
  bps (tighter than Gauntlet's LARGE-bucket 5bps — these are among the
  most liquid ETFs traded, a conservative-toward-the-strategy but
  disclosed choice), min ticket $25, at $10,000 total (house-scale
  convention, same as Gauntlet).
- **Cash proxy**: 0% return (literal cash), not a T-bill or short-
  duration bond ETF (avoids circularity with the rates sleeve).
  Disclosed as conservative: this UNDERSTATES real-world cash yield in
  high-rate periods (2022-2024), which can only make an "out of
  position" period look WORSE than reality — biases toward refutation,
  not support.

## The grid — 2 cells, enumerated in full

1. **`abs_mom_252`**: for each asset, long (equal weight among all
   currently-long assets, rest in cash) iff trailing 252-trading-day
   total return (close-to-close) > 0. Classic time-series/absolute
   momentum (Moskowitz-Ooi-Pedersen; Antonacci "dual momentum" absolute
   leg).
2. **`sma_200`**: for each asset, long (same equal-weight construction)
   iff current close > its own 200-trading-day simple moving average.
   Classic trend-filter (same family Delphi already uses for her
   EXIT rule, applied here as an ENTRY/exposure filter across assets
   instead of a single-name stop).

No top-N selection, no per-asset weighting scheme beyond 1/(number
currently long) — avoiding an extra free parameter. **Grid = 2 cells.**
No cell may be added, removed, or reparameterized after this commit;
any new variant (different lookback, vol-targeting, leverage) is a new
prereg under a new slug.

## Benchmark (FROZEN)

Equal-weight buy-and-hold of the same 17-asset universe, rebalanced
monthly back to 1/17 each, no trend filter, same cost model. Tests
whether TIMING adds value over simply holding the diversified basket
unconditionally.

## Splits (FROZEN; holdout touched once)

- **Warm-up**: bars from first availability serve the 252-day lookback
  only.
- **In-sample**: executions from the first fully-eligible month-end
  (see above) through 2017-12.
- **Holdout**: executions 2018-01 through 2026-06 (once, for whichever
  cell(s) pass stage 1 — both may advance since the grid is only 2
  cells, no top-N cap needed). Includes the 2018 vol spike, 2020 COVID
  crash, 2021-22 inflation/rate shock, and 2022 bond bear market — a
  materially different regime than the in-sample QE-era stretch.

## Pass bars (FROZEN)

**Stage 1 (in-sample, both cells)**: annualized Sharpe → DSR with
`n_trials=2` (negligible deflation at this trial count, computed
honestly rather than assumed away), cell's own skew/kurtosis,
`variance_of_sr` = cross-sectional variance of the 2 in-sample Sharpes.
**Survive iff**: DSR ≥ 0.95 AND net CAGR > the benchmark's in-sample net
CAGR.

**Stage 2 (holdout, survivors only, once)**: PSR vs 0 ≥ 0.95 AND net
CAGR > the benchmark's holdout net CAGR.

**Verdict**: `supported` iff ≥1 cell passes stage 2; `refuted` iff stage
1 or stage 2 leaves zero passers; `inconclusive` only for material data
failure (>20% of intended rebalances impossible from coverage holes).

**Forward gate** (per passing cell, standard house rule): child slug,
paper only, ≥20 monthly grades on the shrunk mean before
`conclude_forward` — same gate every other house strategy faces.

## Multiple-testing accounting

Registering `cross_asset_trend` adds +1 to `hypotheses_ever`; a
counter adjustment of +1 (this doc as citation) brings the total to one
count per grid cell (2 cells = 2 counts), identical bookkeeping
convention to `gauntlet_v1`'s cell-per-count rule. After this prereg the
house counter reads whatever it was before this study, +2.

## Bias checklist — planned handling (final wording at results time)

1. **Survivorship**: fixed, currently-live, liquid ETF universe — no
   delistings in this test window; disclosed above as a scope choice
   (leveraged/inverse ETP survivorship risk is real and explicitly out
   of scope).
2. **Look-ahead**: signal_lag=1 (signals through close of t−1 relative
   to the trading day used for lagged selection, execution at close of
   the rebalance day) — identical mechanical guard as Gauntlet.
3. **Selection**: the 17-name universe was chosen for asset-class
   category coverage and long inception history BEFORE any return was
   examined — one liquid, well-known instrument per slot (e.g., GLD
   for gold, not a screen of all gold ETFs), disclosed as a judgment
   call, not a performance-driven pick. The two signals are the
   complete, pre-committed grid.
4. **Multiple testing**: 2 trials, counted via `hypotheses_ever`
   (above). DSR benchmarked against `n_trials=2`.
5. **Overfitting**: zero free parameters after this commit — lookback
   windows (252-day, 200-day) are the canonical textbook values from
   the cited literature, not tuned to this dataset; portfolio
   construction (equal-weight among currently-long assets) has no
   free knob.
6. **Costs/liquidity**: 3bps slippage disclosed as a judgment call
   (tighter than Gauntlet's LARGE bucket) — results doc must show
   survivor sensitivity at 2× slippage (6bps) as a robustness check, not
   a pass bar.
7. **Regime**: in-sample is dominated by the 2008-2017 QE-era/low-rate
   stretch; holdout (2018-2026) includes a genuine bond bear market
   (2022) and a currency/rate regime change — a materially different
   test than Gauntlet's equity-only regime split.
8. **Small n**: monthly rebalance over an 18+ year window yields roughly
   130-230 in-sample and ~100 holdout monthly observations (exact counts
   reported once bars are pulled) — comparable in count to Gauntlet's
   own per-cell monthly rebalance counts, though DAILY equity-curve
   observations (used for Sharpe) will be far more numerous than
   monthly rebalance counts.

## What this buys

One decision, once: does a stripped-down, long-only-or-cash,
zero-leverage absolute-trend overlay on 17 liquid macro ETFs — the
simplest implementable form of the trend/managed-futures premium —
survive realistic costs, a decade-plus in-sample, and a materially
different-regime decade-long holdout, at the house's own account
constraints? A supported cell becomes citable in Proteus's live thesis
only after the standard ≥20-grade forward gate — never an autopilot.
