# /oracle-research — dossiers-only pass

Writes dossiers WITHOUT triggering scoring/execution. Requires at least 8
fresh dossiers in the result. Use when you want to accumulate research
between full `/oracle` runs.

## Steps

1. Load existing dossiers from `cache/oracle_dossiers.json`.
2. Pick 15–40 candidates from `cache/oracle_screen.json`. Research **wider** than the ~8 you'll ultimately hold, so the dossier scoring — not the screen — selects the book. Prefer names you haven't recently dossiered; the goal is to accumulate a bank of ≥30 dossiers across passes so sizing has real choice.
3. For each candidate, build the dossier **balanced**. The screen surfaces names
   insiders are *buying* — which includes genuine bargains AND falling knives.
   The job is to tell them apart, which means arguing **both** sides honestly and
   answering the one question that decides it: **is the bad news already priced
   in?** Do not put a thumb on either scale — an over-bullish thesis and a
   reflexively-bearish one are both miscalibrated. "Contested" is not
   disqualifying; value names are *always* contested — the edge is the gap
   between price and value given the bear case, not the absence of a bear case.

   - **Ground in current reality (do NOT rely on memory).** Fetch the **current
     price and 52-week high** (broker quote); compute the drawdown. This is the
     non-negotiable part — verify, don't recall.
   - **"Why is it here?"** Verify recent price action against current sources —
     latest 8-Ks, earnings/guidance changes, downgrades, lawsuits, recalls, news.
     **If the name is down >30% from its high, you MUST explain what drove the
     decline** in `decline_explanation` (the falling-knife gate rejects an
     unexplained big-decliner — but this gate is about *honesty*, not pessimism;
     an explained, priced-in decline is a perfectly valid buy).
   - **State both cases, then judge priced-in.** Give the genuine bull case and
     the genuine bear case (the real thesis-killer, not a token). Then the
     decisive call: is the bear case *more* than reflected in the price (→ a
     mispriced bargain) or *less* (→ avoid)? Set scenario probabilities/targets
     to your honest calibrated estimate — neither inflated nor deflated.
   - **Insider context.** Who bought, when, at what price vs. now (underwater?),
     long-tenured management or a new regime? And does it actually check out
     against current filings — don't assume the screen's flag is real.
   - **What would make this wrong?** State the disconfirming evidence you'd watch.
   - Fundamentals via `shared.fundamentals.build_snapshot`; cite ≥1 SEC accession.
   - Rate moat / runway / quality / management on [0, 1] after weighing both sides.
   - `oracle.research.make_dossier(..., current_price=…, high_52w=…,
     decline_explanation=…)` — validates (incl. the falling-knife gate),
     auto-normalizes probabilities, computes derived metrics, records the drawdown.
4. If fewer than 8 fresh dossiers are produced, abort and warn — this command requires that minimum.
5. Save via `oracle.research.save_dossiers`.
6. Persist via `pantheon.persist("oracle", {"cache/oracle_dossiers.json": data})`.

DO NOT place any orders from this command.

## Rebalancing an existing dossier

If you're rewriting a dossier's scenarios after the fact (e.g. swapping
adversarial framing for balanced), use **`oracle.research.update_scenarios(d,
new_scenarios, current_price=…)`** — NOT a hand-edit. The helper requires a
fresh price as a keyword argument, which forces thesis and price to come from
the same moment. A rebalance that rewrites scenarios but reuses the old
`current_price` leaves the dossier internally inconsistent (and was the
silent bug behind the "why is the dossier price different than today's
quote?" question on 2026-06-28).
