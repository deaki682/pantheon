# Prereg — `gauntlet_v2_fundamentals` (the last historical sweep)

- **Sponsor:** operator ("run the gauntlet until you find alpha" —
  accepted under these terms: pre-committed grid, counter-deflated
  bars, mandatory replication for survivors, and the STOPPING RULE in
  §6, which is the binding answer to "until")
- **Committed:** 2026-07-04, BEFORE any SF1 fundamentals row is pulled
  beyond the entitlement QA probes (AAPL depth checks, 2026-07-04).
  SF1 is a FRESH dataset — never used in any house study. SEP bars and
  the `gauntlet_v1_universes` PIT catalog are reused as pricing/
  universe plumbing per standing practice (v1's results doc explicitly
  sanctioned a v2 on new families as a new prereg + fresh counter).

## 1. Question

Do the five strongest DOCUMENTED fundamentals anomalies survive
implementable long-only form, net of costs, against their own
universe's equal weight — where every price-derived family already
died? Fundamentals pass gate G1 (not computable from the tape); G2 is
PARTIAL and said plainly (no constrained counterparty — these are
mispricing claims; net issuance comes closest: the counterparty is
the corporation itself, diluting when overpriced and repurchasing
when not), which is exactly why the bars stay merciless.

## 2. The grid (n_trials = 20, enumerated, FROZEN)

Five signals × N ∈ {25, 50} × bucket ∈ {LARGE (PIT top-500), SMALL
(PIT 501–2000)} — 20 cells, no more:

1. `net_issuance_low`: long the N LOWEST trailing-4Q change in
   weighted shares outstanding (buyback side).
2. `asset_growth_low`: long the N LOWEST y/y total-asset growth.
3. `accruals_low`: long the N LOWEST (netinc_TTM − ncfo_TTM)/assets.
4. `gross_prof_high`: long the N HIGHEST gp_TTM/assets.
5. `roa_high`: long the N HIGHEST netinc_TTM/assets.

Quarterly rebalance on the first universe snapshot of each calendar
quarter (from `gauntlet_v1_universes`), equal weight, `signal_lag=1`.
**Point-in-time discipline: every fundamental is keyed by SF1
`datekey` (the FILING date) — a quarter is usable only from datekey+1,
never from calendardate.** Costs: v1 bucket slippage (LARGE 5bps,
SMALL 25bps), $25 min ticket, $10k/cell; total-return marking.

## 3. Splits (frozen)

In-sample executions 2000-07..2015-12; holdout 2016-01..2025-12,
touched ONCE by in-sample survivors only. Same split dates as v1 for
comparability; SF1 outcomes on these splits have never been computed.

## 4. Bars (frozen)

- **In-sample pass:** DSR ≥ 0.95 at n_trials=20 (grid) — and cited
  against `hypotheses_ever` (=125 at registration) in the checklist —
  AND net CAGR above the same-bucket EW benchmark.
- **Holdout pass:** PSR ≥ 0.95 AND beats the bucket benchmark net.
- **Survivor hygiene:** 2× slippage rerun (verdict must hold) and
  `parameter_cliff_report` across the grid (an isolated-peak survivor
  is treated as noise, stated in advance).
- Any survivor of ALL of that earns the standard ≥20-grade paper
  forward test. Nothing here ever touches live money directly.

## 5. Bias checklist commitments

Survivorship: SEP+DAILY panel, delisted included; SF1 coverage gaps
(names with bars but no fundamentals) disclosed per cell — if SMALL
coverage falls below 80% of the universe, that cell is reported
coverage-impaired, stated before results exist. Look-ahead:
datekey-only keying (the classic fundamentals sin is calendardate).
Multiple testing: 20 cells, counter 105→125 at registration.
Regime: v1's regime table boundaries. Costs: per-bucket + 2× rerun.

## 6. THE STOPPING RULE (the binding "until")

If ZERO cells survive the holdout: **the historical-panel program
ends.** No gauntlet_v3 on price or fundamentals data; the spent
panels buy no further decisions; the hunt for alpha moves EXCLUSIVELY
to (a) the live forward instruments (Proteus, Achilles' fall season,
Nemesis ghost race, quiet-cluster accrual) and (b) reading-based
event families that require operator-commissioned LLM cataloging
budgets, each through the gates as its own prereg. "Run until you
find alpha" terminates here either by finding it or by exhausting
the honest historical search space — both outcomes are answers.
