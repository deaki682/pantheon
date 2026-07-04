# Plutus — live-launch conscious override (operator decision, 2026-07-04)

## The decision

The operator has directed that **Plutus go LIVE with real money**, funded by
Delphi's retiring ~$2,000 large-cap sleeve, running the
`gauntlet_v2_fundamentals` net-issuance-low N50 LARGE strategy.

**The 2026-07-06 session is a transition of power, not a launch-day buy**
(operator clarification, 2026-07-04). Monday the agentic portfolio is
*rearranged*: Delphi's positions are liquidated to cash and swept into
Plutus's sleeve to create the buying power that funds the new regime. Those
sells settle T+1, so Plutus's first quarterly rebalance — his actual first
purchase — follows once the swept capital has settled (Tuesday+), gated
mechanically by his settled-cash check. The launch is the moment he first
holds the basket, which the transition makes possible; it is deliberately
*not* a scramble to buy at Monday's open with unsettled proceeds.

This is a **conscious override**, exactly the Proteus precedent: the
operator is deliberately spending the risk budget the gates exist to
protect. Two house laws are being overridden IN WRITING, knowingly:

1. **"No live money on an unvalidated backtest."** Plutus's strategy is
   SUPPORTED (in-sample DSR + two-regime holdout + 2× cost + cliff), but
   has **ZERO forward grades**. The forward test
   (`cache/lab_forward_net_issuance.json`) started 2026-07-04 and will not
   reach its ≥20-quarter bar for ~5 years. Live money precedes validation.
2. **"The lab is the only door — no god scaffolding without a validated
   slug."** net-issuance is supported, not validated; scaffolding Plutus
   now is early by this rule. Overridden.

## The honest caveats (on the record, unsoftened)

- **It only ties SPY.** Over its own favorable holdout decade (2016-2025),
  the validated equal-weight version returned +14.4%/yr vs SPY's +14.3% —
  a $2k stake beat SPY by ~$220 over ten years, with deeper drawdowns
  (−38% to −41%) and multi-year stretches trailing SPY. It beats its
  equal-weight *benchmark* by ~2.9-3.7%/yr, but SPY is the real
  alternative, and there it is a near-tie.
- **It is a famous, decay-prone anomaly.** Net issuance is in every factor
  fund; McLean-Pontiff measured ~58% post-publication decay. Historical
  survival is not a guarantee of live harvestability.
- **Multiple-testing:** house counter 141 hypotheses ever; several false
  positives are statistically expected. The two-regime OOS survival is why
  it cleared the bar to be a candidate — not proof it is live alpha.
- **Cap-weight and forced-flow alternatives were tested and rejected**
  (cap-weight is a regime bet; index-effect is dead). Equal-weight
  net-issuance is genuinely the best deployable candidate the house has —
  which is a statement about how rare edges are, not how strong this one is.

## What Plutus trades — DELUXE AMENDMENT (2026-07-04, operator directive)

The original launch spec was the pure validated factor (net-issuance-low N50
LARGE equal-weight). The operator then directed the **deluxe package, "even
if it's risky"** — three additions stacked on that spine, all selected in
writing by the operator after seeing the honest return math (they widen both
tails and only *maybe* shift the mean):

1. **Second factor — gross-profitability.** The OTHER gauntlet survivor,
   blended by equal factor rank with net-issuance. The blend itself was never
   gauntleted (a reasonable combination of two separately-supported survivors).
2. **LLM quality overlay, LIVE.** The Lens-B arm-L judgment now steers the
   real book: each quarter the LLM prunes the ~50 composite candidates to the
   healthy, cheap buybacks (~24–40 kept) and assigns conviction. **Zero graded
   rounds** — this is the least validated piece, on real money.
3. **Conviction / cap-weight tilt.** Off equal-weight toward a cap-lean
   (`cap_blend` 0.5) and LLM conviction, chasing SPY (which is cap-weighted)
   rather than tying it. Cap-weight is a MEASURED REGIME BET; this is the lever
   most likely to just add drawdown.

**Honest status of the deluxe stack: none of the three is forward-validated.**
This is a larger override than the launch itself. It is justified only by the
operator's explicit, informed choice — and bounded by two disciplines that do
NOT bend:

- **The pure control is always tracked.** `quarterly_basket` (the frozen N50
  EW spec) and the paper forward test stay pure. Every live rebalance records
  what the control would have held, and grading compares live deluxe
  excess-vs-SPY to the control's. If deluxe does not beat pure over a real
  sample, the additions are noise and get cut — that is the deal.
- **The LLM A/B keeps running on paper** (`cache/lab_buyback_quality_ab.json`,
  arms R/M/L) as the independent grader of the overlay piece.

## Risk controls (hard, non-negotiable)

- **40% drawdown circuit breaker** from peak equity → liquidate + halt. (The
  deluxe concentration makes this MORE likely to trip; that is understood.)
- Per-name cap ~6% (floats to ~2× equal on small baskets) — the tilt may
  concentrate, but no single name runs away.
- ~24–40 names after the LLM prune — more concentrated than the pure 50, by
  design; the diversification a thin factor needs is partly traded for the
  conviction bet.
- Quarterly rebalance only — no intra-quarter churn (net-issuance is a
  slow signal; the churn that sank Delphi is structurally absent).
- Standard live-money gates: `KILL_SWITCH`, `is_live("plutus")`,
  `pre_trade_check` (sleeve>broker halts), `already_placed_today`.
- `PLUTUS_LIVE` defaults FALSE. The operator arms it. Once armed and funded
  by the transition sweep, Plutus's first settled-cash rebalance is the
  launch — no order fires before the swept capital settles.

## The checkpoint (this override is not permanent license)

Plutus is graded like every god. At the forward test's first meaningful
readings (4-8 graded quarters) OR a 40% breaker, the operator revisits on
TWO questions, not one:
1. **Does Plutus beat SPY?** Negative live excess-vs-SPY retires him to the
   ledger, capital to the treasury — the same deal Proteus and Delphi got.
2. **Did the deluxe stack earn its risk?** Live deluxe excess vs the pure
   control's excess. If deluxe trails the pure N50 spec, the LLM + blend +
   tilt are noise and get cut back toward the pure factor — even if Plutus is
   kept. The stack has to prove it added mean, not just variance.

The ledger row will say plainly: launched live, unvalidated, deluxe stack on
a conscious operator override — and whether the additions helped or hurt.
