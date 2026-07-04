# Prereg — Delphi's frozen ruleset, full window (1999→2026)

- **Sponsor:** operator
- **Committed:** 2026-07-04, BEFORE any data pull for this study
  (see §8 on panel reuse — the underlying SEP/DAILY tables have been
  seen by the house; this study's universes, member bars, and every
  cell result have not been computed).
- **Type:** measurement study (plain-prereg path per backlog rules) —
  confirmatory test of a live strategy's ruleset, not a new tradable
  hypothesis. Cells still count toward `hypotheses_ever` at run time.
- **Engine:** `shared/gauntlet.py` — `simulate` with `ExitRules`
  (added 2026-07-04, addendum 3), `periodic_dates`, `benchmark_curve`,
  `excess_stats`, `sharpe_ci`, `summarize_by_period`,
  `parameter_cliff_report` (n/a — no grid), `capacity_stats`,
  `draft_bias_checklist`.

## 1. The question

gauntlet_v1 measured exit-less long-only momentum dead (2000–2015,
all 48 cells) and the #4 replay measured Delphi's rules strong in
2021–2026 on a blind PIT top-119 universe (+56.8pp vs SPY). These are
compatible: different mechanics (MA exit, weekly cadence, top-10
concentration) and different eras. This study runs **Delphi's exact
frozen live ruleset over the full 1999→2026 window on the honest
universe** and asks: is her edge her rules, or her era?

**The decision it buys:** whether Delphi's ruleset (specifically the
20-day-MA exit and weekly cadence, the parts gauntlet_v1 never tested)
deserves continued live capital and the pending universe-switch
decision — or whether she is regime beta that got lucky in a momentum
decade and should go the way of Midas.

## 2. Cells (n_trials = 3, enumerated here, frozen)

1. **`delphi_live`** (PRIMARY): 65-trading-day momentum (closeadj
   total-return basis), top 10 equal-weight (9.5% each, 5% cash
   floor), weekly rebalance (`periodic_dates(days, "W", "last")`,
   `signal_lag=1`), `ExitRules(ma_period=20, cooldown_days=5)`
   (7 calendar ≈ 5 trading days).
2. **`delphi_no_exit`** (ablation): identical, `exits=None`. Isolates
   the MA exit's entire contribution — this is the cell gauntlet_v1
   says should die.
3. **`delphi_monthly`** (ablation): identical to primary but monthly
   rebalance. Isolates the weekly-cadence contribution.

No other variants will be run against this data. Parameters are
Delphi's live values (delphi.md), externally frozen since 2026-06 —
none are tuned in this study. The 20% rebalance band is NOT simulated
(engine rebalances to target weekly); omitting it raises turnover and
therefore costs, which biases AGAINST the strategy — conservative,
disclosed.

## 3. Universe (frozen)

Quarter-end **top 119 US common stocks by Sharadar DAILY marketcap**
(the #4 study's construction, extended): quarter-ends 1999-03-31 →
2026-06-30. Same share-class dedup rule as #4. Universe membership
applies from the first weekly rebalance after the quarter-end through
the next. Members' SEP bars (closeadj + close + OHLC + volume) pulled
for the union of all quarterly lists; delisted members included
through their final bar.

## 4. Execution & costs (frozen)

- Signals at Friday close t, execution at close of first trading day
  ≥ t+1 (`signal_lag=1`); MA exits evaluated daily at raw close per
  `ExitRules`.
- `CostModel(commission_bps=0, slippage_bps=5, min_ticket=25)` —
  gauntlet_v1's LARGE bucket number; these are mega-caps. Robustness
  rerun at 2× slippage (10bps), disclosed not gating.
- Initial capital $10,000 (matches v1 cells; her live $2k with $25
  tickets binds harder — capacity is not the question here, but
  `capacity_stats` is reported anyway).

## 5. Benchmarks (frozen)

1. **EW top-119**: equal-weight of each period's full universe, same
   execution model, min_ticket=0 (measuring stick, not tradable).
2. **SPY total return** via `benchmark_curve` on Sharadar closeadj.

## 6. Metrics & verdict (frozen)

Primary metric: full-window net excess CAGR of `delphi_live` vs the
EW top-119 benchmark (`excess_stats`), with information ratio and
`sharpe_ci` (seed 7) reported.

- **SUPPORTED** iff `delphi_live` full-window excess CAGR > 0 vs BOTH
  benchmarks, net of costs, at 1× slippage.
- **REFUTED** iff excess CAGR ≤ 0 vs the EW top-119 benchmark.
- Either way, publish: per-regime table
  (`summarize_by_period`, boundaries 2003-01-01 / 2008-01-01 /
  2013-01-01 / 2020-01-01 / 2021-06-01), the 2000–2015 sub-window
  excess (the graveyard window, read against gauntlet_v1), all three
  cells side by side, `trade_stats` by exit reason (did the MA exit
  save money or amputate winners?), `turnover_stats`,
  `drawdown_distribution` (seed 7), and the 2× cost rerun.
- The exit rule's contribution = `delphi_live` minus `delphi_no_exit`,
  reported with no pass bar of its own (it informs the narrative, not
  the verdict).

**Consequences.** SUPPORTED → Delphi keeps trading, the
universe-switch decision proceeds on #4 + this study's evidence, and
her capital gates continue to govern scaling exactly as before (this
study validates the ruleset's history, not her live skill).
REFUTED → operator retire-or-demote decision with the numbers; her
live book's fate follows the Midas precedent (ledger row, capital to
treasury) unless the operator explicitly overrides in writing.
One dataset, one decision, once — no re-cuts, no window shopping.

## 7. Bias checklist (pre-answered; finalized at record time via `draft_bias_checklist` + this section)

1. **Survivorship:** universes rebuilt point-in-time from DAILY
   marketcap incl. delisted names; members' bars run through final
   trading day; any price-return-only members disclosed from the
   run's `price_return_only_symbols`.
2. **Look-ahead:** structural (snapshot/day-trim guarantees);
   `signal_lag=1`; universe membership applies only after its
   quarter-end.
3. **Selection:** cells and universe rule enumerated above before any
   pull; parameters are Delphi's pre-existing live values, not chosen
   against this data.
4. **Multiple testing:** n_trials=3, counted into `hypotheses_ever`
   at run time; observed Sharpes read against
   `expected_max_sharpe(3)` and, house-wide, against the counter.
5. **Overfitting:** zero parameters tuned in-study; ablations exist to
   attribute, not to search. No grid beyond the three cells.
6. **Costs/liquidity:** 5bps mega-cap slippage + $25 tickets; 2× rerun
   mandatory; turnover and cost drag published; band omission biases
   against.
7. **Regime:** 27-year window spans dot-com, GFC, 2010s bull, covid,
   2021–26 momentum era; per-regime table mandatory; the 2000–2015
   graveyard sub-window is called out specifically in advance.
8. **Small-n:** daily n_obs ≈ 6,800; weekly decisions ≈ 1,400;
   `sharpe_ci` published. Whatever the verdict, her LIVE validation
   still runs on graded live calls per the capital gates — this study
   cannot substitute for them.

## 8. Panel-reuse disclosure (honesty section)

The SEP/DAILY tables backing this study also backed gauntlet_v1 and
the #4 replay, and the house has SEEN aggregate momentum-family
results on 2000–2015 (all dead, exit-less). The one-dataset-one-
decision rule is honored at the level of the frozen question: this
prereg was written knowing those verdicts, and its cells/bars/verdict
criteria are frozen here, before any cell of THIS study is computed.
The residual contamination risk — that we run this study at all
because #4's hot window flattered her — is real, disclosed, and is
exactly why the REFUTED consequence is pre-committed with teeth.
