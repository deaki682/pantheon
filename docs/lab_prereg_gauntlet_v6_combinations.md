# Prereg — `gauntlet_v6_combinations` (PAPER, committed BEFORE data)

Sponsor: operator ("an entire bounty… tier A now"). Committed to git BEFORE any
return/multiple data is pulled. SF1/DAILY column schema was probed (fields
exist — not returns). House multiple-testing counter at commit: `hypotheses_ever`
153 → 173 (20 new cells; see accounting below).

## What this tests

The Tier-A runnable-now candidates from the 2026-07-04 alpha bounty
(docs/alpha_bounty_2026-07-04.md): **tail-preserving factor combinations** plus
two fundamental-change signals. The house already REFUTED the naive
**mean-rank** composite (`gauntlet_v4`: averaging ranks selects
moderate-at-everything names and discards the tails where alpha lives). v6
changes exactly ONE thing — the aggregation operator — on the same legs:

- **INTERSECTION operator (the fix):** `worst_rank = max(rank_A, rank_B)` with
  rank 0 = best; select the names with the SMALLEST worst-rank. A name is held
  only if it is strong on BOTH legs (deep-in-both / AND-gate). This is
  mathematically distinct from v4's `mean(rank_A, rank_B)` (an average is not a
  max), so no graveyard collision by construction.

### The 8 signals (ranks computed cross-sectionally within bucket per snapshot)

**NEW combinations (min-of-tails intersection):**
1. `quality_at_price` = intersect(gross-prof HIGH, P/S LOW) — Novy-Marx 2013
   "The Other Side of Value": cheap-AND-profitable; rescues v3's stranded P/S.
2. `capreturn_at_price` = intersect(net-issuance LOW, P/S LOW) — buyback
   conditioned on cheapness (avoids the expensive-buyback trap).
3. `netiss_x_grossprof` = intersect(net-issuance LOW, gross-prof HIGH) — the two
   Plutus factors integrated at the tails; adjudicates the deluxe blend.

**NEW fundamental-change signals (single-signal rank):**
4. `delta_gpoa` = Δ(gp/assets) trailing-4Q change — profitability GROWTH
   (Novy-Marx w15940; QMJ's one unowned leg).
5. `delta_ato` = Δ(revenue/NOA) trailing-4Q change — asset-turnover trend
   (Soliman 2008 DuPont). NOA = (assets − cashneq − investments) − (liabilities − debt).

**REFERENCE standalones (already-tested; re-run for apples-to-apples head-to-head,
NOT counted as new cells):**
6. `gross_prof` = gp/assets (owned, v2/v5). 7. `netiss_low` = trailing-4Q
   weighted-shares change (owned, v2). 8. `ps_low` = DAILY price-to-sales
   (inconclusive, v3).

## The grid

8 signals × {LARGE (top-500), SMALL (501-2000)} × {N25, N50} = **32 cells.**
DSR deflation at n_trials = 32 with the cross-sectional `variance_of_sr` over
the grid (NOT the 1.0 default — the v2 DSR=0 bug does not recur).

**Counter accounting (per-cell, matching gauntlet_v1):** 5 NEW signals
(quality_at_price, capreturn_at_price, netiss_x_grossprof, delta_gpoa,
delta_ato) × 4 = **20 new cells** → `hypotheses_ever` 153 → 173. The 3
reference standalones (12 cells) are control re-runs already counted, excluded
from the discovery count.

## Data, universe, execution (identical to gauntlet_v2/v5)

- Universe: frozen `gauntlet_v1_universes` PIT catalog (top-2000 by PIT
  marketcap, quarterly LARGE/SMALL buckets), `shared.populations`.
- Bars: Sharadar SEP, delisted-inclusive, total-return (closeadj).
- Fundamentals: SF1 ARQ keyed by `datekey` (filing-date PIT). Multiples: DAILY
  `ps` at each signal date (as-traded PIT). Signal uses only datekey ≤ D.
- Windows: in-sample 2000-2015, holdout 2016-2025 (touched ONCE).
- Execution: quarterly rebalance, entry at next trading day's close
  (signal_lag), EW top-N, `shared.gauntlet.simulate`, per-bucket CostModel
  (LARGE 5bps / SMALL 25bps), 2× slippage rerun.

## Success thresholds (pre-committed)

A NEW signal is **SUPPORTED** only if, in a NON-ISOLATED cell (a same-signal
neighbor at the adjacent N or bucket also survives):
1. In-sample DSR ≥ 0.95 (n_trials=32, cross-sectional variance_of_sr) AND CAGR
   > same-bucket EW benchmark.
2. Holdout beats same-bucket EW benchmark AND survives 2× slippage.

**Combination-specific gate (the whole thesis):** a combination is only a WIN
over its legs if it EITHER beats the better standalone leg's holdout CAGR, OR
materially reduces holdout max-drawdown vs BOTH legs while not losing return.
The bounty's claim is drawdown/regime-cure, so max-drawdown is a primary
recorded metric, not an afterthought — a combination that merely matches EW
but doesn't improve on its own legs is logged "no better than the legs."

**Change-signal gate (the fund_mom lesson):** `delta_gpoa` and `delta_ato` must
(a) survive as non-isolated, AND (b) beat the in-screen `gross_prof` reference
(else subsumed by the level). They live in the same "improving-fundamentals"
pond that refuted `fund_mom`; if their edge is absorbed by the level factor
they are refuted as relabels.

**Plutus decision:** if `netiss_x_grossprof` beats BOTH standalone legs AND the
current blend logic in both regimes, it is a candidate to replace Plutus's
rank-blend with tail-intersection — forward test decides, live spec unchanged.

**Stopping rule:** if no combination beats its legs on drawdown or return, the
tail-preserving-composite question is answered NO (as mean-rank already was),
and compositing is closed — the standalone factors stay the deployable form.

## Bias checklist (all 8, per shared.lab.BIAS_CHECKLIST)

1. **Survivorship:** SEP delisted-inclusive; SF1/DAILY cover dead filers;
   per-cell coverage reported; P/S coverage (financials lack it) disclosed.
2. **Look-ahead:** SF1 datekey-PIT, DAILY ps as-traded on D, signal ≤ D,
   execution lagged next-day. No restated-data leak (ARQ as-first-filed).
3. **Selection:** 32-cell grid fully enumerated here BEFORE data; the operator
   (max-of-ranks) is fixed in advance — no post-hoc swap to whatever wins.
4. **Multiple-testing:** 32 cells DSR-deflated at n_trials=32, cross-sectional
   variance_of_sr; house counter 153→173 (20 new). ~1-in-20 by chance → the
   two-regime holdout + forward test gate the verdict.
5. **Overfitting:** parameter-cliff / non-isolated-neighbor rule; holdout
   touched once; regime table mandatory; the single operator change vs v4 is
   pre-committed, not searched.
6. **Costs/liquidity:** per-bucket CostModel + mandatory 2× rerun; the P/S
   value leg tilts smaller/cheaper (cost-fragile) — SMALL bucket flagged;
   capacity noted before any capital talk.
7. **Regime-dependence:** two-regime OOS + `summarize_by_period` segments;
   the combination thesis IS regime-cure, so per-regime drawdown is the metric.
8. **Small-n:** N25/N50 benchmarked vs same-universe EW; intersection baskets
   can thin below N in low-overlap snapshots — the realized basket size is
   reported, and a cell that can't fill N is disclosed, not silently padded.

## Candidate gates (lab.md §3b)

- **G1 (tape):** combinations use P/S (a fundamental-scaled multiple the house
  accepted as value, not price-only, in v3); change-signals are pure SF1. PASS.
- **G2 (constraint):** WEAK — mispricing/risk-premium harvests, no forced
  counterparty. This family always scores G2 weak; it lives on G3/G5 + the
  two-regime backtest. Recorded honestly.
- **G3 (capacity-inversion):** intersection baskets concentrate in neglected
  small/mid names — favorable for a tiny book.
- **G4 (arithmetic):** WEAK — drift/quality forecasts, not contractual.
- **G5 (power):** STRONG — continuous cross-sectional sorts every quarter.

## What a win means

SUPPORTED = earned a paper forward test, NOT live money, NOT validated. Famous
anomalies decay (McLean-Pontiff ~58%); fresh graded quarters validate. A
`netiss_x_grossprof` or `quality_at_price` win becomes a Plutus-improvement
candidate for the LAB overlay — never an autopilot edit to his frozen live spec.
