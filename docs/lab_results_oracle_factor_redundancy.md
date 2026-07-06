# Diagnostic — Oracle dossier factor-redundancy check (2026-07-05)

**Question (the decision it buys):** is Oracle's LLM dossier judgment orthogonal to
value + quality + net-issuance factors, or does it re-derive them — the way
`avoidance_direct` collapsed into Plutus's own GPOA + net-issuance? If redundant →
fold Oracle into Plutus. If orthogonal → he is a distinct selection input worth the
forward dossier-vs-screen A/B. **Diagnostic only, paper.**

## Method

95-dossier pool (`cache/oracle_dossiers.json`); 93 with SF1 fundamentals. Standardized
(rank-percentile) the LLM outputs (`conviction`, `derived.asymmetry`, `ratings.quality`)
and six factors computed from SF1 + dossier price: GPOA (gp/assets), ROA (netinc/assets),
CFOA (ncfo/assets), earnings-yield (eps/price), sales-yield (revenue/mktcap), net-issuance
(shareswa YoY). Univariate rank correlations + multiple-OLS R² (how much of the LLM score
the factors span). Chance-level R² for 6 regressors at n=93 ≈ 0.065 (the noise floor).

## Result — Oracle PASSES the test avoidance FAILED

| Oracle score | R² spanned by 6 factors | Read |
|---|---|---|
| conviction | **0.096** | orthogonal (≈ chance floor 0.065) |
| asymmetry | **0.091** | orthogonal |
| conviction + drawdown | 0.111 | orthogonal |

The known factors explain essentially nothing beyond noise — Oracle's headline judgment
is **genuinely orthogonal** to value/quality/net-issuance. This is the OPPOSITE of
`avoidance_direct`, where GPOA-only ≈ the full composite and net-issuance was the
strongest holdout component (the signal WAS the factors).

**Credibility sub-finding (not noise):** the LLM `quality` sub-rating is strongly grounded
in real profitability — `llm_quality ~ ROA` r=**+0.48** (t 5.2), CFOA +0.29, GPOA +0.18.
So the component judgments track real fundamentals (not hallucinated), yet overall
`conviction` is driven by NON-factor considerations (catalyst / asymmetry / structural
mispricing / scenario work). Grounded inputs + a headline judgment not reducible to a
factor screen = the signature a real research edge should have. The one factor that mildly
tilts conviction is net-issuance (r +0.22, t 2.1) — weak.

## Verdict & decision

**Do NOT fold Oracle into Plutus.** He clears the redundancy test that avoidance failed;
his dossier selection is a distinct input, so he earns the forward dossier-vs-screen A/B
rather than a preemptive fold.

**Honest limit — orthogonal ≠ skilled.** This rules out ONE failure mode (redundancy). It
does NOT prove the judgment predicts — Oracle's conviction could be orthogonal AND noise.
Separating "distinct-and-skilled" from "distinct-and-noise" requires forward returns, which
is exactly what `oracle.ab` (dossier vs screen) measures. This diagnostic earns Oracle the
right to be TESTED, not a validation. First LLM-selection signal in the house that did NOT
collapse into factors — a materially better standing than avoidance, still short of proof.
