# Pre-registration: signal-convergence test at the Midas horizon

Committed 2026-07-04 (small hours), before any cross-catalog join exists.

## Question

Midas's core thesis: when multiple independent informed-money signals
fire on the same name, short-term pop probability rises non-linearly
(his 2.5x/5x/8x multipliers — never measured). This weekend produced
three complete, independently-built event catalogs over the same 18
months. Joined, they ask: do multi-signal names actually beat
single-signal names over 5 trading days?

## Design (FROZEN)

- **Spine**: the 934 insider-cluster events (docs/data_oracle_replay_
  graded_2026-07.json) — already graded at 5 trading days vs IWM with
  knowability-keyed entries. The test is CONDITIONAL on a cluster
  firing (his most important channel); it measures whether co-signals
  add, not the co-signals alone.
- **Co-signal flags per event** (complete populations, no sampling):
  1. Earnings 8-K (Item 2.02) filed for the same CIK within the 14
     calendar days BEFORE the cluster's knowable date (Achilles
     catalog, 23,688 events).
  2. Guidance-item 8-K (7.01/8.01) same window (Midas catalog, in
     flight — complete filing-level population; NOT text-classified,
     a disclosed coarsening: "guidance-shaped filing", not "raised").
  3. Activist 13D within 180 days before (already annotated).
  4. Quality-pass flag EXCLUDED from the signal count — Oracle's
     replay measured it as a drag, and it is not one of Midas's seven
     channels.
- **Groups**: cluster-only vs cluster+1 co-signal vs cluster+2-or-more.
- **Metric**: 5-trading-day excess vs IWM (h5, already computed).

## Validation / refutation (FROZEN)

- **Validated**: (2+ co-signal group mean excess) − (cluster-only mean
  excess) > 0 with t ≥ 2, AND monotonic ordering across 0/1/2+ groups.
- **Refuted**: spread ≤ 0 with ≥ 80 events in the 1+ co-signal groups
  combined.
- **Inconclusive**: anything else. One shot, no re-cuts.

## Consequences

None mechanical either way (his multipliers are folklore-in-production;
changing them is a cohort-review decision needing its own prereg).
Validated → the multipliers earn provisional trust. Refuted → his
weekly pick memo must stop citing convergence count as conviction.

## Correction addendum (2026-07-04, committed BEFORE recomputing)

The 2026-07-04 LLM integration audit found the LIVE scorer
(`midas/scoring.py`) counts `earnings_beat`, `guidance_raised`, and
`volume_anomaly` as three independent channels even though one
earnings report routinely trips all three (the beat, same-release
guidance, and the reaction bar itself) — inflating the convergence
tier on a single event. Re-reading this test's own co-signal join
(`co_signals += earnings-8K-within-14d? + guidance-8K-within-14d? +
13D-within-180d?`), it has the identical structural defect: an
earnings 8-K and a guidance 8-K filed on the SAME DATE for the same
issuer are very often the same combined release, counted here as two
separate co-signals.

This is a bug-fix correction, not a re-cut for a better answer (the
same standard applied to the 2026-07-03 RNA extraction fix and the SC
13D naming fix): the ORIGINAL result stands as recorded above and is
NOT retracted. A SECOND, one-time, corrected pass is committed HERE,
before recomputing, with the identical validation/refutation
thresholds:

- **Fix**: if an earnings-catalog filing and a guidance-catalog filing
  share the same `(cik, filed date)`, they collapse to ONE co-signal
  (a same-day combined release), not two. 13D stays independent (a
  different filer, a different document, months apart in practice).
- **Same three groups, same metric, same thresholds** as above,
  applied to the corrected co-signal counts.
- One shot on the correction; no further re-cuts regardless of result.
