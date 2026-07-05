# Lab results — `residual_momentum_llm` (REFUTED, 2026-07-05)

**Verdict: REFUTED.** Factor-neutral (residual) 12-1 momentum does not rescue
momentum where raw died. Base signal on the SMALL bucket (achilles panel; LARGE
pending a bar pull), long top-50 EW, monthly, excess vs SMALL-bucket EW, net cost.

| Arm | in-sample | holdout | holdout @2x cost |
|-----|-----------|---------|------------------|
| **residual** | +0.06%/mo (t 0.21) | +0.49%/mo (t 1.07) | +0.37%/mo (t 0.82) |
| raw 12-1 (control) | −0.02%/mo (t −0.05) | +0.66%/mo (t 1.41) | — |

Fails **criterion 1** (in-sample excess ~0, t 0.21 — nowhere near the t≥2 bar) and
**criterion 4** (residual does NOT beat the raw-momentum control — raw is *larger*
in the holdout, +0.66 vs +0.49). Neither arm is significant in either window;
turnover 0.39/mo (cost drag ~1.4%/yr, 2.8% at 2×). The residual construction added
nothing. **The momentum family is now closed for this book in every form tested** —
raw (gauntlet_v1), curated-universe (Delphi), and residual. No forward test.
`hypotheses_ever` unchanged 196 (preregistered slug). Runner: `run_residual_momentum.py`.
