# /oracle-screen — heavy quarterly screen

Runs the multi-lens universe screen. Takes 40–60 minutes against the full
~7,000 SEC filer universe (network-bound at SEC's 8 req/s ceiling).
Updates all the cache files Oracle and Achilles depend on.

## Steps

1. **Universe.** `shared.edgar.fetch_company_tickers()` returns the master
   ticker→CIK map (~10,000 entries). Filter to whatever sub-universe you
   want — for the full pass, the entire dict.

2. **Lens 1 — Insider clusters.** Threaded fan-out:
   ```python
   from oracle.lenses import make_form4_fetcher
   from shared.insiders import scan_universe
   fetcher = make_form4_fetcher(sym_to_cik, days_back=60)
   clusters = scan_universe(
       list(sym_to_cik.keys()),
       fetcher,
       max_workers=4,  # global rate gate handles thread safety
       checkpoint_every=200,
       on_checkpoint=lambda n, c: json.dump({"clusters": c}, open("cache/oracle_insider_clusters.json", "w")),
   )
   ```
   Output → `cache/oracle_insider_clusters.json`.

3. **Lens 2 — Smart-money 13F holdings.** For each manager name in
   `oracle.smart_money.SMART_MONEY_FUNDS`, look up the CIK (via the tickers
   map or a curated map), find latest 13F-HR via
   `oracle.lenses.find_latest_13fhr_accession`, then fetch the information
   table via `fetch_13f_information_table_xml`. Parse with
   `oracle.smart_money.parse_13f_information_table`. Aggregate via
   `smart_money_holders`. Output → `cache/oracle_smart_money.json`.

4. **Lens 3 — Activist 13D.** Single EDGAR full-text search:
   ```python
   from oracle.lenses import search_recent_13d
   thirteen_ds = search_recent_13d(date_from="...", date_to="...")
   ```
   Filter is already strict (no /A amendments). Output →
   `cache/oracle_activist_13d.json`.

5. **Lens 4 — Broad quality screen.** Per-symbol XBRL fan-out with
   checkpointing:
   ```python
   from oracle.lenses import scan_universe_quality
   quality = scan_universe_quality(
       sym_to_cik,
       checkpoint_every=200,
       on_checkpoint=lambda n, rows: json.dump({"rows": rows}, open("cache/oracle_prescreener.json", "w")),
   )
   ```
   Output → `cache/oracle_prescreener.json`.

6. **Combine.** `oracle.lenses.combine_lenses(universe, insider_clusters=…,
   smart_money=…, activist_symbols=…, quality_rows=…)` produces a
   per-symbol multi-lens row. Rank survivors:
   ```python
   from oracle.screener import rank_survivors
   top = rank_survivors(rows, top_n=100)
   ```
   Output → `cache/oracle_screen.json`.

7. **Cadence + persist.** `oracle.calendar.mark_run(cache/oracle_cadence.json, "screen")`,
   then `pantheon.persist("oracle", {…all five cache files…})`.

## Rate limit

`shared.edgar` enforces a global, thread-safe rate gate at 8 req/s
(`set_rate_limit(n)` to tune). With `max_workers=4` on the insider scan,
threads serialize at the gate — no manual ceiling needed.

## Resilience

- All four lenses checkpoint to disk during the scan; if the process
  dies, restart picks up from the last checkpoint.
- A failed per-symbol fetch is logged and skipped, not retried —
  the universe is too large for tight retry loops.
- Per-symbol errors are absorbed at the fetcher boundary
  (`fetch_insider_txns_for_symbol`, `fetch_quality_snapshot_for_symbol`).
