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

### Stage 1 — Weekly Pre-Scan + Sieve (~7,000 → ~50-200)

6. **Weekly pre-scan.** Midas runs its OWN signal gathering — it does NOT just borrow Oracle's quarterly caches. Start from the FULL universe (`shared.edgar.fetch_company_tickers()`, ~7,000 filers).

   **6a. Fresh insider data (last 14 days).** This is Midas's most important signal source. Oracle's `oracle_insider_clusters.json` is a quarterly batch — signals can be 6+ weeks stale. Instead:
   - `oracle.lenses.search_recent_form4(date_from=14_days_ago, date_to=today)` — single EDGAR full-text search, returns {symbol: [filings]} across the entire universe in seconds.
   - `midas.prescan.form4_fts_to_clusters(fts_results)` — converts to cluster format (counts distinct filers per symbol, keeps only 2+ filer clusters).
   - `midas.prescan.merge_insider_clusters(oracle_cache, fresh_clusters)` — merges with Oracle's cache for breadth; fresh data takes precedence for any overlapping symbols.

   **6b. Recent earnings beats (standalone signal).** Earnings beats are a first-class entry point — a name can enter the sieve purely on an earnings beat, with no other signal needed.
   - Fetch `get_earnings_calendar` for the **past 5 trading days** (not this coming week).
   - For every name that already reported, fetch `get_earnings_results`. Beats become `earnings_surprise` signals.
   - ALSO fetch this coming week's reporters → `earnings_this_week` set. These are EXCLUDED from the sieve (pending binary event, not signal convergence).

   **6c. Smart money + activist 13D (Oracle cache).** These change quarterly, so Oracle's caches are fine:
   - `cache/oracle_smart_money.json` — 13F smart money holdings
   - `cache/oracle_activist_13d.json` — recent 13D filings

   **6d. Guidance raised.** Search EDGAR for recent 8-K filings with items 7.01/8.01, run `guidance_direction()` on each.

   **6e. Short squeeze candidates (finviz).** WebFetch `midas.prescan.FINVIZ_SHORT_URL` to get stocks with >20% short float. Parse with `midas.prescan.parse_finviz_short_text(text)` → `{symbol: short_float_pct}`. Pass as `short_squeezes` to the sieve — strength = min(1.0, pct / 50.0). This fires as an independent signal; combined with insider buying or earnings beats, it creates high-convergence squeeze setups.

   **6f. Volume anomalies (full candidate set).** After assembling all signal sources from 6a-6e, collect every symbol that has at least one signal. Fetch `get_equity_historicals` (30-day daily bars) for ALL of them. `midas.prescan.compute_volume_anomalies(historicals)` → `{symbol: ratio}`. Pass to sieve — ratio > 1.5x fires the signal, strength = min(1.0, ratio / 3.0).

   **6g. Signal prices (freshness gate).** For each symbol with an insider cluster, record the price at signal time from the cluster's `latest_date`. Fetch current prices via `get_equity_quotes`. Pass both as `signal_prices` and `current_prices` to the sieve — names where price moved >15% since the signal fired are filtered out.

   **Key distinction:** `cache/oracle_screen.json` is Oracle's combined top-100 ranking — Midas does NOT use it. Midas starts from fresh signal data (augmented by Oracle's caches for breadth), then applies its own convergence-based ranking.

7. **Run sieve.** `midas.scanner.stage1_sieve(universe, insider_clusters=merged_clusters, smart_money_holders=…, activist_symbols=…, earnings_surprise=…, guidance_raised=…, volume_anomalies=…, short_squeezes=…, market_caps=…, ipo_dates=…, earnings_this_week=…, signal_prices=…, current_prices=…, today=today)`. Checks every symbol in the full universe against all signal sources. Filters out: names listed < 90 days, names with unresolved earnings this week, names where price already moved >15% since signal date. To get IPO dates: batch-fetch `get_equity_fundamentals` for candidates with signals and extract the `ipo_date` field. Output: ~50-200 names with at least one active signal, sufficient trading history, no pending earnings, and fresh signals.

### Stage 2 — Convergence Rank (→ top 10)

8. **Score and rank.** `midas.scanner.stage2_rank(candidates, top_n=10)`. The convergence multiplier non-linearly boosts names with 2+ simultaneous signals.

### Stage 3 — LLM Disqualification Gate (10 → 1)

9. **Research and disqualify.** For each of the top 10 finalists:
   - Fetch current price, 52-week high from `get_equity_quotes` and `get_equity_fundamentals`
   - Fetch latest 8-K filings from EDGAR
   - Review what signals fired and why
   - **The LLM's job is to DISQUALIFY, not to rank.** Look for active thesis-killers:
     - Guidance bomb or earnings miss since the signal fired
     - Ongoing SEC investigation or fraud allegation
     - Delisting risk, going concern
     - Price already gapped 15%+ on the catalyst (move is done)
     - Binary event pending this week (earnings, FDA decision) that turns the trade into a coin flip
   - Build a `WeeklyCatalystDossier`:
     - `catalyst`: the specific event or signal convergence
     - `catalyst_timing`: when does the catalyst resolve?
     - `bull_case`: why could this pop 5-20%?
     - `bear_case`: what kills the thesis?
     - `priced_in_judgment`: is the catalyst already reflected in the price?
     - `disqualified`: True if any thesis-killer is found
     - `disqualify_reason`: specific reason (e.g. "guidance bomb Jun 18, -14% gap")
     - `pop_probability`, `expected_magnitude`, `expected_value`: optional, informational only — these do NOT affect pick_winner
   - **Do NOT set pop_probability to justify the algorithm's ranking.** These fields are for your review only. The pick is mechanical.

10. **Pick the winner.** `midas.scanner.pick_winner(dossiers)` — highest timing-weighted convergence score among non-disqualified names. The LLM cannot promote a name; it can only veto. Save all dossiers to `cache/midas_dossiers.json`.

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
- Let LLM probability estimates affect the pick (score is mechanical)
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
| Short squeeze | finviz screener (>20% short float) | min(1.0, pct / 50.0) |

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
