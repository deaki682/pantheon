# Results — `gauntlet_v6_combinations` — SUPPORTED (netiss∩gross-prof)

- **Prereg:** [docs/lab_prereg_gauntlet_v6_combinations.md](lab_prereg_gauntlet_v6_combinations.md)
  (committed before data; schema probed, zero returns peeked pre-commit)
- **Run:** 2026-07-04/05, `run_gauntlet_v6_pull.py` + `run_gauntlet_v6_screen.py`.
  SF1 ARQ + DAILY P/S, frozen v1 PIT universes, SEP delisted-inclusive TR bars.
- **Grid:** 8 signals × {LARGE,SMALL} × {N25,N50} = 32 cells. variance_of_sr 0.01105.
- **Registry:** `gauntlet_v6_combinations` → **supported → forward_testing**;
  `hypotheses_ever` 153 → 173 (20 new cells).

## The one variable tested

v4 refuted the naive **mean-rank** composite (dilutes the tails). v6 changed
ONE thing — the aggregation operator → **intersection** `max(rank_A, rank_B)`
minimized ("hold only names strong on BOTH legs") — on the same legs.

## Verdict

- **`netiss_x_grossprof` (net-issuance ∩ gross-profitability — Plutus's OWN two
  factors, intersected) — SUPPORTED.** Cleared both gates non-isolated (N25L,
  N50L, N50S). Holdout N50-LARGE **+15.10%, Sharpe 0.90, maxDD 32%** — beats
  BOTH standalone legs (net-issuance +14.40%/mDD40, gross-prof +11.77%/mDD30)
  AND carries a drawdown between them, closer to the better. This is the
  tail-intersection beating the naive blend v4 killed. **The Plutus-upgrade
  finding: intersect his two factors instead of rank-blending them.**
- **`capreturn_at_price` (net-issuance ∩ P/S) — SUPPORTED but NOT better than
  its leg.** All 4 cells cleared both gates, but holdout N50-LARGE +12.97% <
  net-issuance-low +14.40% and drawdown 42% > 40% — the value leg ADDED nothing
  over pure net-issuance. Logged "no better than the legs."
- **`quality_at_price` (gross-prof ∩ P/S) — WEAK / thesis not confirmed.** The
  flagship "drawdown-cure" candidate cleared only a borderline-isolated pair
  (N25S, N50L), barely beat benchmark (+11.43% vs 11.4%), and ran HIGHER
  drawdowns (34–67%) than the standalone factors, not lower. **The
  drawdown-cure thesis for value combinations is REFUTED** — intersecting with
  the value leg added risk, not safety.
- **`delta_ato` (asset-turnover trend, Soliman 2008) — passed the gates (N25L,
  N50L, non-isolated) and beats gross-prof in the holdout (+13.47% vs +11.77%),
  but is HELD pending the pre-committed orthogonalization kill** (must retain
  alpha after controlling for the level factor + accruals + fund-momentum — the
  fund_mom lesson). Not recorded as supported until that clears.
- **`delta_gpoa` (profitability growth) — REFUTED.** Failed the in-sample gate
  (all 4 cells below benchmark). The "improving-fundamentals" pond has now
  killed THREE signals (delta_rnd, fund_mom, delta_gpoa) — the boundary is firm:
  fundamental *change* signals do not survive here; only *levels* do.

## The combination gate (the whole thesis)

Only ONE combination passed "beat the better leg OR cut drawdown vs both legs":
**netiss_x_grossprof.** The two value combinations failed it (added risk or
didn't beat the leg). So the tail-preserving-composite question is answered
**narrowly YES** — but ONLY for intersecting two CORRELATED quality/
capital-return factors, NOT for adding a value leg. Compositing is not a
general drawdown cure; it helped exactly one specific pairing.

## Caveats

1. **Holdout-driven.** netiss_x_grossprof UNDERperformed both legs in-sample
   (+6.86% vs +7.29%/+8.15%) and only wins in the holdout — same regime-favored
   pattern as every survivor. A candidate, not a proven dominant.
2. **High drawdowns.** Even the winner ran 32–60% maxDD — these are
   concentrated equity baskets; the convexity work (docs/return_convexity_pivot)
   is the honest frame for what these are worth for returns.
3. Famous factors, McLean-Pontiff decay, counter 173 — forward test on fresh
   data is the arbiter, not this backtest.

## What this buys

- **A Plutus second-factor construction upgrade CANDIDATE:** replace the deluxe
  rank-blend of net-issuance + gross-prof with the tail-intersection. Decision
  waits for the forward test; live spec unchanged.
- Value-composite and fundamental-change families CLOSED (quality/cap-return at
  a price add nothing; change-signals refuted). The fundamentals frontier is now
  definitively spanned by the level factors: net-issuance, gross-profitability,
  cash-based profitability, and their tail-intersection.
