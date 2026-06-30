# /delphi — full Delphi pass

Momentum compounder. Buy top 10 by 13-week momentum, exit on 20-day MA
break, weekly rebalance. 7 steps.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Safety check.** Refuse if `KILL_SWITCH` exists. Then check `shared.guards.is_live("delphi")` — if `DELPHI_LIVE` env var is not exactly `"true"`, run in **paper mode**: compute everything normally but **do not place broker orders**. Print "PAPER MODE — no orders placed" prominently.

2. **Restore.** Load `cache/delphi_sleeve.json`. If absent, `DelphiSleeve(initial_cash=1000)`.

3. **Fetch universe prices.** Pull 126+ trading days of daily close prices for all ~118 stocks in `delphi.signals.UNIVERSE`. Use Robinhood MCP `get_equity_historicals` (batch up to 10 symbols per call, `interval=day`, `span=year`).

4. **Rank by momentum.**
   - `delphi.screener.score_universe(universe_prices)` — computes 13-week momentum for every stock, filters to names above their 20-day MA, returns ranked list.
   - `delphi.selector.select_top(ranked)` — picks top 10.

5. **Check trailing stops on existing positions.** For each current holding, check if price < 20-day MA. If so, the position is a sell candidate (it won't appear in the top-10 targets because `score_universe` already filters out below-MA names).

6. **Build targets and plan orders.**
   - First, fetch the broker's actual equity positions, then filter through `shared.guards.filter_broker_to_gods(broker_positions)` to strip out pre-existing personal positions. Also fetch recent broker orders via `get_equity_orders` and compute `shared.guards.pending_shares_from_orders(broker_orders)` to account for queued orders awaiting fill. Pass both to `shared.guards.pre_trade_check(filtered, pending_orders=pending)`. If any symbol is out of sync, **halt trading and run `/oracle-reconcile`** before proceeding.
   - `delphi.execution.build_targets(picks, equity=sleeve.equity(marks), risk_budget=1.0)` — equal-weight allocation across the top 10.
   - `delphi.execution.plan_orders(sleeve, targets, prices)` — honors 20% rebal band, min ticket $25.
   - Place market orders via Robinhood, append to `cache/delphi_ledger.jsonl`.

7. **Persist.** Save sleeve + curve + decision log. `pantheon.persist("delphi", ...)`.

## Strategy parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Universe | ~118 large-cap S&P 500 stocks | Liquid, tight spreads, smooth trends |
| Momentum lookback | 65 trading days (~13 weeks) | Sweet spot from backtest |
| Trailing stop | 20-day MA (~4 weeks) | Catches trend breaks without whipsawing |
| Positions | 10 equal-weight | Concentrated enough for alpha, diversified enough to survive |
| Cash floor | 5% | Minimal drag |
| Rebalance band | 20% | Avoids churn from small fluctuations |

## Design rationale (validated by backtest)

- **No regime filter**: the trailing stop IS the risk management. During
  genuine bear markets, names break their MAs and get sold — the portfolio
  naturally de-risks without a separate regime classifier.
- **No sector caps**: momentum clusters in hot sectors. Capping sectors
  would dilute the signal. The trailing stop limits concentration damage.
- **Equal-weight**: simple, avoids over-allocating to names just because
  their momentum score is marginally higher.
- **Large-cap only**: mid-cap and small-cap momentum showed worse Sharpes
  in backtest. Large-cap trends are smoother and trailing stops work better.
