# Results: LLM decision-consistency sweep (Oracle + Midas)

Run 2026-07-04 per the frozen terms of
`docs/pantheon_prereg_decision_consistency.md`. Both re-scoring sets
judged FRESH from blinded stored narratives (no recorded scores
shown), un-anchored across runs. Raw data:
`docs/data_decision_consistency_2026-07.json`.

## Disclosed deviation

The prereg assumed an 8-name Oracle cohort; the actual live cohort
resolved to **5 in-pool names** (PSN, HDSN, VITL, J, CXT — the others
are held positions whose current dossiers were not in the pool). The
top-8 flip test was applied as **top-5** against this real number.
Stated before results, not adjusted after seeing them.

## Oracle: conviction re-scored 5x per specimen (9 specimens: 5 held + 4 top non-held)

| Symbol | Recorded conviction | Mean of 5 blind re-scores | sd | range | Held? |
|---|---|---|---|---|---|
| CXT | 0.19 | 0.554 | 0.073 | 0.190 | ✓ |
| HDSN | 0.23 | 0.484 | 0.038 | 0.090 | ✓ |
| PSN | 0.26 | 0.450 | 0.017 | 0.040 | ✓ |
| J | 0.27 | 0.418 | 0.060 | 0.150 | ✓ |
| INFU | 0.42 | 0.388 | 0.052 | 0.120 | |
| VITL | 0.42 | 0.434 | 0.022 | 0.060 | ✓ |
| INR | 0.47 | 0.324 | 0.037 | 0.100 | |
| ARTV | 0.47 | 0.282 | 0.050 | 0.130 | |
| KRMD | 0.52 | 0.318 | 0.031 | 0.070 | |

**Selection-flip rate: 2/5 draws (40%) put a different top-5 than the
held set** — INFU displaced J in draws 3 and 4. **Trigger MET.**

Note beyond the frozen metric: the blind re-scores as a GROUP
systematically re-rank the recorded order — the four held names with
the LOWEST recorded conviction (CXT 0.19, HDSN 0.23, PSN 0.26, J 0.27)
re-score HIGHEST blind (0.55, 0.48, 0.45, 0.42), while non-held names
recorded HIGHER (INR 0.47, ARTV 0.47, KRMD 0.52) re-score LOWER
(0.32, 0.28, 0.32). This is compatible with a real explanation (the
recorded scores may reflect prior-scenario or interim price
information the blind narrative-only re-read doesn't have) but is
also compatible with plain conviction noise. The frozen metric
(selection-flip) is the one that governs; the compression pattern is
reported for awareness, not adjudicated here.

## Midas: 10 finalists, 5 independent full re-scorings

| Run | Pick | Top-3 by expected_value |
|---|---|---|
| Recorded (live) | **DAKT** (EV 0.070) | DAKT 0.070, APOG 0.054, MLKN 0.043 |
| 1 | APOG | APOG 0.040, ZBIO 0.036, DAKT 0.030 |
| 2 | APOG | APOG 0.036, ZBIO 0.035, DAKT 0.028 |
| 3 | APOG | APOG 0.042, DAKT 0.040, ZBIO 0.039 |
| 4 | **DAKT** | DAKT 0.040, APOG 0.036, ZBIO 0.035 |
| 5 | APOG | APOG 0.046, ZBIO 0.041, DAKT 0.037 |

**Pick-flip rate: 4/5 (80%).** APOG — not DAKT — wins 4 of 5
independent blind re-scorings. DAKT wins only the run that matches the
live pick. **Trigger MET, and by a wide margin against the 40% bar.**

## Correction (found before any rule was wired — read this before the table above)

**The Midas trigger, as originally written up, was WRONG about
consequence.** `midas/scanner.py` states explicitly, in the
`WeeklyCatalystDossier` docstring and in `pick_winner()`'s own comment:
*"pop_probability/expected_magnitude/expected_value are informational
only — they do NOT feed into pick_winner. The pick is purely
mechanical: highest timing-weighted convergence score
(`d.score`) among non-disqualified names."* My prereg asked the
re-scorers to reproduce `expected_value` and treated its argmax as
"the pick" — but that is not the field that actually selects Monday's
stock. **The 80% flip rate is real and reported below, but it does
NOT threaten the live all-in decision**, because Midas was already
architected so this exact judgment cannot drive that decision. Caught
by checking the code before wiring a "mandatory panel" rule into
`midas.md` — which would have been theater protecting a field nobody
uses. Nothing was implemented in Midas's runbook as a result of this
number.

**What Midas's LLM judgment actually gates is the disqualification
veto** (can kill a finalist for an active thesis-killer; cannot
promote one) — and this study did NOT test veto consistency; the
schema only asked for `expected_value`, not a per-name disqualify
decision. That is the real follow-up, not yet run.

Oracle is different and the finding there stands as designed:
`oracle/positioning.py: size_book` sorts candidates by `conviction`
(itself a mechanical transform of the LLM's scenario probabilities and
quality ratings) and keeps the top K for the cohort — conviction IS
the selection mechanism, not an informational side-field. Her result
is genuinely load-bearing.

## Verdicts (frozen rule applied where it actually governs)

- **Oracle: TRIGGERED (40% ≥ 40%).** Conviction is load-bearing for
  cohort selection. A 3-draw median conviction is now MANDATORY in
  `/oracle` sizing before any cohort is cut. Implemented in
  `.claude/commands/oracle.md`.
- **Midas: measured, but the trigger does not apply to a load-bearing
  field.** `expected_value` is 80% unstable, which means it should NOT
  be read by a human as a confidence signal — but it does not touch
  the mechanical pick. No runbook change from this result. The
  disqualification-veto consistency test is the honest open item.

## Reading

Every prior study this weekend measured whether a MECHANICAL signal
predicts returns. This measured whether the JUDGMENT LAYER is even
internally repeatable — and for Oracle, the answer is: not quite (40%
selection-flip on the actual cohort-determining score). For Midas, the
unstable field turned out to be decorative, which is a genuine point
in the architecture's favor: whoever designed `pick_winner()` to be
"purely mechanical" already defended against exactly the failure mode
this study went looking for. The near-miss here is the finding: I
almost reported a false alarm on live all-in capital because I tested
the field that LOOKS like the decision instead of verifying which
field IS the decision. Lesson applied — nothing gets wired into a
runbook without reading the code path first, not just the schema.

## What this does NOT test

Accuracy — whether APOG or DAKT is the better bet, whether Oracle's
conviction predicts returns. That is forward-only, same wall every
other study this weekend hit. This measures process repeatability
only, which is a precondition for accuracy to even be measurable.

## Addendum results: Midas disqualify-veto consistency (2026-07-04)

Run per the pre-committed addendum (blind file with recorded
`disqualified`/`disqualify_reason` stripped — the leak in the earlier
blind file disclosed and fixed). 10 finalists × 5 un-anchored
decisions, production disaster-only framing.

**Result: 0 flips in 50 decisions.** Every recorded veto (HELP, WEN,
AVAV, AOUT) was independently re-derived 5/5 times with the same class
of reason (e.g., HELP: catalyst fully priced after a +42% 3-day run —
all five judges cited the same mechanism); every recorded pass held
5/5. Frozen trigger (≥2/5 on any finalist) NOT fired: the single-pass
veto stands, documented measured-stable.

**The design principle this completes:** across three consistency
probes, the pattern is now clean —

| Judgment type | Measured stability |
|---|---|
| Binary gate w/ enumerated criteria (Midas veto) | 0/50 flips |
| Verdict far from a threshold (RNA read) | 0/5 flips |
| Continuous score AT a threshold (FDXF garbage 0.60, Oracle cut-line conviction) | 40–80% flips |

LLM judgment is reliable when asked "does an enumerated disaster
condition hold?" and dice when asked "is this 0.60 or 0.65?" near a
line that matters. Future god designs should push LLM decisions toward
enumerated binary gates (the Nemesis thesis-break list, the Midas
veto) and away from load-bearing continuous scores — where continuous
scores are unavoidable, the 3-draw median rules now in force are the
mitigation.
