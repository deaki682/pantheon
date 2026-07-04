# /delphi — full Delphi pass

**OPERATOR OVERRIDE — RUN UNCHANGED (2026-07-04, in writing).** Study
#11 (docs/lab_results_delphi_ruleset_fullwindow.md) reported a
refutation of this ruleset; the same-day accuracy audit found the
study MIS-SPECIFIED her rules (see its erratum) — the full-window
question is OPEN pending `delphi_ruleset_faithful`. The operator's
standing directive regardless: **"don't freeze or change her yet."**
Delphi runs exactly as specified below — normal entries, exits, all
five decision points, no freeze — until the operator says otherwise.
The consequence remains OPEN on the operator's desk; no session may
retire, freeze, or modify her on its own initiative, and equally no
session may cite the refuted backtest (or any window of it) as
evidence FOR the strategy. A brief entry freeze existed earlier today
(operator's first interim call) and was reversed by this directive
within the hour.

Momentum compounder with LLM judgment. Mechanical signals produce
recommendations; you review and override at five decision points.
The mechanical system is the default — your job is to catch what
it can't: context, narrative, convergence.

## RULE CHANGE RECORD — once-per-trading-day cadence (2026-07-04, operator approved)

Delphi is a DAILY-BAR strategy (65-day momentum, 20-day MA) that Zeus
dispatches HOURLY. Before this guard, every hourly pass re-ranked on
intraday quotes and traded the whipsaw: 23 orders / $3,506 notional on a
~$1,900 sleeve over Jul 1–3, including a 1-day AMZN round trip and two
orders placed on the July-3 market holiday (both cancelled by the
operator, ledger rows 2026-07-04). The signals only gain information
once per day — at the daily close — so Delphi now TRADES at most once
per trading day; every other hourly pass is monitoring-only.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Safety check.** Refuse if `KILL_SWITCH` exists. Then check `shared.guards.is_live("delphi")` — if `DELPHI_LIVE` env var is not exactly `"true"`, run in **paper mode**: compute everything normally but **do not place broker orders**. Print "PAPER MODE — no orders placed" prominently. **CRITICAL: In paper mode, do NOT update the sleeve, do NOT append to the ledger, and do NOT persist.** Paper mode is read-only — it must never change state.

1b. **Cadence + market-day guard (2026-07-04).** Two checks decide
   whether this pass may TRADE:

   ```python
   from oracle.calendar import is_trading_day, ran_today
   market_open_today = is_trading_day(today)          # weekends AND NYSE holidays
   already_traded    = ran_today("cache/delphi_cadence.json", "trade", today=today)
   trade_pass = market_open_today and not already_traded
   ```

   - If `not market_open_today`: **stop after the safety check.** No
     orders, no sleeve/ledger writes, no persist. The broker queues
     orders placed on closed days and fills them at whatever Monday
     brings — that is how the July-3 mess happened.
   - If `already_traded`: this is a **monitoring-only pass** — you may
     recompute marks and flag anything alarming for the operator, but
     place NO orders and write NO state.
   - Only a `trade_pass` proceeds through the decision points and
     execution below. After a trade pass completes (whether or not any
     order was actually placed — a no-trade decision still consumes the
     day), call `oracle.calendar.mark_run("cache/delphi_cadence.json", "trade")`
     and include `cache/delphi_cadence.json` in the persist.

2. **Restore.** Load `cache/delphi_sleeve.json`. If absent, `DelphiSleeve(initial_cash=1000)`.

3. **Fetch universe prices.** Pull 126+ trading days of daily close prices for all ~118 stocks in `delphi.signals.UNIVERSE` (plus any additions from `cache/delphi_universe_overrides.json` if present). Use Robinhood MCP `get_equity_historicals` (batch up to 10 symbols per call, `interval=day`, `span=year`). Also fetch SPY for breadth context.

4. **Rank by momentum.**
   - `delphi.screener.score_universe(universe_prices, additions=…, removals=…)` — apply any universe overrides.
   - Compute `delphi.signals.breadth(universe_prices)` — % of universe above 20-day MA. This feeds your risk-budget judgment.

### Decision Point 1: EXIT JUDGMENT

5. **Review exit candidates.** `delphi.signals.exit_candidates(sleeve.positions, prices, lookback_prices)` flags every held position where price < 20-day MA. For each:

   - **Look at the numbers**: How far below MA? What's the total return since entry? How long held?
   - **Check why it dropped**: Fetch the latest 1-2 headlines or 8-K filings for the symbol. Is this an earnings miss? Sector rotation? Broad market selloff? Short-term noise?
   - **Decide**:
     - **Exit** (default) — trend is broken, sell it. This is the right call ~80% of the time.
     - **Hold** — the drop is noise (market-wide selloff, one-day overreaction on high volume). Add to `hold_overrides`. Only hold if you have a specific reason — "it might bounce" is not a reason.
     - **Reduce** — split the difference. Sell half, keep half. Treat as an exit for half the shares.
   - **Bias check**: Override sparingly — at most 1-2 names per run; if you're overriding 3+, you're second-guessing the system. (The old "+85% Sharpe 1.51" justification is retired: #4 measured the original alpha claim against a broken SPY leg, and the MA rule's full-window value is OPEN pending `delphi_ruleset_faithful`. The override BUDGET stands on decision-consistency grounds, not on the dead citation.)

### Decision Point 2: ENTRY JUDGMENT

6. **Review entry candidates.** Take the top 20 from the momentum ranking (2x the slots you'll fill). Enrich with cross-signals:
   - `delphi.signals.enrich_with_signals(candidates, insider_clusters=…, smart_money=…)` — load `cache/oracle_insider_clusters.json` and `cache/oracle_smart_money.json` if available.
   - For each of the top 20, quickly assess:
     - **What's driving the momentum?** Earnings beat → strong. Sector tailwind → fine. Short squeeze → veto. One-time event → veto.
     - **Any red flags?** Recent going-concern, restatement, SEC investigation, insider selling → veto.
     - **Signal convergence?** Insider buying + momentum = stronger entry. Smart money + momentum = stronger entry. No convergence = still fine (momentum alone is the primary signal).
   - **Veto** names with clear red flags. Pass `vetoes` to `delphi.selector.select_top(ranked, vetoes=vetoes)`. The selector backfills from further down the ranking.
   - **Bias check**: Veto at most 2-3 names per run. If nothing looks obviously broken, don't veto anything — the momentum signal is the edge, not your stock-picking.

### Decision Point 3: SIZING JUDGMENT

7. **Set conviction weights.** Default is equal-weight (all 1.0). You MAY tilt:
   - **Overweight (1.2–1.5x)**: momentum + insider buying + earnings beat = high conviction. Strong fundamental support for the trend.
   - **Underweight (0.6–0.8x)**: momentum is real but the name is extended (far above 52-week avg), or the sector is crowded in the portfolio.
   - **Never go below 0.5x or above 2.0x** — extreme tilts defeat diversification.
   - Pass as `weight_overrides` to `build_targets`.
   - **Bias check**: If you're tilting more than 3 names, you're over-engineering. Equal-weight is the tested baseline.

### Decision Point 4: RISK BUDGET

8. **Set risk budget.** Check the breadth number from step 4:
   - **Breadth > 60%** (healthy market): `risk_budget = 1.0` (fully invested)
   - **Breadth 40–60%** (narrowing): `risk_budget = 0.85` (slight caution)
   - **Breadth < 40%** (deteriorating): `risk_budget = 0.70` (meaningful cash buffer)
   - These are guidelines, not rules. Use your judgment — a 38% breadth reading during a V-shaped recovery is different from 38% in a slow grind down.
   - Pass to `delphi.rotation.rotation_plan(risk_budget=…)`.
   - **Bias check**: Don't overthink this — the system has no tested regime filter, and adding one ad hoc would be an untested rule change. (The old "+85% with no regime filter" citation is retired per #4/#11-erratum; the guideline stands on simplicity grounds, not on the dead number.)

### Circuit breaker

Before executing, compute current marks and run `sleeve.check_halt(marks)`. If
equity is **40% below peak** (`HALT_DRAWDOWN`), the breaker trips: set
`sleeve.halted = True`, **place NO new buys this run** (the sleeve's `buy()`
already refuses when halted), still process MA-break **exits** to de-risk, and
log the trip. This is Delphi's protection against a momentum crash — the one
regime where mechanical momentum keeps rotating into falling leaders. Only
`sleeve.manual_reset()`-style operator action (clearing `halted`) resumes buys.

### Execute

9. **Build targets and plan orders.**
   - Fetch broker positions, filter through `shared.guards.filter_broker_to_gods()`, check `pre_trade_check`. If mismatch, halt and reconcile.
   - `delphi.execution.build_targets(picks, equity=sleeve.equity(marks), risk_budget=plan["risk_budget"], weight_overrides=overrides)`
   - `delphi.execution.plan_orders(sleeve, targets, prices, hold_overrides=holds)`
   - Place market orders via Robinhood, append to `cache/delphi_ledger.jsonl`.
     **Every ledger row must record `shares` and `price`** — a row without them
     is useless for reconcile.
   - When applying sells to the sleeve, pass the planner's cooldown intent
     through: `sleeve.sell(sym, shares, px, today, set_cooldown=order["set_cooldown"])`.
     Full `momentum_exit` sells cool the name for 7 days; `trim_to_target`
     sells do NOT (a trim keeps the name in the book — cooling it would block
     top-ups and force drift from target).

### Decision Point 5: UNIVERSE CURATION (periodic)

10. **Universe review (quarterly only).** When running the quarterly review:
    - Check for delistings, going-concern filings, or completed mergers → add to removals.
    - Check for recent IPOs or spinoffs that have 6+ months of trading history and are large-cap → add to additions.
    - Save overrides to `cache/delphi_universe_overrides.json`.
    - This is NOT done every run — only when explicitly reviewing the universe.

11. **Persist.** `sleeve.update_peak(marks)` to advance the high-water mark, then
    save sleeve + curve + decision log. `pantheon.persist("delphi", ...)`.

## Decision log

Every run — **including no-trade runs** — append a record via
`delphi.decisions.append_decision(record)` (validated JSONL writer; do NOT
hand-write the file — a malformed write once destroyed the trail). Read it
back with `delphi.decisions.load_decisions()` and roll up override usage with
`delphi.decisions.override_summary()` for the monthly calibration review.
Record shape:
```json
{
  "date": "2026-06-30",
  "breadth_pct": 0.62,
  "risk_budget": 1.0,
  "exit_candidates": 2,
  "exits_overridden": 0,
  "entries_vetoed": 1,
  "vetoed_symbols": ["XYZ"],
  "weight_overrides": {"NVDA": 1.3},
  "positions_after": 10
}
```
This log lets you calibrate: are your overrides helping or hurting?

## Strategy parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Universe | ~118 large-cap S&P 500 stocks | Liquid, tight spreads, smooth trends |
| Momentum lookback | 65 trading days (~13 weeks) | Sweet spot from backtest |
| Trailing stop | 20-day MA (~4 weeks) | Catches trend breaks without whipsawing |
| Positions | 10 equal-weight (with optional LLM tilts) | Concentrated enough for alpha |
| Cash floor | 5% | Minimal drag |
| Rebalance band | 20% | Avoids churn from small fluctuations |
| Risk budget | 0.5–1.0 (LLM-set via breadth) | Light touch, not binary |

## Override budget per run

| Override type | Max per run | Why |
|---------------|-------------|-----|
| Exit holds | 2 | MA exit is the proven edge — don't fight it |
| Entry vetoes | 3 | Momentum signal is primary — veto only clear red flags |
| Weight tilts | 3 names | Equal-weight is tested baseline |
| Risk budget | 0.5–1.0 range | Never go below 50% invested |

## Design rationale

**CORRECTED 2026-07-04** (PIT replay, docs/lab_results_delphi_pit_universe.md —
the old "+53.8pp alpha, Sharpe 1.51" figures were computed against a
broken SPY leg and may not be cited): on honest survivorship-free
data over 2021-06..2026-06, the mechanical system on the curated list
returned +85.6% vs SPY's +86.7% (−1.1pp, Sharpe 0.65) — it matched
the index. The same mechanics on a blind point-in-time top-119-by-
marketcap universe returned +143.5% (+56.8pp, Sharpe 0.87). One
costless bull-window measurement — evidence for the design, not proof
of alpha; the capital gates still run on live graded calls only.
**Full-window status (2026-07-04, twice-revised same day):** study #11
(`delphi_ruleset_fullwindow`) reported a refutation of "her exact
ruleset," but the operator-ordered accuracy audit found the primary
cell MIS-SPECIFIED her rules (standalone daily MA stop on unfiltered
entries, instead of the real MA-as-entry-filter inside the ranking,
no rebalance band, no sell cooldown semantics) — see the erratum in
docs/lab_results_delphi_ruleset_fullwindow.md. Its verdict stands only
for the strawman variant it actually tested; its "MA exit is the
saboteur" headline is RETRACTED as a claim about this design. Two
findings survive the erratum and may be cited: exit-less top-10
momentum on the honest universe earned 6.92%/yr vs the universe's own
equal weight at 7.94%/yr over 1999–2026 (gauntlet-consistent), and
the 2021–26 window is among the strongest momentum regimes in the
panel. The faithful full-window test is `delphi_ruleset_faithful` —
until it reports, the full-window question is OPEN, not answered. The LLM judgment layer is **additive, not
corrective** — it catches edge cases the mechanical system can't see
(news, filings, narrative) without overriding the core signal
(momentum ranking + MA exit).

The override budgets exist because the biggest risk isn't missing a
good trade — it's the LLM second-guessing a system that works. Every
override is a bet that your contextual judgment beats the base rate.
Track them in the decision log and review monthly.
