# Lab prereg — `post_bk_emergence` (COMMITTED BEFORE DATA)

**Sponsor:** operator (the "cram for one more god" campaign, 2026-07-05).
**Backlog:** #4, re-confirmed by the 2026-07-05 growth-hunt as the best-shaped
diversifier survivor. **This document is committed to the repo before any
return is computed.** If any parameter below is changed after seeing data, the
slug is burned and the honest variant is a new slug that says so.

## Hypothesis

Newly-issued common equity of a US company that has just **emerged from Chapter
11** is systematically **underpriced at emergence** and drifts UP over the
following ~3–12 months, because a large class of pre-petition holders is
**contractually forced to sell it regardless of value.**

## The mechanism (G2 — named counterparty + document)

Reorganized equity is typically distributed to the former **creditors** — most
importantly **CLOs and leveraged-loan funds**, whose **indentures and fund
mandates bar them from holding equity** (they are debt vehicles; equity breaches
concentration/eligibility covenants). They must divest the fresh-start shares
into a thin, uncovered, just-relisted market — a **price-insensitive forced
seller**. Sell-side coverage has lapsed (the old CIK was a defaulted issuer),
indices don't yet hold it, and generalist funds screen out "just-bankrupt." The
forced supply clears over a quarter-to-a-year, and the underpricing unwinds.
This is a **structural forced-seller barrier**, the most durable kind in the
house view — a mandate-barred holder cannot un-force itself.

## The five gates (answered before data)

- **G1 (tape test):** NOT a price signal — the trigger is a discrete corporate
  event (Ch11 emergence effectiveness). PASS.
- **G2 (constraint):** counterparty = CLOs / leveraged-loan funds / index
  exclusion; document = CLO indenture equity-divestiture clauses + fund
  mandates. Named and real. PASS.
- **G3 (capacity-inversion):** emergences are small ($100M–$2B reorg equity),
  thin, and un-coverable at a $100M-fund's minimum size → capacity-inverted.
  For a growth mandate this is a DIVERSIFIER, not a scalable engine (accepted:
  we are hunting right-tail ammunition, not beta).
- **G4 (arithmetic):** NO contractual terminal — the payoff is a re-rating
  DRIFT, not a tender/trust value. G4 FAIL, disclosed. This is the weakest gate
  and the reason the backtest bar is set high (below).
- **G5 (power):** ~10–20 tradable US emergences/yr × 10 yr ≈ 100–200 events —
  enough for a backtest, THIN for a live forward test (~15/yr). Noted: if
  supported, this is a slow-cadence diversifier sleeve, not a fast A/B.

## Population (built AFTER this doc is committed)

**Definition:** every US company whose reorganized common equity became publicly
tradable on a major exchange (NYSE/NASDAQ/NYSEMKT) upon emergence from a Chapter
11 filed and confirmed **2015-01-01 … 2024-12-31** (emergence effective date in
that window, leaving ≥ ~6 months of post-emergence bars through 2025-12-31).
Includes both new-CIK/new-ticker reorg equity and continued-ticker reorgs.

**Source & construction:** confirmed emergences identified from EDGAR (8-K Item
1.03/emergence-effectiveness, plan-of-reorganization effectiveness, ASC 852
fresh-start-accounting disclosures) and reputable bankruptcy trackers, then
cross-checked against Sharadar TICKERS/SEP for a tradable post-emergence bar
series. Each name recorded with: filer, emergence effective date, relisting
ticker + exchange, and CIK.

**Survivorship discipline (mandatory):** a reorg equity that **re-filed,
delisted, or went to zero** STAYS in the population and **exits at its last
print** — dropping re-failures would be the exact survivorship inflation that
makes distressed backtests lie. The `coverage_note` will state precisely what is
KNOWN missing (OTC/pink-only reorgs excluded as un-tradable; any emergence we
could not confirm a bar for). The build must be EXHAUSTIVE, not a list of
remembered winners (Hertz/Whiting) — selection into "names I recall" is the
primary failure mode and is explicitly forbidden.

## Test design (frozen)

- **Entry:** first available Sharadar SEP close on/after the emergence effective
  (relisting) date, executed with a **1-day lag** (never the emergence-day close
  used to date the event).
- **Benchmark:** size-matched — the SMALL/MICRO bucket equal-weight over the
  identical window (same engine as the PEAD gauntlet / gauntlet_v1 universes),
  so the excess is bucket-relative, not raw.
- **Horizons:** {63, 126, 252} trading days (~3/6/12 months). **Primary = 252d**
  (the forced-selling unwinds over ~a year). Total-return (closeadj).
- **Costs:** one-way 30bps (these are small/illiquid) + a **2× stress** (60bps).
  Optional −25% stop reported but NOT the primary spec.
- **Regime split:** in-sample = emergences 2015–2019; holdout = 2020–2024
  (touched once). NOTE up front: 2020–2021 is a huge energy/retail emergence
  cluster — the regime table is mandatory and a single-cluster result is a
  refutation, not a win.

## Success thresholds (pre-committed — pass ALL or REFUTED)

1. **In-sample:** primary-horizon mean excess > 0, **t ≥ 2.0**, n ≥ 30.
2. **Holdout:** mean excess > 0 (same sign), n ≥ 20.
3. **Cost:** still positive at 2× cost in the holdout.
4. **Non-isolated:** positive at the primary horizon AND at least one adjacent
   horizon (not a lone lucky 252d cell).
5. **Not single-cluster:** positive excluding the 2020–2021 energy cluster (a
   dedicated ablation — if the entire edge is 2020 oil, it is refuted).

Anything short of all five → **refuted** (terminal per slug). If supported:
`start_forward_test` (paper, ghost engine), and it becomes a **god-scaffold
candidate** under the conscious-override path (supported-not-yet-validated,
the Plutus/Hermes precedent) — NOT an autopilot until ≥20 forward grades.

## Bias checklist (planned handling — finalized at `record_backtest`)

- **survivorship:** re-failures kept, exit at last print; delisted bars included.
- **look_ahead:** entry T+1 after the PUBLIC emergence date; fresh-start
  financials never used before their filing date.
- **selection:** exhaustive population from EDGAR/trackers, not a winners list;
  coverage_note discloses known-missing; bucket-relative benchmark.
- **multiple_testing:** house `hypotheses_ever` (192 at preregister); 3 horizons
  × 2 regimes is a small grid; non-isolated + no-single-cluster rules.
- **overfitting:** thresholds frozen here; holdout touched once; no parameter
  tuned on 2020–2024.
- **costs_liquidity:** 30/60bps + capacity check (`capacity_stats`) — reorg
  equity is thin; if our own fills would move it, disclose.
- **regime:** 2015–19 / 2020–24 split + the mandatory energy-cluster ablation.
- **small_n:** ~100–200 events backtest (adequate); ~15/yr forward (thin —
  disclosed as a slow-cadence sleeve).

## Pre-committed consequence

Supported → forward test + god-scaffold candidacy (convex diversifier sleeve,
right-tail ammunition; sized small, per-name-capped). Refuted → ledger row with
the same prominence as a win; the `nemesis`/`oracle` forced-seller libraries
absorb any reusable plumbing; we move to the next cram candidate
(spinoff-orphans → sub-NAV wind-downs → odd-lot arb).
