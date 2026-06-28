# /delphi — full Delphi pass

Sector rotator. 7 steps.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. **Safety check.** Refuse if `KILL_SWITCH` exists.

2. **Restore.** Load `cache/delphi_sleeve.json`. If absent, `DelphiSleeve(initial_cash=1000)`.

3. **Fetch sector + SPY history.** Pull 126+ days of close prices for SPY and each of the 11 SPDR sector ETFs (XLK, XLF, XLE, XLV, XLI, XLP, XLY, XLU, XLRE, XLB, XLC). Use Robinhood MCP `get_equity_historicals`.

4. **Compute regime + sector ranking.**
   - `delphi.signals.score_sectors(sector_prices, spy_prices)` for the composite.
   - `delphi.rotation.rotation_plan(spy_prices, sector_scores)` -> {regime, breadth, risk_budget, sectors}.

5. **Per-sector stock screen.** For each chosen sector, pull a small list of candidate stocks (top by market cap inside the sector, or from Oracle's screen). `delphi.screener.build_candidate(...)` each. `delphi.selector.select_for_sectors(...)` to keep top 4 per sector.

6. **Build targets and plan orders.**
   - `delphi.execution.build_targets(picks_by_sector, equity=sleeve.equity(marks), risk_budget=plan["risk_budget"])`.
   - `delphi.execution.plan_orders(sleeve, targets, prices)` — honors 20% rebal band, ETF blocklist, min ticket $25.
   - Place market orders via Robinhood, append to `cache/delphi_ledger.jsonl`.

7. **Persist.** Save sleeve + curve + decision log. `pantheon.persist("delphi", ...)`.

## Risk-off

When `regime == "risk_off"`, the plan returns `risk_budget=0` and the
targets dict is empty — so all positions sell to cash.
