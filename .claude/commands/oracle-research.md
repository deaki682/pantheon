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

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/` into the working tree so this session starts with real state, not empty defaults.

1. Load existing dossiers from `cache/oracle_dossiers.json`.
2. **Refresh stale dossiers first.** Run `oracle.research.check_staleness(dossiers)`
   — this flags any dossier older than 14 days OR whose price has drifted >20%
   from its scenario anchor. For each flagged name, re-research it from scratch:
   fetch fresh price/52w high, re-read recent filings, rebuild the thesis and
   scenarios. Use `oracle.research.make_dossier(...)` (not `update_scenarios`)
   so the full dossier is replaced, not patched. Replace the old dossier in the
   list. This ensures the bank never goes stale between screens — a dossier
   written 2 months ago whose company just reported earnings gets rewritten
   with current information before Oracle scores it.
3. **Pick candidates deterministically.** Call
   `oracle.screener.pick_candidates("cache/oracle_screen.json", "cache/oracle_dossiers.json", n=40)`
   — this returns the top N undossiered names from the screen, sorted by
   composite score. Do NOT hand-pick or cherry-pick — use the list it returns,
   in order. Research **wider** than the ~8 you'll hold so the dossier scoring,
   not the screen, selects the book. The goal is to accumulate a bank of ≥30
   dossiers across passes so sizing has real choice.
4. For each candidate, build the dossier **balanced**. The screen surfaces names
   insiders are *buying* — which includes genuine bargains AND falling knives.
   The job is to tell them apart, which means arguing **both** sides honestly and
   answering the one question that decides it: **is the bad news already priced
   in?** Do not put a thumb on either scale — an over-bullish thesis and a
   reflexively-bearish one are both miscalibrated. "Contested" is not
   disqualifying; value names are *always* contested — the edge is the gap
   between price and value given the bear case, not the absence of a bear case.

   - **Ground in current reality (do NOT rely on memory).** Fetch the **current
     price and 52-week high** from the broker — use `get_equity_quotes` for the
     current price and `get_equity_fundamentals` for `high_52_weeks`. These
     broker-sourced values MUST be passed to `make_dossier` as `broker_price=`
     and `broker_high_52w=`. The validator cross-checks them against any
     LLM-supplied values and rejects on >5% divergence. This prevents
     hallucinated price data from entering the pipeline. Compute the drawdown
     from the broker values. This is the non-negotiable part — verify, don't
     recall.
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
     decline_explanation=…, broker_price=…, broker_high_52w=…)` — validates
     (incl. the falling-knife gate AND broker price cross-check),
     auto-normalizes probabilities, computes derived metrics, records the
     drawdown. **Both `broker_price` and `broker_high_52w` are required** —
     fetch them from `get_equity_quotes` and `get_equity_fundamentals`
     respectively. Omitting them produces an unverified dossier (logged as a
     warning); supplying values that diverge >5% from broker raises a
     DossierError.
5. If fewer than 8 fresh dossiers are produced (counting both refreshed and new), abort and warn — this command requires that minimum.
6. Save via `oracle.research.save_dossiers`.
7. Persist via `pantheon.persist("oracle", {"cache/oracle_dossiers.json": data})`.

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

## Reference-class priors (measured 2026-07-03 — read before every dossier)

The full-population cluster replay (docs/oracle_replay_results_2026-07.md,
934 events, 2025–26) measured the pond every screen candidate swims in:

- **Base rate: 32% of insider clusters beat IWM at 12 months.** The
  median cluster name TRAILS small-caps by ~27%; p10 is −88%. The upside
  is a thin right tail (best event +955%). Your default posture on any
  cluster name is therefore skepticism — the average name on your desk
  loses, and the entire strategy is finding the tail.
- **A cluster is table stakes, not conviction.** Mechanically bought,
  the signal was REFUTED (−6.4%/yr vs IWM). Only selection can clear
  that drag. Write every dossier as if the burden of proof is on the
  bull case, because measured, it is.
- **Quality-screen pass + cluster was the WORST cell** (−12.4%, t −2.0;
  exploratory decomposition, one window — treat as a flag, not a law).
  Plausible mechanism: trailing fundamentals lag real deterioration, so
  "still looks clean + insiders buying the dip" often means the filings
  haven't caught up yet. When the screen says quality-pass, ask "what
  would these numbers look like NEXT quarter?" rather than taking the
  pass as comfort.
- **Activist 13D was the only lens that pointed positive** (+15%, noisy,
  n=26). A 13D alongside a cluster deserves real weight in the read.

These priors change how dossiers are READ, not what the sleeve does —
no mechanical rule changed. Any screen-weighting change requires its own
pre-registration on data the 2025–26 replay never touched.
