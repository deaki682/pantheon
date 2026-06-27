# /oracle-research — dossiers-only pass

Writes dossiers WITHOUT triggering scoring/execution. Requires at least 8
fresh dossiers in the result. Use when you want to accumulate research
between full `/oracle` runs.

## Steps

1. Load existing dossiers from `cache/oracle_dossiers.json`.
2. Pick 15–40 candidates from `cache/oracle_screen.json`. Research **wider** than the ~8 you'll ultimately hold, so the dossier scoring — not the screen — selects the book. Prefer names you haven't recently dossiered; the goal is to accumulate a bank of ≥30 dossiers across passes so sizing has real choice.
3. For each candidate:
   - Fetch fundamentals via `shared.fundamentals.build_snapshot` (cached 30 days).
   - Read SEC filings: latest 10-K, 10-Q, 8-K via `shared.edgar`.
   - Compose business + thesis paragraphs.
   - Lay out 3 scenarios (bull/base/bear) with target prices and probabilities.
   - Rate moat / runway / quality / management on [0, 1].
   - Cite at least one accession.
   - `oracle.research.make_dossier(...)` — auto-normalizes probabilities and computes derived metrics.
4. If fewer than 8 fresh dossiers are produced, abort and warn — this command requires that minimum.
5. Save via `oracle.research.save_dossiers`.
6. Persist via `pantheon.persist("oracle", {"cache/oracle_dossiers.json": data})`.

DO NOT place any orders from this command.
