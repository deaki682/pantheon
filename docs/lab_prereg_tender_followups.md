# Prereg — two tender-family follow-ups (committed before outcomes)

- **Sponsor:** operator ("test more hypotheses", 2026-07-04)
- **Committed:** 2026-07-04, before any SC TO-C sweep and before any
  operating-company outcome is computed. The #7 CEF filing-date entry
  question is SPENT (refuted); both slugs below ask materially
  different questions with different populations/anchors.

## Slug A — `cef_tender_toc_anchor`

**Question:** #7 found the post-TO-I window significantly negative and
hypothesized the convergence is priced at the earlier ANNOUNCEMENT.
Test it: for CEF tenders where a communication filing (SC TO-C)
precedes the SC TO-I by ≥1 calendar day, does entry at the first close
strictly after the EARLIEST TO-C earn positive market-adjusted CAR?

- **Gates:** G1 pass (filing anchor), G2 pass (same constrained fund),
  G3 pass, G4 pass, G5 uncertain — TO-C usage among CEFs is unknown;
  n<30 → INCONCLUSIVE, honestly reported.
- **Population (frozen):** the #7 catalog's 153 CEF events (fixed,
  already built) joined to ALL SC TO-C filings by the same CIKs from
  the same 2020Q1–2026Q2 full-index sweeps; event kept iff earliest
  TO-C ≥ 1 day before its TO-I. Same listing screen (≥15 bars in 30
  pre-anchor calendar days).
- **Metric/verdict (frozen):** CAR vs SPY at +25 trading days from the
  TO-C anchor. SUPPORTED iff shrunk mean > +1.0%, t ≥ 2, n ≥ 30;
  REFUTED iff shrunk ≤ 0 at n ≥ 30; else INCONCLUSIVE.
- **Note:** outcomes for these events at the LATER TO-I anchor are
  known (#7). This anchor's outcomes are not. The overlap is disclosed,
  not hidden; the question (announcement-day entry) was never tested.

## Slug B — `issuer_tender_operating`

**Question:** do OPERATING-COMPANY issuer self-tenders (SC TO-I,
non-CEF) — the company itself bound by its own filed dutch/fixed-price
terms — earn positive market-adjusted CAR through the offer window?

- **Gates:** G1 pass, G2 pass (the issuer, bound by its own TO-I),
  G3 partial (mixed sizes — disclosed, small-cap cut preregistered
  below), G4 pass (filed price/range), G5 pass (hundreds of filings).
- **Population (frozen):** the same 3,010-row 2020Q1–2026Q2 SC TO-I
  full-index catalog, MINUS CEF-matched events; filer → ticker by (1)
  SEC company_tickers CIK map, then (2) exact name match into the full
  Sharadar SEP TICKERS universe (delisted INCLUDED, price-window
  checked against the filing date) so dead filers are recovered, not
  silently dropped; category restricted to US common stock classes;
  180-day per-CIK dedup; unmatched disclosed with counts. Same
  pre-anchor listing screen. Equity tenders only in effect: bars must
  exist for the common — debt-only tender filers without listed common
  land in the disclosure.
- **Metric/verdict (frozen):** CAR vs SPY at +25 trading days from the
  first close strictly after the TO-I filing date. Same bars as A.
- **Preregistered secondary (non-gating):** market-cap split at $2B
  (Sharadar DAILY marketcap nearest the filing date) — the G3
  capacity-inversion cut: does the effect live in the small half?

## Shared bookkeeping

Counter: +2 at registration (one per slug); secondaries only count if
run. Costs: event studies are gross (disclosed; supports bar of +1.0%
shrunk partly covers). Regime: per-year tables mandatory. Both slugs
report BOTH raw and listing-screened populations, verdict on screened
(the frozen populations say listed/priced).
