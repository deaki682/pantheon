# Prereg — CEF issuer-tender convergence (backlog #7)

- **Sponsor:** operator (Proteus's shelved thread, adopted house-wide)
- **Committed:** 2026-07-04, BEFORE any filing catalog or price outcome
  is pulled for this study. First study selected under the lab's
  candidate gates (lab.md §3b).
- **Slug:** `cef_tender_convergence`

## 0. Candidate gates (the reason this is top of queue)

- **G1 tape:** PASS — the signal is a regulatory filing (SC TO-I), not
  derivable from past prices.
- **G2 constraint:** PASS — the constrained counterparty is the FUND
  ITSELF, bound by its own tender-offer terms (SC TO-I: offer to buy
  back shares at a stated NAV-linked price, open ≥20 business days by
  rule 14e-1(a)). The document IS the constraint.
- **G3 capacity inversion:** PASS — CEFs are small and thin; tenders
  often carry odd-lot priority; institutions cannot size in.
- **G4 arithmetic:** PASS — the terminal value is quasi-contractual
  (e.g., 98% of NAV at expiration) rather than a drift forecast.
- **G5 power:** PASS-expected — issuer tenders are a dense, recurring
  event stream; the catalog will confirm n.

## 1. Question

When a listed closed-end fund announces an issuer tender offer (SC
TO-I), does its market price earn positive market-adjusted returns
from announcement into the offer window — the mechanical
price-toward-NAV convergence Proteus's thread hypothesized?

**Decision it buys:** whether a tender-announcement strategy earns a
paper forward test (the standard ratchet — never live from a
backtest), and whether the house builds the standing SC TO-I watch
into `shared/event_calendar.py`.

## 2. Population (frozen, complete-catalog rule)

- **Events:** ALL SC TO-I filings (EXCLUDING amendments "SC TO-I/A")
  filed 2020-01-01 → 2026-05-15 (end chosen so every event's outcome
  window completes by the data pull), via EDGAR full-text search,
  filer matched to a listed CEF (Sharadar SFP TICKERS category
  "CEF"). One event per fund per 180 calendar days (the first filing
  starts the event; later filings inside 180d are the same tender's
  paperwork).
- **Match rule:** EFTS display-name ticker → SFP CEF ticker;
  unmatched filers resolved by exact name match against SFP names;
  still-unmatched events land in the mandatory `unpriceable`
  disclosure with counts — never silently dropped.
- **Bars:** Sharadar SFP daily closes (dividend-adjusted where
  `closeadj` present) for matched funds and SPY.

## 3. Metric & execution (frozen)

`shared.gauntlet.event_car`: entry at the close of the FIRST trading
day strictly AFTER the filing date; market-adjusted CAR vs SPY total
return at offsets 0..25 trading days (≥20 business-day statutory
minimum offer period ≈ the offer window). PRIMARY statistic: mean and
shrunk-mean market-adjusted CAR at offset 25, with t-stat, win rate,
and per-offset curve. No costs modeled in the event study (disclosed;
a forward test, if earned, carries real spreads — CEF spreads are
wide and this is named in the bias checklist).

## 4. Verdict (frozen)

- **SUPPORTED** iff shrunk mean CAR(25) > +1.0% AND t ≥ 2.0 AND
  n ≥ 30 priced events.
- **REFUTED** iff shrunk mean CAR(25) ≤ 0 with n ≥ 30.
- **INCONCLUSIVE** otherwise (including n < 30 — reported, no verdict
  forced).
- SUPPORTED earns `start_forward_test` (paper, ≥20 graded live events
  on the shrunk mean, per the standard gate). Nothing here ever
  touches live money directly.

## 5. Secondary analysis (preregistered, non-gating, may lag)

The discount-conditioned cut Proteus's thread named: events where the
filing body states the fund's NAV, permitting a discount-at-
announcement calculation; subgroup CAR for stated-discount ≥ 12% vs
< 12%. Extraction coverage disclosed (filings without parseable NAV
are listed); this cut informs the forward-test design but does not
gate the §4 verdict.

## 6. Bias checklist (pre-answers; finalized at record time)

1. **Survivorship:** population from EDGAR filings (not from surviving
   funds); funds delisted after tendering keep their SFP bars through
   final day; unmatched/unpriceable events disclosed with counts.
2. **Look-ahead:** entry strictly after the filing date; EFTS filing
   dates are acceptance dates; PITEventFeed conventions.
3. **Selection:** complete SC TO-I catalog in the window — no
   examples-that-came-to-mind; the window and dedup rule are frozen
   above before the catalog exists.
4. **Multiple testing:** 1 primary statistic + 1 preregistered
   secondary cut; counter +2 at record time (house counter cited).
5. **Overfitting:** zero tuned parameters (offset 25 is the statutory
   window, threshold +1.0%/t≥2 frozen here).
6. **Costs/liquidity:** event study is gross; CEF spreads are wide and
   would consume small CARs — the SUPPORTED bar (+1.0% shrunk) exists
   partly for this; a forward test grades net at real fills.
7. **Regime:** 2020–2026 window spans covid crash, ZIRP, the 2022 rate
   shock (which blew CEF discounts wide), and two bull legs; CAR
   reported by calendar year as the regime table.
8. **Small-n:** shrunk mean is the cited effect; n reported per
   offset; no verdict below n=30.
