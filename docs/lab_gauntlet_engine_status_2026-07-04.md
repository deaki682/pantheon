# The Gauntlet — engine build status (2026-07-04)

> **RESOLVED same day:** the market-cap blocker below is closed. The
> operator bought the Sharadar fundamentals entitlement hours after
> this doc was written; see the addendum at the bottom for what was
> verified and what changed. The blocker section is kept as written
> for the record.

Backlog #9, phase (a): "engine + SEP bulk pipeline." Not a hypothesis,
not a backtest — no `shared.lab` registry entry, no ledger row. This is
a build-status note so the next lab session (or the operator) doesn't
have to re-derive what's done and what's blocked.

## Built

- **`shared/gauntlet.py`** — the simulation engine:
  - `CostModel` — linear commission+slippage cost, applied on every
    simulated fill.
  - `pit_snapshot` / `build_snapshots` — point-in-time universe
    construction from any `{date, ticker, value_field}` row source.
    No-lookahead is structural: a snapshot for date D only ever reads
    rows dated exactly D.
  - `dollar_volume_pit_universe` — an interim liquidity-proxy universe
    builder (price x volume) built on the confirmed-working SEP bulk
    endpoint. See blocker below on why this exists instead of a true
    market-cap universe.
  - `simulate` — the daily-bar event loop: rebalances on every
    snapshot date, marks equity daily, applies the cost model on every
    fill, carries forward the last known price across bar gaps (a
    trading halt, not a survivorship hole — SEP bars already run
    through a name's true last trading day).
  - `summarize` — annualized Sharpe/Sortino/CAGR/max-drawdown/win-rate
    off a daily equity curve.
  - `expected_max_sharpe` / `probabilistic_sharpe_ratio` /
    `deflated_sharpe_ratio` — Bailey & Lopez de Prado (2014)'s deflated
    Sharpe ratio, implemented from scratch (no scipy/numpy in this
    environment — Acklam's rational approximation stands in for
    `norm.ppf`). This is the concrete meaning of backlog #9's
    "deflated-Sharpe / multiple-testing-corrected bar": a strategy's
    raw in-sample Sharpe must clear `expected_max_sharpe(grid_size)`,
    not zero, before it earns a holdout pass.
  - `tests/test_gauntlet_engine.py` — 19 tests, synthetic data only:
    cost model, no-lookahead guarantee, buy/hold/rebalance fills net of
    slippage, weight-overallocation guard, drawdown/Sharpe arithmetic,
    and DSR's core property (a fixed observed Sharpe gets LESS
    convincing as the grid size grows).
- **`shared/sharadar.fetch_sep_bulk_range`** — bulk SEP pull for a date
  range across ALL tickers in one paginated call (omit `ticker` to get
  the full cross-section), instead of one call per name. Verified live
  2026-07-04: a single trading day returns 6,835 rows in one page at
  `qopts.per_page=10000`. This is the actual "bulk" half of the
  pipeline — it scales; see the storage note below on why the *fetch*
  scaling doesn't by itself make a full-panel build tractable yet.

## Blocker: no point-in-time market-cap source is currently entitled

Verified live against the real API, 2026-07-04:

- `SHARADAR/DAILY` (the per-day marketcap/valuation-multiples table)
  returns **HTTP 200 with the correct schema but zero rows** for every
  query tried — `AAPL` alone, `AAPL` with a date range, and a full
  cross-section with no ticker filter at all. The table is not
  entitled on this Nasdaq Data Link subscription.
- `SHARADAR/SF1` (fundamentals, which also carries a `marketcap`
  field) IS entitled, but only as a **thin trailing-two-fiscal-year
  slice**: querying `AAPL` alone returns exactly 2 rows, both
  `dimension=MRY` (trailing annual). No `MRQ`/`ARQ` dimension is
  available, and a bulk (no-ticker) `SF1` query returns zero rows the
  same way `DAILY` does — SF1 access here appears to be ticker-scoped
  and depth-limited, not the full historical fundamentals panel.
- `SHARADAR/SEP` (price bars) has neither restriction: per-ticker and
  bulk (no-ticker, date-range) queries both return full data.

**Net effect:** a true point-in-time, market-cap-based universe (what
backlog #9 and backlog #4's "Delphi PIT universe" both assume) cannot
be built from currently-purchased data. `dollar_volume_pit_universe`
above is a stand-in using price x volume from the confirmed-working
SEP feed — a LIQUIDITY proxy, not a SIZE proxy (a high-float,
low-price name can outrank a thinly-traded large-cap). Any grid or
backtest that ships on this proxy before real market-cap data lands
must name the substitution explicitly in its bias checklist's
`selection` item.

**Decision needed from the operator** before phase (b)'s factory
prereg can honestly define its universe:
1. Buy the Nasdaq Data Link add-on that entitles `SHARADAR/DAILY` (or
   full-depth `SF1` with `MRQ`/`ARQ` dimensions), or
2. Accept the dollar-volume proxy for phase (b), with the bias caveat
   above baked into the prereg, or
3. Source point-in-time membership/market-cap elsewhere (e.g. a
   dedicated index-membership vendor) — this would also unblock
   backlog #4, which hits the identical wall.

## Storage note (why "bulk" fetch alone isn't "build the panel")

The full Sharadar panel is large even at SEP-only scope: ~6,800
tickers pricing on a given day x ~2,500 trading days/decade is on the
order of 17M OHLCV rows. `shared.historicals`'s per-symbol JSON store
(`cache/shared_bars.json`) was sized for the hundreds-of-names scope
every other house study uses, not tens of millions of rows in one
file. `shared.gauntlet.simulate` therefore takes `bars_by_symbol` as a
plain in-memory argument rather than assuming a full-panel cache
exists — phase (b)'s prereg should scope the candidate universe first
(via `dollar_volume_pit_universe` or whatever market-cap source the
operator picks) and only then bulk-fetch bars for names that actually
appear in some snapshot, not the full ~20k-name roster.

## Not started

Phases (b) in-sample-grid prereg, (c) in-sample screen, (d) holdout
pass, (e) forward tests — all still open, and (b) is gated on the
market-cap decision above. Backlog line #9 updated to point here.

## Addendum (2026-07-04, later the same day): blocker RESOLVED

The operator chose option 1 and bought the fundamentals entitlement.
Root cause of the earlier zero-row results, now precisely understood:
the prior subscription was **SEP only**, and unentitled Sharadar
tables serve a free *sample* instead of erroring — `DAILY`'s sample is
XOM Oct–Dec 2018 only, `SF1`'s is Dow-30 names at annual (MRY)
dimension. Real queries outside the sample return HTTP 200 with zero
rows, which is what the morning's probes hit.

Verified live after the upgrade:

- `DAILY` per-ticker: AAPL 2024-01-02..05 returns 4 rows with
  marketcap/ev/pe/pb/ps (marketcap and ev in **USD millions**).
- `DAILY` bulk cross-section: 5,631 rows for 2024-01-02 and 5,518 for
  2010-01-04, each in a single page — no per-name calls needed.
- History depth: AAPL rows exist at 2000-12-29 and 1999-01-29 but not
  1998-06-30 — coverage starts **late 1998**, matching SEP's span, so
  a "decade+" panel is available with room to spare.
- Delisted coverage: SIVBQ has rows through 2023-03-28 (SVB
  bankruptcy) and BBBYQ through 2023-05-02 (delisting) — market cap
  runs through each name's final trading day, so PIT universes will
  correctly contain the names that later died.
- `SF1` full depth: AAPL `ARQ` returns 128 quarterly rows back to
  1993-12-31 — the quarterly point-in-time fundamentals dimension
  exists now, not just the trailing-2-year MRY sample.

What changed in code: `shared.sharadar.fetch_daily_bulk_range` (bulk
DAILY pull, mirrors `fetch_sep_bulk_range`) is the sanctioned door;
its rows feed `shared.gauntlet.pit_snapshot(value_field="marketcap")`
directly. `dollar_volume_pit_universe` is superseded as a SIZE proxy
and survives only as a liquidity screen. **Phase (b) — the factory
prereg — is unblocked**, and backlog #4 (Delphi PIT universe) is
unblocked by the same purchase.

## Addendum 2 (2026-07-04, evening): comprehensiveness review — dividend bug fixed, event-feed guard, regime splits

A pre-phase-(b) review of "what does the engine NOT account for" found
one genuine defect and two missing guards. All three are now in
`shared/gauntlet.py`, each with regression tests (10 new; engine suite now 26 test
functions — the “19 tests” claimed earlier in this doc was itself an
overcount; it was 16):

- **Dividends were silently dropped (FIXED — was a real bug).**
  `simulate()` marked and filled on SEP `close`, which is
  split-adjusted but dividend-EXCLUSIVE — every curve was a
  price-return curve, understating total returns ~2%/yr and
  differentially penalizing value/quality/dividend families vs
  zero-yield growth, corrupting exactly the cross-family ranking the
  factory exists to produce. `simulate()` now marks on
  `close_total_return` (Sharadar `closeadj`, already carried by
  `to_shared_bars`) for any symbol whose bars have it completely;
  symbols with gaps fall back to `close` WHOLE (mixing fields would
  fake a jump at every gap) and are disclosed in the result's new
  `price_return_only_symbols`. A results doc citing a run with a
  non-empty list must say so. Regression test: a flat-price dividend
  payer whose price-return curve is flat but whose total-return curve
  compounds.

- **`PITEventFeed` — structural no-lookahead for event data (NEW).**
  The bar-trimming guarantee never covered event feeds (insider
  clusters, PEAD, spinoffs, lockups), which join in through the spec's
  closure — a fresh lookahead surface. `PITEventFeed` requires every
  row to carry the date the information became PUBLIC (default field
  `public_date`; constructor refuses rows without it — a cluster row
  keyed on transaction date would leak the 2–10 day filing lag), and
  select() functions touch events only via `upto(as_of)` / `on(day)` /
  `by_symbol(as_of)`. Event-driven grid families in the factory prereg
  must route their event tables through this class.

- **`summarize_by_period` — per-regime disclosure (NEW).** Splits one
  equity curve at boundary dates and summarizes each segment. Every
  factory results doc must print per-regime splits so a survivor that
  is one warm regime plus noise is visible (the spinoff ocean lesson:
  +41% warm vintage, −1% out of regime).

Still NOT accounted for, disclosed for the prereg to handle: slippage
is a flat 10bps placeholder (per-liquidity-bucket numbers are a prereg
obligation; re-run survivors at 2–3× assumed costs), no intraday
prices (intraday stops only approximable at the close, disclosed
per-family), and the LLM factor stays out of the simulation entirely —
mechanical skeletons + headroom brackets in the grid, actual LLM lift
measured only forward via ghost control arms (training-data
contamination makes historical LLM judgment unrunnable; see the
blinded-reader precedent).

## Addendum 3 (2026-07-04, night): exit-rule engine + uncertainty/robustness toolkit

Post-gauntlet_v1 comprehensiveness pass #2, operator-directed ("as
comprehensive as possible"). The two branches of the day (v1 factory
run; comprehensiveness review) are now merged — the engine carries the
pro-rata fill fix, signal_lag, total-return marking, and everything
below. Engine suite: 26 → 57 tests.

**`ExitRules` — daily position-level exits (the big one).** What the
90 rank-and-hold cells deliberately lacked and every live god actually
runs: `ma_period` (Delphi's 20-day-MA break), `stop_loss_pct`
(Achilles -8%, Midas -10%), `trailing_stop_pct`, `time_stop_days`
(Achilles 5d, Midas Friday), `profit_target_pct`, `cooldown_days`
(Delphi 7d, Achilles 4wk). Triggers evaluate on RAW split-adjusted
OHLC (what a god computes at the broker) — intraday rules use the
day's low/high, gap-throughs fill at the open, close-only bars degrade
to close-crossing; fills convert to the marking series so cash stays
dividend-correct. Exits run before same-day rebalances; exited names
can't be re-bought same day; every trade now carries a `reason`.
**This unblocks the Delphi full-window ruleset study** (her exact
rules, 1998→2026, on the v1 universe catalog) and honest PEAD/basket
simulations for Achilles-family cells.

**`delist_exit_haircut`** — robustness mode for the documented
optimistic delisting bias: force-sell on a symbol's final panel bar at
(1 − haircut) × final close, reason `delisting_exit`, instead of the
legacy sellable-stale-close. Rerun survivors at 0.0 and 0.5.

**Analytics that results docs kept hand-rolling:**
- `excess_stats(curve, benchmark_curve)` — benchmark-relative CAGR
  gap, beta, annualized alpha, tracking error, information ratio,
  up/down capture. The v1 lesson (the bar is benchmark-relative) as a
  function.
- `trade_stats(trades)` — FIFO round-trips: win rate, avg win/loss,
  profit factor, median holding days, per-exit-reason breakdown ("did
  the stop save money or amputate winners?").
- `turnover_stats(trades, curve)` — annual turnover + cost drag in
  bps/yr (the fee-engine check, mechanized).
- `periodic_dates(days, "W"|"M", "first"|"last")` — canonical weekly/
  monthly rebalance calendars.

**Uncertainty & study tooling:**
- `sharpe_ci(curve)` — circular block-bootstrap CI on annualized
  Sharpe (seeded, deterministic). Point-estimate Sharpes without
  intervals invite over-reading; results docs should quote both.
- `walk_forward_windows(days, train_days, test_days)` — K rolling
  train/test splits; the defense against "the one split flattered it".
- `parameter_cliff_report(cells)` — overfit smell-test: flags cells
  whose metric is an isolated peak vs one-step parameter neighbors
  (65d working while 55d and 75d fail is noise wearing a crown).
- `event_car(events, bars, benchmark_bars)` — the event-study engine
  for PITEventFeed populations: entry at first close strictly after
  public date, per-offset mean/median CAR vs benchmark on total-return
  series, mandatory `unpriceable` disclosure + coverage note. Turns
  backlog #1 (quiet clusters), #7 (CEF tenders), #8 (PEAD horizon)
  into one-call studies once their populations are deposited.

Still open (next tier, offered): SPY/benchmark curve builder from
Sharadar in one call; capacity analysis (position size vs ADV per
fill); multi-sleeve portfolio combiner (correlated-drawdown studies on
simulated books); Monte-Carlo trade-order shuffle for drawdown
distributions; sector/exposure attribution once SF1 sector metadata is
cached; a lab bridge that drafts the eight bias-checklist answers
directly from a run's own disclosures (coverage, costs, splits, trial
count).
