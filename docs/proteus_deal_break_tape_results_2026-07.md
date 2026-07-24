# Deal-break reversion tape study — results (Proteus v2, 2026-07-24)

**Question.** Conditional on a true arb-relevant deal break (US-listed target,
definitive whole-company deal, target cap ≥ $100M, pending ≥ 30d), what does the
target tape do after the break, and does the typed break reason predict it?

**Prereg.** Recipe journaled BEFORE any return data (proteus journal row 87,
2026-07-24, persisted to `claude/live` commit `7955039a` before execution): population
recipe, admission gates, typed reasons, day0 rule, PRIMARY = +21 trading-day
SPY-excess, decision rule (subgroup passes iff n≥8, mean ≥ +3%, hit ≥ 60%,
drop-max-name mean ≥ +1.5%), priors. Lab slug `deal_break_reversion_tape`
(hypotheses_ever 198). One dataset, one decision.

**Population.** 288 unique 8-K accessions from the full 2015–2024 census of the two
high-precision FTS phrasings, every document fetched and classified (8-agent
fan-out); 98 true-break rows → 46 deduped deals → typed exclusions (mergers-of-equals,
related-party rollups, no-premium structures) and $100M cap gate → 34 admits; plus 14
prominent breaks (Source B recall check), each verified against its own 8-K/6-K with
accession cited. n = 48. Tape: Sharadar SEP resolved as-of (delisted names covered:
RADCQ, LKSDQ, IRBTQ, MNR2, FGL1, …); benchmark SPY (SFP, dividend-adjusted). Zero
truncated series at +63d.

## Verdict — REFUTED as a buy signal

No typed subgroup passes the preregistered bar. The lane's standing default at any
future break (incl. a Hermes break-stop exit) is **STAND ASIDE**; this base rate is
quoted AGAINST any name-specific entry thesis.

| Reason (typed) | n | +21d mean | +21d median | hit | drop-max mean | pass? |
|---|---|---|---|---|---|---|
| REG_BLOCK | 32 | -3.98% | -2.68% | 41% | -4.81% | fail |
| MUTUAL_STRATEGIC | 5 | -1.95% | -1.2% | 40% | -4.28% | fail |
| ACQUIRER_WALK_MAE | 3 | 7.16% | 5.97% | 100% | 4.46% | fail |
| TARGET_VOTE_FAIL | 3 | -9.11% | -10.38% | 33% | -15.14% | fail |
| OTHER | 3 | 12.53% | 9.96% | 100% | 6.1% | fail |
| ACQUIRER_WALK_FIN | 2 | -3.51% | -3.51% | 50% | -30.58% | fail |

Aggregate (n=48): +5d mean −3.63% (hit 31%), +21d mean −2.34% (hit 48%), +63d mean
−1.07% (hit 54%). The 8 events with break-day flush ≤ −15% (AJX, LKSD, SPWH, SIMO,
RAD-17, ODP, AKRX, ROG) averaged **−11.76%** +21d excess, hit 25%: the flush is
information, not overshoot. The prereg prior (REG_BLOCK cleanest positive) graded
WRONG — the only powered cell (REG_BLOCK n=32) runs −3.98% mean, 41% hit. The two
positive cells (ACQUIRER_WALK_MAE, OTHER, n=3 each) are unpowered anecdotes.

## Raw event table

day0 = first session whose close follows the public break (Source-B rows use the
doc-verified first-tradable date). Entry = day0 adjusted close. Excess = target −
SPY, close-to-close, trading days. Src A = phrase census, B = verified prominent.

| day0 | ticker | src | reason | cap $M | flush | +5d exc | +21d exc | +63d exc |
|---|---|---|---|---|---|---|---|---|
| 2015-04-27 | TWC | A | REG_BLOCK | 41,787 | +0.7% | +1.5% | +16.5% | +22.2% |
| 2016-03-09 | VSLR | A | ACQUIRER_WALK_FIN | 555 | +1.2% | -16.2% | -30.6% | -27.7% |
| 2016-04-06 | AGN | A | REG_BLOCK | 93,363 | +3.5% | -10.7% | -13.4% | -5.3% |
| 2016-05-02 | BHI | A | REG_BLOCK | 21,175 | -2.0% | -5.6% | -3.0% | -8.0% |
| 2016-05-11 | ODP | B | REG_BLOCK | 3,350 | -40.4% | -2.5% | -5.3% | -8.1% |
| 2016-06-29 | WMB | B | OTHER | 15,491 | +1.0% | -3.7% | +10.0% | +44.4% |
| 2016-07-18 | HE | A | REG_BLOCK | 3,504 | -7.3% | +3.5% | -0.7% | -2.2% |
| 2017-02-14 | HUM | A | REG_BLOCK | 30,819 | -0.4% | -1.2% | +4.4% | +6.9% |
| 2017-02-15 | CI | A | REG_BLOCK | 37,445 | -0.1% | -0.0% | +2.3% | +7.3% |
| 2017-04-18 | FGL | A | REG_BLOCK | 1,622 | -0.2% | -1.5% | -0.1% | +6.2% |
| 2017-06-29 | RAD | A | REG_BLOCK | 4,141 | -26.5% | -18.3% | -24.7% | -34.0% |
| 2017-09-14 | LSCC | A | REG_BLOCK | 682 | -0.3% | -6.2% | -4.4% | -5.6% |
| 2017-12-29 | BCEI | A | MUTUAL_STRATEGIC | 613 | -6.9% | -0.5% | -4.1% | +0.3% |
| 2018-01-03 | MGI | A | REG_BLOCK | 715 | -9.0% | -1.3% | -5.6% | -27.3% |
| 2018-02-23 | XCRA | A | REG_BLOCK | 536 | +0.1% | +4.8% | +21.6% | +43.7% |
| 2018-04-23 | AKRX | B | ACQUIRER_WALK_MAE | 2,468 | -33.8% | +11.3% | +2.9% | +26.8% |
| 2018-07-26 | NXPI | B | REG_BLOCK | 33,839 | -5.7% | +3.3% | -2.4% | -17.1% |
| 2018-08-09 | RAD | A | TARGET_VOTE_FAIL | 1,835 | -11.5% | -8.1% | -19.9% | -17.2% |
| 2018-08-09 | TRCO | A | REG_BLOCK | 2,948 | +2.9% | +0.1% | +6.5% | +14.1% |
| 2018-12-18 | RCII | B | OTHER | 773 | -9.8% | +28.8% | +25.4% | +39.9% |
| 2019-03-22 | PVAC | A | MUTUAL_STRATEGIC | 795 | -5.1% | -15.5% | -16.4% | -46.4% |
| 2019-07-23 | LKSD | A | REG_BLOCK | 115 | -34.2% | -50.4% | -35.5% | -53.3% |
| 2019-09-11 | STC | A | REG_BLOCK | 801 | +4.7% | +1.8% | +6.4% | +13.4% |
| 2020-01-02 | PACB | A | REG_BLOCK | 787 | +0.4% | -10.5% | -6.7% | -22.0% |
| 2020-05-05 | RESI | B | OTHER | 432 | -9.4% | -0.7% | +2.2% | +2.2% |
| 2020-10-05 | GILT | A | ACQUIRER_WALK_MAE | 289 | +1.9% | -6.7% | +12.6% | +28.9% |
| 2021-04-07 | GNW | B | ACQUIRER_WALK_FIN | 1,775 | -3.7% | +3.5% | +23.6% | +2.9% |
| 2021-07-26 | WLTW | B | REG_BLOCK | 29,202 | -9.0% | -0.2% | +3.4% | +17.6% |
| 2021-09-01 | MNR | A | TARGET_VOTE_FAIL | 1,851 | +0.2% | -1.8% | +2.9% | +10.5% |
| 2021-10-01 | FIVN | A | TARGET_VOTE_FAIL | 10,949 | +4.7% | -15.4% | -10.4% | -27.7% |
| 2021-12-03 | SPWH | A | REG_BLOCK | 738 | -19.7% | -16.2% | -20.6% | -12.3% |
| 2021-12-13 | MX | B | REG_BLOCK | 802 | -0.9% | +8.9% | +9.9% | +1.4% |
| 2022-01-21 | FVCB | A | MUTUAL_STRATEGIC | 278 | -0.9% | +1.0% | +7.3% | +8.7% |
| 2022-02-14 | AJRD | B | REG_BLOCK | 3,146 | -5.6% | +2.6% | +3.6% | +15.8% |
| 2022-11-02 | ROG | B | REG_BLOCK | 4,317 | -44.3% | -19.6% | -15.7% | +4.5% |
| 2022-11-10 | PTRS | A | MUTUAL_STRATEGIC | 167 | +2.3% | -1.6% | +4.6% | +2.7% |
| 2023-05-05 | FHN | A | REG_BLOCK | 8,087 | +8.7% | -11.4% | +0.8% | +17.4% |
| 2023-05-23 | TGNA | A | REG_BLOCK | 3,641 | +2.6% | -4.9% | -9.7% | -4.3% |
| 2023-07-27 | SIMO | A | ACQUIRER_WALK_MAE | 1,725 | -19.6% | +20.4% | +6.0% | +8.6% |
| 2023-08-16 | TSEM | B | REG_BLOCK | 3,719 | -10.7% | -1.8% | -12.5% | -14.0% |
| 2023-10-23 | AJX | A | MUTUAL_STRATEGIC | 150 | -30.8% | -4.1% | -1.2% | +12.2% |
| 2024-01-03 | PNM | A | REG_BLOCK | 3,571 | +0.7% | -4.1% | -14.0% | -14.4% |
| 2024-01-30 | IRBT | A | REG_BLOCK | 473 | -8.1% | -13.1% | -23.4% | -42.5% |
| 2024-03-04 | SAVE | B | REG_BLOCK | 707 | -10.8% | -21.8% | -20.1% | -39.3% |
| 2024-09-19 | MGRC | A | REG_BLOCK | 2,509 | +0.2% | +11.1% | +7.2% | +12.8% |
| 2024-11-15 | CPRI | A | REG_BLOCK | 2,317 | +2.3% | -4.1% | +2.6% | -0.5% |
| 2024-11-19 | HMST | B | REG_BLOCK | 209 | +3.2% | -1.5% | -3.1% | -16.3% |
| 2024-12-12 | ACI | A | REG_BLOCK | 10,724 | +4.9% | +4.5% | +8.4% | +22.9% |

## Limitations (journaled, non-decisional)

1. **Event-time**: day0 keys to the termination-public date as prereged; for
   court-blocked deals the economic death often traded EARLIER at the ruling (CPRI
   10/24 ruling vs 11/14 termination; SAVE 1/16 ruling vs 3/4 termination). A
   ruling-date recut is NEW work requiring a fresh recipe and its own decision.
2. **Recall**: phrase census caught ~55% of the prominent-breaks list (20/36); quiet
   small-cap mutual terminations phrased otherwise are under-sampled; Source B skews
   REG_BLOCK-large. The REG_BLOCK n=32 cell is the trustworthy one.
3. Cap gate uses last close BEFORE termination. `announced_when` unknown for most
   census rows → day0 = next session after the 8-K date.
4. Sub-$100M drops (12): DEST ANCB SXE YTRA QUMU CDOR CXDC STCN MTCR INFI JVA BATL.
   Excluded prominent (rule): superior-proposal chains (SAVE-22, KSU, APC, VSM),
   renegotiated-closed (TIF, TCO, FSCT, DLPH), no definitive agreement (HPQ, PRGO,
   QCOM), non-US-listed (CGX.TO), out-of-window (X).

Full machine-readable table incl. verification accessions:
`cache/proteus_study_deal_break_tape.json` (state branch `claude/live`).
