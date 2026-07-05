# Prereg — `gauntlet_v5_newfundamentals` (PAPER, committed BEFORE data)

Sponsor: operator ("search far and wide, need an alpha for the gauntlet").
Date committed: 2026-07-04. House multiple-testing counter at commit:
`hypotheses_ever` 141 → 142 (this slug).

This prereg is committed to the repo BEFORE a single return/bar is pulled.
The SF1 **column schema** was probed first (confirming which fields exist —
NOT returns), which is infrastructure verification, not data peeking. If any
return data was peeked before this commit, the slug is burned.

## What this tests

A fresh, pre-committed grid of the THREE new fundamentals families that
survived the 2026-07-04 six-front alpha sweep (docs to be linked in results),
plus gross-profitability as an in-screen REFERENCE for a head-to-head against
the factor the house already trades (Plutus's second factor). The sweep killed
payout-yield (subsumed by net-issuance), distress (short-leg-trapped),
intangible-value (long-only leg loss + parameter-laden), and forced flows
(dead by literature — Greenwood-Sammon 2025). The three survivors here are the
runnable-now, distinct, real-prior candidates.

### The three signals (all pure SF1, datekey point-in-time)

**A. `cash_op` — cash-based operating profitability** (Ball, Gerakos,
Linnainmaa & Nikolaev 2016, JFE). Operating profitability purged of the
accrual component:
```
OP_ttm  = revenue − cor − sgna + rnd            (trailing-4Q sums; R&D added back)
COP_ttm = OP_ttm − Δreceivables − Δinventory + Δpayables + Δdeferredrev
signal  = COP_ttm / assets                       (rank DESC; high = good)
```
Δ = year-over-year change (t vs t−4 quarters) of the balance-sheet item.
Deliberately a REDUCED form of the full Ball et al accrual set (Sharadar
lacks clean prepaid/accrued-expense fields — disclosed limitation). Thesis:
subsumes accruals (dead here) AND beats gross-profitability (supported here) —
Novy-Marx & Medhat 2025 find profitability the least-decayed anomaly.

**B. `delta_rnd` — abnormal R&D increase** (Eberhart, Maxwell & Siddique
2004, JF). GAAP forces R&D expensing, mechanically depressing current earnings
of firms stepping up innovation investment:
```
signal = (rnd_ttm_t − rnd_ttm_{t−4Q}) / assets_t     (rank DESC; big step-up = good)
```
Only R&D-active names (rnd_ttm > 0 in both periods) are eligible; the rest are
excluded and the coverage disclosed. Distinct from intangible-value (which is
the R&D *level* in book) — this is the *change*.

**C. `fund_mom` — fundamental momentum** (Novy-Marx 2015; Chan-Jegadeesh-
Lakonishok 1996), estimate-free (Sharadar has no analyst consensus):
```
SUE  = (eps_q − eps_{q−4}) / stdev(eps_q − eps_{q−4} over trailing 8Q)   (seasonal random walk)
dROE = roe_ttm_t − roe_ttm_{t−4Q},   roe_ttm = netinc_ttm / equity
signal = mean( zscore_x(SUE), zscore_x(dROE) )        (cross-sectional z, rank DESC)
```
Needs ≥8 quarters of EPS history. **G1 orthogonalization is a hard kill
criterion** (below): fundamental momentum correlates with price momentum,
which is DEAD here — a surviving cell must retain alpha after controlling for
12-1 price momentum, or it is price momentum relabeled and is refuted.

**D. `gross_prof` — REFERENCE (already SUPPORTED, gauntlet_v2)**: `gp_ttm /
assets`, rank DESC. Re-run inside this identical screen for an apples-to-apples
head-to-head — the "does a new signal BEAT what Plutus owns?" test.

## The grid (pre-committed, no post-hoc additions)

4 signals × {LARGE (top-500 by PIT marketcap), SMALL (501-2000)} × {N25, N50}
= **16 cells.** DSR deflation uses n_trials = 16 with the cross-sectional
`variance_of_sr` over the grid (the v1/v2 convention — NOT the 1.0 default that
caused the DSR=0 bug; that bug does not recur). The house `hypotheses_ever`
counter increments by 1 (one slug), per house convention.

## Data, universe, execution (identical to gauntlet_v2)

- **Universe:** the frozen `gauntlet_v1_universes` PIT catalog (top-2000 by
  point-in-time marketcap, quarterly LARGE/SMALL buckets), `shared.populations`.
- **Bars:** Sharadar SEP, delisted-inclusive, total-return (closeadj).
- **Fundamentals:** Sharadar SF1 ARQ, keyed by `datekey` (FILING date = point-
  in-time; no look-ahead). Signal computed from filings with datekey ≤ signal
  date only.
- **Windows:** in-sample 2000-2015, holdout 2016-2025 (touched ONCE).
- **Execution:** quarterly rebalance, entry at the next trading day's close
  (signal_lag), equal-weight top-N, `shared.gauntlet.simulate`, per-bucket
  `CostModel` (LARGE 5bps / SMALL 25bps slippage), initial 10k.

## Success thresholds (pre-committed — the arbiter, not enthusiasm)

A signal is **SUPPORTED** only if, in a NON-ISOLATED cell (a same-signal
neighbor at the adjacent N or bucket also survives — the asset-growth
isolated-peak lesson):
1. **In-sample:** DSR ≥ 0.95 (n_trials=16, cross-sectional variance_of_sr)
   AND CAGR > the same-bucket equal-weight benchmark.
2. **Holdout (touched once):** beats the same-bucket EW benchmark 2016-2025
   AND survives a 2× slippage rerun.
3. **`fund_mom` only:** the surviving cell's monthly excess returns retain a
   positive, non-trivial alpha after regressing on a 12-1 price-momentum
   long-short factor built from the same panel. Fail → refuted as price-mom.

**Head-to-head (the Plutus decision):** a SUPPORTED new signal whose excess
also exceeds the in-screen `gross_prof` reference in BOTH regimes is a
candidate to UPGRADE Plutus's second factor. A new signal that beats EW but
NOT gross_prof is logged "real but not better than what we own."

**Stopping rule:** if nothing clears, the fundamentals frontier is declared
spanned by what the house owns (net-issuance + gross-profitability), and the
search routes to structure/event families (a god build, not the gauntlet) —
that is the search completing, not failing.

## Bias checklist (all 8, per shared.lab.BIAS_CHECKLIST)

1. **Survivorship:** SEP is delisted-inclusive; SF1 covers dead filers.
   Per-cell coverage (names priced / names in universe) reported; the
   `missing` list is the disclosure. Known gap: deep-OTC/pre-1998 thin.
2. **Look-ahead:** SF1 keyed by `datekey` (filing date), signal uses only
   datekey ≤ signal date; execution lagged to next-day close. No restated-
   data leakage (ARQ as-first-filed dimension).
3. **Selection:** the 16-cell grid is fully enumerated here BEFORE data; no
   cell is added, dropped, or re-specified after seeing returns.
4. **Multiple-testing:** 16 cells → DSR deflated at n_trials=16 with cross-
   sectional variance_of_sr; house `hypotheses_ever` 141→142. ~1-in-20 look
   good by chance is exactly why the two-regime holdout + forward test exist.
5. **Overfitting:** parameter-cliff (non-isolated-neighbor) rule; holdout
   touched once; `summarize_by_period` regime table mandatory in results.
6. **Costs/liquidity:** per-bucket CostModel + mandatory 2× slippage rerun;
   `capacity_stats` (participation vs ADV) reported before any capital talk;
   SMALL bucket is the cost-fragile one and is stress-flagged.
7. **Regime-dependence:** two-regime OOS split; the holdout is a different
   decade; per-period breakdown reported so a single-era artifact shows.
8. **Small-n:** N25/N50 baskets, benchmark-relative vs same-universe EW (an
   anomaly must beat the naive book, not merely be positive); sharpe_ci
   quoted, not the point estimate.

## Candidate gates (lab.md §3b — answered in writing)

- **G1 (tape):** PASS for all three — computed from SF1 fundamentals, not
  price/volume. `fund_mom` carries a price-momentum-overlap RISK, handled by
  the explicit orthogonalization kill criterion above.
- **G2 (constraint):** WEAK for all three — these are characteristic/
  underreaction premia, not forced-flow events (no named constrained
  counterparty). Operator override to proceed is implicit in the "gauntlet a
  factor" directive; recorded honestly. The gauntlet measures whether the
  statistical edge is real net of cost — G2 governs the QUEUE, not whether a
  panel test is valid.
- **G3 (capacity-inversion):** cash_op/gross_prof broad (large-cap harvestable
  → lower priority in principle); delta_rnd/fund_mom concentrate in small,
  low-coverage names (fits the tiny book). Reported, not gating here.
- **G4 (arithmetic):** WEAK — all three are drift/quality forecasts, not
  contractual terminal values. The house's honest standing caveat.
- **G5 (power):** STRONG — continuous cross-sectional sorts on the whole
  panel every quarter; ample observations for a powered in-sample/holdout test.

## What a win means (and does not)

SUPPORTED = earned a paper forward test, NOT live money, NOT validated.
Famous anomalies decay (McLean-Pontiff ~58%); only fresh post-2026 graded
quarters validate. A supported head-to-head winner over gross_prof becomes a
candidate to upgrade Plutus's LAB overlay — never an autopilot edit to his
live book (that stays the frozen validated spec until a forward test says
otherwise).
