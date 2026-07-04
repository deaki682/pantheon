# Pre-registration: survivorship-correction of the insider-cluster replay via Sharadar SEP

Committed 2026-07-04, BEFORE any price bar or excess-return outcome
exists for this study. This is backlog item #6
(docs/RESEARCH_BACKLOG.md) — the first study through the Sharadar SEP
feed (docs/sharadar_qa_2026-07-04.md), doubling as its trial by fire.

## Question

The frozen 2026-07-03 replay (docs/oracle_prereg_cluster_replay.md,
docs/oracle_replay_results_2026-07.md) refuted the insider-cluster
signal at 12 months (n=291, −6.38%, t −1.06) but had to bucket 42/934
events (4.5%) as "unresolved-unpriceable" because Robinhood's
historicals API serves no bars for delisted/renamed/OTC-only tickers.
Does pricing those 42 events with Sharadar SEP (survivorship-bias-free,
purchased specifically to close this hole) move the verdict, and does
this study's outcome validate Sharadar as the house's answer to the
broker's delisted-bars wall?

## Feasibility check already performed (disclosed, not a data peek)

Before writing this prereg, `shared.sharadar.resolve_ticker()` was run
against all 42 unpriceable tickers (TICKERS metadata only — company
name/exchange/price-date-window fields — no SEP price bars, no return
of any kind was touched). This is the same class of feasibility check
the house has already treated as pre-prereg-safe (e.g. "is the
population buildable" checks before backlog items were queued). Result,
disclosed in full before any bar is fetched:

- **34 of 42 events: NO MATCH.** Symbol not in the ~21,893-company SEP
  TICKERS universe at all (ETST, LBSR, MYCB, NWPP, QNBC, LCTC, LARAX,
  GTHP, VREOF, SCND, CSBB, RYES, VWFB, NNUP, LAWIL, GGROU, CWGL, CCFN,
  BUKS, PGIM, IVFH, WBHC, and repeats of these). These are deep
  OTC/pink-sheet microcaps that evidently never had the NYSE/NASDAQ/AMEX
  history Sharadar's SEP product is built from.
- **4 of 42 events (NORD x2, UTGN x2): FALSE-POSITIVE MATCH.** The
  ticker exists in SEP but its priced window (NORD 2014-03-26 to
  2017-09-01; UTGN 1990-06-19 to 2001-12-31) does not cover the event
  dates (2025-10-14, 2025-05-08/2026-05-20) — a different, long-dead
  company recycled the same symbol decades before today's OTC issuer
  reused it. `resolve_ticker(as_of=...)` is written to filter these out
  by window when `as_of` is passed; confirmed it correctly rejects the
  match (falls through to "no match in window" territory) rather than
  silently grading the wrong company. Two more repeats (CHUC, PALX)
  behave identically: CHUC's SEP window ends 2023-11-14, before its
  2025-12-17 event; PALX's ends 2000-03-07, nearly a quarter-century
  before its 2026-04-20 event.
- **1 of 42 events (OABIW): WRONG INSTRUMENT.** The base ticker OABI
  (common stock) resolves and prices fine, but the actual Form 4 filer
  bought the WARRANT (OABIW), a distinct leveraged instrument the
  broker also could not price. Substituting the common stock's return
  for a warrant purchase would misrepresent the position actually taken
  — this is excluded from the correction on instrument-mismatch grounds,
  not data availability, and stays unpriceable.
- **1 of 42 events (PHXE-P): GENUINE MATCH.** Ticker resolves, window
  (2025-09-30 to 2026-07-02) covers the event date (2025-09-30) and
  entry date, and PHXE-P is itself the registered security class the
  Form 4 was filed against (no instrument substitution).

**Consequence, decided here before any price is pulled**: this study
grades exactly the ONE genuinely resolvable event (PHXE-P) under the
IDENTICAL frozen rules from the original prereg. It does NOT lower the
bar to admit false-positive ticker matches or cross-instrument proxies
— both of the shortcuts above would have been easy ways to inflate n
and are explicitly refused.

## Method (identical to the frozen original, per docs/oracle_prereg_cluster_replay.md)

- **Entry price**: first Sharadar SEP daily close on or after
  knowable_date + 5 calendar days.
- **Horizons**: +126 trading days (~6mo) and +252 trading days (~12mo)
  counted in the priced series' own trading-day index from entry;
  graded only where the horizon has elapsed as of 2026-07-04.
- **Benchmark**: IWM total return over the identical calendar window
  (broker historicals, same source as the original study).
- **Excess** = stock simple return − IWM simple return over the same
  entry→exit dates.

## What would count as validation / refutation of the CORRECTION

This single additional event cannot on its own flip a 291-event
12-month verdict; the pre-registered bar is therefore about the
DISCLOSURE, not a new statistical test:

- **Vendor validated for this use case**: if Sharadar had resolved a
  material fraction (pre-registered threshold: ≥50%) of the 42 gap
  events to genuine, correctly-windowed, correct-instrument matches.
- **Vendor does not close this particular gap**: if it resolves fewer
  than that (this is what the feasibility sweep above already shows:
  1/42 = 2.4%, so this arm is decided before a single bar is fetched).
  The house conclusion in that case: Sharadar SEP is validated for its
  QA'd use cases (renamed/bankrupt/acquired NYSE-NASDAQ-AMEX names —
  backlog #4, #8) but does NOT reach the deep-OTC insider-cluster tail
  that this replay's population disproportionately samples. That tail
  remains a disclosed, irreducible-with-current-vendors survivorship
  hole for cluster-signal work specifically.
- The 12-month headline (−6.38%, n=291) is reported updated with
  whatever n the one new event adds (n=291 or 292 depending on whether
  PHXE-P's own 252-trading-day horizon has elapsed by 2026-07-04); the
  refutation verdict from the original frozen study is NOT reopened by
  one event either way.

## What this is NOT

- Not a re-cut of the 892 already-graded events — those stand exactly
  as frozen in docs/data_oracle_replay_graded_2026-07.json.
- Not a change to any live rule. Oracle trades her cohort regardless.
- Not the final word on Sharadar for the house — backlog #4 and #8
  target different (exchange-history, not deep-OTC) populations where
  the vendor's QA'd strengths actually apply; this study's null result
  here says nothing about those.
