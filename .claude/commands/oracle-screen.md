# /oracle-screen — heavy quarterly screen

Runs the multi-lens universe screen across ~7,000 SEC filers. Takes
40–60 minutes. Updates all the cache files Oracle and Achilles depend on.

## Steps

1. Fetch the SEC company tickers index via `shared.edgar` (`fetch_submissions` is per-symbol; for the index, hit `https://www.sec.gov/files/company_tickers.json`).

2. Build the universe (~7,000 names).

3. Multi-lens parallel scan:
   - **Insider clusters**: `shared.insiders.scan_universe(symbols, fetcher, max_workers=6, checkpoint_every=200)`. Each fetcher pulls recent Form 4 filings and parses to `InsiderTxn`. Output -> `cache/oracle_insider_clusters.json`.
   - **Smart-money 13F**: parse the most recent 13F filings of names in `oracle.smart_money.SMART_MONEY_FUNDS`. Output -> `cache/oracle_smart_money.json`.
   - **Activist 13D**: fetch recent SC 13D filings via EDGAR full-text search. Filter to fresh (not /A). Output -> `cache/oracle_activist_13d.json`.
   - **Broad quality screen**: pull fundamentals snapshots; run `oracle.prescreener.prescreen`. Output -> `cache/oracle_prescreener.json`.

4. Combine via `oracle.screener.multi_lens_score` for each universe symbol that hit at least one lens.

5. Rank survivors via `oracle.screener.rank_survivors` (top 100). Output -> `cache/oracle_screen.json`.

6. Update screen cadence in `cache/oracle_cadence.json` via `oracle.calendar.mark_run`.

7. Persist all changed cache files via `pantheon.persist("oracle", ...)`.

## Resilience

- Checkpoint every 200 names so a crash doesn't lose 6 hours of work.
- A failed per-symbol fetch is logged and skipped, not retried — the universe is too large for tight retry loops.
- Rate-limit to <= 10 req/s to SEC.
