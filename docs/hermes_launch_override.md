# Hermes — live merger-arb A/B, conscious override (operator decision, 2026-07-04)

## The decision

The operator directed a live-money **merger-arbitrage** engine — **Hermes**
(god of commerce, negotiation, and crossing boundaries) — built as an A/B that
puts real capital on the LLM's judgment and measures, in dollars, what that
judgment is worth. This is the return/convexity pivot's first engine
(docs/return_convexity_pivot_2026-07-04.md) and the house's first strategy
chosen for being BOTH high-return-convex AND uniquely LLM-advantaged.

This is a **conscious override**, the Plutus/Proteus precedent: real money on a
strategy with NO in-house backtest — the honest reason is stated below and the
risk is bounded by design, not by prior validation.

## The A/B — Arm A is LLM, live, real money (operator directive)

Inverted from the Plutus buyback A/B (there both arms were paper). Here:

- **Arm A — LIVE, REAL MONEY, LLM-judged (the active strategy).** For each
  announced cash-merger target, the LLM reads the deal's BREAK RISK — regulatory
  (antitrust/CFIUS), financing conditions, MAC clauses, target-board/shareholder
  hurdles, timeline, spread-vs-risk — and decides which spreads to harvest and
  which to avoid. Only LLM-approved deals get real capital.
- **Arm B — PAPER, mechanical control (takes ALL detected deals).** Every
  detected cash deal, no judgment, no filter.
- **LLM-lift = A − B**, in real-vs-paper return AND convexity (`floor`,
  `right_tail_share`, expectancy). This is the quantified answer to "does the
  LLM's deal-break reading add money?" — the whole experiment. If A does not
  beat B over a real sample, the LLM adds nothing here and the engine reverts to
  mechanical (or retires).

The LLM's job — reading unstructured deal documents to judge one specific
situation's asymmetry — is exactly where its edge is unique and a screen is
blind. Merger-arb scores 4/4 on the LLM-benefit heuristic (unstructured text,
specific-situation judgment, prunes an over-productive filter, asymmetric
payoff).

## What Hermes trades

Small/mid-cap **cash** merger targets (the capacity-inverted subset below
arbitrage-fund minimums — the special-situations sweep's strongest gate
profile: G2 signed merger agreement, G4 contractual terminal = the offer price,
G3 capacity-inverted, G5 30-80 small-cap cash deals/yr). Long the target
post-announcement below the deal price; hold to resolution. **Cash deals only**
(stock/mixed need an acquirer short the broker can't do). Completion → cash-out
near the offer (small spread win + occasional topping bid). Break → bounded
loss. This is the convex shape: many small bounded wins, rare bounded losses,
occasional right-tail bonus.

## The honest caveats (unsoftened)

- **NO in-house backtest.** A clean historical backtest is completion-biased —
  deal breaks don't delist, so scanning delisted-flatline names sees only
  winners and hides the floor. We go live on the STRONG ACADEMIC PRIOR
  (Mitchell-Pulvino 2001, Baker-Savasoglu 2002) + a bounded contractual floor,
  NOT a house backtest. The completion-only probe (`run_mergerarb_probe.py`) is
  a labeled lower-bound sanity read of spread magnitude + deal count only.
- **The edge is decayed and thin net of cost** (Jetley-Ji 2010: spreads shrank
  >400bp since 2002). The residual lives in the small/illiquid subset below
  arb-fund minimums and in the deal-break-risk premium (the negative skew is
  compensation, not free money). Real fills + spread + slippage bite hardest
  exactly there — the net-of-cost question is the experiment.
- **This is the LLM's audition on real money.** If the LLM can't beat the
  mechanical arm at avoiding breaks, the whole "gods' unique power" thesis takes
  a real, measured hit here. That is the point of putting money on it.

## Risk controls (hard — this is why real money here isn't reckless)

- **Bounded contractual floor per deal:** the downside is the break (~−15 to
  −25%), NOT −80%. Merger-arb's ruin risk is low BECAUSE the floor is bounded
  and ~90% of announced cash deals close.
- **Small per-deal sizing + diversification:** never all-in one deal; spread
  across several live deals so one break is survivable (target book-level worst
  ≤ ~−12%, the convexity bar). No single deal above a hard % cap.
- **Break-signature exit:** if a held name gaps DOWN through a stop or the LLM
  flags a break event (regulatory block, financing fail), exit immediately —
  don't ride a broken deal to zero.
- **Standard live gates:** `KILL_SWITCH`, `is_live("hermes")` (env
  `HERMES_LIVE` defaults FALSE — operator arms it), `pre_trade_check`,
  `already_placed_today`, journaled entry before any order.
- **Funding:** small dedicated sleeve (operator sets the amount at arming); does
  not touch other gods' capital.

## The checkpoint

At N graded deals (suggest 20) or a date, the operator revisits on the metric
that matters: **LLM-lift (Arm A − Arm B).** Positive and material → the LLM's
deal-reading is real alpha and Hermes earns more capital. Zero or negative →
the LLM adds nothing over mechanical here; revert to mechanical or retire. Plus
the absolute question: did Arm A beat cash/SPY net of cost at all. Either way
the ledger row is written: launched live, unbacktested, on a conscious override,
to measure whether an LLM can read a deal better than a screen.
