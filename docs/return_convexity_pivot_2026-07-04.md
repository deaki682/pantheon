# The Return / Convexity Pivot (2026-07-04)

Operator refocus: **returns are the goal.** This document records why the
factor-research path caps near the index, the measurement that proves it, and
the new objective function all return-oriented (convex) engines are graded on.

## The return equation (why the search was pointed at the smallest lever)

Total dollar return decomposes into levers, ranked by impact:
1. **Capital / scale** — the largest multiplier; operator decision.
2. **Beta** — most of any strategy's return is just equity exposure.
3. **Concentration** — a small book's biggest available lever.
4. **Convexity / right tail** — where dollar growth on small capital comes from.
5. **Leverage** — forbidden here (long-only, no margin/options).
6. **Alpha (selection)** — what the gauntlet hunts; real but scarce and tiny.

The gauntlet optimized **#6 with maximum rigor while ignoring #1–#4**, which
move returns 10–100× more. Worse, it *selected for* the property that caps
returns: diversified, robust, low-tail edges — the mathematical opposite of
convexity.

## The proof (convexity re-score of the factor survivors, holdout window)

`shared.gauntlet.convexity_stats` run on the existing supported baskets, at two
levels — per **name** (the raw material held) vs per **quarter basket** (what
the strategy delivered):

| Strategy | per-NAME | per-QUARTER basket |
|---|---|---|
| cash_op N50 LARGE | floor −49%, max +135%, right_tail_share 0.44 | floor −12%, max +26%, tail 0.32 |
| gross-prof N50 LARGE | floor −69%, max +123%, tail 0.44 | floor −10%, max +21%, tail 0.35 |
| cash_op N50 SMALL | floor −80%, **max +280%**, tail 0.50 | floor −12%, max +41%, tail 0.40 |

**The finding:** the winners were in the book — individual holdings ran +135%,
and +280% in small-caps, in a single quarter. Equal-weighting 50 of them
**averaged the convexity out of existence**: a +280% name was 1/50th of the
book, so the basket's best quarter was +41% and it typically delivered a smooth
~+4%/quarter. The factor path took convex raw material and *deliberately
destroyed the convexity to buy robustness.* That is the "ties SPY" result,
explained mechanically. The old tests were correct; they optimized the wrong
objective for a return goal.

## The cost of the fix, and therefore the mandate

Concentration recovers the upside (the basket max moves back toward the
+135%/+280% name level) — **but it also recovers the floor** (−49% to −80% per
name). So the entire job of a convex engine is:

> **preserve the large right tail while bounding the floor.**

A concentrated cash_op book would give the +280% upside AND the −80% floor —
that is gambling, not a return engine. The edge is finding structures where the
floor is bounded independently of the upside:
- **Merger-arb (cash):** floor = the deal-break, contractually ~−15 to −20%, NOT
  −80%; upside = the spread + occasional topping bid. Bounded floor by construction.
- **Post-emergence equity:** floor ≈ 0 per name, occasional +100%+; sample many
  to catch the tail. Convexity from the right tail, not a bounded single bet.

## The new objective function (pre-committed bar for convex engines)

Return-oriented engines are graded with `convexity_stats` on their per-trade
(per-event) outcomes, NOT on mean-excess-vs-benchmark. To be worth
concentrating capital on, a convex engine must clear the bar the diversified
factor baskets already set:

- **`right_tail_share` > ~0.35** — MORE tail than a factor basket (else
  concentration bought nothing but variance).
- **`floor` no worse than ~−12%** at the STRATEGY level (per-event floor may be
  larger, but position sizing must keep the book-level worst bet survivable) —
  i.e., a bounded downside the diversified basket also had.
- **positive `expectancy`** net of cost, and a documented `payoff_ratio`.
- Survivability first: a strategy with a great expectancy and an unbounded floor
  is refused — ruin risk voids compounding.

The discipline does not go away; it is repointed from "is this thin edge
statistically real" to "is the downside survivable and the upside large."

## Deployment map (roles, not a bake-off)

- **Plutus / factor sleeves** = the disciplined **beta core** (most capital,
  ~market return, thin quality tilt). NOT the return engine — correctly demoted.
- **Convex satellite** = merger-arb + post-emergence (researched, disciplined,
  bounded-floor convexity) and **Proteus** (discretionary concentrated
  convexity across the whole market). This is where dollars are made.
- **Capital is the payoff:** the disciplined search is an audition; when one
  convex engine proves itself forward, the return move is to fund it, not to
  find ten more 1% factor edges.

## Next builds

1. **Merger-arb convex engine** — cleanest bounded floor, gauntlet-testable on
   SEP bars (cash-deal price signature: gap → flatline-near-ceiling → delist).
   Graded on the convexity bar above. First prototype of the return program.
2. **Post-emergence equity** — biggest right tails; EDGAR population build.
3. Carry the `floor` / `right_tail_share` bar into both preregs as the
   pre-committed success metric.
