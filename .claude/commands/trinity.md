# /trinity — refresh dashboard with live prices

Lightweight routine for intraday updates. Run every 15–30 min during
market hours via a timed routine. 5 steps.

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Load sleeves.** Read `cache/oracle_sleeve.json`, `cache/delphi_sleeve.json`, `cache/achilles_sleeve.json`, `cache/midas_sleeve.json`, and `cache/nemesis_sleeve.json` (if present — Nemesis's live sleeve exists but may be empty while she paper-trades). Construct sleeve objects via each class's `.load()`.

2. **Fetch live quotes.** Collect every symbol held across all four sleeves. Fetch current prices via Robinhood `get_equity_quotes`. Also fetch SPY for Delphi overlay reference.

3. **Update curves.** For each god, compute `sleeve.equity(quotes)` using the live prices. Call `trinity_dashboard.append_curve_point("cache", god, equity, today)` for each. These intraday points are baked into the dashboard HTML — they don't need to be separately persisted (each god's main run writes the official daily curve point).

4. **Rebuild dashboard.** `trinity_dashboard.write_dashboard("cache/trinity_dashboard.html")`.

5. **Persist.** `pantheon.persist("shared", {"cache/trinity_dashboard.html": html}, branch="claude/live")`.

## Notes

- This command does NOT trade. It only reads sleeves, fetches quotes, and regenerates the dashboard.
- If no positions are open across all four gods, still run — the dashboard shows cash balances and equity history.
- The dashboard auto-refreshes in the browser every 15 min (`<meta http-equiv="refresh">`), so new data appears on the next page reload after this routine pushes.
- To install on your phone: open the dashboard URL in Safari/Chrome, tap Share → Add to Home Screen. It opens as a standalone app.
- The dashboard is persisted under the "shared" ownership prefix. Curve files are owned by their respective gods and are persisted during each god's main run.
