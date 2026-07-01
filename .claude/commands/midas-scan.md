# /midas-scan — weekly universe scan (heavy half)

The heavy, network-bound half of Midas. Scans the full ~7,000-name
universe, gathers all seven signal channels, runs the sieve, ranks by
convergence, and writes the top 10 finalists to `cache/midas_scan.json`.

It does **not** research, pick, or trade — that's `/midas`. This skill is
read-only with respect to the sleeve: it never touches
`cache/midas_sleeve.json` or the ledger. Run it on the weekend; `/midas`
consumes its output on Monday.

Why split: stages 1-2 are almost all the network calls (EDGAR full-text,
finviz, per-name historicals) and almost all the context. Isolating them
means an entry pass stays light and a failed scan never risks the sleeve.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Safety check.** Kill switch only (`shared.guards.kill_switch_active`). If present, stop — no scan needed if we're liquidating. No `is_live` check: the scan never trades, so paper vs live is irrelevant here.

### Stage 1 — Weekly Pre-Scan + Sieve (~7,000 → ~50-200)

2. **Weekly pre-scan.** Midas runs its OWN signal gathering — it does NOT just borrow Oracle's quarterly caches. Start from the FULL universe (`shared.edgar.fetch_company_tickers()`, ~7,000 filers).

   **2a. Fresh insider data (last 14 days).** This is Midas's most important signal source. Oracle's `oracle_insider_clusters.json` is a quarterly batch — signals can be 6+ weeks stale. Instead:
   - `oracle.lenses.search_recent_form4(date_from=14_days_ago, date_to=today, cik_to_symbol=invert(universe))` — single EDGAR full-text search, returns {symbol: [filings]} across the entire universe in seconds. Form 4 `display_names` never carries a ticker in parens (unlike 13D) — the issuer is always the *last* entry, so the ticker must be resolved via a CIK -> symbol map built from `universe` (inverted from `shared.edgar.fetch_company_tickers()`), not from the display name text.
   - `oracle.lenses.filter_form4_open_market_buys(fts_results)` — **required before clustering.** The raw FTS match includes every Form 4 (grants, option exercises, tax-withholding sales — codes A/M/F), which vastly outnumber genuine open-market buys (code P) at large, well-staffed issuers. Skipping this step makes "insider cluster" measure officer headcount, not accumulation. Fetches each filing's XML body (URL is derivable from the `filer_cik`/`primary_document`/`accession` fields `search_recent_form4` already attaches) and keeps only code-P buys >= $10k.
   - `midas.prescan.form4_fts_to_clusters(buy_filtered_results)` — converts to cluster format (counts distinct filers per symbol, keeps only 2+ filer clusters). Must run on the buy-filtered dict, not the raw FTS output.
   - `midas.prescan.merge_insider_clusters(oracle_cache, fresh_clusters)` — merges with Oracle's cache for breadth; fresh data takes precedence for any overlapping symbols.

   **2b. Recent earnings beats (standalone signal).** Earnings beats are a first-class entry point — a name can enter the sieve purely on an earnings beat, with no other signal needed.
   - Fetch `get_earnings_calendar` for the **past 5 trading days** (not this coming week).
   - For every name that already reported, fetch `get_earnings_results`. Beats become `earnings_surprise` signals.
   - ALSO fetch this coming week's reporters → `earnings_this_week` set. These are EXCLUDED from the sieve (pending binary event, not signal convergence).

   **2c. Smart money + activist 13D (Oracle cache).** These change quarterly, so Oracle's caches are fine:
   - `cache/oracle_smart_money.json` — 13F smart money holdings
   - `cache/oracle_activist_13d.json` — recent 13D filings

   **2d. Guidance raised.** Search EDGAR for recent 8-K filings with items 7.01/8.01, run `guidance_direction()` on each.

   **2e. Short squeeze candidates (finviz).** WebFetch `midas.prescan.FINVIZ_SHORT_URL` to get stocks with >20% short float. Parse with `midas.prescan.parse_finviz_short_text(text)` → `{symbol: short_float_pct}`. Pass as `short_squeezes` to the sieve — strength = min(1.0, pct / 50.0). This fires as an independent signal; combined with insider buying or earnings beats, it creates high-convergence squeeze setups.

   **2f. Volume anomalies (full candidate set).** After assembling all signal sources from 2a-2e, collect every symbol that has at least one signal. Fetch `get_equity_historicals` (30-day daily bars) for ALL of them. `midas.prescan.compute_volume_anomalies(historicals)` → `{symbol: ratio}`. Pass to sieve — ratio > 1.5x fires the signal, strength = min(1.0, ratio / 3.0).

   **2g. Signal prices (freshness gate).** For each symbol with an insider cluster, record the price at signal time from the cluster's `latest_date`. Fetch current prices via `get_equity_quotes`. Pass both as `signal_prices` and `current_prices` to the sieve — names where price moved >15% since the signal fired are filtered out.

   **Key distinction:** `cache/oracle_screen.json` is Oracle's combined top-100 ranking — Midas does NOT use it. Midas starts from fresh signal data (augmented by Oracle's caches for breadth), then applies its own convergence-based ranking.

3. **Run sieve.** `midas.scanner.stage1_sieve(universe, insider_clusters=merged_clusters, smart_money_holders=…, activist_symbols=…, earnings_surprise=…, guidance_raised=…, volume_anomalies=…, short_squeezes=…, market_caps=…, ipo_dates=…, earnings_this_week=…, signal_prices=…, current_prices=…, today=today)`. Checks every symbol in the full universe against all signal sources. Filters out: names listed < 90 days, names with unresolved earnings this week, names where price already moved >15% since signal date. To get IPO dates: batch-fetch `get_equity_fundamentals` for candidates with signals and extract the `ipo_date` field. Output: ~50-200 names with at least one active signal, sufficient trading history, no pending earnings, and fresh signals.

### Stage 2 — Convergence Rank (→ top 10)

4. **Score and rank.** `midas.scanner.stage2_rank(candidates, top_n=10)`. The convergence multiplier non-linearly boosts names with 2+ simultaneous signals. Returns a list of finalist dicts carrying `symbol`, `score`, `convergence_count`, `active_signals`, `signal_details`, `sector`, `market_cap`, and score `components`.

### Persist the scan (no trade)

5. **Save the finalists.** `midas.scanner.save_scan("cache/midas_scan.json", finalists=ranked, scanned_at=<UTC ISO timestamp>)`. Pass the timestamp explicitly (the scanner never reads the clock itself) so `/midas` can detect a stale scan. Do NOT write `midas_dossiers.json` here — that's Stage 3, owned by `/midas`.

6. **Persist.** `pantheon.persist("midas", {"cache/midas_scan.json": data}, branch="claude/live")`. This is the ONLY file this skill writes. It never touches `midas_sleeve.json`, `midas_ledger.jsonl`, or `midas_curve.json`.

## What /midas-scan does NOT do

- Build catalyst dossiers or run the disqualification gate (that's `/midas`)
- Pick a winner
- Place any order or touch the sleeve/ledger/curve
- Run `is_live` / paper-mode branching — it never trades, so it doesn't matter

## Handoff

`/midas` reads `cache/midas_scan.json` via `midas.scanner.load_scan(...)`.
If that file is missing or its `scanned_at` is more than ~3 days old,
`/midas` will refuse to enter and tell you to run `/midas-scan` first —
so run this on the weekend before the Monday entry.

## Signal Channels

| Signal | Source | Strength |
|--------|--------|----------|
| Insider cluster | `shared.insiders.cluster_signal` via fresh Form 4 FTS | n_insiders / 4 |
| Earnings beat | `achilles.earnings.compute_surprise` | surprise_strength curve |
| Smart money | `oracle.smart_money.smart_money_holders` | n_holders / 3 |
| Activist 13D | `oracle.lenses.search_recent_13d` | 1.0 (binary) |
| Guidance raised | `shared.edgar.guidance_direction` | 1.0 (binary) |
| Volume anomaly | `get_equity_historicals` (30-day bars) | min(1.0, ratio / 3.0), fires at 1.5x |
| Short squeeze | finviz screener (>20% short float) | min(1.0, pct / 50.0) |
