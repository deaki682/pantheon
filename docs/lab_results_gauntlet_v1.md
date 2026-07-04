# Lab Results — `gauntlet_v1` (the strategy factory, backlog #9)

**Slug:** `gauntlet_v1` | **Date:** 2026-07-04 | **Sponsor:** operator | **Verdict: REFUTED**

Prereg: `docs/lab_prereg_gauntlet_v1.md` (committed 2026-07-04 before any
Sharadar panel pull beyond single-ticker/day entitlement probes, per
`docs/lab_gauntlet_engine_status_2026-07-04.md`). Engine: `shared/gauntlet.py`,
extended same day with the `signal_lag` execution-lag guard (commit
`80405e3`) the prereg's §4 execution model requires.

## Population

Monthly point-in-time LARGE/SMALL universes built from the full Sharadar
SEP+DAILY panel per the prereg's §3 mechanical screens, saved as the house
population `gauntlet_v1_universes`
(`cache/shared_pop_gauntlet_v1_universes.json`, 612 rows — one per
signal-date × window × bucket, 1999-12 through 2025-11). Coverage note
carried on the population record: median 3 names/date (max 16, 0.06%) had a
DAILY marketcap but no SEP bar and were excluded; SMALL fills to exactly
1500 names from ~2003 on (1421–1500 in 2000–2002, before that many names
cleared the price/liquidity floors); ranks 2001+ (true micro-caps) excluded
by design, not omission.

## The grid

90 pre-committed cells (15 signal families × N∈{10,25,50} ×
{LARGE,SMALL} — full enumeration in the prereg §5). Zero cells added,
removed, or re-parameterized after the prereg commit.

## Result

| Metric | Value |
|---|---|
| Cells run | 90 (all) |
| Stage 1 (in-sample, 2000-07..2015-12) survivors — DSR ≥ 0.95 (n_trials=90) AND beat bucket benchmark | 10 / 90, all in the **low-vol family** (`vol_L63`, `vol_L126`); every momentum, reversal, size, and neglect cell failed stage 1 |
| Stage 2 (holdout, 2016-01..2025-12, touched once) — top 5 of the 10 by DSR advance | `vol_L126__N10__LARGE`, `vol_L126__N25__LARGE`, `vol_L126__N50__LARGE`, `vol_L126__N50__SMALL`, `vol_L63__N25__LARGE` |
| Stage 2 outcome | All 5: holdout PSR vs 0 = 1.0 (genuinely positive risk-adjusted returns), but **none** beat the matching bucket's equal-weight benchmark net CAGR 2016–2025 — zero stage-2 passers |
| Factory-level mean excess (mean in-sample CAGR gap vs same-bucket EW benchmark, all 90 cells) | **−5.47%/yr** (14/90 cells individually positive) |
| Factory-level mean excess, shrunk (n=90) | **−4.48%/yr** |
| 2× slippage sensitivity (prereg-mandated check on the 5 stage-2 cells) | `vol_L126__N10__LARGE` IS 9.15%/HO 8.52%; `vol_L126__N25__LARGE` IS 9.27%/HO 6.69%; `vol_L126__N50__LARGE` IS 9.48%/HO 8.55%; `vol_L126__N50__SMALL` IS 8.85%/HO 4.13%; `vol_L63__N25__LARGE` IS 8.81%/HO 8.76% — verdicts unchanged at 2× costs |

**Verdict vs the frozen pass bars (prereg §7):** refuted iff stage 1 or
stage 2 leaves zero passers. Stage 2 left zero — **REFUTED**, factory-wide.

## Reading the result

The one family that cleared the deflated in-sample bar — low-volatility —
is exactly the family whose academic story is "leverage-constrained
investors overpay for lottery-like high-vol names," and it is also the
family most mechanically loaded on **regime**: low-vol tilts win big in
crash-heavy samples and lag in one-directional bull markets. The in-sample
window (2000–2015) contains the dot-com crash and the GFC; the holdout
(2016–2025) is a ten-year bull interrupted by one fast COVID crash. All
five survivors posted PSR = 1.0 in the holdout — they were not bad
strategies in absolute terms — but the matching passive benchmark did
better over the same stretch. **The refutation is itself the regime
finding**: the in-sample edge these cells cleared was crash exposure being
priced back into a calm decade, not a persistent, harvestable alpha.

Momentum (8 variants), reversal (3), size (1), and neglect (1) — 13 of 15
signal families across all N/bucket combinations (78 of 90 cells) — failed
even the in-sample deflated-Sharpe bar at this house's cost model and
scale. That is the graveyard this factory was built to produce: these are
not fringe variants, they are the textbook implementations of the four
best-documented cross-sectional equity anomalies, and none of them clear
realistic costs at $10k/cell with a 90-way multiple-testing correction.

## Bias checklist

Recorded in full in `cache/lab_registry.json` (`strategies.gauntlet_v1.backtest.bias_checklist`,
persisted to `origin/claude/live`) via `shared.lab.record_backtest`. Summary:

- **survivorship**: Sharadar SEP/DAILY include delisted names through their
  final trading day (spot-verified: SIVBQ, BBBYQ). 27.2M in-sample bars
  across 14,240 tickers, 0 skipped. DAILY-vs-SEP mismatch: median 3
  names/date (0.06%, max 16) excluded and disclosed. Delisted positions
  sell at a stale final close at the next monthly rebalance — optimistic,
  which can only have understated the refuted families' losses.
- **look_ahead**: signals computed through signal-date t's close; execution
  at t+1's close via the engine's `signal_lag` feature (added before any
  screen run — the screen could not execute without it). Marketcap dated t
  is used only for t's signal, traded t+1. No fundamentals, no restatement
  exposure.
- **multiple_testing**: 90 trials by design, all counted —
  `hypotheses_ever` went 1→91 at prereg time (registry counter adjustment,
  cited in the prereg §8). DSR benchmarked against `n_trials=90` with the
  grid's own cross-sectional Sharpe variance. Holdout touched exactly once,
  by the top 5 only; no cell beyond the 90 was ever computed.
- **overfitting**: zero free parameters after the prereg commit — windows,
  N, buckets, floors, costs, splits, and bars were all frozen before data.
  The refutation is itself the overfitting demonstration: 10 cells cleared
  a deflated in-sample bar and all 5 advancing cells failed out-of-sample
  against the benchmark.
- **regime**: in-sample spans the dot-com crash and GFC; holdout is one
  long bull with a fast COVID crash (prereg §9.7 named clearing both as the
  regime test). Low-vol passed the crash-heavy sample and failed the bull
  decade against the benchmark — see "Reading the result" above.
- **selection**: population is every name passing the prereg's mechanical
  screens on each of 186 IS + 120 HO month-ends — no hand-picking, saved as
  the house population `gauntlet_v1_universes` (612 rows, coverage note
  above). The grid itself was the complete pre-committed catalog; nothing
  added or removed post-commit.
- **costs_liquidity**: per-bucket linear slippage (LARGE 5bps, SMALL
  25bps), $25 min ticket, $3 price floor, $1M median-21d-dollar-volume
  floor, at $10k/cell. 2× slippage sensitivity on the 5 stage-2 cells left
  every verdict unchanged (table above).
- **small_n**: ~3,900 in-sample daily returns and 186 IS + 120 HO monthly
  rebalances per cell; DSR/PSR computed with each cell's own n_obs, skew,
  and kurtosis. Factory-level mean_excess (−5.47%/yr, shrunk −4.48%/yr) is
  the mean IS CAGR gap across all 90 cells; shrinkage on n=90 leaves the
  sign untouched. No forward test follows a refuted verdict.

## Known documentation gap

The registry's `notes` field, written when `record_backtest` ran, points to
`docs/data/gauntlet_v1/` for "per-cell data." That directory was never
created and the per-cell daily equity curves (90 cells × ~300 months each)
were not separately archived as flat files — they do not survive past the
scratch session that computed them, per the project's design (heavy
intermediate computation is not meant to persist; only the record you
choose to `persist()` does). **The complete surviving record of this run's
numbers is the registry entry itself**
(`cache/lab_registry.json` → `strategies.gauntlet_v1`, persisted to
`origin/claude/live`) plus this document, which transcribes it in full. Any
future work needing the raw per-cell curves (e.g. a closer look at *why*
the 5 low-vol survivors underperformed the benchmark specifically) would
need to re-run the frozen grid definition against the `gauntlet_v1_universes`
population — the universe and cost model are both already house assets, so
that re-run is cheap; it just wasn't archived as a separate doc this time.

## Decision

**REFUTED**, factory-wide, per the prereg's pre-committed pass bars
(§7). `shared.lab.record_backtest` recorded this as `gauntlet_v1: refuted`
— terminal for this slug. No forward test follows (only `supported`
backtests earn the paper forward gate). This closes backlog #9. Backlog
#4 (Delphi point-in-time universe rebuild) rides the same engine
(`shared/gauntlet.py`, `signal_lag`) and the same Sharadar bulk-fetch
plumbing, but is a distinct hypothesis (is Delphi's own 118-name momentum
backtest survivorship-biased?) and remains open — the factory's refutation
says nothing about whether *that specific* backtest's evidence is real.
