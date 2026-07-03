# Pre-registration: judge-consistency probe (the boundary-noise test)

Committed 2026-07-03, before any probe run exists.

## Question

Live money now flows through gate-relevant scores rendered by a single
judge (plus two refuters): FDXF passed the veto at garbage 0.60, HONA
was condemned at 0.65, Q survived history's test at exactly 0.60. Is a
0.05 difference *discrimination* or *dice*? Nobody has measured the
run-to-run variance of the judgment layer that the veto rule executes.

## Design (FROZEN)

- Specimens: FDXF (recorded 0.60 — the pass-line case), HONA (0.65 —
  the fail-line case), RNA (0.45/watch — the verdict-flip case). All
  three have complete stored extraction sets on disk from the
  2026-07-03 deep reads; the probe re-judges from those IDENTICAL
  extractions — no re-reading, so extraction variance is excluded by
  construction and only judgment variance is measured.
- Per specimen: 5 independent judges, production judgment prompt,
  extended thinking, NO knowledge of the recorded scores or of each
  other (un-anchored). No refuters — the probe measures the raw judge,
  not the corrected pipeline.
- 15 judge runs total. Names are current positions/candidates with no
  outcomes yet, so training-data contamination is structurally absent.

## Metrics and decision rule (FROZEN)

- Per specimen: range and standard deviation of incentive_alignment and
  garbage_barge_risk; verdict distribution; and the **veto-flip rate** —
  the fraction of the 5 judges whose output lands on the OPPOSITE side
  of the live veto (condemned vs not) from the recorded production call.
- **If any specimen's veto-flip rate is ≥ 20% (≥1 of 5 judges):** a
  consensus rule becomes MANDATORY in the runbook — any future name
  whose garbage score lands within ±0.05 of the 0.6 line, or whose
  verdict is avoid with conviction < 0.7, gets a 3-judge median before
  the veto applies to live money.
- **If all specimens flip at 0/5:** the single-judge + two-refuter
  standard stands, documented as measured-stable.
- One shot; the consensus rule triggers on the pre-stated threshold,
  not on how the results feel.
