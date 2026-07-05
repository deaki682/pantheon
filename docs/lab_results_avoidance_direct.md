# Lab results — `avoidance_direct` (mechanical arm) — SUPPORTED (weak), 2026-07-05

**Verdict: SUPPORTED at the precondition.** Excluding mechanically-distressed
small-caps improves the basket and beats random exclusion — the pre-committed bar.
The whole "LLM = avoidance" thesis is NOT refuted; the LLM-vs-mechanical forward
A/B is justified. But the effect is small and decays out-of-sample — a modest
overlay, not an engine.

Universe: SMALL/MICRO PIT (achilles panel; LARGE pending). Distress composite from
SF1 (low ROA + low CFOA + low GPOA + high dilution, PIT by datekey). Monthly
rebalance; 'avoidance alpha' = (universe minus top-k% distress) EW minus full EW.
Arm B (distress) vs Arm C (random). In-sample ≤2015 / holdout 2016+.

| k | IS distress (t) | IS random | HO distress (t) | HO random |
|---|---|---|---|---|
| 5% | +0.086%/mo (**3.77**) | +0.004% | +0.026% (0.92) | −0.013% |
| 10% | +0.163%/mo (**4.16**) | +0.001% | +0.060% (1.21) | +0.009% |
| 20% | +0.271%/mo (**4.30**) | +0.002% | +0.107% (1.47) | −0.014% |

**Reading.** In-sample: distress-exclusion avoidance-alpha is strongly positive
(t≈4), monotonic in k, and cleanly beats random (~0). Holdout: positive and beats
random at EVERY k (non-isolated), but NOT independently significant (t≈1–1.5), and
the magnitude decayed (~1%/yr). So: the signal is real, the direction holds
out-of-sample, but it's a small, decaying overlay — consistent with avoidance being
a genuine-but-modest, capability-frontier (decaying) edge. It clears the
pre-committed precondition (Arm B > Arm C, both windows, non-isolated), so
`avoidance_overlay` (#14) is NOT dead and the forward LLM-vs-mechanical A/B proceeds.
Caveat: mechanical-only; the LLM increment (the real question) is untested. Runner:
`run_avoidance_direct.py`.
