# Prereg — Delphi point-in-time universe replay (backlog #4)

- **Type:** measurement study (no tradable claim, no registry slug —
  /lab liturgy step 3; same discipline: this doc commits before any
  study metric is computed).
- **Sponsor:** operator (backlog #4). **Date:** 2026-07-04.
- **House multiple-testing context:** `hypotheses_ever` = 91 at commit
  time. This study adds exactly TWO pre-committed strategy runs (one
  replication, one correction) and no grid.

## Question

Delphi's runbook cites "+85.2% total return, Sharpe 1.51, +53.8pp
alpha over SPY" (commit `d265cdc`, 2026-06-30) as the evidence behind
the mechanical momentum system — and it bears on her capital ceiling.
That backtest ran on the **2026-curated 119-name universe applied to
the past** with broker data that only serves currently-listed names.
Does the evidence survive (a) survivorship-free prices and (b)
point-in-time universe membership?

## Reconstruction disclosures (before data)

- The original backtest cache (`cache/delphi_bt_stock_prices.json`,
  results/curve files) no longer exists; the exact original window is
  unrecoverable. The claim was committed 2026-06-30 from ~5-year
  broker history; the window is reconstructed as **2021-06-30 →
  2026-06-30** and this is frozen here.
- The original used broker `close` (split-adjusted, not
  dividend-adjusted). This study uses Sharadar `closeadj` (split+
  dividend-adjusted) for stocks AND for the SPY benchmark (SFP) —
  a consistent total-return basis. Directionally this HELPS the
  replication (dividends added on both sides).

## Design — exactly two runs, same code path

Both runs execute `delphi.backtest.run_backtest` — the very code the
claim came from — with its shipped defaults (rebalance every 5 trading
days, top 10 by 65-day momentum filtered to price ≥ 20-day MA,
equal-weight with 20% per-name cap, 5% cash floor, 20% rebalance band,
7-day cooldown, $25 min ticket). The only code change permitted is a
`universe_fn(date)` parameter that defaults to the existing frozen
`UNIVERSE` constant (behavior-preserving; tests must stay green).

- **Run A — replication:** universe = the frozen 2026 curated list
  (119 names), Sharadar closeadj bars. Reproduces the claim's method
  on honest prices.
- **Run B — point-in-time correction:** at each rebalance day, the
  universe is the **top 119 US common stocks by Sharadar DAILY
  marketcap as of the most recent calendar-quarter-end**, effective
  from the first trading day after that quarter-end (mirrors live
  Delphi's quarterly curation cadence; quarter-ends 2021-06-30 →
  2026-03-31). Delisted names included through their final trading
  day; a mechanical, blind proxy for "what a large-cap curator could
  have listed then." ADRs/funds are excluded by restricting to SEP
  (common stocks); no other filter.

No third variant, no parameter changes, no window changes — any
follow-up is a new prereg.

## Metrics

Per run: total return, alpha vs SPY (closeadj total-return basis over
the identical window), Sharpe (the backtest module's own formula), max
drawdown. Benchmark: SPY buy-and-hold from SFP closeadj.

## Frozen interpretation criteria

1. **Replicates:** Run A total return within [+60%, +110%] (band
   allows for data-source and window-reconstruction differences).
   Outside the band → the original number itself is not reproducible;
   report that with the same prominence.
2. **Artifact verdict:** Run B alpha < 50% of Run A alpha, or
   Run B alpha ≤ 0 → the runbook's +85%/+53.8pp citation is declared
   survivorship/look-ahead-inflated: the design-rationale paragraph in
   `.claude/commands/delphi.md` gets the measured Run B numbers and a
   pointer to the results doc, and Delphi's capital-scaling case rests
   on live/ghost grades only (her gates already require them).
3. **Survives verdict:** Run B alpha ≥ 50% of Run A alpha AND > 0 →
   the citation stands, annotated with the PIT-corrected number.
4. Either way the result gets a RESEARCH_LEDGER row and the backlog #4
   line closes.

## Data plan (pulled after this commit)

- Stocks: existing staged Sharadar SEP export (2014-10..2026-01, all
  US stocks incl. delisted — house infrastructure from gauntlet_v1)
  plus an incremental SEP pull 2026-02-01..2026-06-30. Warmup bars
  from 2021-02-01 for the 65-day momentum + 20-day MA at the window
  start.
- Universe B membership: SHARADAR/DAILY marketcap cross-sections at
  the 20 quarter-end signal dates 2021-06-30..2026-03-31.
- Benchmark: SHARADAR/SFP SPY closeadj (verified entitled).

## Bias handling (all eight, planned)

1. **Survivorship:** SEP includes delisted names through final trading
   day; Run B's universe is built per-date from names alive then. The
   frozen-list Run A retains the original's survivorship ON PURPOSE —
   it is the thing being measured against.
2. **Look-ahead:** Run B membership uses quarter-end marketcap
   effective the NEXT trading day; signals use bars through the
   rebalance day itself exactly as the original code does (both runs
   share this convention, so the comparison isolates membership).
3. **Selection:** universes are mechanical (frozen list vs top-119 by
   marketcap); no hand-picking anywhere in this study.
4. **Multiple testing:** two runs, both pre-committed here; no
   variants tried and discarded; house counter cited above.
5. **Overfitting:** zero tuned parameters — all strategy knobs are
   Delphi's shipped constants from the claim's own commit.
6. **Costs/liquidity:** the original backtest charged no costs; both
   runs inherit that (disclosed) — the comparison is like-for-like,
   and adding costs would only further shrink whatever survives.
7. **Regime:** single 5-year window by construction (the claim's own
   window); no out-of-window inference will be drawn — this study
   judges the CITATION, not the strategy's future.
8. **Small n:** one window, two runs; no statistical validation
   claimed — the deliverable is the measured gap between A and B.
