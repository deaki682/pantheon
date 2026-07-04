# Results — Delphi point-in-time universe replay (backlog #4)

- **Prereg:** [docs/lab_prereg_delphi_pit_universe.md](lab_prereg_delphi_pit_universe.md)
  (committed 2026-07-04 before study data was assembled)
- **Run:** 2026-07-04, `run_delphi_pit.py`, executing
  `delphi.backtest.run_backtest` — the claim's own code — with only
  the prereg's `universe_fn` parameter added (behavior-preserving,
  tests green).
- **Window:** 2021-06-30 → 2026-06-30 (reconstructed; original cache
  gone). **Data:** Sharadar SEP/SFP closeadj (delisted included), 200
  tickers; DAILY marketcap at 21 quarter-ends; SQ→XYZ rename resolved
  via `shared.sharadar.resolve_ticker` (zero missing tickers after).

## Verdict (per the frozen criteria)

| criterion | outcome |
|---|---|
| 1. Replicates (A total in [+60%, +110%]) | **YES — almost exactly**: +85.61% vs the claimed +85.2% |
| 2/3. Artifact test (B alpha vs half of A alpha) | **NOT an artifact — B beats A**: the PIT universe *outperforms* the curated list |

But the headline is what replication exposed: **the claim's total
return is real and its alpha is not.**

| run | total return | SPY (same window) | alpha | Sharpe | maxDD | trades |
|---|---|---|---|---|---|---|
| **Claimed** (runbook, commit `d265cdc`) | +85.2% | ≈ +31% implied | **+53.8pp** | **1.51** | — | — |
| **A — frozen 2026 list, honest data** | +85.61% | **+86.69%** | **−1.08pp** | 0.65 | −30.0% | 1,964 |
| **B — PIT top-119, quarterly** | **+143.51%** | +86.69% | **+56.82pp** | 0.87 | −29.9% | 1,990 |

Three findings, in order of importance:

1. **The +53.8pp alpha does not survive: the SPY benchmark leg of the
   original backtest was broken.** SPY's actual total return over the
   same five years was +86.7% (Sharadar SFP closeadj; independently
   confirmed against the broker: SPY ≈ $745 on 2026-07-02 vs $428 on
   2021-06-30, plus dividends). The original run credited SPY with
   roughly +31%. On honest data the mechanical system on the curated
   list **matched the index** (−1.1pp) — it did not beat it by 54
   points. The Sharpe 1.51 figure also fails to replicate (0.65 on
   the same list, window, and near-identical total return); it likely
   shares whatever defect produced the SPY leg (a shorter effective
   data window is the leading suspect; unrecoverable since the
   original price cache was never persisted).
2. **Point-in-time membership does NOT indict the strategy — it
   vindicates it.** The blind top-119-by-marketcap universe (renamed,
   acquired, and delisted names included; TWTR-era constituents and
   all) delivered +143.5%, +56.8pp over SPY, Sharpe 0.87. The
   hand-curated 2026 list turns out to be the *conservative* choice:
   at each quarter-end it was missing 27–33 of the actual top-119
   (BRK.B, LIN, TMUS, BKNG, SPGI, and — decisively for a momentum
   strategy — PANW, ANET, CRWD, KKR, GEV, PLTR, APP as they earned
   their way in). Hindsight curation *muted* the backtest rather than
   inflating it. The classic survivorship story runs backwards here.
3. **Delphi's live rule set is better than her evidence was.** The
   edge, if any, is in the momentum + MA-exit mechanics on a genuinely
   large-cap universe — but the honest measured statement is "+56.8pp
   over one five-year bull window on a PIT universe, costless
   simulation, n=1 window," not "+53.8pp alpha, Sharpe 1.51."

## Consequences (as frozen in the prereg)

- The runbook's design-rationale citation is **corrected in
  `.claude/commands/delphi.md`**: measured numbers, pointer here.
  The old +53.8pp/Sharpe-1.51 figures may not be cited again.
- Delphi's capital-scaling case continues to rest on her live/ghost
  graded calls (her gates already require exactly that); this study
  neither advances nor retires the ceiling.
- Universe curation insight (information, not a rule change): the
  quarterly curation decision point now has measured evidence that
  omitting mechanical top-cap members costs momentum alpha. Any rule
  change (e.g., seeding curation from the PIT top-119) is a separate
  decision for the operator/Delphi runbook, not this study.

## Bias checklist (all eight, as run)

1. **Survivorship:** B's universes built per-date from DAILY marketcap
   with delisted/renamed names included (SQ→XYZ resolved; TWTR-era
   members present through their final trading day). A's frozen list
   retains the original's survivorship deliberately — it is the thing
   measured. Zero tickers missing bars after rename resolution.
2. **Look-ahead:** B membership effective the first trading day after
   each quarter-end; both runs share the original code's same-day
   signal/trade convention, so the A-vs-B comparison isolates
   membership. A's frozen list is look-ahead by construction —
   measured, and it turned out to *hurt* rather than help.
3. **Selection:** universes fully mechanical (frozen constant vs
   top-119 by marketcap among the three Domestic Common Stock
   categories). Dual-class listings retained per the blind rule
   (GOOG excluded only because the curated list carries GOOGL — both
   appear in B where ranks warrant; disclosed).
4. **Multiple testing:** exactly the two pre-committed runs; nothing
   tried and discarded. House counter 91 at prereg (this measurement
   study registered no new tradable hypothesis).
5. **Overfitting:** zero tuned parameters — Delphi's shipped constants
   from the claim's own commit, one window, no variants.
6. **Costs/liquidity:** both runs costless, matching the original
   (disclosed in prereg). Costs would shave both A and B; B's margin
   over A (+58pp) is far outside any cost differential at ~2,000
   trades on mega-caps.
7. **Regime:** one 5-year bull window by construction — the study
   judges the citation, not the strategy's future. No out-of-window
   inference drawn.
8. **Small n:** n=1 window, 2 runs; no statistical claim made. The
   deliverable is the measured A/B/SPY gap and the exposure of the
   benchmark-leg error.

## Delisted/renamed handling detail

`run_backtest` sells a position with no current bar at its average
entry price (the original code's convention). This affects only B
(A's frozen names never delist in-window) and biases B *downward* —
acquired names' run-ups are surrendered (e.g. TWTR). B won anyway.

## Artifacts

- `docs/data/delphi_pit/delphi_pit_results.json` — both runs' full
  results blocks; equity curves alongside.
- House population `delphi_pit_top119` — the 21 quarter-end top-119
  lists with coverage note (`shared.populations`).
