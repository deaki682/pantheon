# /delphi — full Delphi pass

Sector rotator with SPY core-satellite overlay. 8 steps.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Safety check.** Refuse if `KILL_SWITCH` exists. Liquidate all sector positions if so. Then check `shared.guards.is_live("delphi")` — if `DELPHI_LIVE` env var is not exactly `"true"`, run in **paper mode**: compute everything normally but **do not place broker orders** in steps 6–7. Log the planned orders to the decision log so they can be reviewed. Print "PAPER MODE — no orders placed" prominently.

2. **Restore.** Load `cache/delphi_sleeve.json`. If absent, `DelphiSleeve(initial_cash=1000)`.

3. **Fetch sector + SPY history.** Pull 126+ days of close prices for SPY and each of the 11 SPDR sector ETFs (XLK, XLF, XLE, XLV, XLI, XLP, XLY, XLU, XLRE, XLB, XLC). Use Robinhood MCP `get_equity_historicals`.

4. **Compute regime + sector ranking.**
   - `delphi.signals.score_sectors(sector_prices, spy_prices)` for the composite.
   - `delphi.rotation.rotation_plan(spy_prices, sector_scores)` -> {regime, breadth, risk_budget, sectors}.

5. **Per-sector stock screen.** For each chosen sector, pull a small list of candidate stocks (top by market cap inside the sector, or from Oracle's screen). `delphi.screener.build_candidate(...)` each. `delphi.selector.select_for_sectors(...)` to keep top 2 per sector.

6. **Build targets and plan sector orders.**
   - First, run `shared.guards.pre_trade_check(broker_positions)` — fetch the broker's actual equity positions and compare against the sum of all three sleeves. If any symbol is out of sync, **halt trading and run `/oracle-reconcile`** before proceeding.
   - `delphi.execution.build_targets(picks_by_sector, equity=sleeve.equity(marks), risk_budget=plan["risk_budget"])` — score-weighted allocation (more dollars to higher-scored picks).
   - `delphi.execution.plan_orders(sleeve, targets, prices)` — honors 20% rebal band, ETF blocklist, min ticket $25.
   - Place market orders via Robinhood, append to `cache/delphi_ledger.jsonl`.

7. **SPY overlay.** After sector orders settle, deploy idle cash into SPY (core-satellite: sector picks are the satellite, SPY is the core). `delphi.execution.overlay_orders(sleeve, targets, prices)`. This ensures cash earns market return instead of sitting idle — the single biggest driver of Delphi's alpha.

8. **Persist.** Save sleeve + curve + decision log. `pantheon.persist("delphi", ...)`.

## Risk-off

When `regime == "risk_off"`, the plan returns `risk_budget=0` and the
targets dict is empty — sector positions sell to cash. SPY overlay
position is retained (we want market exposure even in risk-off — the
regime filter is about sector conviction, not market timing).

## Design rationale (validated by backtest)

- **SPY overlay**: idle cash earning 0% dragged returns by ~17% vs SPY.
  The overlay closes that gap. Validated: +9.3% alpha, positive in both
  halves of the test period (Apr 2025 – Jun 2026).
- **Score-weighted allocation**: tilts capital toward higher-conviction
  picks. Consistent improvement over equal-weight.
- **2 names per sector**: with a $1k sleeve, 6 positions at ~$150 beats
  12 positions at ~$75. Meaningful conviction sizing.
- **Quality weight removed**: fundamentals quality is a look-ahead bias
  in backtests and showed no predictive value in the ghost shadow.
  Momentum-only stock selection within sectors.
