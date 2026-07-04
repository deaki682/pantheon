# Pre-registration: PEAD hold-horizon sensitivity (5 vs 10 vs 20 trading days)

Committed 2026-07-04, BEFORE any bar beyond the frozen 5-day window is
fetched. Backlog item #8 (docs/RESEARCH_BACKLOG.md).

## Question

The reaction-gate replay (docs/achilles_prereg_reaction_gate.md,
docs/achilles_replay_results_2026-07.md) found the drift **inconclusive
at a 5-trading-day hold**: rewarded-group excess −0.60% (t −0.96),
sold-group −1.60% (t −2.27, real), spread t 1.07 — real avoidance
signal, no real BUY signal, at 5 days. Achilles' live rule holds 5
days. Does extending the hold to 10 or 20 trading days reveal drift the
5-day window is too short to catch — as PEAD theory (drift accrues over
20-60 days, strongest in neglected names) would predict — and is that
extension concentrated in the small-cap/neglected subset?

## Population (REUSED, not resampled)

The exact 293 already-**graded** events from the frozen 2026-07-03
replay (docs/data_achilles_gate_results_2026-07.json) — the random
600-event sample of Item-2.02 8-Ks (2025-01-02..2026-05-31), restricted
to the 293 that were both non-lukewarm (reaction ≥+3% or ≤−3%) and
priceable by the broker. **No new sampling, no new EDGAR pull.** Only
the price window is extended — this is the same discipline as the
oracle_prereg_cluster_replay_sharadar correction (same events, more
horizon), not a fresh cut of the population.

## Method (extends the frozen original exactly)

- **Entry**: unchanged — next session's OPEN after the reaction day
  (already computed, `entry` field in the data file). Verified by
  hand-reproducing RICK and CMTL's frozen `ret5`/`excess` from raw
  broker bars before writing this prereg (open-to-close-at-Nth-session
  convention confirmed byte-for-byte).
- **New horizons**: close on the 10th and 20th trading session counting
  entry date itself as session 1 (matches the frozen 5-day convention:
  exit was the 5th such session).
- **Benchmark**: IWM, identical entry/exit dates, same convention.
- **Excess** = stock simple return − IWM simple return, entry OPEN to
  exit CLOSE.
- **Not-elapsed**: events whose entry is too recent for the horizon to
  exist yet (max entry in the sample is 2026-06-01; +20 trading days
  lands right around today, 2026-07-04) are reported as not-elapsed,
  not dropped or forced.
- **Neglect proxy (disclosed limitation, same as the original study's
  smallmid_slices)**: CURRENT (2026-07-04) market cap via
  `get_equity_fundamentals`, not as-of-event — the broker has no
  historical market-cap endpoint. Terciles: small (<$2B), mid
  ($2-10B), large (>$10B). This is a coverage PROXY, not analyst-count
  data (unavailable to the house); disclosed as approximation, exactly
  like the original replay's exploratory small-cap sub-slice.

## What would count as validation / refutation

- **Drift emerges**: at 10 or 20 trading days, rewarded-group mean
  excess > 0 with t ≥ 2, OR (rewarded − sold) spread > 0 with t ≥ 2 —
  either constitutes evidence the 5-day hold is cutting the trade short.
- **No drift at any horizon tested**: neither 10 nor 20 trading days
  reaches t ≥ 1.5 on the rewarded-group excess or the spread. Achilles
  keeps her 5-day hold; extending it would only add unrewarded holding-
  period risk.
- **Neglected-name test (exploratory, reported regardless of
  direction, not a standalone validation gate — same status as the
  original study's small-cap cut)**: does the small-cap tercile's
  10/20-day spread exceed the all-cap spread?
- Both horizons (10 and 20 trading days) are reported together in one
  shot — no sequential peeking, no horizon dropped if inconvenient.

## What this is NOT

- Not a live-rule change on its own — if a horizon validates, the hold
  parameter change goes through its own operator decision, not an
  automatic rewrite.
- Not a re-grade of the frozen 5-day numbers, which stand exactly as
  published.
- The market-cap proxy is CURRENT-cap, so any small-cap-tercile finding
  describes "names that are small today," not necessarily "names that
  were small/neglected at the time of the 2025-early-2026 event" — a
  name could have grown or shrunk since. Flagged, not correctable with
  data currently on hand.
