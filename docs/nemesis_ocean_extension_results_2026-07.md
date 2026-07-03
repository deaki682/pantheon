# Results: spinoff ocean extension, 2021–2024 vintages

Graded 2026-07-03 per the frozen terms of
`docs/nemesis_prereg_ocean_extension.md`. Reference-class measurement
only — no live-rule changes were on the table either way. Full event
table: `docs/data_ocean_extension_2026-07.json`.

## Population

- Daily-index sweep 2021-06-01..2024-12-31: **75 10-12B registrants**
  (complete population, no FTS truncation).
- Triage: **66 confirmed spinoffs**, 9 excluded (direct listings, bank
  holdco registrations, shells), every exclusion logged with reason.
  NOTE: the first triage pass scanned only the 10-12B primary document
  and wrongly excluded 42 real spinoffs (Organon, GXO, Constellation…)
  whose spin language lives in Exhibit 99.1 — the same primary-doc-only
  defect fixed in the Nemesis reader on 2026-07-03. Caught by exclusion-
  rate smell-test, repaired by exhibit-directory scan.
- Tickers: 56 resolved (registry, XBRL cover facts, or 10-K cover
  pages — never from memory). 8 registrants are never-traded SEC shells
  (no periodic report ever filed) — excluded from BOTH bounds.
- **Disappeared bucket (10 names, reported per prereg):** LYLT
  (bankrupt 2023 — a true −100%-class outcome), TSVT (acquired by BMS),
  ZIMV (acquired), EHAB (acquired), KLG (acquired by Ferrero), MURA
  (wound down), TPCO + Outdoor Products Spinco (ticker unresolvable),
  ORBS + RENX (identity drift: bars begin 949–1052 days after the
  10-12B under renamed successor tickers; spin-era trading unpriceable).
  Most of the acquisitions closed at premiums, so the worst-case bound
  below is known to be far too pessimistic; dispositions noted by name.

## The regime answer

Frozen trigger (production `assess_window`), frozen slicing, frozen
exits (150d / −40%), 5bps/side, entries at trigger-fire close. 48
events fired (4 of them — SNDK, RHLD, TWNPQ, DMNIF — are late-2024
registrants whose windows landed in 2025–26 and overlap the first ocean
study; disclosed, reported in their entry-year rows).

| Cut | n | mean excess vs SPY | t | win |
|---|---|---|---|---|
| All events | 48 | **−1.0%** | −0.24 | 50% |
| Worst case (disappeared = −100%) | 58 | −18.1% | −3.0 | 41% |
| Vintage 2021 | 9 | +0.1% | 0.0 | 33% |
| Vintage 2022 | 11 | −2.8% | −0.4 | 45% |
| Vintage 2023 | 15 | +5.0% | +0.9 | 60% |
| Vintage 2024 | 9 | +2.1% | +0.2 | 67% |

Portfolio path ($2,000, 5 slots, frozen rules, 2021→2026):
**$2,000 → $1,754 (−12.3%)** across 4.5 years in which SPY roughly
doubled.

**Pre-committed interpretation applies: the trigger is
REGIME-DEPENDENT.** Per-event mean excess in the 2021–24 reference
class is indistinguishable from zero (and the portfolio path is
negative). The 2025–26 warm-vintage result (+41.2% buy-all) does not
generalize backward: it was carried by two tail names in a friendly
tape. The post-dump window, mechanically harvested, has NO reliable
per-event edge across regimes.

## What this means for Nemesis (no rules changed)

1. The buy-all leg was never the strategy; it is the CONTROL. This
   result recalibrates expectations for that control: near-zero mean,
   lottery tail, real disaster risk (LYLT went to zero; TWNPQ gapped
   through its stop in study 1).
2. The measured value in the Nemesis stack remains the VETO — 3/3 on
   pre-registered history, and the reading condemned the worst names.
   A near-zero-mean pond with fat tails on both sides is exactly where
   discarding the left tail pays. The live three-leg race (buy-all vs
   veto-filtered vs own-picks) is now even more the whole question.
3. Combined 4.5-year reference class (this study + study 1) is the
   base-rate document November's live grades compare against.
4. Runbook gains the pre-committed risk disclosure: do not extrapolate
   warm-vintage economics; expect the control leg to hover near zero
   excess in normal/bear tapes.
