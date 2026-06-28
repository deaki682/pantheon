# /oracle-research — dossiers-only pass

Writes dossiers WITHOUT triggering scoring/execution. Requires at least 8
fresh dossiers in the result. Use when you want to accumulate research
between full `/oracle` runs.

## Steps

1. Load existing dossiers from `cache/oracle_dossiers.json`.
2. Pick 15–40 candidates from `cache/oracle_screen.json`. Research **wider** than the ~8 you'll ultimately hold, so the dossier scoring — not the screen — selects the book. Prefer names you haven't recently dossiered; the goal is to accumulate a bank of ≥30 dossiers across passes so sizing has real choice.
3. For each candidate, build the dossier **adversarially**. The screen surfaces
   names insiders are *buying* — which includes genuine bargains AND falling
   knives (a quality name down 50% on a real, thesis-killing problem). The
   research's job is to tell them apart, and the only way is to verify against
   **current** sources and argue the bear case — never the model's prior.

   - **Ground in current reality (do NOT rely on memory).** Fetch the **current
     price and the 52-week high** (broker quote). Compute the drawdown.
   - **"Why is it here?"** Verify recent price action against current sources —
     the latest 8-Ks, earnings/guidance changes, downgrades, lawsuits, recalls,
     recent news. **If the name is down >30% from its high, you MUST explain what
     drove the decline** and pass it as `decline_explanation` to `make_dossier`
     (the falling-knife gate rejects the dossier otherwise — by design).
   - **Argue the bear case for real.** The bear scenario is not a token low
     number — it's the actual thesis-killer (e.g. "growth admitted misleading +
     fraud suit + organic revenue now negative"). Set the bear probability and
     target to reflect it honestly; a credible bear case should pull the score
     down on its own.
   - **Insider context.** Who bought, when, at what price vs. now (are they
     underwater?), and is it long-tenured management or a new regime signaling?
   - **What would make this wrong?** State the disconfirming evidence you'd watch.
   - Fundamentals via `shared.fundamentals.build_snapshot`; cite ≥1 SEC accession.
   - Rate moat / runway / quality / management on [0, 1] — *after* the bear work,
     not before.
   - `oracle.research.make_dossier(..., current_price=…, high_52w=…,
     decline_explanation=…)` — validates (incl. the falling-knife gate),
     auto-normalizes probabilities, computes derived metrics, records the drawdown.
4. If fewer than 8 fresh dossiers are produced, abort and warn — this command requires that minimum.
5. Save via `oracle.research.save_dossiers`.
6. Persist via `pantheon.persist("oracle", {"cache/oracle_dossiers.json": data})`.

DO NOT place any orders from this command.
