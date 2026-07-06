# Oracle pipeline rebuild — cold start #2 through the fixed machine (2026-07-06)

After the ~30-bug audit (docs/oracle_pipeline_audit_2026-07-06.md), the sourcing
pipeline was rebuilt and re-run. This is the honest re-answer to "no FPH to be found —
the selection process isn't adding up."

## What was fixed (all committed, tested)

- **Gate fail-opens closed:** `book_survives_goodwill` fails CLOSED on book floors
  (None no longer passes the MNRO trap); `is_primary_citation` uses word-boundary /
  accession-number matching (no more "consensus-1"/"accrued" faking a primary source).
- **Screen phantom-floors:** neglect rejects blank/missing currency; a floor whose
  senior-claim input is absent is marked untrusted. asset_revaluation emits floor_type,
  drops plant-heavy industries, and splits cost-overstates REITs (office/retail/hotel/
  healthcare) into a down-weighted `suspect` family.
- **Ranker (oracle/fundability.py):** floor-agnostic discount (reads land-NAV), per-family
  verification budgets, family-aware sweet spot for cost-basis floors, deterministic
  deeper-discount tiebreak, cost-overstates/commodity down-weighting.
- **Freshness now WIRED + fail-closed:** `run_oracle_pipeline.py` runs both legs, dedupes
  consistently, ranks per-family, and the caller applies `apply_full_reconciliation`
  (all three checks) to the queue via live broker fundamentals. `is_clean` fails closed.

## FPH is found — and graded honestly

In the rebuilt per-family queue FPH ranks **#3 in land_nav**, and after the (now-wired)
freshness pass it is **#1 in the land family at an 81% discount**. The machine surfaces it
on its own. Blind primary-source verification then grades it **WATCH, not FUND**: the land
floor is real and deep (Valencia + Great Park carried far below entitled-market value, book
alone 2.2x price, no distress, no dilution — it passes the cost-overstates / asserted-NAV /
goodwill traps), but there is **no realization catalyst** (controlled by Lennar/GFFP, no
buyback/dividend, cash reinvested into a new asset-management arm). The earlier "FPH = best
FUND (convexity 0.131)" was itself an artifact of the buggy gate; the fixed machine both
finds it AND grades it correctly.

## Freshness caught the traps the old path missed

IXHL (stale $48M -> $1.38B, above floor), SDHC (stale -> $813M premium homebuilder),
BNC + AVX (crypto-treasury shells) — all auto-dropped before spending verification.

## Rebuild verification result

| Verdict | Names |
|---|---|
| **FUND (new)** | **STHO** — ~60% discount to a wind-down NAV whose dominant asset is a LIQUID marked-to-market SAFE stake worth (net of margin) more than the whole stock; active monetization + 2028 debt wall. A land-family name the old net-cash-only pipeline could never surface. |
| **WATCH** | **FPH** (deep real land floor, no catalyst), LPA (IFRS already fair-values its property — no hidden upside), BCYC (real cash but ~$66M/qtr melt, partners walked) |
| **KILL** | AFCG (cannabis lender/BDC, asserted Level-3 NAV, 23.5% non-accrual), BRNS (approved reverse merger hands 66% of cash away), FBIO (minority-interest consolidation artifact + preferred + one-time PRV windfall), NXDT (Dondero affiliated-NAV, external-manager trap), IMA (dilutive melting ice cube) |

## The book now

**FUND: XBIT (conv 0.127, hard net cash) · STHO (0.070, liquid SAFE-backed wind-down) ·
STRS (0.022, approved liquidation).** WATCH bench headed by FPH. The land/asset-revaluation
family — previously invisible to the ranker and never in the unified pipeline — now
contributes a verified FUND (STHO) and the deepest WATCH (FPH), which was the whole point.
