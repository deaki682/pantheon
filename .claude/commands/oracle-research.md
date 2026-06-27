# /oracle-research — dossiers-only pass

Writes dossiers WITHOUT triggering scoring/execution. Requires at least 8
fresh dossiers in the result. Use when you want to accumulate research
between full `/oracle` runs.

## Model routing

Filing reading is high-token / low-reasoning — cheap inference matches the
task. For each filing body (10-K, 10-Q, 8-K, S-1, proxy), dispatch the read
via the Agent tool with `model: "sonnet"` (or `"haiku"` for short
filings). The subagent's job is: pull the relevant section, extract
business model, recent results, key risks, and any quoted figures with
exact text. Reserve the main session model (Opus) for synthesis: choosing
scenarios, weighting probabilities, writing the thesis paragraph,
deciding citations. The 10-K read alone can be 30k+ input tokens; routing
to Sonnet saves roughly 5× on that step at near-identical extraction
quality.

Example dispatch:
```
Agent({
  subagent_type: "Explore",
  model: "sonnet",
  description: "Read 10-K Item 1A + 7",
  prompt: "Read this 10-K body. Return a structured summary:
    - business: 2 sentences on what they do
    - moat: any defensibility claims with exact quotes
    - top 3 risks from Item 1A with exact quotes
    - latest revenue, OCF, FCF figures with exact lines
    Body: <filing text>"
})
```

## Steps

1. Load existing dossiers from `cache/oracle_dossiers.json`.
2. Pick 8–15 candidates from `cache/oracle_screen.json`. Prefer names you haven't recently dossiered.
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
