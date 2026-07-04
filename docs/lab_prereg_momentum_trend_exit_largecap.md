# Prereg — `momentum_trend_exit_largecap` (house lab, sponsor: operator)

- **Date:** 2026-07-04. Committed BEFORE the study's only new data pull
  (SPY 2000–2021) and before any metric is computed.
- **House counter:** registering this hypothesis makes
  `hypotheses_ever` = 92.
- **Provenance (contamination disclosed):** this hypothesis was formed
  by looking at data. The Delphi PIT replay
  ([results](lab_results_delphi_pit_universe.md)) measured +56.8pp
  over SPY for weekly 65-day momentum with a 20-day-MA trend exit on a
  point-in-time top-119 large-cap universe — over 2021-06..2026-06,
  one costless bull window. That window is therefore BURNED for
  validation and is excluded here entirely. This study tests the
  mechanics on 2000-07..2021-06 — twenty-one years that played no role
  in forming the hypothesis (and which contain the two regimes that
  killed plain momentum in gauntlet_v1).

## Mechanism, who loses, why unarbitraged

In the registry record (`new_strategy` fields): cross-sectional
momentum from underreaction/slow diffusion, PLUS a time-series trend
exit (price < 20-day MA → cash) that truncates the crash left tail —
the best-documented reason long-only momentum implementations fail
(momentum crashes) and the standard published cure. Losers: late
reactors on the way up; disposition-effect holders on the way down.
Unarbitraged in implementable long-only form because the overlay
demands high turnover, tracking-error tolerance, and sitting in cash
against a benchmark — career-impossible for institutions, feasible for
a $2k sleeve.

## The one test

`delphi.backtest.run_backtest` — shipped constants (65-day momentum,
top 10, price ≥ 20-day MA to be held, 5-trading-day rebalance, 5% cash
floor, 20% per-name cap, 20% band, 7-day cooldown, $25 ticket),
initial $10,000, WITH the delisting-exit fix (commit `4816307`; a
collapse exits at its last traded close, not entry price).

- **Universe:** point-in-time top 119 US common stocks (TICKERS
  categories: the three Domestic Common Stock classes) by SHARADAR/
  DAILY marketcap at each calendar-quarter-end signal date 2000-06-30
  .. 2021-03-31 (84 dates, from the existing month-end house caches),
  effective the first trading day after. Renamed/delisted members
  auto-resolved to Sharadar final tickers via
  `shared.sharadar.resolve_ticker`; any member with no resolvable bars
  is counted and disclosed.
- **Window:** executions 2000-07-03 → 2021-06-30. No other window will
  be run.
- **Prices:** Sharadar SEP closeadj (delisted included); SPY benchmark
  from SFP closeadj.
- **Costs:** 5 bps per side on every trade's notional, deducted
  first-order (sum of trade notional × 5 bps, subtracted from final
  equity without compounding relief — conservative). Disclosed rather
  than modeled inside the engine because the engine is the claim's own
  code and stays untouched.
- **Benchmarks:** (1) SPY buy-and-hold, costless. (2) The same 84
  top-119 lists held equal-weight, rebalanced quarterly, 5 bps
  slippage, via `shared.gauntlet_fast.run_cell` — the "own universe"
  bar that killed the gauntlet's momentum cells.

## Metrics and frozen success criteria

Net total return, net CAGR, Sharpe (the backtest module's own
formula), max drawdown; calendar-month excess returns vs SPY (n ≈ 252
months) with a plain t-statistic.

- **Supported iff ALL of:** net CAGR > SPY CAGR; net CAGR > EW-119
  net CAGR; monthly-excess-vs-SPY t ≥ 1.5.
- **Refuted iff:** net CAGR ≤ SPY CAGR, or net CAGR ≤ EW-119 net CAGR.
- **Inconclusive** otherwise (t between 0 and 1.5 with both CAGRs
  beaten), with the numbers published.

One run. No parameter variation — any variant is a new slug and a
fresh counter increment.

## Forward test (only if supported)

Paper only, lab ghost ledger: maintain the strategy portfolio
prospectively in weekly `/lab` tending; one grade = one calendar
month's portfolio excess vs SPY. Standard gate: ≥ 20 grades, positive
SHRUNK mean, `conclude_forward` settles it. A validated verdict makes
the strategy citable in a live thesis — never an autopilot; any live
adoption (e.g. by Delphi) is a separate operator decision.

## Bias checklist (planned handling)

1. **Survivorship:** SEP/DAILY include delisted names through final
   trading day; universes built per-date; renames auto-resolved;
   unresolvable members counted in the results coverage note. The
   delisting-exit fix ensures collapses realize their losses.
2. **Look-ahead:** membership from quarter-end marketcap effective the
   next trading day; signals use bars through the rebalance day (the
   engine's shipped same-day convention, identical to the citation
   under test and to both benchmarks' construction — and the gauntlet
   measured the one-day-lag variant of momentum as DEAD, so this
   convention is not what any surviving edge would rest on).
3. **Selection:** mechanical universe rule, zero hand-picks; the
   strategy form is Delphi's shipped constants, chosen before this
   study by her design history.
4. **Multiple testing:** hypothesis #92 house-wide. Related trials
   this year: gauntlet_v1's 48 momentum cells (all refuted — monthly,
   no trend exit, different family branch) and the two PIT-replay runs
   (measurement study, discovery sample). This is the FIRST test of
   the momentum+trend-exit form; one run only.
5. **Overfitting:** zero knobs tuned here — every constant predates
   this study; single window; the discovery window is excluded.
6. **Costs/liquidity:** mega-cap top-119 names at $10k scale; 5 bps
   per side; results must also show the 2× (10 bps) figure as a
   disclosure, not a bar.
7. **Regime:** 2000-2021 spans dot-com crash, GFC, ZIRP bull, COVID
   crash — the regimes that killed plain momentum in the gauntlet. If
   the trend exit is the load-bearing difference, this window is where
   it must show.
8. **Small n:** one 21-year curve, ~252 monthly excess observations;
   t ≥ 1.5 required in-sample; ≥ 20 forward grades on the shrunk mean
   before any validation claim.
