# Results: full-population insider-cluster replay (Oracle signal)

Graded 2026-07-03 per the frozen terms of
`docs/oracle_prereg_cluster_replay.md`. One shot, no re-cuts. Per-event
data: `docs/data_oracle_replay_graded_2026-07.json`.

## Population

- Every Form 4 filed 2025-01-01..2026-05-31, from EDGAR daily indexes:
  **258,503 accessions across 368 filing days** (complete population, no
  FTS truncation). ~78,900 candidate filings fetched and XML-parsed
  (candidacy pre-filter per prereg amendment); **12,546 open-market
  buys** confirmed; **934 cluster events** across 713 tickers.
- All 991 buys from the first fetch tranche were missing filing dates
  (pre-patch); every one was re-fetched and recovered EXACTLY — entries
  key off knowability (filing availability), never off transaction dates.
- 42 events (4.5%) unpriceable — no bars at the broker (delisted /
  acquired / OTC names Robinhood doesn't carry). Named in the data file,
  excluded from grading, per prereg. Note the direction of this hole:
  it removes both acquisitions-at-premium and worthless delistings.

## Headline: the frozen verdict is REFUTED

Excess return vs IWM, entry at first close ≥ knowability + 5 days:

| Horizon | n graded | mean excess | t | win rate |
|---|---|---|---|---|
| 5 trading days | 892 | +0.43% | 1.13 | 47% |
| 10 trading days | 891 | +0.68% | 1.33 | 46% |
| ~6 months (126td) | 612 | **−4.12%** | −1.66 | 33% |
| ~12 months (252td) | 291 | **−6.38%** | −1.06 | **32%** |

The frozen refutation clause — 12-month excess ≤ 0 with n ≥ 150 — is
met (n=291, −6.4%). **Bought mechanically, the average insider cluster
LOST to small-caps over this window.** The median event lost to IWM by
26.7%; p10 was −88.5%. The distribution is a lottery ticket: two-thirds
of cluster names crater or stagnate, a thin right tail moonshots
(max +955% — a 6-buyer microcap cluster).

Dose-response (12-month excess by buyer-count tercile): −10.4% → −5.6%
→ −3.1%. Direction is right (more buyers = less bad) but every tercile
is underwater and none is significant.

**Convergence (pre-registered test): NOT validated.** Multi-lens events
(2+ of: cluster, 13D, 13F, quality) averaged −8.4% at 12 months vs
−3.3% for cluster-only — the wrong direction, though neither is
statistically distinguishable. On this window, lens-stacking did not
rescue the signal.

Short horizons (the Midas byproduct cut): +0.4%/+0.7% at 5/10 days,
positive but insignificant. Suggestive of a small announcement-pop,
nothing more. LOOK, DON'T TOUCH.

## Integrity checks performed

- Hand-recomputed a sampled event's 12-month excess from raw bars:
  matches to 4 decimal places. Entry dates verified after knowability.
- The 13D annotation initially found zero activist filings after
  2025-01 — EDGAR renamed the form `SC 13D` → `SCHEDULE 13D` in the
  structured-data transition. Caught by the plateau smell-test, fixed,
  rescanned all 500 index days. (Production `oracle/lenses.py` already
  used the new token; only this study's first pass was affected. The
  legacy helper `is_fresh_13d` in `oracle/smart_money.py` still matches
  only the old names — flagged for cleanup, it is not in the live path.)

## Honest reading

1. **What is refuted:** the cluster trigger as an AUTO-BUY. Buying every
   tight cluster equal-weighted underperformed IWM at 6 and 12 months in
   this sample. The raw signal, mechanically harvested, was not alpha in
   2025–26.
2. **What is NOT refuted by this test:** Oracle as a selector. She does
   not buy every cluster — she reads ~40 dossiers per cohort and picks
   8. A 32%-win, fat-right-tail universe is survivable, even lucrative,
   for a good selector (the IAUX-type events exist), and fatal for an
   indiscriminate one. This replay measures the pond, not the fisher.
   Whether her selection adds enough to clear the pond's −6% drag is
   exactly what her graded journal calls will answer — and the capital
   gates (alpha_t ≥ 2 before scaling) now look prescient rather than
   bureaucratic.
3. **Regime caveat, stated once:** the 12-month cohort is entries
   Jan–Jul 2025, whose forward windows ride one of the strongest
   small-cap rallies on record. Excess-vs-IWM was a maximally hard test
   in this regime. That is a reason the magnitude may overstate the
   drag; it is not a reason to un-refute the clause.
4. **Consequences under the freeze:** no live-rule changes. Oracle
   trades her cohort as written. But expectations change: the burden of
   proof is on her dossier layer, and cohort-2 selection should treat
   "cluster exists" as table stakes, not conviction.

## The live tail (byproduct — candidates only, NOT signals)

253 clusters aged 6–15 months whose stock has not re-rated (last close
≤ entry +10%), ranked by lens convergence then cluster dollars — the
"Oracle would have found it, window still open" list. Full list:
`docs/data_oracle_live_tail_2026-07.json`. Top of the list: PSEC, ROP,
MDRR, MNR, MAGN (3 lenses each); CRSP, TXO, SEVN, AMR, VRCA, ZBIO
(2 lenses, $18M–$53M clusters). Every name still requires a full
balanced dossier before it can enter any cohort — this replay just
showed why that filter is the whole game.

## Addendum (2026-07-03, post-verdict): lens decomposition — LOOK, DON'T TOUCH

Diagnostic slice of the same graded events, run after the frozen verdict
to locate the convergence drag. Multiple comparisons; one window; no
rule may cite this without fresh-data pre-registration.

12-month excess vs IWM by lens combination:

| Group | n | mean | t |
|---|---|---|---|
| Cluster only | 114 | −3.3% | −0.3 |
| Cluster + quality-pass (no other lens) | 151 | **−12.4%** | **−2.0** |
| Cluster + activist 13D | 26 | +15.3% | +0.6 |
| Three lenses | 9 | −42.6% | −3.1 |

The convergence failure is concentrated in the QUALITY lens. Candidate
mechanism: the quality screen scores trailing filings, so "clean books +
insiders buying the dip" selects businesses whose deterioration hasn't
reached the filings yet, while names that already failed the screen are
washed out. The 13D lens — the rarest — was the only one pointing
positive. 5-day cut (Midas-relevant): 2+ lenses +0.63% vs cluster-only
+0.17%, insignificant; short-horizon convergence directionally survives.

Standing follow-up (queued): pre-register the quality-lens test on data
this replay never touched (2026–27 accumulating clusters, or a 2022–24
backfill) before any cohort-2 screen change.
