# Results: judge-consistency probe (the boundary-noise test)

Run 2026-07-03 per the frozen terms of
`docs/nemesis_prereg_judge_consistency.md`. 15 judge runs (FDXF, HONA,
RNA × 5), each judging from the IDENTICAL stored extraction sets that
fed the recorded production calls — extraction variance excluded by
construction; only judgment variance measured. Judges un-anchored (no
recorded scores, no sight of each other), production scoring law, full
reasoning effort, no refuters.

## Results

Veto line: condemned = verdict "avoid" OR garbage_barge_risk > 0.60.

| Specimen | Recorded call | Probe garbage scores | Probe verdicts | Veto flips |
|---|---|---|---|---|
| FDXF | watch / 0.60 → **buyable** | 0.60, 0.60, 0.65, 0.65, 0.70 | 3× watch, 2× avoid | **4/5 (80%)** |
| HONA | watch / 0.65 → condemned | 0.55, 0.65, 0.65, 0.65, 0.70 | 5× watch | 1/5 (20%) |
| RNA | watch / 0.45 → buyable | 0.25, 0.30, 0.30, 0.32, 0.40 | 5× watch | **0/5 (0%)** |

## Reading

- **RNA is what stability looks like:** five independent judges, same
  side, garbage clustered 0.25–0.40, far from the line. Away from the
  boundary, the single-judge standard is measured-reliable.
- **FDXF is what dice look like:** the recorded 0.60 — exactly at the
  pass line — was the MINORITY read. Four of five judges on identical
  facts would have condemned it (two by verdict, three by score). The
  production judgment that keeps FDXF buyable is a coin-flip artifact,
  not a discrimination.
- **HONA sits between:** condemnation held 4/5; the score hovers at the
  line but the median (0.65) matches the recorded call.
- Score variance overall is modest (range ≤ 0.15 everywhere); the
  problem is not wild judges, it is that two live names sit ON the
  threshold, where modest variance decides real money.

## Consequence (pre-committed, now in force)

The frozen trigger — any specimen flipping ≥ 1/5 — fired (FDXF 4/5,
HONA 1/5). Per the prereg, the runbook now REQUIRES a 3-judge median
for any boundary judgment: garbage within ±0.05 of 0.60, or "avoid"
with conviction < 0.7. Two additional un-anchored judges over the same
extractions; per-field median; then refuters. Implemented in
`.claude/commands/nemesis.md` deep-read stage 5.

Immediate application: FDXF's mandatory August 10-K re-read runs under
the panel rule. Note the probe's own medians — FDXF 0.65/watch — land
FDXF on the CONDEMNED side; the August re-read (fresh 10-K facts +
panel) is where that gets settled for live purposes. FDXF sits in the
watch queue, not the buy list, so no live order rests on the disputed
call today.

Raw judgments: session archive `judge_probe/probe_summary.json` and the
workflow journal (15/15 runs completed, 0 errors).
