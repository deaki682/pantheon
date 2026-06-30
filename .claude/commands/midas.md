# /midas — weekly diamond finder

Run Midas's complete weekly cycle: scan the full universe, funnel to 10
finalists, deep-research each, pick ONE stock, enter Monday, manage
through the week.

Midas is maximally concentrated: one stock, all-in, one week. The edge
is signal convergence — when multiple independent informed-money signals
fire on the same name, the probability of a short-term pop increases
non-linearly.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Safety check.** Kill switch, `is_live("midas")` check. If not live, paper mode. **CRITICAL: In paper mode, do NOT update the sleeve, do NOT append to the ledger, and do NOT persist.** Compute everything normally, print what *would* happen, then stop. Paper mode is read-only — it must never change state.

2. **Restore state.** Read `cache/midas_sleeve.json`. If absent, initialize `MidasSleeve(initial_cash=1000.0)` and save.

3. **Process settlements.** `sleeve.process_settlements(today)`.

4. **Check existing position.** If Midas has an open position:
   - Fetch current price via `get_equity_quotes`.
   - **Hard stop:** If `sleeve.check_stop(current_price)`, exit immediately via broker market sell. `sleeve.exit(price=px, today=today, reason="hard_stop")`.
   - **Time stop:** If `sleeve.should_time_stop(today)` (it's Friday or later), exit via broker market sell. `sleeve.exit(price=px, today=today, reason="time_stop")`.
   - **Circuit breaker:** `sleeve.check_halt()` — if 40% drawdown from peak, liquidate.
   - **Top up:** If position is still open and `sleeve.cash > 50`, buy more of the same symbol with all available cash (minus $10 fee reserve). Compute shares = `(sleeve.cash - 10) / current_price`. Place fractional-share market order, update sleeve, append to ledger. Midas is all-in — idle cash is wasted capital.
   - If position still open after checks, skip to step 13 (persist) — we're mid-week, no new entry.

5. **If no position is open and it's not Monday**, skip to step 13. Midas only enters on Mondays.

### Stage 1 — Quantitative Sieve (~7,000 → ~50-200)

6. **Load signal data.** Start from the FULL universe (`shared.edgar.fetch_company_tickers()`, ~7,000 filers), NOT Oracle's top-100 screen. Load the **raw lens caches** from Oracle's quarterly scan — these cover the entire universe, not the ranked subset:
   - `cache/oracle_insider_clusters.json` — every insider buying cluster found across all ~7,000 filers
   - `cache/oracle_smart_money.json` — all smart money 13F holdings (full universe coverage)
   - `cache/oracle_activist_13d.json` — every fresh 13D filing found (full EDGAR search)
   - Fetch this week's earnings reporters via Robinhood `get_earnings_calendar` (~50-100 names per week). Split into two sets:
     - `earnings_this_week`: symbols with reports **not yet released** (report date is today or later this week). These are pending binary events — exclude from the sieve.
     - Already-reported: symbols that reported in the last 5 days. Fetch `get_earnings_results` for these only. Beats become `earnings_surprise` signals; misses are ignored.
   - For guidance raised: search EDGAR for recent 8-K filings with items 7.01/8.01, run `guidance_direction()` on each
   - **Volume anomaly**: For candidates with at least one other signal, fetch `get_equity_historicals` (30-day daily bars). Compute `volume_anomalies = {sym: last_5d_avg_vol / 30d_avg_vol}`. Pass to sieve — ratio > 1.5x fires the signal, strength = min(1.0, ratio / 3.0). This is the most week-specific signal and naturally co-occurs with other catalysts.
   - **Signal prices** (for freshness gate): For each symbol with an insider cluster, record the price at signal time from the cluster's `latest_date`. Fetch current prices via `get_equity_quotes`. Pass both as `signal_prices` and `current_prices` to the sieve — names where price moved >15% since the signal fired are filtered out (signal is stale / already priced in).

   **Key distinction:** `cache/oracle_screen.json` is Oracle's combined top-100 ranking — Midas does NOT use it. Midas starts from the raw signal data which covers the full universe, then applies its own convergence-based ranking.

7. **Run sieve.** `midas.scanner.stage1_sieve(universe, insider_clusters=…, smart_money_holders=…, activist_symbols=…, earnings_surprise=…, guidance_raised=…, volume_anomalies=…, market_caps=…, ipo_dates=…, earnings_this_week=…, signal_prices=…, current_prices=…, today=today)`. Checks every symbol in the full universe against all signal sources. Filters out: names listed < 90 days (unreliable signals on new listings), names with unresolved earnings this week (binary gamble, not signal convergence), names where price already moved >15% since signal date (stale signals). To get IPO dates: batch-fetch `get_equity_fundamentals` for candidates with signals and extract the `ipo_date` field. Output: ~50-200 names with at least one active signal, sufficient trading history, no pending earnings, and fresh signals.

### Stage 2 — Convergence Rank (→ top 10)

8. **Score and rank.** `midas.scanner.stage2_rank(candidates, top_n=10)`. The convergence multiplier non-linearly boosts names with 2+ simultaneous signals.

### Stage 3 — Deep Research (10 → 1)

9. **Build weekly catalyst dossiers.** For each of the top 10 finalists:
   - Fetch current price, 52-week high from `get_equity_quotes` and `get_equity_fundamentals`
   - Fetch latest 8-K filings from EDGAR
   - Review what signals fired and why
   - **Answer the key question:** What specifically could move this stock THIS week?
   - Build a `WeeklyCatalystDossier`:
     - `catalyst`: the specific event or signal convergence
     - `catalyst_timing`: when does the catalyst resolve?
     - `bull_case`: why could this pop 5-20%?
     - `bear_case`: what kills the thesis?
     - `priced_in_judgment`: is the catalyst already reflected in the price?
     - `pop_probability`: honest estimate 0-1
     - `expected_magnitude`: expected % move if it pops
     - `expected_value`: probability × magnitude

10. **Pick the winner.** `midas.scanner.pick_winner(dossiers)` — highest expected value. Save all dossiers to `cache/midas_dossiers.json`.

### Execute

11. **Size and enter.** Midas goes all-in: compute shares = `(sleeve.cash - fee_reserve) / entry_price`. Set `exit_date` to Friday of this week.
    - Check `shared.guards.already_placed_today(ledger, symbol, "buy", today)`
    - Place fractional-share market order via Robinhood MCP
    - `sleeve.enter(symbol=…, shares=…, price=…, today=…, score=…, convergence_count=…, signals=…, exit_date=friday)`
    - Append to `cache/midas_ledger.jsonl`

12. **Update peak.** `sleeve.update_peak(marks)`.

13. **Persist.** Save `cache/midas_sleeve.json`, append to `cache/midas_curve.json`, then `pantheon.persist("midas", files, branch="claude/live")`.

## Exit Rules

| Condition | Trigger | Action |
|-----------|---------|--------|
| Price drops 10% from entry | Any intraday check | Market sell immediately |
| Friday (or exit_date reached) | `should_time_stop(today)` | Market sell at close |
| 40% drawdown from peak equity | `check_halt()` | Halt sleeve, liquidate |
| Kill switch | `KILL_SWITCH` file | Liquidate immediately |

No profit target — let winners run to Friday. The asymmetry: cut losers at -10%, let winners go +5-20%+.

## What /midas does NOT do

- Enter on any day other than Monday
- Hold more than one position
- Hold through the weekend
- Override the convergence scoring with gut feel
- Add positions because the broker holds them (sleeve is authoritative)

## Signal Channels (from existing infrastructure)

| Signal | Source | Strength |
|--------|--------|----------|
| Insider cluster | `shared.insiders.cluster_signal` via Oracle screen | n_insiders / 4 |
| Earnings beat | `achilles.earnings.compute_surprise` | surprise_strength curve |
| Smart money | `oracle.smart_money.smart_money_holders` | n_holders / 3 |
| Activist 13D | `oracle.lenses.search_recent_13d` | 1.0 (binary) |
| Guidance raised | `shared.edgar.guidance_direction` | 1.0 (binary) |
| Volume anomaly | `get_equity_historicals` (30-day bars) | min(1.0, ratio / 3.0), fires at 1.5x |

## Calibration

Midas generates ~50 graded trades/year — the fastest calibration path in Pantheon. After each trade, `WeeklyResult` is appended to `sleeve.weekly_results`. Key metrics:
- Hit rate (% of trades with positive return)
- Per-signal attribution (which channels predict pops?)
- Convergence validation (do multi-signal picks outperform single-signal?)
- Alpha vs SPY benchmark

Capital stays at $1,000 until 30+ graded trades show alpha > 0, alpha_t >= 2.0, and convergence validates.

## Key Files

| File | Purpose |
|------|---------|
| `cache/midas_sleeve.json` | Cash, position, weekly results, peak equity |
| `cache/midas_dossiers.json` | This week's top-10 catalyst dossiers |
| `cache/midas_ledger.jsonl` | Every order placed (for reconcile) |
| `cache/midas_curve.json` | Equity timestamps for dashboard |
| `cache/midas_cadence.json` | Last-run timestamps |
