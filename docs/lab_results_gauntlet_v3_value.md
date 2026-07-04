# Results — `gauntlet_v3_value` — INCONCLUSIVE (value is alive, not cleanly harvestable standalone)

- **Prereg:** [docs/lab_prereg_gauntlet_v3_value.md](lab_prereg_gauntlet_v3_value.md)
  (with a documented pre-data benchmark amendment)
- **Run:** 2026-07-04, `run_gauntlet_v3.py`; DAILY PIT multiples + SEP bars
- **Registry:** `gauntlet_v3_value` → **inconclusive** (backtested);
  `hypotheses_ever` 133

## Verdict: INCONCLUSIVE

| multiple | in-sample survivor? | holdout 1× | holdout 2× |
|---|---|---|---|
| price-to-sales LARGE | yes (+9.3%) | PASS (+12.3%) | **PASS (+12.3% vs 11.4%)** |
| price-to-sales SMALL | yes (+11.4%) | PASS (+9.6%) | fail (+9.0% vs 9.5%) |
| earnings-yield L/S | yes | fail | — |
| EV/EBITDA L/S | yes | fail | — |
| price-to-book L/S | **NO** (failed in-sample) | — | — |

Value beat its EW benchmark in-sample in 6/8 cells. But in the bull
holdout only **price-to-sales** sustained, and only the LARGE cell
survived 2× cost — with NO parameter-robust neighbor (its SMALL twin
died at 2×, its multiple-peers died at the holdout). By the frozen
isolated-peak rule it earns no standalone forward test.

Not refuted (genuine two-regime signal in price-to-sales), not clean
support (no robust survivor). **price-to-book failing in-sample is
itself a clean literature confirmation** — B/M is the weakest value
multiple in the modern era, and the house measured exactly that.

## The indicated follow-up (a new prereg, not tonight)

Value's signal is real but thin standalone. The two constructions with
a real prior:
1. **Composite** — net-issuance + gross-profitability (both SUPPORTED
   in v2) + price-to-sales, rank-combined. JKP (2023) find composites
   the most robust factor form; this is the natural next grid.
2. **LLM value-trap overlay (Lens B)** — a "why is it cheap" read on
   the mechanical value shortlist, the textbook quality-on-value
   overlay. The exact mechanical-filter-plus-reading shape the house's
   one real edge fits.
