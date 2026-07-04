# Results: insider-cluster replay, survivorship correction

Run 2026-07-04 per the frozen terms of
`docs/lab_prereg_cluster_survivorship_correction.md`. One shot, no
re-cuts.

## What was attempted

All 42 events tagged `unpriceable_no_bars` in
`docs/data_oracle_replay_graded_2026-07.json` were run through
`shared.sharadar.resolve_ticker(sym, as_of=event_date)`.

- **7 of 42** returned a TICKERS hit from the resolver.
- **35 of 42** returned no match at all (Sharadar's NYSE/NASDAQ/AMEX-
  centric universe does not carry these tickers — mostly OTC/pink-sheet
  or bulletin-board names, consistent with the prereg's stated
  expectation that Sharadar would not resolve all 42).

## Manual verification caught 4 false positives among the 7 "resolved" hits

Per the prereg's frozen method, a resolved hit is only valid if the
event's knowable/entry date falls inside the candidate's
`[firstpricedate, lastpricedate]` window. Checking each of the 7:

| Ticker (event date) | Sharadar hit | Coverage window | Verdict |
|---|---|---|---|
| NORD (2025-02-03, 2025-05-16) | Nord Anglia Education Inc | 2014-03-26 → 2017-09-01 | **FALSE MATCH** — ticker recycled/reused; the 2025 insider-cluster company is not this one |
| UTGN (2025-05-06, 2026-05-18) | UTG Inc | 1990-06-19 → 2001-12-31 | **FALSE MATCH** |
| CHUC (2025-12-17) | Charlie's Holdings Inc | 2003-10-15 → 2023-11-14 | **FALSE MATCH** (event postdates last price by >2 years) |
| PALX (2026-04-20) | Palex Inc | 1997-03-20 → 2000-03-07 | **FALSE MATCH** |
| PHXE-P (2025-09-29) | Phoenix Energy One LLC | 2025-09-30 → 2026-07-02 | **GENUINE** — dates align, currently live |

This is a real gap in `shared.sharadar.resolve_ticker`: when a symbol
has exactly one TICKERS candidate and that candidate's window does
NOT cover `as_of`, the function's window filter (`if windowed: hits =
windowed`) leaves `hits` unfiltered rather than treating "single
candidate, out of window" as no-match — so it silently returns a
same-ticker, wrong-company hit instead of raising. All 4 false matches
here would have contaminated the study with an unrelated, long-dead
company's price history had they not been checked by hand against the
window before use. **Not fixed in this session** (a library correctness
fix is out of scope for a research pass and needs its own tests) —
flagged here for a follow-up ticket. Every number below uses ONLY the
one genuine resolution (PHXE-P); the 4 false matches were discarded
before any return was computed on them.

## Genuine resolution: PHXE-P

- Event date 2025-09-29, knowable date 2025-10-01, entry = first close
  ≥ knowable + 5 calendar days = **2025-10-06 close $20.30** (Sharadar
  SEP).
- h126 (~6mo) target 2026-04-06 (elapsed as of today 2026-07-04): close
  **$24.70** → stock return **+21.67%**. IWM over the identical window
  (2025-10-06 close $246.81 → 2026-04-06 close $252.36, broker bars):
  **+2.25%**. **Excess = +19.43%.**
- h252 (~12mo) target ~2026-10-06: **not yet elapsed** — cannot grade.

## Corrected headline numbers

| Horizon | Original n / mean | Newly resolved | Corrected n / mean | Move |
|---|---|---|---|---|
| ~6 months (126td) | 612 / −4.12% | +1 (PHXE-P, +19.43%) | **613 / −4.08%** | +0.04pp — immaterial |
| ~12 months (252td) | 291 / −6.38% | 0 (only genuine resolution hasn't reached 12mo) | **291 / −6.38%** | unchanged |

Both moves fall inside the prereg's pre-declared "no material change"
band (±2pp at 6mo; fewer than 5 events resolving at 12mo). The frozen
**REFUTED** verdict on the original 2026-07-03 replay is untouched —
this correction does not reverse it in either direction, and per the
prereg it could not have on 1-2 microcap data points regardless of
sign.

## Honest reading

1. **The correction mostly failed to correct anything** — not because
   the delisted names were checked and found immaterial, but because
   Sharadar's SEP product, despite covering 15,593 delisted companies,
   does not reach the specific population of thinly-traded/OTC tickers
   that Robinhood also couldn't price. Both vendors have the same blind
   spot for this bottom-of-the-barrel microcap slice. The backlog's
   framing ("dead names were buys too") remains an OPEN, UNANSWERED
   question for 35 of 42 events — this study neither confirms nor
   refutes what those names actually did.
2. **What Sharadar's ticker-recycling trap demonstrates in practice**:
   4 of 7 raw resolver hits were wrong companies. Any future study
   pulling Sharadar data through `resolve_ticker` for a small-cap/OTC
   population MUST manually verify `firstpricedate`/`lastpricedate`
   against the event date before trusting a single-candidate hit — the
   resolver's own window check does not protect against this case.
3. **The one genuine data point (PHXE-P, +19.4% excess) is a reminder
   of the population's own finding**: the distribution is a lottery
   with a thin positive right tail (original study's max was +955%).
   One more lottery ticket landing positive changes nothing about the
   mean.
4. **Consequence**: no verdict change, no rule change. Backlog item #6
   is answered as "attempted, data does not exist in an available
   vendor for the bulk of this subset" rather than "measured and
   found immaterial" — a meaningfully different conclusion the
   backlog's original framing didn't anticipate, and worth carrying
   forward: any future attempt at this population needs an OTC-market
   data vendor (e.g. a pink-sheets-specific feed), not another
   NYSE/NASDAQ-centric one.

## Follow-ups filed

- `shared.sharadar.resolve_ticker` window-fallback gap (single
  candidate, out-of-window, still returned) — needs a fix + test
  before any study leans on unverified single-candidate resolutions.
- Backlog item #6 restated: closed as "vendor-blocked for 41/42 names,"
  not struck as fully answered. A genuine survivorship correction for
  this population needs OTC-coverage data, not Sharadar SEP.
