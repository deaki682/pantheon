# Prereg — `sp500_index_effect` (forced-flow: S&P 500 additions)

- **Sponsor:** operator (forced-flow family, alpha map #14 — highest-
  prior untested)
- **Committed:** 2026-07-04, BEFORE any outcome is computed. Event
  population parsed from Wikipedia's "Selected changes" table
  (effective date + added ticker + announcement date from the S&P
  citation ref); prices from Sharadar SEP (delisted-inclusive).

## Question & the decision it buys

When S&P announces a stock's addition to the index, index funds must
buy it by the effective date — a hard, documented forced flow (G2 pass:
the counterparty is a mandate-bound index fund). Does the added stock
earn positive market-adjusted return from ANNOUNCEMENT to EFFECTIVE
(the tradeable window), and **does it survive post-2010** (the decision:
is this a DEPLOYABLE edge for a live god, or a decayed textbook relic)?

## Population (frozen)

All S&P 500 ADDITION events with a parseable announcement date strictly
before the effective date, from the Wikipedia changes table. Added
tickers resolved to Sharadar final tickers; events whose added ticker
has no SEP bar in the window land in `unpriceable` (disclosed).
Effective testable range ~1998-2026 (SEP starts 1998).

## Metric & verdict (frozen)

`event_car`: entry at the first close strictly AFTER the announcement
date; market-adjusted CAR vs SPY at offsets 0..25 trading days. Key
readouts: CAR at the effective date (median ~7 td) and at +25.
Mandatory **pre-2010 vs 2010-onward split** (the decay test).

- **SUPPORTED (deployable):** 2010-onward subset shrunk mean CAR at the
  effective-window peak > +0.5% AND t ≥ 2 AND n ≥ 30.
- **REFUTED / DECAYED:** 2010-onward shrunk mean ≤ 0 (or t<2) at n≥30 —
  the effect is a historical relic, not a live edge.
- **INCONCLUSIVE:** n < 30 in the modern subset.

Costs: gross event study; the +0.5% bar is a spread buffer (index adds
are liquid large-caps, so costs are low — a point in the family's favor
if it survives).

## Bias checklist (at record)

Survivorship: population is EVENTS (from the changes list), not
survivors; delisted added-then-removed names kept via SEP. Look-ahead:
entry strictly after announcement. Selection: "Selected changes"
completeness caveat disclosed (Wikipedia may omit some); the modern
subset (2018+, ~15-23/yr) is well-covered. Multiple testing: 1 primary
+ the pre/post-2010 split; counter +1. Regime: the split IS the regime
test. Small-n: modern subset n reported; no verdict below 30.

## Deployability note (for the god question)

Even a SUPPORTED verdict here is a PAPER forward-test earner, not a live
launch — the modern index effect is thin and fast (a ~7-day window),
and a live version needs the announcement caught same-day. If the modern
subset is dead (the likely prior), this family is CLOSED for the god and
net-issuance remains the candidate.
