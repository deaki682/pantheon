# Sharadar SEP acceptance QA — PASSED (2026-07-04)

Subscribed by the operator; key in .claude/settings.json env
(NASDAQ_DATA_LINK_API_KEY). This QA deliberately computed NO study
metrics — spot-checks only, so no dataset was burned.

## Probes and results

| Check | Result |
|---|---|
| AAPL 4:1 split (2020-08-31) | PASS — close continuous (split-adj), closeunadj 500.04→129.04 |
| TWTR (take-private 2022-10-27) | PASS — bars while alive, last bar exactly 2022-10-27, zero after |
| ATVI (acquired 2023-10-13) | PASS — last bar 2023-10-12, zero after |
| SVB (failed 2023-03) | PASS with law below — lives under final ticker SIVBQ, history to 1990, 2021 bars at real prices (~$566) |
| Original Bed Bath & Beyond | PASS with law below — lives under BBBYQ (1992–2023-05-02); meme-era 2022 bars at real prices ($10.51) |
| FB→META rename | PASS — FB-era bars under META; resolvable via relatedtickers |
| Universe size | 21,893 SEP companies, 15,593 delisted (71%) — the survivorship hole, quantified |

## THE INTEGRATION LAW (learned live, enforced by shared/sharadar.py)

**SEP keys ALL history to the company's FINAL ticker.** Querying a
historical symbol raw returns nothing (SIVB, FB) or — worse — THE
WRONG COMPANY: "BBBY" today is the Overstock/Beyond lineage (it
recycled the ticker in 2025); the real Bed Bath is BBBYQ. An
unresolved query is how a study silently analyzes the wrong firm.

Therefore: `shared.sharadar.resolve_ticker(symbol, as_of=...)` before
ANY bar fetch — it sweeps ticker + relatedtickers against the locally
cached full TICKERS universe (cache/shared_sharadar_tickers.json) and
disambiguates recycled tickers by price-date window; ambiguity without
as_of raises rather than guesses. `ingest_symbols()` does the whole
dance and reports failures explicitly. Direct SEP queries bypassing
the resolver are a violation.

## Known limitations (from vendor research + QA)

- History starts 1998 for prices (metadata earlier); no ETFs/CEFs
  (SFP is a separate product, not purchased).
- No historical index constituents — small/mid-cap-as-of must be
  reconstructed from market-cap fields (affects backlog #4 method).
- open/high/low/close are split-adjusted; closeadj (split+div) is
  carried as close_total_return; fully unadjusted OHLC not provided
  (closeunadj only).

## Consequences

Backlog #4, #6, #8 unblocked. First study through the feed: #6
(survivorship-corrected insider-cluster replay) — prereg BEFORE the
study data pull, per house rules. QA tickers (TWTR/SIVB/BBBY/ATVI/
FB/AAPL) are disjoint from any study metric computed here (none).
