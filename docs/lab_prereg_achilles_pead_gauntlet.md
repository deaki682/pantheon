# Prereg — `achilles_pead_gauntlet` (PAPER, committed BEFORE data)

Sponsor: operator (via the "improve the older gods" pass, 2026-07-05).
Status at filing: preregistered. Git history is the timestamp that proves
"before data."

## Why this study exists

Achilles is the only older god **still LIVE on a mechanical spine that has
never been through the full gauntlet.** He buys post-earnings beats the market
rewarded, holds ~5 days, -8% stop, up to 12 names, betting on Post-Earnings
Announcement Drift. Two prior signals say the live long thesis is on thin ice:

- The **reaction-gate replay** (2026-07-03, RESEARCH_LEDGER): rewarded beats
  showed **no 5-day drift anywhere** (small/mid −0.9%); the only real signal was
  the SHORT side (sold beats kept falling, t −2.3) — which a long-only book
  can't trade. Verdict: "inconclusive, buy-side absent."
- The house-wide gauntlet lesson: simple mechanical buy-triggers measure ~zero
  after costs + same-universe benchmarks (gauntlet_v1).

That replay was a lighter test (no two-regime holdout, no 2× cost, no
parameter-cliff, a broad small/mid bucket). This study settles it at full rigor
and answers the question the replay left open: **does long-only PEAD, in the
neglected sub-universe Achilles actually targets, with the reaction gates,
survive the gauntlet — or does it need to be narrowed, reframed, or retired?**

## What this tests

A survivorship-free replay of Achilles' actual live rules on Sharadar SEP/SF1,
1998→2025, two-regime holdout, 2× cost stress, parameter-cliff discipline.

### The signal (no analyst estimates required)

PEAD needs an earnings-surprise measure. Sharadar SF1 has reported EPS but not
consensus estimates, so we use the classic academic definition that needs only
reported history:

- **SUE (Standardized Unexpected Earnings), seasonal random walk (Bernard-Thomas):**
  `SUE = (EPS_q − EPS_{q-4}) / σ(ΔEPS over the trailing 8 quarters)`, keyed to
  `datekey` (the SF1 filing date) so nothing is used before it was public. A
  "beat" is SUE in the top quantile (pre-committed threshold below), not a
  headline vs a re-stated estimate.
- **The reaction gate (from SEP prices around `datekey`):** `reaction =
  (close_{report+1} − close_{report-1}) / close_{report-1}`. Direction gate:
  reaction > 0 (only beats the market rewarded — Achilles is long-only). The
  **magnitude gate** is a tested axis (below), the exact question raised by the
  BOLD/`RUNUP_FIRED_CAP` lesson: does dropping already-fired beats help?
- **Entry** the next trading day after the reaction bar; hold H trading days;
  -8% hard stop (Achilles' live rule, fixed); equal-weight basket; one slot per
  symbol; 4-week cooldown after a stop.

## The grid (pre-committed, no post-hoc additions) — 18 cells

- **Hold period H:** {5, 10, 20} trading days (Achilles is 5; test the drift's
  actual half-life, which the Nemesis exit-curve work showed can be longer).
- **Reaction-magnitude cap:** {none, 0.20, 0.10} — directly tests whether the
  `MAX_REACTION_PCT` guard just added to the scanner earns its place.
- **Universe:** {SMALL (PIT marketcap rank 501–2000), MICRO (rank 2001–3500)} —
  PEAD is academically strongest in neglected/thin-coverage names; the replay's
  broad small/mid bucket may have diluted exactly where the edge lives.

Fixed across all cells: SUE top-quintile beat threshold, -8% stop, next-day
entry, equal-weight, 4-week cooldown. `hypotheses_ever` 173 → 191 (+18 cells) —
the multiple-testing burden is counted honestly.

## Data, universe, execution

- **Bars:** Sharadar SEP, survivorship-free, `resolve_ticker(as_of=)` keyed to
  the final ticker (THE LAW, docs/sharadar_qa_2026-07-04.md). Delisted names
  included; the coverage_note discloses the deep-OTC hole SEP can't serve.
- **Fundamentals:** SF1 ARQ dimension, `datekey`-PIT (filing date), same
  discipline as gauntlet_v2/v5.
- **Universe:** monthly PIT marketcap-rank buckets (reuse `shared.populations`
  `gauntlet_v1_universes` where they align; rebuild the MICRO band).
- **Benchmark:** each cell vs its OWN bucket's equal-weight over the identical
  holding windows (the gauntlet standard — beat the universe, not just cash),
  plus SPY-TR as a secondary read.
- **Costs:** per-bucket spread/slippage model, and every verdict must survive
  **2× that cost** — decisive for thin MICRO names where the edge can live
  entirely inside the spread.

## Success thresholds (pre-committed — the arbiter, not enthusiasm)

A cell is SUPPORTED only if ALL hold:
1. Beats its bucket equal-weight in the **in-sample** window (2000–2015) after 1× cost.
2. Beats it again in the **holdout** window (2016–2025, touched once) after 1× cost.
3. Still positive-excess at **2× cost** in the holdout.
4. **Not an isolated peak** — at least one adjacent grid cell (±1 on H or the
   reaction cap) also clears (1)–(3). A lone surviving cell is a description, not
   a strategy.
DSR computed with the cross-sectional `variance_of_sr` convention (the fixed
one), n_trials = 18.

## Bias checklist (all 8, per shared.lab.BIAS_CHECKLIST)

1. **survivorship** — Sharadar SEP includes delisted/acquired/bankrupt; entries
   key to the final ticker via `resolve_ticker`. Known hole: deep-OTC/pink names
   outside SEP's exchange history (disclosed in the coverage_note, same as the
   insider-cluster replay).
2. **look_ahead** — SUE uses SF1 `datekey` (filing date), reaction uses SEP
   closes around that date; entry is the NEXT trading day. No datum precedes its
   public availability; restated financials are avoided by using as-reported ARQ.
3. **selection** — the event population is EVERY SF1 quarterly filing in the PIT
   universe with a computable SUE and a verifiable reaction bar, not hand-picked
   beats. Defined here, before results.
4. **multiple_testing** — 18 pre-committed cells; `hypotheses_ever` moves
   173→191. No post-hoc cells. Prior Achilles/house tries counted in the ledger.
5. **overfitting** — 3 fixed rules + 3 gridded knobs over thousands of events;
   the non-isolated-peak rule (success #4) is the explicit overfitting guard.
6. **costs_liquidity** — per-bucket cost model + mandatory 2× survival; MICRO
   band is the acid test — a thin-name drift can be entirely inside the spread,
   and if it only survives at 1× it is not deployable at Achilles' size.
7. **regime** — in-sample spans dot-com + GFC; holdout spans 2016–2025. The
   edge must clear BOTH; the house has already watched one warm-vintage +41%
   collapse to −1% out of regime (Nemesis), so a single-regime pass fails.
8. **small_n** — report raw n, the shrunk mean excess, and the forward-test n
   needed before a live sizing change. A SUPPORTED cell still requires ≥20 graded
   PAPER forward trades before it changes live Achilles.

## Pre-committed decision rule (the whole point — no wiggle room)

- **SUPPORTED** (≥1 non-isolated cell clears all four thresholds): Achilles' PEAD
  edge is real in that (H, cap, universe) configuration. Adopt the winning
  parameters (likely: narrow the universe toward MICRO/neglect, set H and the
  reaction cap to the surviving cell), keep him live, and size with confidence
  once the forward test confirms.
- **REFUTED** (no cell survives, OR only the SHORT side does as the replay hinted):
  the long-only PEAD-drift spine does not clear the gauntlet. Then, in order of
  preference: (a) **narrow** Achilles to the exact sub-population that DID survive
  if one exists but fails the non-isolated rule (a weaker keep); (b) **reframe**
  him the way Oracle was reframed — his measured edge becomes the *ban* (don't buy
  sold beats) + the confirming signals as the thesis, not the drift; or (c)
  **retire** him and return the sleeve, per the Delphi/Midas precedent. The
  operator makes the call on the numbers, as with Delphi.
- **INCONCLUSIVE** (thin/degenerate n in the surviving band): treat as REFUTED for
  the live spine; the burden is on the edge to show up, not on us to keep looking.

No Achilles backtest may ever be cited as evidence FOR the strategy except a
SUPPORTED cell here, forward-confirmed. PAPER ONLY — a SUPPORTED cell is citable
in the runbook, never an autopilot sizing change without ≥20 graded forward trades.
