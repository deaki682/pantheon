# Oracle freshness reconciliation — cross-check the screen vs a live broker feed (2026-07-06)

Operator question: "we're using Sharadar; it depends how fresh the info is — are
we not cross-referencing fresh Robinhood data?" Correct instinct — and it closed
the #1 precision-only hole (stale share count) at the SCREEN stage.

`oracle/freshness.py`: the neglect / asset-revaluation screens compute the
discount off Sharadar's DAILY marketcap, which uses Sharadar's share count — and
that count LAGS post-quarter conversions / reverse splits / raises. FTH broke here
(Sharadar 1.34M shares → $31M cap → phantom "85% below net cash"; the true
post-conversion count was 25.78M → $590M cap → ABOVE net cash). Robinhood's
fundamentals feed carries the CURRENT count, so cross-referencing it turns three
precision-only traps into screen-stage catches:

1. **Fresh market cap** → recompute the discount; DROP a name whose live cap is
   back above its floor (the stale-count artifact). `stale_marketcap` flags a
   >20% Sharadar-vs-live divergence.
2. **P/B sanity** → a below-cash/below-book thesis needs 0 < P/B < ~3. P/B ≤ 0 =
   NEGATIVE book (no floor — FTH −0.22, BATL −0.42); P/B ≥ 3 = a data/currency
   artifact (LAWR reported yen → a phantom "net cash" while trading at 119× book).
   `book_contradicts_floor`.
3. **Description** → catches crypto-treasuries the NAME hides: AVX ("AVAX One"),
   BNC ("CEA Industries"/BNB), NAKA ("Nakamoto"), AIFC ("AI Financial"), SKYA
   ("SkyAI"/stablecoin) — their floor is a volatile coin pile. `crypto_treasury`.

## First run — reconciling the top-40 neglect candidates against Robinhood

| Bucket | n | names |
|---|---|---|
| **DROPPED** (fresh cap above floor — Sharadar stale) | 1 | FTH ($31M→$590M) |
| **FLAGGED** (below floor but contradicted) | 7 | AIFC, SKYA, AVX, BNC, NAKA (crypto), BATL (neg book), LAWR (pb 119, yen) |
| **CLEAN** (pass all 3) | 32 | incl. ESBA/BHM, stale-corrected ($128M→$970M, $39M→$108M) but still below floor |

**8 of the top 40 (20%) were stale-count or crypto/currency landmines caught with
NO 10-Q read.** The verification queue now starts from 32 clean names, not 40 with
8 traps. This is the highest-leverage hardening yet: a live broker feed is fresher
than any quarterly fundamentals vendor, and its P/B + description fields are two
free cross-checks on top of the market cap.

## Caveats (honest)

- A live SHARE COUNT catches stale-COMMON changes (conversions/splits/raises); it
  does NOT include as-converted preferred or in-the-money warrants (INVE's 7.13M
  preferred) — that fully-diluted haircut is still a 10-Q job.
- `robin_stocks` is absent in this environment, so `shared.broker` returns nothing
  from a plain script; the live feed is fetched via the operator/assistant's MCP
  `get_equity_fundamentals` (≤10 symbols/call) and handed to `apply_reconciliation`
  / `reconcile_with_fundamentals`. Run it on the ranked shortlist (the top of the
  discount list, where stale caps masquerade as the deepest discounts).

## Standing use

Between sourcing and dossier-writing, reconcile the screen shortlist against the
live broker feed and drop/flag before spending verification effort. It is the
cheapest possible filter — one batched quote call turns the deepest, most
suspicious "discounts" from landmines into a clean queue.
