# Prereg — Delphi's ruleset, faithful semantics, full window (1999→2026)

- **Sponsor:** operator
- **Committed:** 2026-07-04, BEFORE any faithful-cell result is
  computed. This is the CORRECTION study for
  `delphi_ruleset_fullwindow`, whose erratum (operator-ordered
  accuracy audit, same day) found the primary cell mis-specified her
  rules: it simulated a standalone DAILY MA stop on MA-unfiltered
  entries, where her real code (`delphi/signals.py::rank_by_momentum`)
  uses the 20-day MA as an ENTRY FILTER inside the ranking, plus a 20%
  rebalance band and cooldown-on-any-sell that were unmodeled.
- **Slug:** `delphi_ruleset_faithful` (new; refuted-is-terminal
  applies per slug — the prior slug's verdict stands for the variant
  it froze).

## 1. Question and decision

Same question as #11, now against her ACTUAL semantics: does Delphi's
real ruleset beat its own universe's equal weight and SPY, net of
costs, over 1999→2026? The decision it buys: the still-open
retire-or-demote question (currently mooted by the operator's written
override AND by the #11 erratum) gets decided on a study that tested
what she actually runs.

## 2. Faithful semantics (frozen; each maps to her code/runbook)

- **Selection** (`rank_by_momentum` exactly): rank by 65-trading-day
  momentum (`prices[-1]/prices[-66] − 1`) computed on split-adjusted
  `close` — the broker-bar basis her live signals use — RESTRICTED to
  names whose close ≥ their 20-day SMA (same close series). Top 10,
  equal-weight at 9.5% (5% cash floor; 20% per-name cap never binds).
- **Band:** `rebalance_band=0.20` (trim only above target×1.2, top up
  only below target×0.8, full dropout exits always fire) — matches
  `delphi/backtest.py` sells/buys logic.
- **Cooldown:** `sell_cooldown_days=5` (≈7 calendar) after any full
  exit, blocking re-entry — matches sleeve cooldown.
- **No ExitRules** — the MA lives inside selection, as in her code.
- **Execution:** `signal_lag=1` (signals at close t, fills at close of
  the next trading day); marking/fills on the total-return series
  (engine standard); costs 5bps slippage, $25 min ticket; $10k/cell.
- **Universes/benchmarks/data:** identical to #11 — same 110 quarterly
  PIT top-119 universes, same 419-ticker bar panel, same EW-universe
  benchmark and SPY total-return leg. Panel reuse disclosed in §5.

## 3. Cells (n_trials = 2, frozen)

1. **`faithful_daily`** (PRIMARY — current live semantics per the
   2026-07-04 once-per-trading-day cadence rule): selection evaluated
   every trading day, band-damped.
2. **`faithful_weekly`** (the original +85% claim's cadence,
   `REBALANCE_INTERVAL_DAYS=5`): selection evaluated on the first
   trading day after each Friday close.

Robustness (disclosed, not gating): primary rerun at 2× slippage.
No other variants against this data.

## 4. Verdict (frozen — same bars as #11)

- **SUPPORTED** iff `faithful_daily` full-window net excess CAGR > 0
  vs BOTH the EW top-119 benchmark and SPY at 1× costs.
- **REFUTED** iff excess vs the EW benchmark ≤ 0.
- Publish regardless: both cells side by side with #11's cells, the
  same regime table (boundaries 2003/2008/2013/2020/2021-06), the
  2000–2015 graveyard sub-window, trade_stats/turnover, sharpe_ci,
  drawdown_distribution, 2× rerun.
- Consequence: verdict REPLACES #11's as the operative full-window
  answer on her design. REFUTED reopens retire-or-demote for the
  operator (the standing written override remains until they act);
  SUPPORTED stands as historical evidence only — capital gates still
  run on live graded calls.

## 5. Bias checklist deltas from #11 (all eight re-answered at record time)

Unchanged: survivorship, look-ahead structure, costs model, capacity,
regime coverage, small-n handling — same panel, same disclosures.
Changed/notable:
- **Selection/overfitting:** parameters remain her pre-existing live
  values; the CORRECTION itself was specified from her code, not from
  peeking at candidate results (no faithful cell was computed before
  this prereg's commit — the runner phase did not exist yet).
- **Multiple testing:** +2 cells (house counter 96→98 at record time).
  Cumulative Delphi-family cells against this panel now 5 (#11's 3 +
  these 2), all enumerated across the two preregs; the verdict
  criterion remains benchmark-relative sign, robust to selection among
  a handful of cells.
- **One dataset, one decision:** this panel has now bought #11's
  (mislabeled-variant) decision. Re-use here is the erratum-correction
  path the house has used before (Midas convergence correction,
  backlog #6 correction) — same data, corrected implementation,
  question unchanged, disclosed. The corrected verdict is the LAST
  decision this panel buys for Delphi's ruleset family.
