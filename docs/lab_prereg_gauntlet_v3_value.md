# Prereg — `gauntlet_v3_value` (the value family)

- **Sponsor:** operator ("run every perceivable alpha strategy")
- **Committed:** 2026-07-04, BEFORE any DAILY valuation-multiple
  cross-section for the rebalance dates is pulled or any value cell is
  computed. DAILY multiples were probed once (AAPL 2015-06-30, schema
  confirmation only). Reuses the `gauntlet_v1_universes` PIT catalog
  and SEP bars as plumbing (v1's sanctioned reuse for v2/v3).

## Gates

G1 pass (a valuation ratio is fundamentals/price, not tape-derivable
alone). G2 PARTIAL, stated: value is a mispricing/risk-premium claim,
not a constrained-counterparty structure — hence the merciless
benchmark-relative bar. G3 fine at house scale. G4 n/a (no contractual
terminal value — a drift claim, honestly labeled). G5 pass.

## The grid (n_trials = 8, enumerated, FROZEN)

Four valuation multiples, ranked on DAILY point-in-time ratios
(computed by Sharadar daily from then-known fundamentals — PIT by
construction, no restatement), long the cheapest N=50, equal weight,
quarterly, next-trading-day-close execution:

1. `value_pb_low`: long the 50 LOWEST price-to-book (pb > 0).
2. `value_ps_low`: long the 50 LOWEST price-to-sales (ps > 0).
3. `value_ep_high`: long the 50 LOWEST positive price-to-earnings
   (= highest earnings yield; non-positive PE EXCLUDED — disclosed
   selection, standard in the literature).
4. `value_evebitda_low`: long the 50 LOWEST positive EV/EBITDA
   (non-positive excluded, disclosed).

× buckets {LARGE (PIT top-500), SMALL (501–2000)} = 8 cells.

**Single N=50 by design:** the house is multiple-testing-constrained
tonight, not capacity-constrained, so the trial budget is spent on
signal diversity across families (v2 quality, v3 value), NOT on an N
sweep within a family. N=25 concentration is deliberately NOT tested;
this is stated so a future N-sweep is a new prereg, not a silent
degree of freedom.

## Benchmark (frozen) — the correctness upgrade over v2

An in-run `bench_ew` cell (equal-weight ALL bucket members each
quarter, same execution + costs, min_ticket 0) is computed as the
verdict benchmark — the same-convention EW-of-universe, not a reused
scalar. The v1 in-sample EW CAGR scalars (LARGE 5.51%, SMALL 6.79%)
are reported as a cross-check; a material divergence is itself a
disclosed finding about v1/v2's reused-scalar convention.

## Splits, bars, verdict (frozen — identical machinery to v2)

- In-sample 2000-07..2015-12; holdout 2016-01..2025-12, survivors
  only, touched once.
- Costs: LARGE 5bps / SMALL 25bps slippage, $25 ticket, $10k/cell,
  total-return marking, signal_lag execution at next-day close.
- In-sample pass: DSR ≥ 0.95 at n_trials=8 (cited also vs
  hypotheses_ever at registration) AND net CAGR > in-run bench_ew.
- Holdout pass: PSR ≥ 0.95 AND beats bench_ew net.
- Survivor hygiene: 2× slippage rerun + parameter_cliff_report across
  the value family (signal-neighbors); isolated peak = noise.
- Any full survivor earns a ≥20-grade paper forward test. Never live
  from a backtest.

## Stopping rule (inherited)

v3 runs under gauntlet_v2's §6 stopping rule: if v2 AND v3 together
produce zero holdout survivors, the historical-panel program ends and
the alpha hunt moves exclusively to live/forward instruments and
operator-commissioned reading-based event catalogs (per docs/alpha_map.md).

## Bias checklist (finalized at record)

Survivorship: SEP delisted-inclusive; DAILY-multiple coverage per cell
disclosed (names in-universe with no pb/pe that quarter); PE/EVEBITDA
positive-only exclusion counted per rebalance. Look-ahead: DAILY
multiples are as-of-date; entry next trading day. Multiple testing:
8 cells; counter +8 at registration (125→133). Regime: v1 boundaries.
Costs: per-bucket + 2× rerun.
