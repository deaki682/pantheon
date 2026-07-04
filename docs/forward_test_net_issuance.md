# Forward test — net-issuance-low N50 LARGE (gauntlet_v2)

The house's first supported strategy on its clean out-of-sample test.
Because the 2000–2025 historical panel is SPENT (v2 used its holdout),
fresh post-2026 quarters are the only uncontaminated arbiter.

- **Tracker:** `cache/lab_forward_net_issuance.json` (persisted, lab-owned)
- **Runner:** `run_forward_net_issuance.py` — `roll` (grade matured
  quarter + open next), `status`, self-contained (pulls fresh Sharadar)
- **Registry:** grades flow to `gauntlet_v2_fundamentals.forward` via
  `record_forward_grade`; ≥20 graded quarters with positive shrunk mean
  excess to `conclude_forward`

## Frozen convention (matches the validated backtest exactly)

Signal at quarter-end (SF1 datekey ≤ D), universe = top-500 by DAILY
marketcap, long the 50 lowest trailing-4-quarter weighted-shares change,
equal weight, **entry at the next trading day's close**, hold to next
quarter-end, grade the basket's total-return excess vs SPY. One graded
observation per quarter — ~5 years to n=20. That slowness IS the honest
cost of validating a quarterly factor; nothing goes live before it.

## Status at seeding (2026-07-04)

First observation open: **2026Q3**, signal 2026-06-30, entry 2026-07-01
(50 names incl. GM −12.8%, AIG, VOD, HCA, KR, the big-bank buybacks),
grade due 2026-09-30. 0/20 graded.

## Do NOT change the tracked version

The forward test tracks the EXACT version that earned "supported."
Cap-aware / composite / LLM-overlay improvements are SEPARATE hypotheses
with their own forward tests — changing this one would forfeit the
gauntlet evidence that justified forward-testing it at all.
