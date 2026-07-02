# Nemesis v1 (crash-fade contrarian) — archived verdicts

The name Nemesis originally belonged to a crash-fade/rotation contrarian
(built and retired 2026-07-02 after five refutations; see git history and
docs/nemesis_prereg_news_bounce.md). The name now belongs to the
spinoff/special-situations reader. These are v1's recorded backtest verdicts,
preserved so they are never re-learned with money:

## Backtest verdict (2017-07 → 2024-06, frozen params, one shot — recorded 2026-07-02)

Walk-forward, next-open fills, 10bps RT costs, episode-clustered, ETF level,
run strictly on pre-hypothesis data (the 2024-26 matrix window was burned as
hypothesis-formation). 128 XLK-crash events, 58 episodes:

- **DESTINATION leg: REFUTED.** −0.84% mean net (−1.16pp excess, 40% hit).
  Walk-forward matrices kept picking receivers that bled in new regimes
  (Jan-2022: XLB three times, −0.6%/−5.2%/−5.7%). "Where the money goes" did
  not transfer across regimes. Do not promote this leg without overwhelming
  forward ghost evidence; treat its ghost entries as a monitoring control.
- **FADE leg (sector-ETF level): NO EXCESS.** +0.33% net vs +0.32%
  unconditional — buying the dip in a sector ETF is just market beta, and it
  went NEGATIVE in the 2022 bear (−0.57%/event), positive in up years. The
  sector-level bounce in the 2024-26 matrix was regime, not edge.
- **Still open:** the SINGLE-NAME no-news fade — the strategy's actual core
  claim — was NOT tested (survivorship-clean single-name history unavailable);
  cross-sectional 1-week reversal is a different (stronger) effect than
  sector-level. That question belongs to the ghost's forward sample alone.

## Backtest verdict #2 — single-name fade, both tiers (2018-01 → 2024-06, recorded 2026-07-02)

40 large (Delphi universe, stride) + 40 quality-gated small/mid (Oracle
prescreener, stride), pre-registered validity filter (60 usable), frozen crash
params, next-open fills, 10bps/80bps costs, point-in-time EDGAR news check,
episode-clustered. 966 large + 763 small crash events:

- **FADE (no-company-news crashes): REFUTED IN BOTH TIERS.** Large −1.52pp
  excess (46% hit), small −1.30pp excess (46% hit). Ex-2020 it's ~zero, never
  positive enough to clear costs.
- **The conditioning INVERTED:** crashes WITH company news outperformed
  (large +0.51pp, small +1.99pp, neither significant after multiple tests).
  "No news" ≠ "no reason": the filter only sees COMPANY filings, so
  market-wide panics (2020: −4 to −6pp) tag as "no news" while being the
  most news-driven moves of all. A crash with no company story during a
  market storm is beta collapse in progress, not mispricing.
- **Cumulative status: every Nemesis leg tested is refuted or beta**
  (destination ETF rotation, sector-ETF fade, single-name no-news fade ×2
  tiers). Nemesis is MOTHBALLED as a capital candidate. The ghost may run as
  free research; any revival requires a materially different hypothesis
  (e.g. market-calm conditioning), pre-registered, not post-hoc rummaging.
