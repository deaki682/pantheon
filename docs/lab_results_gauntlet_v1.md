# Results — `gauntlet_v1` (the strategy factory, backlog #9 phases c–d)

- **Prereg:** [docs/lab_prereg_gauntlet_v1.md](lab_prereg_gauntlet_v1.md)
  (committed 2026-07-04 before any panel pull; grid, splits, and bars
  frozen there)
- **Run:** 2026-07-04, `run_gauntlet_screen.py` (stage 1) and
  `run_gauntlet_holdout.py` (stage 2), engine `shared/gauntlet.py` +
  `shared/gauntlet_fast.py` (equivalence-pinned)
- **Data:** Sharadar SEP + DAILY (entitled 2026-07-04). In-sample
  panel: 27,239,343 SEP rows, 14,240 tickers, 1998-12-01→2016-01-31,
  0 rows skipped.

## Verdict

**REFUTED** (registry record 2026-07-04, terminal). Stage 1 killed
80/90 cells; the one holdout pass killed the remaining five: every
top-5 low-vol cell earned positive absolute returns out-of-sample
(PSR vs zero = 1.0000) but **none beat its bucket's equal-weight
benchmark in 2016–2025** — and the prereg's bar was benchmark-relative
for exactly this reason. The factory produced a graveyard and zero
forward tests. `hypotheses_ever` stands at 91; any v2 is a new prereg.

## Stage 1 — in-sample screen (all 90 cells, executions 2000-07..2015-12)

Benchmarks (equal-weight of the full eligible bucket, same execution
model and slippage, min_ticket=0):

| bucket | CAGR | Sharpe | maxDD |
|---|---|---|---|
| LARGE | 5.51% | 0.36 | −57.4% |
| SMALL | 6.79% | 0.40 | −61.1% |

Family results (net of costs; Sharpe min/median/max across cells):

| family | cells | Sharpe range | survivors |
|---|---|---|---|
| momentum (8 variants × 3 N × 2 buckets) | 48 | −0.16 / 0.15 / 0.33 | **0** |
| reversal (3 × 3 × 2) | 18 | −0.15 / 0.14 / 0.24 | **0** |
| low-vol (2 × 3 × 2) | 12 | 0.63 / 0.77 / 0.84 | **10** |
| size (1 × 3 × 2) | 6 | 0.28 / 0.37 / 0.44 | **0** |
| neglect (1 × 3 × 2) | 6 | 0.08 / 0.25 / 0.31 | **0** |

The graveyard, plainly: **every long-only momentum, reversal, size,
and neglect cell died in-sample** — most with negative absolute CAGR
after costs (short-lookback momentum was catastrophic: −70% to −82%
max drawdowns; equal-weight monthly-rebalanced long-only momentum
never beat its bucket's own equal-weight portfolio). This is the
empirical floor under every god's priors the backlog item asked for:
the simplest implementable forms of these famous anomalies do not
survive costs and a same-universe benchmark in 2000–2015.

**Low-volatility is the sole surviving family**: 10 of 12 cells
cleared DSR ≥ 0.95 (n_trials=90, variance_of_sr = 0.0556 measured
across the grid) AND beat their bucket benchmark. Sharpe 0.74–0.84 vs
benchmarks' 0.36–0.40, with visibly shallower drawdowns (−31% to −45%
vs −57%/−61%). Consistent with the literature: the low-vol anomaly was
strongest precisely in samples containing two crashes.

Top-5 by DSR (advance to holdout): `vol_L126__N50__SMALL`,
`vol_L63__N25__LARGE`, `vol_L126__N10__LARGE`, `vol_L126__N25__LARGE`,
`vol_L126__N50__LARGE`. The four cells with DSR = 1.0 at float
precision all sit inside the top 4, and rank 5 exceeds rank 6 at the
10th decimal — so the advancing SET is independent of any tie-break.

## Stage 2 — holdout (top-5 cells, executions 2016-01..2025-12, touched once)

Holdout panel: 18.36M SEP rows, 13,343 tickers (253 off-calendar rows
skipped, 0.001%). Benchmarks: LARGE 11.43% CAGR / Sharpe 0.70; SMALL
9.50% / 0.53 — a bull decade.

| cell | CAGR | Sharpe | maxDD | PSR vs 0 | beats benchmark | PASS |
|---|---|---|---|---|---|---|
| vol_L126__N50__SMALL | 5.57% | 0.47 | −41.4% | 1.0000 | no (9.50%) | **no** |
| vol_L63__N25__LARGE | 9.22% | 0.76 | −29.8% | 1.0000 | no (11.43%) | **no** |
| vol_L126__N10__LARGE | 8.85% | 0.75 | −26.1% | 1.0000 | no (11.43%) | **no** |
| vol_L126__N25__LARGE | 6.97% | 0.57 | −34.4% | 1.0000 | no (11.43%) | **no** |
| vol_L126__N50__LARGE | 8.79% | 0.69 | −35.0% | 1.0000 | no (11.43%) | **no** |

Reading: real defensiveness (drawdowns −26% to −41% vs benchmarks'
COVID-era troughs, all-positive absolute returns) — but the in-sample
Sharpe advantage came from a sample containing two deep crashes, and
in a decade with one fast crash and a long melt-up, low-vol lagged the
market it was drawn from. Prereg §9.7 named this exact failure mode.
Low-vol survives as a risk-shaping observation, not as citable alpha.

## Coverage / survivorship disclosure (mandatory)

- In-sample panel: 27.24M SEP rows across 14,240 tickers; 0 unparsable.
  Delisted names present through their final trading day (Sharadar SEP
  convention, verified on SIVBQ/BBBYQ at entitlement time).
- DAILY (marketcap) vs SEP mismatch: median 3 names per signal date
  (0.06% of the ~5,900 DAILY names/date; max 16) had a DAILY marketcap
  but no SEP bar that day and were excluded — negligible, disclosed.
- Universe funnel per signal date (medians): 5,925 DAILY names → 765
  dropped by the $3 price floor, 1,977 by the $1M median-dollar-volume
  floor → 2,848 eligible → LARGE = top 500, SMALL = next 1,500 (SMALL
  filled to exactly 1,500 in later years; 1,421–1,500 in the early
  2000s when fewer names cleared the floors).
- No cell ever had fewer eligible names than its N — the prereg's
  short-universe fallback (hold all eligible) never fired.
- Delisting exits are optimistic by construction: a dead name's stale
  final close is sellable at the next monthly rebalance (prereg §4
  disclosure). Direction of bias: overstates returns, more so in SMALL
  — and therefore does NOT rescue the refuted families, whose failure
  it can only have understated.

## Operational defaults beyond the prereg (all in `screen_manifest.json`)

- Initial capital $10,000/cell (min_ticket $25 binds only on
  sub-0.25% rebalance deltas).
- Benchmarks run min_ticket=0 (a 500-name EW benchmark at $10k has $20
  tickets; it is a measuring stick, not a tradable cell).
- If fewer than N eligible: hold all eligible at 1/n (never fired).
- Ranking ties break by ticker (deterministic).
- Reference-engine equivalence: `run_cell` is pinned to
  `shared.gauntlet.simulate` by tests; building those tests exposed
  and fixed a sequential-fill allocation bug in the reference engine
  (buys now scale pro-rata under a cash shortfall).

## Bias checklist (final wording in the registry record)

Filled at record_backtest time — the eight planned answers from prereg
§9 held; the material updates from the actual run are the coverage
numbers above and the robustness disclosure below.

## Robustness disclosure (prereg §9.6 — not a pass bar)

The five holdout cells rerun at 2× slippage (LARGE 10 bps, SMALL 50
bps; `run_gauntlet_robustness.py`, `docs/data/gauntlet_v1/robustness_results.json`):

| cell | IS CAGR @1× → @2× | HO CAGR @1× → @2× |
|---|---|---|
| vol_L126__N50__SMALL | 10.27% → 8.85% | 5.57% → 4.13% |
| vol_L63__N25__LARGE | 9.22% → 8.81% | 9.22% → 8.76% |
| vol_L126__N10__LARGE | 9.50% → 9.15% | 8.85% → 8.52% |
| vol_L126__N25__LARGE | 9.54% → 9.27% | 6.97% → 6.69% |
| vol_L126__N50__LARGE | 9.70% → 9.48% | 8.79% → 8.55% |

Monthly low-vol turnover is low; doubling slippage moves CAGR by well
under 1.5%/yr everywhere and changes no verdict in either direction.

## Registry / bookkeeping

- `gauntlet_v1` → `refuted` (terminal) in `cache/lab_registry.json`,
  full 8-item bias checklist in the record; factory-level
  mean_excess = −5.47%/yr (mean IS CAGR gap vs bucket benchmark
  across all 90 cells; 14/90 positive).
- `hypotheses_ever` = 91 (1 prior + 90 gauntlet cells; counted at
  prereg time).
- House population `gauntlet_v1_universes` (612 rows: 306 month-ends ×
  2 buckets with full member lists + coverage note) — reusable for
  backlog #4 (Delphi PIT) and any future panel study.
- Per-cell data: `docs/data/gauntlet_v1/` (screen results + manifest,
  holdout results, robustness results).

## Merge note (2026-07-04, late) — the "documentation gap" was a branch gap

A parallel session, reconstructing this study's documentation without
visibility into the running session's branch, wrote an alternate
version of this doc (preserved in git history on `origin/main` before
this merge) stating that `docs/data/gauntlet_v1/` "was never created"
and that the registry entry was the only surviving record. That was
true on that branch and false in the repository as a whole: the
per-cell artifacts (screen_results, screen_manifest, holdout_results,
robustness_results) exist at `docs/data/gauntlet_v1/` and merged to
the mainline with this note. Lesson for the house filed where it
belongs: parallel sessions must check ALL `origin/claude/*` branches
before declaring an artifact lost.
