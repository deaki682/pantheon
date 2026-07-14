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

0a. **PAUSE gate (check FIRST — audit 2026-07-10: the freeze must hold even
   when /hermes is invoked directly, not via Zeus).** `shared.guards.is_paused("hermes")`
   → a pause freezes DEPLOYMENT, never abandons live money. While paused:
   - **TEND-ONLY:** reconcile broker fills into the sleeve, mark the book, and
     check every open deal's break-stop / completion / deal-break news — a
     triggered break-stop or a completed deal STILL EXECUTES (those are
     promises). Persist what changed.
   - Do NOT detect new deals, run new LLM reads, enter anything, or top up.
   - Print the pause `reason` and end. Only the operator lifts the freeze
     (delete/flip `cache/hermes_paused.json`).

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
   - **Shared-pool buying-power gate (2026-07-14, house-wide).** You are the
     only god that BUYS on opportunity without a self-funding sell, so this is
     yours to watch most. The account is ONE cash pool shared by every god; your
     sleeve `cash` ($659.56 on 2026-07-14) can overstate what is actually
     spendable (real account buying power that day was $237). Before entering a
     NEW deal, read the LIVE broker buying power (`get_portfolio` →
     `buying_power`, or `get_accounts`) and cap the order at
     `shared.guards.spendable_buying_power(broker_bp)` — never size from sleeve
     cash alone. Over-deploying the shared pool is exactly what froze you on
     2026-07-07. (The operator sold ~$930 of a personal holding on 2026-07-14 to
     back the gods' dry powder; the pool is larger now but still shared.)

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

2. **Find the COMPLETE deal universe (systematic — not a session watchlist).**
   Run `python3 run_hermes_sourcing.py` (→ `cache/hermes_deal_universe.json`). It
   sweeps EDGAR's daily form indexes for the TARGET's own merger/tender paper
   (DEFM14A / PREM14A / DEFM14C / PREM14C / SC 14D9) over a trailing ~120-day
   window — the complete population, no keyword, keyed to the target CIK. This
   REPLACES the old ad-hoc "build a watchlist from news/EDGAR" step, which was a
   sourcing SLIVER: it surfaced only what a run happened to find, and a missed
   deal is both an un-tradable loss AND a biased denominator that makes the Arm-A/B
   lift lie (Arm B = "every DETECTED deal" is only an honest control if detected ==
   all). `hermes.sourcing.new_candidates(...)` drops deals already tracked. The
   enumerator does NOT decide cash-vs-stock or price — every candidate carries
   `requires_read=True`; that is Stage 3's job. For each candidate you take
   forward, record: target symbol, cash offer price, current price
   (`get_equity_quotes` — the ONLY price authority), expected close,
   spread = offer/price − 1. Verify it is CASH and the target is tradable
   (`get_equity_tradability`). (Known gap the sweep discloses: a deal whose only
   paper so far is an 8-K merger agreement with no proxy/14D-9 yet is caught on the
   next sweep once the proxy files — supplement with an 8-K Item 1.01 check when a
   fresh announcement is known.)

3. **The LLM read (Arm A — this is the experiment). PINNED BRAIN: the Opus tier
   at HIGH effort — non-negotiable.** The read rides real money on a tiny deal
   universe (dozens), so the brain is never economized, and the A/B only means
   something if the read is a FIXED variable rather than whatever model Zeus
   happened to dispatch (the 2026-07-07 calibration proved a weaker model
   confidently flips real keep/drop calls). If THIS session is already the Opus
   tier, do the read inline at high effort. If it is NOT, delegate the read to a
   subagent pinned `model: 'opus', effort: 'high'` (the `opus` alias = the current
   strongest Opus) and use its verdict. Either way, pass `read_model` / `read_effort`
   to `record_detection` (they default to the pinned Opus/high) so every graded
   deal carries which brain made the call. For EACH detected deal, read the break
   risk with real effort (the edge is reading, not the headline):
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
   - **The ATOMIC order flow (audit 2026-07-10 — this ordering is the incident
     fix, never deviate):**
     1. `append_order(LEDGER_PATH, OrderRecord(order_id="intent", symbol, "buy",
        dollars, date, status="placed"))` — the INTENT row goes in BEFORE the
        broker sees the order, so a crash mid-placement leaves a ledger claim,
        never an invisible order.
     2. `place_equity_order` (fractional market/limit buy).
     3. On the fill: `book.enter(..., order_id=<broker order id>)` — the atomic
        door appends the FILLED ledger row (actual shares + fill price) and
        SAVES the sleeve to disk in the same call. An order can no longer exist
        at the broker with the sleeve un-mutated (the state the auto-run
        exploited). `enter` also refuses non-cash deals, non-ISO
        `expected_close`, and a same-day ledgered duplicate.
     4. If the fill is pending at session end: the intent row already carries
        the claim; next session's step-0b reconcile picks the fill up.
   - **Two-sided reconcile before ANY entry:** `hermes.sleeve.hermes_reconcile(
     book, broker_shares)` must return [] — it replays the ledger's fill rows
     against the sleeve and broker, and the "personal overlap" excuse never
     applies to a symbol Hermes's own ledger claims. Non-empty = HALT entries,
     reconcile first.
   - **Marks discipline:** `book.missing_marks(marks)` must be [] before
     trusting any break-stop/breaker answer — a missing quote silently marks a
     position at entry (zero loss).

5. **Mark + curve.** `book.equity(marks)`, append `{date, equity, spy}` to
   `cache/hermes_curve.json`.

6. **Grade the A/B.**
   - **Sweep the dropped deals FIRST (audit 2026-07-10 — mandatory, every
     session):** `hermes.ab.sweep_unresolved(ab, marks=…, spy_price=…, today=…)`
     paper-grades every unresolved detection past its expected close at the
     market price — fetch quotes for ALL unresolved detected symbols, not just
     held ones. Without this only kept deals grade, and the lift is biased on
     the exact half that matters most (avoidance is the LLM's one measured-real
     skill).
   - Then `hermes.ab.llm_lift(ab)` — report Arm A (LLM kept) vs Arm B (all
     detected) convexity + the lift once a few deals have graded. This is the
     headline the checkpoint judges.

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
