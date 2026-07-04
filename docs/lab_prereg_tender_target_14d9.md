# Prereg — `tender_target_14d9` (third-party tender targets)

- **Sponsor:** operator ("run it until you find another positive" —
  with the multiple-testing discipline stated: bars stay frozen, the
  counter ticks, and any positive's first stop is out-of-sample
  replication, not celebration)
- **Committed:** 2026-07-04, BEFORE any 14D-9 sweep or outcome.

## Gates

- **G1:** pass — anchored to the target board's SC 14D-9 filing.
- **G2:** pass — the ACQUIRER is bound by its filed tender offer
  (price, minimum condition, 20-business-day window); the target's
  14D-9 is the board's on-record response. Two constraint documents.
- **G3:** partial, honestly — merger arb is institutional territory;
  the house's capacity story (odd-lot priority exempting small holders
  from proration) is NOT testable from bars (it is per-holder
  mechanics) and is therefore explicitly NOT part of this study's
  claim. This study measures the gross drift that must exist FIRST.
- **G4:** pass — quasi-contractual terminal value: the filed offer
  price, realized on completion; deal breaks are the left tail.
- **G5:** pass — dense event stream.

## Population (frozen)

ALL "SC 14D9" filings (exact form type; /A excluded) 2016-01-01 →
2025-12-31 from EDGAR quarterly full-index. Filer = the target.
CIK→ticker via the Sharadar SEP TICKERS universe's `secfilings`-
embedded CIK (delisted names INCLUDED — successful targets delist, so
any current-registrant matching would keep only busted deals; this is
the study's load-bearing anti-survivorship choice), restricted to US
common categories, price-window checked at the filing date; 180-day
per-CIK dedup; pre-filing listing screen (≥15 bars in 30 days);
unmatched disclosed with counts.

## Metric & verdict (frozen, family-standard)

Market-adjusted CAR vs SPY TR at +25 trading days from the first
close strictly after the 14D-9 filing (`event_car`); full curve to
+40 and per-year table published. SUPPORTED iff shrunk mean CAR(25) >
+1.0% AND t ≥ 2 AND n ≥ 30; REFUTED iff shrunk ≤ 0 at n ≥ 30; else
INCONCLUSIVE. **A SUPPORTED verdict triggers an immediate 2010–2015
out-of-sample replication under a new slug before any forward-test or
live-relevance conversation — the TO-C lesson, now standing policy.**

## Bias checklist (finalized at record)

Survivorship is THE designed-for risk here (see population); costs
are gross with the +1.0% buffer rationale; regime table per year;
expected shape: modest positive mean with a fat left tail (broken
deals) — a mean dragged negative by breaks is a legitimate refutation
of harvestability, not an excuse.
