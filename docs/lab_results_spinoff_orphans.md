# Lab results — `spinoff_orphans` (REFUTED, 2026-07-05)

**Verdict: REFUTED — decisively, and in the wrong direction.** The small/
neglected spinoff-orphan tail does not get underpriced-and-drift-up; it
**underperforms** the size-matched SMALL/MICRO equal-weight benchmark, worst in
the holdout. All five pre-registered criteria fail.

Prereg: `docs/lab_prereg_spinoff_orphans.md` (committed before data). Population:
227 US spinoffs 2015-2024 (exhaustive research fan-out), 204 US-parent
major-exchange, **200 priceable / 89 small-micro tail**. Benchmark: SMALL/MICRO
EW index built from the achilles panel (SEP has no ETFs). Entry T+1 after the
child's first-trade date; delisted series exit at last print (kept).

## Results — excess vs size-matched SMALL/MICRO EW

| Subset | 63d | 126d | 252d |
|--------|-----|------|------|
| FULL SET (control) | −1.97% (t −1.1) | −1.59% | +1.55% (t 0.4) |
| **SMALL tail (primary)** | **−6.81% (t −1.9)** | **−9.29% (t −2.0)** | **−9.33% (t −1.4)** |
| — small in-sample 2015-19 | +4.07% | +1.75% | +0.12% (t 0.01) |
| — small **holdout 2020-24** | **−22.1% (t −4.4)** | **−24.8% (t −3.7)** | **−22.6% (t −2.1)** |
| — small holdout @2× cost | −22.7% | −25.4% | −23.2% |

## Reading

1. **The small tail is the WORST subset, not the best** — the exact opposite of
   the thesis (criterion 5: small −9.3% vs full +1.6% at 252d). Whatever forced
   selling exists is either efficiently absorbed, or (more likely) small
   spinoffs are structurally the *worse* half — the parent kept the good
   business and spun the problem child, and it keeps underperforming.
2. **The holdout is catastrophic (−23%, t −2 to −4.5).** In-sample was merely
   flat (+0.1% at 252d — already not support); the 2020-2024 cohort of small
   spinoffs was dumped and *stayed down*. No re-rating drift anywhere.
3. **The refutation is robust to its own bias.** The population's survivorship
   floor (under-captured micro failures) biases the measured excess UPWARD —
   the true result is even more negative. The one bias that could rescue the
   hypothesis works *for* it, and it still fails. This is a clean kill, not a
   population artifact (contrast `post_bk_emergence`, where the population was
   too skewed to trust either way).

## Consequence

`spinoff_orphans` → **refuted** (terminal per slug). The small-spinoff
forced-seller edge is not real for a long-only book at these costs. The
`nemesis` spinoff library is retained as mechanical plumbing only; no PEAD-style
"the drift is there but untradable" residual — here the drift is *negative*.
Note for `event_diversifier_sleeve` (#15): spinoff-orphans is NOT an available
component. Moving to the next cram candidate.

Per-run data: `run_spinoff_backtest.py`, `scratchpad/spinoff_bt.log`.
