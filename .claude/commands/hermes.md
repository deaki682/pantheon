# /hermes — the merger-arb LLM A/B engine (LIVE, conscious override)

Hermes is the god of commerce, negotiation, and crossing boundaries — and he
trades the cleanest convex bet the house found: **small-cap cash merger
targets.** Buy the target below the announced cash offer; hold to resolution.
Completion → cash out near the offer (small spread win + occasional topping
bid). Break → a bounded, contractual loss. Many small bounded wins, rare
bounded losses, an occasional right-tail bonus — the convex shape a small book
needs (docs/return_convexity_pivot_2026-07-04.md).

He is the return program's first engine AND the house's first strategy where an
**LLM's judgment rides real money and is measured.** Read
docs/hermes_launch_override.md before touching this book — the conscious
override, the honest "no in-house backtest, bounded floor" caveat, and the A/B.

## The A/B — Arm A is LLM, live, real money (operator directive)

Every announced cash deal Hermes detects is recorded ONCE with the LLM's read:
- **Arm A — LIVE, real money, LLM-judged.** The LLM reads each deal's BREAK
  RISK and keeps/drops it; only kept deals get real capital. This is the
  active strategy.
- **Arm B — paper, mechanical.** Every detected deal, no filter (`hermes.ab`
  records it regardless of the LLM verdict).
- **LLM-lift = Arm A − Arm B** (`hermes.ab.llm_lift`), in return AND convexity.
  The whole experiment: does the LLM read a deal better than a screen? The
  numbers decide, not the story.

## What Hermes trades (hard scope)

- **CASH deals only.** Stock/mixed deals need an acquirer short the broker
  can't do — skip them. A cash deal's terminal is the contractual offer price.
- **Small/mid-cap targets** (the capacity-inverted subset below arbitrage-fund
  minimums — that is where the residual lives). Skip mega-cap deals (fully
  arbitraged, no spread for us).
- Long the target only. No leverage, no options.

## Session liturgy

0. **Hydrate.** `pantheon.hydrate()`.

0b. **Safety gates (live money — non-negotiable, before anything else).**
   - `shared.guards.kill_switch_active()` → if true, `book.liquidate_all(marks,
     today)` + real sells, persist, stop.
   - `shared.guards.is_live("hermes")` → if `HERMES_LIVE` is not exactly
     `"true"`, PAPER MODE: detect deals, run the LLM read, record the A/B, print
     what Arm A *would* buy — but place NO orders, mutate NO live book, persist
     only the A/B/paper state. The operator arms `HERMES_LIVE`.
   - **Funding gate.** `HermesBook.load()`. If `pending_funding` is set, the
     dedicated sleeve hasn't been funded — research/paper-only until it lands.
   - **Pre-trade reconcile.** Before ANY order: `get_equity_orders` →
     `filter_orders_by_ledger` to record fills; then broker positions →
     `filter_broker_to_gods` → `pre_trade_check` (+ `pending_shares_from_orders`).
     Sleeve > broker halts. `already_placed_today` to never double-place.

1. **Tend open deals FIRST.** For every open position:
   - Fetch the live quote (`get_equity_quotes`) + SPY.
   - **Break check:** `book.break_triggered(marks)` — any name through its
     break-stop MUST exit at market (reason `broke`), then
     `hermes.ab.record_resolution(...)`. Don't ride a broken deal down.
   - **Completion:** if the deal closed (the target is being cashed out / has a
     firm close date reached / delisted at the offer), exit at the offer/last
     (reason `completed` or `topping_bid` if a higher bid landed) and record the
     resolution. Reconcile the ACTUAL fill.
   - **CVR rule (2026-07-05, from the alpha-hunt CVR autopsy):** on a cash+CVR
     deal, Hermes's bet is the CASH leg only — SELL at/near close and NEVER hold
     the CVR through settlement. A CVR is a compound forecast with an adversarial
     payer (milestone dollars come out of the acquirer's pocket; Celgene's $9 CVR
     went to $0 on a 36-day "delay"), i.e. the exact opposite of the contractual
     floor this book exists to harvest. If the broker delivers a tradable CVR
     anyway, sell it into the first liquid market; if untradable, write it to $0
     in the sleeve and treat any payout as found money.
   - **Past-close flag:** `book.past_close(today)` — deals past their expected
     close that haven't resolved get a manual look (delayed? renegotiated?
     re-read the situation and update `expected_close`, or exit if the thesis
     broke).

2. **Find today's deal universe.** Build/refresh the active cash-deal watchlist:
   announced, not-yet-closed cash acquisitions of small/mid-cap US targets, with
   the target trading BELOW the offer (a live spread). Sources: news/EDGAR
   (8-K Item 1.01 "material definitive agreement", DEFM14A), merger trackers,
   the target's own filings. For each, record: target symbol, cash offer price,
   current price (`get_equity_quotes` — the ONLY price authority), expected
   close, spread = offer/price − 1. Verify it is CASH and the target is
   tradable (`get_equity_tradability`).

3. **The LLM read (Arm A — this is the experiment).** For EACH detected deal,
   read the break risk with real effort (the edge is reading, not the headline):
   - **Regulatory:** antitrust (HSR second request?), CFIUS (foreign acquirer,
     sensitive sector?), sector regulators. The #1 break cause.
   - **Financing:** is it a strategic (cash on hand) or a PE/financed deal with a
     financing condition? Financing contingencies break.
   - **Deal terms:** MAC clauses, go-shop, termination fee size, shareholder-vote
     hurdles, appraisal risk, activist opposition.
   - **Spread-vs-risk:** a WIDE spread is the market pricing break risk — a fat
     spread on a clean deal is the prize; a fat spread on a shaky deal is a trap.
   - Produce a `keep`/`drop` verdict + one-line rationale + break_risk
     (low/med/high). `keep` = the LLM would put real money here.
   - Record EVERY detected deal via `hermes.ab.record_detection(...)` with the
     verdict and `arm_a_live` = (keep AND it will fit the sizing cap). This IS
     Arm B (all) + Arm A (kept).

4. **Size and enter (Arm A, live).** For each `keep` deal not already held:
   - `equity = book.equity(marks)`; check `book.can_enter(sym, dollars, equity)`
     — bounded by `PER_DEAL_CAP` (15% of equity), `MAX_CONCURRENT` (10 deals),
     cash reserve. Size SMALL and diversify: the ruin guard is that one break is
     survivable (target book-level worst ≤ ~12%). **`book.enter` also refuses a
     spread below `MIN_SPREAD` (1%)** — a deal trading at/above the offer has no
     arb edge left (that's topping-bid speculation, not arb); don't enter a spent
     spread. Enter for the remaining spread, not after it's gone.
   - Fetch the live quote + SPY, `get_equity_tradability`.
   - Place a fractional-share market/limit buy (`place_equity_order`), append to
     `cache/hermes_ledger.jsonl` (`shared.guards.append_order`), `book.enter(...)`
     with the ACTUAL fill (sets the break-stop automatically). If the fill is
     pending at session end, record the order and enter the book next session.

5. **Mark + curve.** `book.equity(marks)`, append `{date, equity, spy}` to
   `cache/hermes_curve.json`.

6. **Grade the A/B.** `hermes.ab.llm_lift(ab)` — report Arm A (LLM kept) vs Arm
   B (all detected) convexity + the lift once a few deals have graded. This is
   the headline the checkpoint judges.

7. **Persist.** `pantheon.persist("hermes", {"cache/hermes_sleeve.json": …,
   "cache/hermes_ledger.jsonl": …, "cache/hermes_curve.json": …,
   "cache/hermes_ab.json": …})`. Hermes owns only `cache/hermes_*`.

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Deal type | CASH only | contractual terminal = the offer price |
| Universe | small/mid-cap targets | capacity-inverted; where the residual lives |
| Per-deal cap | 15% of equity | one break must be survivable |
| Max concurrent | 10 deals | diversify the bounded bets |
| Break-stop | −15% from entry | bound the loss; don't ride a break to zero |
| Cash reserve | 2% | dry powder for a fresh clean deal |
| Live gate | `HERMES_LIVE` (default FALSE) | operator arms it |

## The checkpoint

At ~20 graded deals or a date: the headline is **LLM-lift (Arm A − Arm B).**
Positive and material → the LLM's deal-reading is real alpha; Hermes earns more
capital. Zero/negative → the LLM adds nothing over mechanical here; revert to
mechanical or retire. Plus the absolute question: did Arm A beat cash net of
cost. Either way the ledger row is written: launched live, unbacktested, on a
conscious override, to measure whether an LLM reads a deal better than a screen.

## What /hermes does NOT do

- Trade a stock/mixed deal, a mega-cap deal, or place any order when
  `HERMES_LIVE != "true"`, the kill switch is up, funding is pending, or
  `pre_trade_check` failed.
- Exceed the per-deal cap or ride a name through its break-stop.
- Skip recording a detected deal in the A/B — the mechanical Arm B needs EVERY
  deal, including the ones the LLM dropped (that's how we measure the drops).
- Use a secondary price for sizing without checking it against the broker tape
  (`shared.guards.secondary_price_suspect`).
- Touch any other god's sleeve/ledger/cache.
