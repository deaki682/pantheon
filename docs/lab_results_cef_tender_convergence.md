# Results — `cef_tender_convergence` (backlog #7)

- **Prereg:** [docs/lab_prereg_cef_tender_convergence.md](lab_prereg_cef_tender_convergence.md)
  (committed 2026-07-04 before any catalog or price pull)
- **Run:** 2026-07-04, `run_cef_tenders.py` (catalog → outcomes),
  engine `shared.gauntlet.event_car`
- **Data:** EDGAR quarterly full-index sweeps 2020Q1–2026Q2 → 3,010
  raw SC TO-I filings → 153 CEF-matched events (180-day dedup) across
  87 listed funds; Sharadar SFP daily bars + SPY total return
- **Registry:** `cef_tender_convergence` → **refuted** (terminal),
  `hypotheses_ever` 98→100

## Verdict

**REFUTED** — and not as a null: post-filing tender windows carry a
*significantly negative* market-adjusted drift.

| population | n | mean CAR(25) | shrunk | t | win rate |
|---|---|---|---|---|---|
| **Listed (primary)** | 132 | **−1.81%** | −1.57% | **−3.91** | 33.3% |
| Raw (incl. sparse-quote vehicles) | 153 | −0.86% | −0.76% | −1.88 | 39.2% |

Means and medians agree (−1.81% vs −1.67%) — no outlier dependence.
The CAR curve is negative from offset 3 and takes its second leg down
through offsets 20–25, the expiry/proration window.

## What the first pass caught (and why the primary is the listed cut)

The frozen population is "listed CEFs"; the operational proxy (SFP
category = CEF) admitted sparse-quote vehicles whose stale prints
manufactured artifacts — VCX produced six *bit-identical* +314% CAR3
readings from a 73-bar zombie series; MSIF had zero 2024 bars yet two
2023–24 "events". The listing screen (≥15 bars in the 30 calendar
days BEFORE filing — pre-event data only) removed 21 events across 4
tickers (MSIF ×7, VCX ×6, EIIA ×5, FSCO ×3), all disclosed. Both
cuts are reported above; the verdict is the same sign under both, and
*stronger* on the clean cut. Also disclosed: a name-parsing bug in the
first catalog build broke the name-match fallback; the fix added 24
listed events BEFORE any outcome was computed.

## Per-year table (regime disclosure)

| year | n | mean CAR(25) |
|---|---|---|
| 2020 | 15 | +0.1% |
| 2021 | 20 | +0.7% |
| 2022 | 13 | +2.9% |
| 2023 | 30 | −2.9% |
| 2024 | 47 | −1.4% |
| 2025 | 21 | +0.2% |
| 2026 | 5 | −6.5% |

No year clears the +1.0% bar; the lone meaningfully positive year
(2022) is the rate-shock cohort, n=13.

## Reading the refutation

The gates were right about the *structure* and wrong about the
*residual*: the fund really is a constrained NAV-linked buyer — but
(a) the tender is typically press-released before the SC TO-I lands,
so the convergence is plausibly priced before this study's entry;
(b) the contractual price applies only to the prorated fraction of
shares actually accepted; and (c) discounts re-widen into expiry,
which is exactly where the curve's second leg down sits. As a
tradeable rule at the filing-date entry, the edge is not just absent
— it is significantly the wrong sign. An earlier-anchor variant
(press-release entry) would be a NEW hypothesis with a different
event feed and must pass the gates again.

## Coverage / disclosures

100% pricing coverage on the listed population after the screen; the
2,813 unmatched filers are operating companies and UNLISTED interval
funds (quarterly repurchase vehicles with no market price — out of
scope by the frozen definition, listed with counts in the catalog).
The preregistered secondary (stated-NAV discount ≥12% cut) was not
run: the slug went terminal-refuted on the primary, mooting it.
Artifacts: `docs/data/cef_tenders/results.json` + catalog in scratch
(regenerable from `run_cef_tenders.py catalog`).
