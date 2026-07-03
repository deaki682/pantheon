# Pre-registration: spinoff ocean extension, 2022–2024 vintages

Committed 2026-07-03, before any data exists. One-shot terms as always.

## Question

Everything Nemesis-related was validated on a single warm vintage
(2025–26 buy-all: +41.2% vs SPY +30.2%, alpha carried by two names). The
2022–2023 spinoff class distributed into a bear market with credit
stress. Same frozen trigger, hostile weather: **is the post-dump window
a real structural effect, or a bull-market artifact?**

This is REFERENCE-CLASS MEASUREMENT, not a gate. Pre-committed
interpretation: if bear-vintage per-event mean excess is negative, the
trigger is regime-dependent and that goes into the runbook as a risk
disclosure — but NO live rule changes either way. The freeze holds.

## Population (FROZEN)

- 10-12B / 10-12B/A registrants from EDGAR **daily form indexes**
  2021-06-01 .. 2024-12-31 (complete population; the FTS pagination
  failure mode is bypassed entirely).
- Spinoff triage identical to the 2026-07-03 cross-check procedure:
  fetch each registrant's 10-12B, keep names whose filing carries
  spin-off/distribution-to-holders language; log every exclusion with
  its reason.
- Tickers resolved by CIK against the official registry, then per-CIK
  submissions verification (the Enviri parent-contamination check).

## Known limitation, disclosed first (FROZEN handling)

Delisted/acquired/dead spincos may have no bars at the broker. Every
distributed spinoff that is unpriceable is REPORTED BY NAME in a
"disappeared" bucket with a best-effort manual disposition (acquired at
premium vs delisted worthless — these are opposite outcomes and cannot
be auto-scored). The portfolio simulation is reported BOTH ways:
excluding disappeared names, and worst-case scoring them −100% at their
last priceable date. If the two numbers straddle zero, the vintage is
declared unmeasurable rather than spun.

## Simulation (FROZEN — identical to the 2026-07-03 ocean sim)

- Slicing: first bar with volume ≥ max(10,000, 2% of series max).
- Trigger: nemesis/window.py exactly as frozen (10–90 days, vol ≤ 0.5,
  low behind 5 sessions). First fire = entry at that close.
- Exits: 150 calendar days or −40% on closes, whichever first. 5bps/side.
- Portfolio: $2,000 start, 5 slots, equity/5 at entry, one shot per name,
  chronological. Benchmark: SPY over the identical span. Per-event
  excess also reported per vintage-year.

## Outputs

1. Per-vintage (2022/2023/2024) event table and portfolio path.
2. The regime answer: per-event mean excess by vintage, with the warm
   2025–26 vintage restated alongside for contrast.
3. Combined 4.5-year reference class (~40–60 events expected) — the
   base-rate document November's live grades get compared against.
