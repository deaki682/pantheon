# Lab prereg — `thematic_etf_firesale_reversal` (COMMITTED BEFORE DATA)

**Sponsor:** lab (alpha-hunt full-sweep survivor #18, 2026-07-05). **Committed before
any data is touched.** PAPER ONLY. This is the strongest of the two "forced-flow
UNDERLYING side" survivors — the never-tested seam the 14-domain sweep surfaced.

## Hypothesis

When a **thematic / niche equity ETF shrinks** (sustained net redemptions), its
Authorized Participants must sell the fund's underlying basket into the open market.
For constituents where the **ETF's position is large relative to the stock's own
average daily volume (ADV)**, that forced selling pushes price *below* fundamental
value, and the dislocation **reverts** once the outflow pressure exhausts. Going
long the most-pressured, most-illiquid orphaned constituents at exhaustion — measured
against a size-and-sector-matched benchmark — earns a positive reversal.

## Mechanism (the causal chain, why a forced seller pays you)

An ETF redemption is non-discretionary: when shares are redeemed, the AP receives the
in-kind basket and unwinds it, and the fund's holdings shrink by mandate — the sale is
bound by the fund's replication obligation, not by anyone's view of value. In a *broad*
ETF the per-name flow is a drop in each constituent's ocean and any dislocation is
instantly arbitraged (this is the Greenwood-Sammon offset that killed the S&P
index-effect). In a *thematic/niche* ETF the same dollar of outflow lands on a handful
of small, illiquid names the fund owns in size — often the ETF holds multiples of a
constituent's daily volume — so the forced sale moves price and no deep-pocketed
arbitrageur can cheaply absorb it (capacity-inverted: the edge exists *because* it is
too small and illiquid for large capital). The 2024-26 literature documents the inflow
side directly (Ponzi Funds, arXiv 2405.12768: ~20x-ADV positions, >40% flow-return
correlation, ~-6%/yr specialized-ETF constituent alpha, reversal concentrated in the
most-illiquid names). This prereg tests the OUTFLOW/reversal symmetry long-only.

## Falsifiable claim

Long a basket of the most forced-sold (high fund-flow-pressure ÷ ADV), most-illiquid
constituents of shrinking thematic ETFs, entered at outflow-exhaustion and held to a
fixed horizon, earns POSITIVE excess return vs a size-and-sector-matched equal-weight
benchmark, in-sample AND holdout, net of realistic microcap round-trip cost. If the
excess is ≤0 net of cost, or the small/illiquid subset is the WORST subset (the
spinoff_orphans/ipo_lockup failure mode), the hypothesis is false.

## What makes it pass the gates (honest reads, incl. the failing one)

- **G1 (not price):** PASS. The signal is a *flow state* — net fund redemption ×
  constituent weight ÷ constituent ADV — observed from fund shares-outstanding and
  holdings, not a price forecast.
- **G2 (named forced counterparty + binding document):** PASS-with-caveat. The redeeming
  AP unwinding the in-kind basket is the forced seller; the binding document is the
  fund's creation/redemption basket + prospectus replication mandate. Caveat: the
  open-market sale is one step removed from the redemption (AP intermediates), and the
  offset that kills the index-effect genuinely cannot reach this illiquid tail.
- **G3 (capacity-inversion):** STRONG PASS — the load-bearing gate. The effect lives
  ONLY where fund position ≫ constituent ADV; uneconomic for large capital; a $19k book
  is the ideal size. Ponzi-Funds confirms reversal strongest in the most-illiquid names.
- **G4 (contractual/mechanical payoff):** **FAIL — the honest weak point.** There is no
  contract pulling price back; "price pressure reverts" is a mean-reversion FORECAST.
  This is the exact shape of two TERMINAL house refutations — `ipo_lockup_reversion`
  (−10.4%) and `spinoff_orphans` (−9.3%, the small tail the WORST subset). The whole
  test is built to confront that headwind head-on (see the size-matched benchmark guard
  and the pre-committed wrong-sign kill).
- **G5 (power ≥20 events/12mo):** PLAUSIBLE, unverified — to be confirmed in the build.

## Test design (FROZEN before data)

- **Universe (defined blind):** all US-listed **thematic / sector / niche equity** ETFs
  that existed at ANY point 2015-01-01 → 2025-12-31 with a stated non-broad theme and
  ≥15 equity constituents. **Survivorship-critical:** INCLUDE ETFs that later closed or
  liquidated (a closing thematic ETF is the purest forced-seller event). EXCLUDE
  broad-market (SPY/IVV/VTI/IWM/QQQ-class), leveraged/inverse, and bond/commodity funds.
- **Flow signal (per ETF, daily):** net creation/redemption = Δ(shares-outstanding) ×
  NAV. Redemption pressure on constituent *i* = (net redemption $ × weight_i) ÷ ADV_i
  (dollar). "Forced-sold" = sustained (multi-day) negative pressure in the top decile.
- **Entry:** LONG-ONLY, T+1 after outflow pressure EXHAUSTS (pressure crosses back above
  a frozen threshold after a sustained-negative run) — a flow-state trigger, NOT a
  calendar date. Equal-weight the qualifying constituents.
- **Horizons:** {21, 63, 126} trading days; primary 63d.
- **Benchmark — THE decisive guard:** excess vs a **size-AND-sector-matched
  equal-weight** basket (reuse the achilles/gauntlet SMALL/MICRO bucket benchmark,
  sector-refined). Raw return is explicitly NOT the metric — otherwise we merely
  re-discover that illiquid microcaps drift down (the spinoff_orphans trap).
- **Costs:** realistic microcap round-trip spreads baked in (50bps-several %), + 2× stress.
- **Regime split:** in-sample ≤2019-12-31 / holdout 2020-2025.

## Data reality (the gating build — disclosed like call_evasion's transcripts)

The signal needs, survivorship-free: (1) daily ETF **shares-outstanding** (to compute
net flow) and (2) constituent **weights**. Shares-outstanding history is obtainable;
full *daily historical holdings for CLOSED ETFs* is the hard part (issuers publish
current baskets; delisted-fund holdings archives are scarce). First-pass build plan:
periodic holdings snapshots (issuer files / N-PORT quarterly) × daily shares-outstanding
flow × Sharadar SEP constituent bars (delisting-inclusive) × ADV. If a
survivorship-complete panel cannot be built, the slug **stays `preregistered`** (NOT
recorded refuted — never burn a slug on inadequate data; the `post_bk_emergence`
precedent).

## Success thresholds (committed before data)

Supported iff the long forced-sold-constituent basket earns **positive excess vs the
size-and-sector-matched EW benchmark at 63d, in-sample AND holdout, net of realistic
microcap cost + 2× stress**, AND the effect is monotone in pressure-÷-ADV (more-pressured
= more reversal), AND the small/illiquid subset is NOT the worst subset. ≥20 tradable
events/12mo for G5. Anything less → the ratchet's honest verdict; a clean pass earns a
≥20-trade paper forward test, never live autopilot.

## Pre-committed consequence

- Positive, monotone, holdout + net-of-cost, small-subset-not-worst → SUPPORTED; open
  the forward paper test; candidate component of the `event_diversifier_sleeve` (#15).
- Excess ≤0 net of cost, OR non-monotone, OR small/illiquid subset worst (the
  spinoff_orphans shape) → **REFUTED (terminal)**; the "buy the forced-sold microcap
  orphan and harvest reversion" family is then dead across all three tested forms
  (spinoff, lockup, ETF-firesale) and closes.
- Data un-buildable survivorship-free → stays `preregistered`, documented, not refuted.
- Ledger row either way. Expected-value honest: G4 fails and two neighbors died in this
  exact shape — refutation is the base-rate outcome and a *valued* result.

## Bias checklist (addressed before data)

- **survivorship:** dead/closed ETFs and delisted constituents INCLUDED (Sharadar SEP
  delisting-inclusive; the closing-ETF event is the core case, so excluding it would
  invert the study).
- **look_ahead:** flow signal uses only shares-outstanding + holdings known as of each
  date; entry T+1; forward returns strictly post-entry.
- **selection:** universe defined blind by theme + constituent-count rule, not by
  outcome; no cherry-picking of "good" ETFs.
- **multiple_testing:** one slug, ticks `hypotheses_ever`; horizons {21,63,126} pre-declared
  with 63d primary (not max-picked post hoc).
- **regime:** in-sample ≤2019 / holdout 2020-25 spans COVID fire-sales and the 2022 rate
  shock — both heavy-outflow regimes, a fair test of the mechanism.
- **costs_liquidity:** realistic microcap spreads (the edge lives where costs are HIGHEST)
  + 2× stress; net-of-cost is the binding criterion, not gross.
- **small_n:** power (events/12mo) is a pre-committed kill gate (G5 <20 → fail); the
  forward test requires ≥20 graded trades before any validation claim.
