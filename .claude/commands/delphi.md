# /delphi — full Delphi pass

Momentum compounder with LLM judgment. Mechanical signals produce
recommendations; you review and override at five decision points.
The mechanical system is the default — your job is to catch what
it can't: context, narrative, convergence.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Safety check.** Refuse if `KILL_SWITCH` exists. Then check `shared.guards.is_live("delphi")` — if `DELPHI_LIVE` env var is not exactly `"true"`, run in **paper mode**: compute everything normally but **do not place broker orders**. Print "PAPER MODE — no orders placed" prominently. **CRITICAL: In paper mode, do NOT update the sleeve, do NOT append to the ledger, and do NOT persist.** Paper mode is read-only — it must never change state.

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
   - **Bias check**: The mechanical system's MA exit is what made the backtest work (+85% Sharpe 1.51). Override sparingly — at most 1-2 names per run. If you're overriding 3+, you're second-guessing the system.

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
   - **Bias check**: The backtest had NO regime filter and still returned +85%. Don't overthink this — the trailing stop already de-risks the portfolio naturally.

### Execute

9. **Build targets and plan orders.**
   - Fetch broker positions, filter through `shared.guards.filter_broker_to_gods()`, check `pre_trade_check`. If mismatch, halt and reconcile.
   - `delphi.execution.build_targets(picks, equity=sleeve.equity(marks), risk_budget=plan["risk_budget"], weight_overrides=overrides)`
   - `delphi.execution.plan_orders(sleeve, targets, prices, hold_overrides=holds)`
   - Place market orders via Robinhood, append to `cache/delphi_ledger.jsonl`.

### Decision Point 5: UNIVERSE CURATION (periodic)

10. **Universe review (quarterly only).** When running the quarterly review:
    - Check for delistings, going-concern filings, or completed mergers → add to removals.
    - Check for recent IPOs or spinoffs that have 6+ months of trading history and are large-cap → add to additions.
    - Save overrides to `cache/delphi_universe_overrides.json`.
    - This is NOT done every run — only when explicitly reviewing the universe.

11. **Persist.** Save sleeve + curve + decision log. `pantheon.persist("delphi", ...)`.

## Decision log

Every run, append a brief JSON record to `cache/delphi_decisions.jsonl`:
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

The mechanical momentum system delivered +85% total return, Sharpe 1.51,
+53.8pp alpha over SPY in backtesting. The LLM judgment layer is
**additive, not corrective** — it catches edge cases the mechanical
system can't see (news, filings, narrative) without overriding the
core signal that produces alpha (momentum ranking + MA exit).

The override budgets exist because the biggest risk isn't missing a
good trade — it's the LLM second-guessing a system that works. Every
override is a bet that your contextual judgment beats the base rate.
Track them in the decision log and review monthly.
