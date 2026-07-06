# Oracle selection-pipeline audit — full bug ledger (2026-07-06)

Prompted by "no FPH to be found — the selection process isn't adding up," then "every
potential bug." Six adversarial code-audits across the active cold-start pipeline
(sourcing screens → freshness → fundability ranker → verification gate → runners/wiring).
**~30 distinct defects.** The individual algorithms are mostly sound; the WIRING between
them is pervasively broken — components were built and unit-tested in isolation and never
integrated, so the "machine" that produced the cold-start book was really a hand-assembled
single-leg subset with most of its guards inert.

## The meta-finding

The cold-start book (XBIT, STRS) rests on genuine primary-source verification of *those two
names*. But the SELECTION that produced them was **not the designed machine**: the
asset-revaluation leg was never in the unified path, freshness never ran, and the ranker
was never fed the full candidate set. So "the top of the universe" is unsupported — they're
the best of a truncated, un-reconciled, net-cash-only slice. That is exactly the smell.

## CRITICAL — the pipeline never ran as designed

1. **Asset-revaluation leg never wired into the combined file.** `run_oracle_sourcing.py`
   imports only forced_seller / hard_catalyst / neglect (never `asset_revaluation`); the
   combined `cache/oracle_sourced_candidates.json` contains 0 of the 85 land names. The
   entire FPH family is invisible to the unified pipeline; FPH only ever surfaced because a
   manual pass ranked the separate asset-reval file.
2. **Freshness + fundability ranker never called by any runner.** `freshness.apply_reconciliation`
   and `convex_dossier.rank_fundable` are referenced only in tests and docstrings. No runner
   reconciles the candidates or ranks the full 365; the ~54 that got ranked were a manual/head
   subset. This is why zero candidates carry freshness flags.

## HIGH — correctness holes in the screens and the safety gate

3. **Verification gate defeated by a default: `book_survives_goodwill` defaults `None`, and
   `None is not False` → True** (convex_dossier.py:258). A book-floor dossier passes the
   goodwill trap without the tangible-book check ever running — the MNRO kill, reopened.
   Unknown must fail-closed for book/asserted floors.
4. **Primary-source trap defeated by substring matching** (convex_dossier.py:215-226).
   `is_primary_citation` markers like `"s-1"`, `"acc "`, `"10-q"` fire on incidental text
   ("consen**sus-1**", "**acc**rued"), so a snapshot-only citation passes — the XRN hole.
   And it checks *any* citation, not the one backing the FLOOR.
5. **Blank currency defaults to USD** (neglect_screen.py:164): `(currency or "USD") != "USD"`
   admits a foreign filer with a missing TICKERS currency, re-creating the phantom
   filer-currency-floor-vs-USD-cap discount the FX guard exists to block.
6. **Null balance-sheet fields coerce to 0 → phantom floors** (neglect_screen.py `_num`;
   same in asset_revaluation.py:89). A missing `debt` line ⇒ full cash counted as net-cash
   (the XRN "debt-free off a missing line" trap); a missing `liabilities` ⇒ entire current
   assets reported as an NCAV net-net floor.
7. **`is_clean()` fails open** (freshness.py:111): an un-reconciled candidate returns True.
   Since reconciliation never runs, the gate cited to "gate the verification queue" passes
   everything.
8. **Office/Retail/Hotel/Healthcare REITs mis-classified as land** (asset_revaluation.py:63-65):
   for a re-rated-down office market, depreciated cost is a CEILING, not a floor — yet these
   post the HIGHEST coverage scores (BHM 23x, ESBA 13x) and would monopolize the land_nav
   verification slots, burying genuine land developers (FPH) again.
9. **Combined vs standalone neglect files disagree** (323 vs 280 names): two divergent truth
   sources for the same leg; downstream reads one and silently loses the delta. Non-reproducible.
10. **Pool-exclude reads the wrong nesting level** (run_oracle_neglect_screen.py:79 /
    run_oracle_sourcing.py:50): iterates `data.values()` instead of `data["dossiers"]`, so the
    already-held/already-dossiered exclude set is near-empty and dedup is effectively disabled
    for the neglect leg (asset-reval does it correctly — an inconsistency).

## MEDIUM

11. Ranker annualization inflates thin short-horizon bets: +5%/1mo scores 0.60 > +50%/12mo =
    0.50 (convex_dossier.py:73-75) — treats a one-shot bounded loss as annually repeatable.
12. `recent_dilution` guard dead-by-default — `prior_sharesbas_by_ticker` defaults `{}`, so the
    flag is False for every name (neglect_screen.py:216-218).
13. Resource reserves (gold/coal/uranium at cost) get the same hard-floor gate as appreciating
    land; `commodity_dependent` flag computed but never used to down-rank (asset_revaluation.py).
14. `apply_reconciliation` runs only the marketcap check, never the crypto / book-contradiction
    checks — 2 of 3 advertised freshness checks silently omitted (freshness.py:116).
15. `reconcile_marketcap` fails open when the broker cap is missing — the stale-count name it
    exists to catch is retained whenever the live feed is unavailable (freshness.py:61).
16. Catalyst-fired can be funded: both signals (`recent_runup_pct`, verifier `catalyst_fired`)
    default to "not fired" and nothing cross-checks them against price history at gate time.
17. Stale `floor_hardness`/`convexity_score` left on a verify FAIL — a killed name still
    outranks honest ones in the research view (convex_dossier.py:272-279).
18. `floor_type` divergence between legs (neglect emits it, asset-reval doesn't) → dedup keeps
    the wrong record + a latent `KeyError` crash in run_oracle_catalyst_overlay.py:75/92.
19. "Agricultural Inputs" (fertilizer/chemical plants) and "Paper & Paper Products" (mills)
    wrongly in the appreciating-land set — plant-heavy PP&E that depreciates, against the
    lens's own exclusion rule (asset_revaluation.py:55,60).
20. `sweep_by_form` returns `[]` silently when `cik_to_ticker` is unset + `tradable_only=True`
    (forced_seller_sourcing.py:349) — looks identical to "no filings."
21. `cik_to_ticker_map` inversion collapses multi-ticker CIKs (GOOG/GOOGL, BRK.A/B) to one
    arbitrary share class (forced_seller_sourcing.py:342).
22. Event-leg dossier dedup no-ops: sweeps take `exclude_ciks` but the runner has only ticker
    keys, so already-dossiered names re-enter the verify gate every session.

## LOW

23. Crypto name/description markers are bare substrings → false matches ("defi" in "Definitive",
    "crypto" in "cryptographic", drops a legit RFID name) and false misses (" bnb " won't match
    "(BNB)") — neglect_screen.py:68 and freshness.py:43-47.
24. `runway_quarters`/`eroding` mislabel a tangible-book-floor name off a net-cash figure that
    isn't its floor (neglect_screen.py).
25. FLOOR_BASIS 4-level ladder collapses to 3 hardness weights on re-stamp — cash ranks
    identically to net-net (convex_dossier.py:275).
26. Length `_req`s gameable by whitespace padding; `DEAD_TRIGGERS` never gates funding
    (convex_dossier.py).
27. Double-space company names shift the daily-index column split → filer silently dropped
    (forced_seller_sourcing.py:328).
28. Whole-window fetch failure indistinguishable from "no filings" — no fetched/failed-days
    counter (forced_seller_sourcing.py:316).
29. Bare `except: pass` on exclude-pool load → corrupt cache silently yields empty exclude set;
    combined-write partial-write risk on non-FileNotFound errors (run_oracle_sourcing.py).
30. Daily-index files fetched twice per window (forced-seller + catalyst passes) — 2× network,
    not a correctness bug (run_oracle_sourcing.py:65,76).

## Already fixed this session (fundability ranker → tested module `oracle/fundability.py`)

- discount is floor-agnostic (reads nav_at_cost for land names) — the bug that buried FPH;
- per-family verification budgets so net-cash can't monopolize the slots;
- steeper >80% trap penalty; coverage-only fallback no longer needs a marketcap.

## What actually fixes the rest

Not more point-patches — an **integration rebuild**: one runner that (1) runs ALL legs incl.
asset-revaluation, (2) reconciles freshness onto every persisted record, (3) ranks the full
365 per-family through the fundability module, (4) feeds the verification queue — plus
hardening the gate's two fail-open holes (goodwill default, substring citation match) so the
four traps can't be defeated by defaults. Then re-run the cold start against a pipeline that
actually executes as designed, and re-check whether XBIT/STRS survive names that were never
allowed to compete (FPH first).
