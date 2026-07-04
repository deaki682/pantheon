# Prereg — `gauntlet_v1` (the strategy factory, backlog #9 phase b)

- **Slug:** `gauntlet_v1` (factory-level; survivor cells get child slugs, §8)
- **Sponsor:** operator (green-lit 2026-07-04)
- **Date:** 2026-07-04 — committed BEFORE any panel data is pulled.
  The git timestamp of this file is the proof. The only Sharadar
  queries made before this commit were entitlement probes (single
  tickers/days, documented in
  [the status doc](lab_gauntlet_engine_status_2026-07-04.md)); no
  strategy signal has been computed against any data.
- **Engine:** `shared/gauntlet.py` (phase a, built and tested 2026-07-04)

## 1. Deliverable

A quantitative graveyard: every one of the 90 grid cells below gets an
in-sample verdict published in `docs/lab_results_gauntlet_v1.md`, dead
families with the same prominence as survivors. At most 5 cells touch
the holdout, once. At most the holdout passers earn paper forward
tests. This document freezes everything a cell is allowed to be.

## 2. Data (all Sharadar via Nasdaq Data Link, entitled 2026-07-04)

| Table | Use | Span used |
|---|---|---|
| SEP | daily bars: signals (`closeadj`), execution prices (`closeadj`), liquidity (`close` × `volume`), price floor (`close`) | 1998-12-01 → 2025-12-31 |
| DAILY | `marketcap` (USD millions) for point-in-time size universes | 1998-12-01 → 2025-12-31 |

No other data source. Names present in SEP but absent from DAILY on a
signal date are ineligible that date and are counted in the coverage
note of the results doc (survivorship disclosure).

## 3. Universe construction (frozen)

At each **signal date** t (last trading day of calendar month):

1. Eligible = names with a DAILY `marketcap` row AND a SEP bar dated t.
2. Drop names with unadjusted `close` < $3.00 at t.
3. Drop names whose median daily dollar volume (`close` × `volume`)
   over the trailing 21 trading days ending t is < $1,000,000.
4. Rank remaining names by `marketcap` descending:
   - **LARGE** = ranks 1–500
   - **SMALL** = ranks 501–2000
5. Per-cell: names lacking the full lookback window a signal needs
   (e.g. 273 trading days of bars for mom_L252_S21) are ineligible for
   that cell on that date. Disclosed as the recency-of-listing
   restriction inherent to lookback signals.

Ranks 2001+ (true micro-caps) are OUT OF SCOPE for v1 — costs at house
size are not credibly modelable there. Stated here so their absence in
results is by design, not omission.

## 4. Execution model (frozen)

- **Signal date** t = last trading day of month m. All signals use data
  through the close of t and nothing later.
- **Execution date** = first trading day of month m+1, at that day's
  `closeadj`. No same-day signal-and-trade: the engine must apply a
  one-trading-day signal lag (`signal_lag=1`, an engine feature added
  after this prereg commits; the screen cannot run without it).
- Equal weight 1/N across the cell's selected names, remainder in
  cash. No leverage, long only.
- **Costs** (`shared.gauntlet.CostModel`), frozen per bucket:
  - LARGE: commission 0 bps, slippage 5 bps, min ticket $25
  - SMALL: commission 0 bps, slippage 25 bps, min ticket $25
- Delisted names: SEP bars run through a name's true final trading
  day; a position whose bars end is sold at its final close at the
  next monthly rebalance. This is optimistic by the true
  recovery/halt gap (direction of bias: overstates returns, more so
  in SMALL). Disclosed here and again in results.

## 5. THE GRID — 90 cells, enumerated in full

**Signals (15):**

| id | family | rule (rank, select top N) |
|---|---|---|
| mom_L21_S0 | momentum | highest closeadj return over [t−21, t] |
| mom_L63_S0 | momentum | highest return over [t−63, t] |
| mom_L126_S0 | momentum | highest return over [t−126, t] |
| mom_L252_S0 | momentum | highest return over [t−252, t] |
| mom_L21_S21 | momentum | highest return over [t−42, t−21] |
| mom_L63_S21 | momentum | highest return over [t−84, t−21] |
| mom_L126_S21 | momentum | highest return over [t−147, t−21] |
| mom_L252_S21 | momentum | highest return over [t−273, t−21] |
| rev_L5 | reversal | lowest return over [t−5, t] |
| rev_L10 | reversal | lowest return over [t−10, t] |
| rev_L21 | reversal | lowest return over [t−21, t] |
| vol_L63 | low-vol | lowest stdev of daily returns over [t−63, t] |
| vol_L126 | low-vol | lowest stdev of daily returns over [t−126, t] |
| size | size | smallest marketcap at t |
| neglect | neglect | lowest median 21-day dollar volume at t |

(Windows are in trading days; returns from `closeadj`.)

**Portfolio sizes (3):** N ∈ {10, 25, 50}.
**Universes (2):** {LARGE, SMALL}.
**Rebalance (1):** monthly, as §4. Not a free axis.

**Grid = 15 × 3 × 2 = 90 cells**, cell id
`{signal}__N{n}__{bucket}` (e.g. `mom_L252_S21__N25__SMALL`). No cell
may be added, removed, or re-parameterized after this commit; any new
variant is a new prereg under a new slug.

## 6. Splits (frozen; holdout touched once)

- **Warm-up:** bars from 1998-12-01 serve lookbacks only.
- **In-sample:** executions 2000-07 through 2015-12 (186 months).
- **Holdout:** executions 2016-01 through 2025-12 (120 months). Run
  ONLY for the ≤5 stage-1 survivors, ONCE. No cell that failed stage 1
  ever touches holdout data — including "just to see".
- No embargo period beyond the split: forward tests (paper, live-ish
  time) are the third, uncheatable sample.

## 7. Pass bars (frozen)

**Benchmarks:** per bucket, the equal-weight portfolio of ALL eligible
names (§3 steps 1–4), executed identically (§4, same costs, monthly).

**Stage 1 — in-sample screen (all 90 cells):**
- Compute each cell's net daily curve → annualized Sharpe (`summarize`).
- DSR per `deflated_sharpe_ratio` with `n_trials=90`, `n_obs` = count
  of IS daily returns, cell's own skew/kurtosis, `variance_of_sr` =
  cross-sectional variance of the 90 IS Sharpes.
- **Survive iff:** DSR ≥ 0.95 AND net CAGR > matching bucket
  benchmark's net CAGR. Of survivors, only the **top 5 by DSR**
  advance (hard cap).

**Stage 2 — holdout (≤5 cells, once):**
- **Pass iff:** holdout PSR vs 0 ≥ 0.95 (`probabilistic_sharpe_ratio`,
  cell's holdout moments) AND holdout net CAGR > matching benchmark's
  holdout net CAGR.

**Factory verdict (`gauntlet_v1` registry record):**
- `supported` iff ≥1 cell passes stage 2 → those cells go to forward
  tests (§8).
- `refuted` iff stage 1 or stage 2 leaves zero passers.
- `inconclusive` only for material data failure (>20% of intended
  rebalances impossible from coverage holes), documented in results.

**Forward gate (per passing cell):** child slug, paper only, on the
lab ghost ledger. One grade = one execution-month's portfolio excess
return vs the matching benchmark over the same month. Standard house
gate: ≥20 grades, positive SHRUNK mean, `conclude_forward` settles it.

## 8. Multiple-testing accounting (house counter mechanics)

- Registering `gauntlet_v1` adds +1 to `hypotheses_ever`; a counter
  adjustment of **+89** (recorded in the registry with this doc cited)
  brings the total to one count per grid cell. After this prereg the
  house counter reads **91** (1 prior + 90 gauntlet cells).
- Survivor child slugs (e.g. `gauntlet_v1__mom_L252_S21__N25__SMALL`)
  are re-registrations of already-counted cells: each is accompanied
  by a **−1 adjustment** at registration so no cell is counted twice.
  Child slugs cite THIS document as their prereg (their design was
  frozen here; nothing about them is post-hoc except which ones
  survived).
- Any analysis beyond the 90 cells (new signal, new N, new bucket, new
  rebalance frequency) is a new prereg and a fresh count. There is no
  "quick extra look".

## 9. Bias checklist — planned handling (final wording at results time)

1. **Survivorship:** Sharadar SEP/DAILY include delisted names through
   their final trading day (verified live: SIVBQ, BBBYQ). Universes are
   built per-date from names alive THAT day. Names in SEP but missing
   from DAILY are counted and disclosed. Delisting exit optimism
   disclosed (§4).
2. **Look-ahead:** signals through close of t, execution at close of
   t+1 (§4); marketcap dated t is derived from t's close and t's
   latest share count — used only for t's signal, traded t+1.
   Restatements don't apply (no fundamentals in v1 signals).
3. **Selection:** the population is every name passing §3's mechanical
   screens on each date — no hand-picking, no example-driven inclusion.
   The grid itself is the complete pre-committed catalog of variants.
4. **Multiple testing:** 90 trials by design; DSR benchmarked against
   `n_trials=90`; house counter at 91 cited in the results checklist.
5. **Overfitting:** zero free parameters after this commit — every
   knob (windows, N, buckets, floors, costs, splits, bars) is frozen
   here. The IS/holdout split plus the ≤5-survivor cap bounds
   selection intensity on the holdout.
6. **Costs/liquidity:** per-bucket slippage (§4), $1M/day median
   dollar-volume floor, $3 price floor, min ticket $25. SMALL slippage
   of 25 bps is an estimate; results doc must show survivor
   sensitivity at 2× slippage (50 bps) as a robustness disclosure —
   NOT as a pass bar (the bar stays as §7).
7. **Regime:** IS spans dot-com crash, 2003–07 bull, GFC, ZIRP
   recovery; holdout spans 2016–2025 (COVID crash, 2021 melt-up, 2022
   rate shock, 2023–25). A cell must clear both to survive, which is
   the regime test.
8. **Small n:** ~3,900 IS daily observations and 186 monthly
   rebalances per cell; DSR/PSR use the actual `n_obs` with the cell's
   own higher moments. Forward gate needs ≥20 monthly grades before
   validation means anything.

## 10. What this buys

One decision, once: which of these 90 mechanical, long-only,
monthly-rebalanced price/size/liquidity strategies — the simplest
implementable forms of the best-documented cross-sectional anomalies —
actually survive costs, a 16-year in-sample, a 10-year holdout, and
deflation for 90 tries, at the house's own scale. Dead cells become
the empirical floor under every god's priors (the graveyard is the
product). Survivors become citable only after the forward gate, never
autopilots. Event-driven families (earnings, filings, index events)
are explicitly OUT of v1 — they need the event caches and their own
prereg.
