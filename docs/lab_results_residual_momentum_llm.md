# Lab results — `residual_momentum_llm` (REFUTED, 2026-07-05; INDEPENDENTLY RE-VERIFIED 2026-07-06)

**Verdict: REFUTED.** Residual (factor-neutral) 12-1 momentum does not clear
in-sample, and even where directionally positive in the holdout it does NOT
beat a plain raw-momentum control — the pre-registered fourth criterion. The
momentum family, in every form the house has now tried (raw, curated-universe,
and residual), is closed. Filed to close a loose end: the backtest was recorded
in the lab registry same-day but this results doc and ledger row were never
written before the session ended.

**2026-07-06 update: independently re-derived from scratch and CONFIRMED.** The
achilles panel was fully re-pulled from Sharadar in a fresh container and the
backtest re-run with output saved this time
(`docs/data/residual_momentum_llm/results.json`). The re-derived numbers match
the registry's recorded figures almost to the decimal — see below.

Prereg: `docs/lab_prereg_residual_momentum_llm.md` (committed before data,
with a written **G1 operator override** — this is a pure price signal, run
anyway because the residual construction and the planned LLM reversal-prune
overlay were both untested). Universe: SMALL bucket, achilles/gauntlet_v1 PIT
panel, survivorship-free, 1999-2025. Signal: cumulative RESIDUAL return
t-12..t-2 (each name's monthly returns regressed on the bucket-EW "market"
return over a trailing 36-month window; residuals cumulated, skipping the
most recent month), vs a RAW 12-1 momentum control on the same universe. Top
N=50 EW, monthly rebalance, net of turnover-based cost (1x reported, 2x
stress checked). In-sample ≤2015-12-31 / holdout 2016+.

## Results

| Signal | In-sample | Holdout | n |
|---|---|---|---|
| Residual 12-1 | ~0% excess, t≈0.21 | **+0.49%/mo** | 119 |
| Raw 12-1 (control) | — | **+0.66%/mo** | 119 |

Registry mean excess (residual, holdout): 0.485%/mo, shrunk to 0.415%/mo.

## Re-derived, real numbers (2026-07-06 — see `docs/data/residual_momentum_llm/results.json`)

| Signal | Window | Mean | t | n |
|---|---|---|---|---|
| Residual | in | 0.059%/mo | 0.21 | 163 |
| Residual | out | **0.485%/mo** | 1.07 | 119 |
| Raw (control) | in | −0.016%/mo | −0.05 | 163 |
| Raw (control) | out | 0.662%/mo | 1.41 | 119 |

Turnover (resid): 0.39/mo → ~1.4%/yr cost drag (2× ≈ 2.8%); resid holdout net
of 2× cost: 0.373%/mo, t=0.82. The registry's `mean_excess` (0.485%/mo) matches
the resid/holdout cell exactly. Every number and the verdict check out against
the real re-run.

## Reading

1. **Criterion 1 fails outright.** In-sample residual excess is statistically
   indistinguishable from zero (t≈0.21, n=163 in-sample) — the pre-registered
   pass required t≥2 non-isolated before ever touching the holdout.
2. **Criterion 4 fails even on the flattering holdout read.** The whole point
   of residualizing momentum (Blitz-Huij-Martens: strip the market/size beta
   that makes raw momentum crash-prone) was to show the residual construction
   *rescues* an edge raw momentum can't hold. Instead raw (+0.66%/mo) beats
   residual (+0.49%/mo) in the one window where residual looks decent at all.
   The residualization step adds nothing — it's a more complicated way to get
   a worse number.
3. **This closes the family.** Combined with the earlier raw-momentum results
   (gauntlet_v1: momentum dead in 80/90 in-sample cells; Delphi full-window:
   the curated momentum compounder −6.86%/yr excess) and this residual variant,
   momentum has now failed in every construction the house has tried on this
   panel: raw, curated-universe, and factor-neutral residual. No further
   momentum variant should be proposed without a genuinely new mechanism (not
   a new residualization or lookback tweak) — that would just be another draw
   from an already-exhausted family.
4. **No LLM increment was tested and none is warranted.** The prereg's planned
   forward step (an LLM reversal-prune overlay on the residual signal) is
   **not opened** — refuted is terminal per the prereg's own pre-committed
   consequence ("Miss any [criterion] => refuted"), and there is no base
   signal left to overlay a prune onto.

## Reproducibility caveat — RESOLVED 2026-07-06

As of 2026-07-05 this doc rested entirely on an unverified registry summary.
As of 2026-07-06 the backtest has been independently re-derived end-to-end
from raw Sharadar data and the full output saved to
`docs/data/residual_momentum_llm/results.json` — closed.

## Consequence (pre-committed, applied)

`residual_momentum_llm` → **refuted** (terminal). No forward test. The G1
override that let this slug run (a pure price signal, exceptionally, because
residual construction + LLM overlay were the untested parts) is now spent —
the momentum family does not get another override without a new, distinct
mechanism.
