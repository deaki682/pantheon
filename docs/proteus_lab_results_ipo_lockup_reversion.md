# Proteus Lab — Results: IPO Lockup-Expiration Reversion

**Slug:** `ipo_lockup_reversion` | **Date:** 2026-07-04 | **Verdict: REFUTED**

Prereg: `docs/proteus_lab_prereg_ipo_lockup_reversion.md` (committed
2026-07-04, commit `f612d6c`, before any price bar or IPO list was pulled).

## Population construction

Complete 2023 IPO calendar pulled from stockanalysis.com/ipos/2023
(154 rows, full year, not hand-picked). Filtered per prereg:

- **Excluded 51 SPACs** by name pattern (`*Acquisition Corp*`,
  `*Acquisition Group*`, `*Acquisition Corporation*`, plus 3 more
  identifiable blank-check vehicles by sponsor name: SilverBox Corp III,
  Trailblazer Merger Corporation I, Pono Capital Three).
- **Excluded 1 spinoff** (Strong Global Entertainment, SGE — distributed
  to Live Ventures shareholders, not an underwritten primary offering,
  so it has no comparable lockup mechanic).
- **Excluded 3 foreign dual/cross-listings** (DistIT AB, Softing AG,
  YanGuFang International — already-public foreign issuers doing a
  secondary US listing, not a standard 180-day-lockup primary IPO).
- **Excluded 4 rows with no recorded IPO price** on the source
  aggregator (UZX, AXG, GMEX, HERE) — a data-availability gap in the
  source, not a performance-based exclusion.
- **Excluded 15 rows priced above $10.00** — these are the well-known,
  heavily-covered 2023 IPOs (ARM, Birkenstock, Instacart/CART, Kenvue,
  Klaviyo, Cava, etc.). The $10.00 price ceiling is an **operational
  proxy for "<$300M offer size, low analyst/media coverage"** — see
  Selection bias item below for why this proxy was used instead of
  per-name S-1 offering totals, and its limits.

This leaves **80 candidate small-cap IPOs**. Entry: close on trading day
185 from first trade (5 sessions past the standard 180-day lockup).
Hold 60 trading days, exit at close. Excess = stock return − SPY return
over the identical calendar window.

## Data gap: 15/80 names could not be priced

`get_equity_historicals` returned `not_found` for 15 names; a follow-up
`get_equity_quotes` call confirmed 12 as `inactive_instruments` and 3 as
`missing_instruments` on the broker. Spot-verification (WebSearch) on
5 of the 15 found:

- **MGOL** (MGO Global) — business-combined into Heidmar Maritime
  (ticker now HMR, Feb 2025); the merger postdates my exit window, but
  the broker's historicals API cannot serve bars under the retired
  ticker at all.
- **JNVR** (Janover) — rebranded to DeFi Development Corp (DFDV, a
  Solana-treasury vehicle) in 2025; same broker limitation.
- **IVP** (Inspire Veterinary Partners) — confirmed delisted from
  Nasdaq for cause (Jan 2026, bid-price failure after a cumulative
  250:1 reverse split), now OTC at $0.01. A real, severe value-
  destruction outcome my data source cannot price for my 2024 window.
- **LQR** (LQR House) — multiple Nasdaq delisting determinations
  (2023-2025), forced reverse split. Also likely a bad outcome.
- **SPGC** (Sacks Parente Golf, renamed Newton Golf Co.) — still
  nominally listed but collapsed to sub-$1 (chairman bought stock at
  $0.36 in Dec 2024); broker flags it inactive anyway.

The remaining 10 (WLGS, HRYU, SRM, WRNT, ELWS, PXDT, DTCK, BREA, SGN,
PWM) were not individually re-verified past the quotes check — stopping
here is a deliberate effort-law tradeoff: of the 5 checked, **0 were
clean survivors** (all were distress-driven ticker changes, delistings,
or near-total collapses), so the pattern is already directional and
each further confirmation is unlikely to change the conclusion below.

**This is a real, disclosed survivorship gap, and it points the wrong
way for the hypothesis**: every verified case among the missing 15 is a
worse outcome than a typical surviving name, not better. The 65-name
result below is therefore more likely to *overstate* the true
population's mean excess than understate it.

## Result

n=65 (raw entries in `docs/proteus_lab_prereg_ipo_lockup_reversion.md`'s
population, minus the 15 unpriceable names).

| Metric | Value |
|---|---|
| Mean excess (raw) | **-10.41%** |
| Mean excess (shrunk, prior_n=20, prior_mean=0) | **-8.01%** |
| t-statistic | **-0.62** |
| Median excess | **-33.07%** |
| Win rate (excess > 0) | **18/65 = 27.7%** |
| Largest single event | BMR +1011.53% excess (an 11x biotech move — this ONE event is larger in magnitude than the entire 65-name net excess; excluding it, the other 64 names average roughly -25.9% excess) |

Full per-name table (entry/exit dates, prices, returns) in
`/tmp/claude-0/.../scratchpad/compute_lockup.py` output, reproducible
from the prereg's population + entry rule.

**Verdict vs pre-registered thresholds:** mean excess <= 0 →
**REFUTED**, unambiguously — not even close to the inconclusive band.
The distribution also fails the "no single event >40% of total excess"
supported-criterion on its own: one outlier (BMR) exceeds 100% of the
net excess in magnitude, meaning the arithmetic sign of the naive mean
is itself an artifact of a single lottery-ticket biotech name, not a
population-wide reversion effect. The median (-33%) and win rate
(27.7%) are the more honest description of what actually happened to
most names: they kept falling for 60 trading days after the lockup
"cleared," they did not revert.

## Bias checklist (`proteus.lab.BIAS_CHECKLIST`)

- **survivorship**: 15/80 (18.75%) of the population could not be
  priced because the broker's historicals API does not serve bars for
  tickers that are inactive/renamed/delisted as of today, regardless of
  whether they had real trading data during my 2024 entry/exit window.
  Of the 5 spot-checked, all 5 were distress outcomes (delisting,
  forced reverse split, business-combination exit, or sub-$1 collapse).
  This means the reported -10.4% mean excess is very likely an
  OPTIMISTIC estimate of the true population mean — the true number is
  probably more negative. I could not obtain a free alternate data
  source (stooq.com returned 503 via the proxy; stockanalysis.com's
  history page redirects a renamed ticker to its successor's current
  price series, not the historical pre-rename data) within reasonable
  effort, so the survivors-only result is reported with this caveat
  attached rather than silently treated as complete.
- **look_ahead**: entry is fixed at trading-day 185 from each name's own
  first trade — a purely calendar/count-based rule using only
  information available at IPO time (the 180-day lockup term is
  boilerplate, stated in the S-1/424B4 before day 0). No name was
  entered or excluded based on anything that happened after its own
  IPO date. SPY's return is measured over the identical calendar dates
  as each stock, not a fixed universal window.
- **selection**: population built from a complete public calendar (all
  154 2023 IPOs), filtered by mechanical, pre-stated rules (SPAC-name
  pattern, spinoff, foreign cross-listing, missing price, price>$10)
  applied uniformly before any return was computed. The one place a
  proxy stood in for the prereg's literal criterion: "offer size <
  $300M" was approximated by "IPO price <= $10.00" rather than
  per-name S-1 offering totals, because verifying exact offer size for
  ~150 candidates via individual EDGAR filings would have cost roughly
  as many tool calls as the entire rest of this study for a threshold
  that, on inspection, cleanly separates this list already (the
  <=$10 cohort are uniformly obscure microcaps; the >$10 cohort are the
  year's recognized large IPOs — ARM, Birkenstock, Kenvue, etc. — with
  no ambiguous middle case observed). Disclosed as an approximation,
  not hidden.
- **multiple_testing**: this is hypothesis #1 in
  `cache/proteus_lab.json`'s `hypotheses_ever` counter — the very first
  strategy registered in the lab. No prior variant of this idea was
  tried against this or any other data before this cut.
- **overfitting**: two knobs (185-trading-day entry offset, 60-day
  hold), both fixed by the mechanism (lockup length + a round-number
  hold) in the prereg before any data was seen. Neither was adjusted
  after seeing the result — the -10.4%/-33% median result is the first
  and only cut on this design.
- **costs_liquidity**: not formally modeled (no spread/slippage
  deduction applied), but irrelevant to the verdict — the effect is
  negative before costs, so costs only make the refutation stronger.
  Worth noting qualitatively: many of these names show violently
  reverse-split-adjusted price series (e.g. VCIG's entry/exit prices
  are in the millions post-adjustment, GDHG and CHSN in the tens of
  thousands) — a strong tell that this population skews toward names
  that were structurally distressed (chronic sub-$1 pricing forcing
  repeated reverse splits) even before accounting for the 15 that
  disappeared entirely. A thin-liquidity discount was not needed to
  reach a negative verdict, but would have made it more negative still.
- **regime**: single sample — 2023 IPO class held into 2024 (a
  disinflation/soft-landing rally year for SPY, +3% to +19% depending
  on the specific 60-day window, per the per-name SPY returns above).
  Even against a broadly rising market, small-cap IPO names cratered on
  a 60-trading-day post-lockup horizon (median -33%). This looks less
  like a lockup-specific supply shock and more like the well-documented
  general small-cap-IPO long-run underperformance pattern continuing
  past the lockup date rather than reversing at it. Generalization to a
  down-market regime is unproven but the sign of the effect (still
  negative) would not obviously need a down-market to hold.
- **small_n**: raw n=65 (>= the prereg's n>=30 floor). Shrunk mean
  (prior_n=20, prior_mean=0) is -8.01%, close to the raw -10.41% since
  n=65 dominates the prior — the shrinkage does not rescue this toward
  zero in any meaningful way. No forward test is warranted (see
  Decision below); a forward test only follows a `supported` backtest.

## Decision

**REFUTED.** The mechanism as pre-registered (mean reversion after a
calendar-certain, information-free supply shock) does not show up in
the complete-catalog test. If anything, the median name kept falling
for 60 trading days past the point the lockup "cleared" — consistent
with the broadly documented small-cap-IPO long-run underperformance
literature continuing past the lockup date, not a distinct reversal
event at it. `proteus.lab.record_backtest` records this as
`ipo_lockup_reversion: refuted` — terminal for this slug. A revised
hypothesis (different entry/hold window, a different population
definition, or a different mechanism entirely) would need a fresh slug
and a fresh prereg, per the lab's one-way-ratchet rule.
