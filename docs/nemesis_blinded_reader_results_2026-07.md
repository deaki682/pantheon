# Results: blinded reader-accuracy study — BLOCKED at the gate

Run 2026-07-04 per `docs/nemesis_prereg_blinded_reader.md`. The frozen
de-anonymization gate fired. The study does NOT proceed to reads.

## The gate result: 48/48 identified

An incentivized red-team agent, shown only the masked documents, was
asked to name each company. Result:

- **45 of 48** named the EXACT ticker at 0.96–0.99 confidence.
- The other 3 named the correct COMPANY under a different ticker
  (TWNPQ→"Twin Hospitality/TWNP", VSXY→"Victoria's Secret/VSCO",
  DMNIF→"Grafiti Holding"). All correct identifications.
- **Effective identification: 48/48. Clean specimens: 0.**

Two independent failure modes, both fatal:

1. **Masking leakage.** Mechanical entity-masking missed names in
   exhibit filenames (`a2022biohavenresearchltdin.htm`), cross-line-break
   occurrences, EINs, and SEC file numbers. Fixable in principle.
2. **Un-blindable by description.** Even with perfect entity masking,
   "largest US nuclear operator" (CEG), "cancer early-detection blood
   test" (GRAIL), "GE's healthcare imaging business" (GEHC) identify
   themselves. Large, famous spinoffs cannot be anonymized — the
   business IS the fingerprint. NOT fixable by better masking.

## Verdict (frozen): INCONCLUSIVE — insufficient clean n

The prereg required ≥20 clean specimens and pre-committed to reporting
"insufficient-clean-n rather than borrowing." Clean n = 0. **The
retrospective blinded design is infeasible on this population**, and no
amount of deep reading would change that — running the 48 reads was
CANCELLED (they would measure recognition, not judgment, and fooling
ourselves is the one outcome the whole apparatus exists to prevent).

## What this actually establishes

1. **The gate worked.** It caught total contamination BEFORE 48
   expensive reads produced a falsely-reassuring "the reading predicts
   outcomes!" — which recognition alone would have manufactured. A
   safety mechanism firing is a success, not a waste.
2. **Reader accuracy cannot be measured retrospectively on known
   large-cap spinoffs.** The question "does the reading add selection
   value?" has exactly one uncontaminated venue: NAMES WHOSE OUTCOMES
   DO NOT YET EXIST.
3. Therefore **the live ghost three-leg race IS the reader-accuracy
   test** — buy-all vs veto-filtered vs own-picks, graded forward on
   spincos as they distribute. The ≥20-grade checkpoint is not one
   test among many; after tonight it is THE load-bearing measurement
   of whether the reading earns its tokens. Nothing retrospective can
   substitute.

## Salvage path (needs its own prereg; not run tonight)

A retrospective reader test could work on GENUINELY OBSCURE microcap
spinoffs (no analyst coverage, forgettable businesses) where neither
entity leakage nor description uniquely identifies — but that
population barely overlaps the ocean class, and most of its names are
unpriceable. Deferred as a possible future design, explicitly not a
re-cut of this one.
