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

**HOLDOUT PENDING — this line is replaced by the stage-2 outcome.**

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

**PENDING — filled by run_gauntlet_holdout.py output.**

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

**PENDING — survivor sensitivity at 2× SMALL slippage (50 bps), filled
after stage 2.**
