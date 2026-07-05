# Results — `gauntlet_v5_newfundamentals` — SUPPORTED (cash_op only)

- **Prereg:** [docs/lab_prereg_gauntlet_v5_newfundamentals.md](lab_prereg_gauntlet_v5_newfundamentals.md)
  (committed before data; SF1 column schema probed, zero returns peeked pre-commit)
- **Run:** 2026-07-04, `run_gauntlet_v5_pull.py` + `run_gauntlet_v5_screen.py` +
  `run_gauntlet_v5_audit.py`. Data: SF1 ARQ (625,129 filing-dated rows,
  1998-2025), frozen `gauntlet_v1_universes` PIT catalog, SEP delisted-inclusive
  total-return bars both windows.
- **Grid:** 4 signals × {LARGE, SMALL} × {N25, N50} = 16 cells. cross-sectional
  `variance_of_sr` = 0.01519, `expected_max_sharpe(16)` = 0.222.
- **Registry:** `gauntlet_v5_newfundamentals` → **supported → forward_testing**;
  `hypotheses_ever` 141 → 153 (12 new cells; gross_prof 4 cells are a control
  re-run already counted in v2).

## Verdict

- **`cash_op` (cash-based operating profitability, Ball-Gerakos-Linnainmaa-
  Nikolaev 2016) — SUPPORTED.** All 4 cells cleared BOTH gates (in-sample DSR
  ≥ 0.95 + beat same-bucket EW; holdout beat benchmark) AND survived 2× cost.
  Non-isolated (the whole family, both N and both buckets). The house's THIRD
  supported backtest.
- **`delta_rnd` (abnormal R&D increase, Eberhart-Maxwell-Siddique 2004) —
  REFUTED.** Dead in-sample (all 4: CAGR −0.07% to +2.32%, DSR ≈ 0, none beat
  benchmark). Its clean 2016-25 holdout pass is MOOT — a cell that fails the
  pre-committed first gate cannot be resurrected by the second. A textbook
  demonstration of why the gate order is committed in advance.
- **`fund_mom` (fundamental momentum, Novy-Marx 2015, estimate-free SUE+dROE) —
  NOT SUPPORTED (isolated).** Only N50-LARGE cleared both gates; its strong
  in-sample SMALL cells (+10.3%/+8.7%) FAILED the holdout (+7.8%/+8.3% < 9.5%
  bench). One isolated cell → treated as noise by the pre-committed parameter-
  cliff rule. Corroborating: its in-sample GFC segment was −13.9% (the worst
  crash reading in the grid — the momentum-crash signature), consistent with
  fund_mom being a fundamental shadow of the dead price-momentum factor. The
  price-momentum orthogonalization kill (prereg) is therefore MOOT — no
  fund_mom family reached the non-isolated bar to need killing.
- **`gross_prof` (reference, already supported in v2) — RE-CONFIRMED** at
  N50-LARGE (both gates), calibrating the screen against the known factor.

## The numbers (full grid)

In-sample benchmarks (same-bucket EW, frozen v1): LARGE 5.51%, SMALL 6.79%.
Holdout benchmarks: LARGE 11.43%, SMALL 9.50%.

| cell | IS CAGR | IS DSR | HO CAGR | HO@2× | both gates? |
|---|---|---|---|---|---|
| cash_op N25 LARGE | +6.30% | 1.00 | +15.99% | +15.90% | ✅ |
| cash_op N25 SMALL | +8.08% | 1.00 | +13.83% | +13.13% | ✅ |
| cash_op N50 LARGE | +5.80% | 1.00 | +18.87% | +18.80% | ✅ |
| cash_op N50 SMALL | +7.93% | 1.00 | +15.34% | +14.67% | ✅ |
| delta_rnd (all 4) | −0.07..+2.32% | ≈0 | (pass, moot) | — | ❌ IS-dead |
| fund_mom N25 SMALL | +10.28% | 1.00 | +7.77% | fail | ❌ HO-fail |
| fund_mom N50 LARGE | +5.52% | 1.00 | +13.74% | +13.48% | ✅ (isolated) |
| fund_mom N50 SMALL | +8.73% | 1.00 | +8.32% | fail | ❌ HO-fail |
| gross_prof N50 LARGE | +8.15% | 1.00 | +11.77% | +11.71% | ✅ (reference) |

## The caveats — front and center (a win is audited hardest)

**1. cash_op's in-sample edge is recovery-concentrated, and it is NOT crash-
robust in large caps.** Regime breakdown (in-sample):

| segment | cash_op N50 LARGE | gross_prof N50 LARGE | cash_op N50 SMALL |
|---|---|---|---|
| 2000-06..2003-12 (dot-com) | **−6.9%** | −2.3% | +4.5% |
| 2008..2009 (GFC) | **−4.0%** | −0.1% | −7.0% |
| 2010..2015 (recovery) | +14.9% | +16.1% | +15.4% |

In LARGE, gross_prof was the better factor in-sample (+8.15% vs +5.80%) AND
fell less in BOTH crashes. cash_op's full-window edge leans on the recovery.

**2. The "cash_op beats gross_prof" head-to-head is HOLDOUT-driven and
regime-flavored.** In-sample it splits (gross_prof wins LARGE, cash_op wins
SMALL). Only in the holdout does cash_op win both buckets — and its holdings
are a mega-cap tech/quality basket (AMZN, NVDA, META, AAPL, ADBE, QCOM), so the
+23.6% 2020-25 leg partly rides the mega-cap-growth regime — the SAME regime
bet the house already flagged for cap-weighting (docs/dev_net_issuance_weighting.md).
cash_op is a **co-equal, holdout-favored variant** of the profitability axis,
NOT a demonstrated dominant upgrade.

**3. The whole 2016-25 holdout was broadly kind** — 12-13 of 16 cells passed it,
including in-sample-dead delta_rnd. The DISCRIMINATING gate was the crash-heavy
2000-15 in-sample screen, which is exactly where delta_rnd died and fund_mom
went isolated. cash_op passing there (all 4) is the load-bearing evidence.

**4. Famous, decay-prone, and G2/G4-weak.** Profitability is in every factor
fund; McLean-Pontiff ~58% decay. cash_op has no forced counterparty (G2 weak)
and is a quality forecast, not a contractual payoff (G4 weak). SUPPORTED =
earned a paper forward test, NOT validated, NOT live money. Multiple-testing:
house counter 153 → several false positives expected; two-regime + 2× survival
is why it clears the bar to forward-test, not proof it is live alpha.

## What this buys (the decisions)

- **A third supported factor for the lab's forward-test slate.** cash_op N50
  (both buckets) accrues paper forward quarters on fresh data; ≥20 graded
  quarters on the shrunk excess validate or refute.
- **A Plutus second-factor CANDIDATE — not an automatic swap.** cash_op is a
  legitimate candidate to replace gross-profitability as Plutus's quality
  factor, but the evidence is holdout-weighted and possibly a mega-cap-growth
  regime bet. The decision waits for the forward test; nothing touches Plutus's
  live spec now (it stays the frozen validated net-issuance + gross-profitability
  deluxe stack).
- **delta_rnd and fund_mom: closed.** Abnormal-R&D refuted; fundamental momentum
  is a non-isolated-failing momentum shadow. Neither returns without genuinely
  new structure.

## Net map movement

The fundamentals frontier is now essentially spanned: net-issuance, gross-
profitability, and cash-based profitability are the survivors — all three the
same two axes (capital-return + quality), all long-only equal-weight, all
holdout-favored. The price and event/forced-flow families remain dead. The
search is converging: the house's harvestable edge is a narrow quality/
capital-return band, and cash_op sharpens the quality end of it.
