# /midas — weekly entry + position management (light half)

Run Midas's entry and management cycle: read this week's finalists from a
prior `/midas-scan`, deep-research each, pick ONE stock, enter Monday, and
manage the open position through the week.

The heavy universe scan lives in **`/midas-scan`** — run that on the
weekend first. This skill consumes its `cache/midas_scan.json` output; it
does NOT scan the universe itself.

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

### Load this week's finalists (from /midas-scan)

6. **Load the scan.** `midas.scanner.load_scan("cache/midas_scan.json")`. This is the top-10 ranking produced by `/midas-scan` over the weekend.
   - **If the file is missing** (`load_scan` returns `{}`) OR `scanned_at` is more than ~3 days old, **abort the entry** and tell the user to run `/midas-scan` first. Do NOT fall back to scanning the universe here — the whole point of the split is that the heavy scan is a separate pass. A stale scan means stale signals; entering on it would defeat the freshness gates the scan applied.
   - Otherwise, take `data["finalists"]` — the ranked top 10 (each carries `symbol`, `score`, `convergence_count`, `active_signals`, `signal_details`, `sector`, `market_cap`).

### Stage 3 — LLM Disqualification Gate (10 → 1)

9. **Research and disqualify.** For each of the top 10 finalists:
   - Fetch current price, 52-week high from `get_equity_quotes` and `get_equity_fundamentals`
   - Fetch latest 8-K filings from EDGAR
   - Review what signals fired and why
   - **MANDATORY tape check — do NOT trust `report_date`.** Fetch 30-day historicals (`get_equity_historicals`) and run `midas.prescan.find_reaction_bar(bars)`. This hands you the *actual* reaction bar from the tape: its `date`, `gap`, `pre_price`, and `age_days` (trading days since the move). The calendar `report_date` routinely lags the tape (DAKT and PRGS both failed here — 2/2), so eyeballing it is not enough. **Disqualify if** `age_days` shows the drift window has closed (older than ~3 trading days) **or** the move from `pre_price` to the current price already exceeds ~15% (`STALENESS_PCT`) — the catalyst is priced in. Record the reaction date and drift in `disqualify_reason`. (Stage 1 already applies this gate mechanically; this is the human/LLM backstop, and it only works because the reaction data is handed to you here — not because you remembered to look.)
   - **The LLM's job is to DISQUALIFY, not to rank.** Look for other active thesis-killers:
     - Guidance bomb or earnings miss since the signal fired
     - Ongoing SEC investigation or fraud allegation
     - Delisting risk, going concern
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
   - **Carry the scan's numbers into the dossier.** Copy `score`, `convergence_count`, and `signals` (the `active_signals` map) straight from the loaded finalist onto the `WeeklyCatalystDossier`. `pick_winner` ranks on `d.score`, so it MUST be the scan's score — do not recompute or invent it.
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
| `cache/midas_scan.json` | This week's top-10 finalists from `/midas-scan` (input) |
| `cache/midas_sleeve.json` | Cash, position, weekly results, peak equity |
| `cache/midas_dossiers.json` | This week's top-10 catalyst dossiers |
| `cache/midas_ledger.jsonl` | Every order placed (for reconcile) |
| `cache/midas_curve.json` | Equity timestamps for dashboard |
| `cache/midas_cadence.json` | Last-run timestamps |
