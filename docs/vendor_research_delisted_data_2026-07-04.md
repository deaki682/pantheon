# Vendor research: survivorship-bias-free US daily price data (2026-07-04)

Commissioned by the operator alongside the house-lab build. Decision
pending — nothing purchased. Backlog items #4, #6, #8 are blocked on
this. Full comparison below, as delivered by the research pass.

## Ranked recommendation

1. **Sharadar Equity Prices (SEP) via Nasdaq Data Link** — ~20,000 US
   companies INCLUDING delisted, back to 1998; explicitly marketed as
   survivorship-bias-free; `permaticker` stable IDs give point-in-time
   ticker mapping (a 2021 name that died in 2022 is servable as it
   traded). REST API + bulk CSV + Python client, runs headless on
   Linux (our stack). Individual tier ballpark $40-60/mo but the
   current price is LOGIN-GATED and unverified — must create a free
   account to confirm before committing.
   Weaknesses: history starts 1998; NO ETFs/CEFs (separate SFP
   product); NO historical index constituents (small/mid-cap-as-of
   must be reconstructed from market-cap fields); split-adjusted OHLC
   + unadjusted close only.

2. **Norgate Data US Stocks Platinum** — delisted back to 1990 PLUS
   historical index constituents (Russell/S&P membership as-of-date —
   directly solves Delphi's point-in-time universe, backlog #4).
   VERIFIED $630/12mo (~$52.50/mo). Practitioner gold standard for
   delisted coverage. Weakness: Windows desktop updater + local
   proprietary DB, Python lib reads locally — no REST API, no native
   Linux; would need a Windows VM/export step.

3. **EODHD "EOD All World"** — $19.99/mo or $199/yr verified. ~11,000
   delisted US companies since 2000; pre-2018 delistings EOD-only
   (fine); but per-ticker completeness is opaque (their own docs route
   you to support). Budget/cross-check feed, not a primary source for
   event studies.

Excluded: CRSP (institutional-only via WRDS), Databento (history
starts 2023), Algoseek (quote-only institutional pricing), Polygon/
Massive (repeated practitioner complaints about delisted metadata;
Starter tier only 5yrs), FMP (delisted LIST endpoint but price-history
completeness undocumented), Tiingo ($30/mo, real but least-documented
delisted EOD coverage of the contenders).

## Decision frame for the operator

- If the login-gated Sharadar individual price comes back <= ~$60/mo:
  Sharadar SEP is the pick (Linux-native API beats Norgate's Windows
  tax for an automated house).
- If Sharadar prices high OR index constituents matter more than API
  ergonomics: Norgate Platinum at a verified $630/yr — accepting a
  Windows VM export step.
- EODHD at $199/yr is the fallback if budget is the binding constraint.

## What the purchase unblocks (docs/RESEARCH_BACKLOG.md)

- #4 Delphi point-in-time universe (Norgate's constituents do this
  natively; Sharadar approximates via market-cap fields)
- #6 survivorship-corrected insider-cluster replay (the acceptance
  test for whichever vendor we buy)
- #8 PEAD horizon sensitivity replay
