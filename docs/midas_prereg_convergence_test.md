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
