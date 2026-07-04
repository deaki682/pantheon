# The Gauntlet — engine build status (2026-07-04)

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
