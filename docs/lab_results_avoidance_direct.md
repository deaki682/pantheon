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

## Robustness pass (2026-07-05) — the support is weaker than it first read

Decomposing the distress composite into its 4 components (each run ALONE as the
exclusion signal, k=10%) and breaking the holdout out by year:

| Signal | in-sample (t) | holdout (t) |
|--------|---------------|-------------|
| ROA-only | +0.10% (2.32) | +0.02% (0.49) |
| CFOA-only | +0.11% (3.34) | +0.04% (0.77) |
| **GPOA-only (quality)** | +0.11% (4.65) | **+0.05% (1.49)** |
| **Dilution-only (= net-issuance)** | +0.09% (4.19) | **+0.06% (1.89)** |
| COMPOSITE | +0.16% (4.16) | +0.06% (1.21) |

**Two honest downgrades:**
1. **It's largely Plutus's own factors.** GPOA-only holdout (+0.05%) ~= the composite
   (+0.06%), and dilution-only (= net-issuance, Plutus's other factor) is the
   STRONGEST single holdout component. The mechanical "avoidance" alpha is dominated
   by gross-profitability + net-issuance — the two factors Plutus already trades. It
   is NOT a novel avoidance edge; it re-derives known quality/capital-return factors.
2. **The holdout is a 2021 phenomenon.** Composite holdout by year: 2021 +0.55%/mo
   (t 3.41), but 2020 −0.22, 2025 −0.30, 2017/2019 negative. Strip 2021 (the
   post-COVID junk-rally reversal) and the out-of-sample support mostly evaporates.

**Consequence.** The mechanical precondition technically cleared its pre-committed
bar (beat random, both windows), so the slug stays `forward_testing` — but the
"SUPPORTED" is qualified: the mechanical signal is factor-redundant and
regime-concentrated. **The forward LLM arm's bar is now sharper: it must add
avoidance BEYOND gross-profitability + net-issuance, not merely beat random.** If
the LLM read only re-derives Plutus's factors, it adds nothing. Runner:
`run_avoidance_decomp.py`.
