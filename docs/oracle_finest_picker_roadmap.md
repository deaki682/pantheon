# Oracle — the finest LLM stock picker (build reference, 2026-07-06)

A skeleton of what Oracle looks like at its highest degree: an instrument that
funnels thousands of names down to the most desirable few, where **the edge is
the LLM's read, not a screen.** This is the target we build toward — reference
it as we go. It is a vision, not yet the runbook.

---

## The creed (three clauses, none optional)

1. **Verify facts ruthlessly.** Every number in a thesis is checked against a
   primary filing. Phantom floors, fired catalysts, hostile raids dressed as
   activism, goodwill masquerading as book — all killed. This is honesty, not
   caution.
2. **Have courage about theses.** The *thesis* is allowed to be unproven. A
   catalyst-driven re-rating the LLM reads and the screen can't is exactly the
   bet Pantheon exists to test. Fund it (paper first), predict falsifiably,
   grade it.
3. **Grade without mercy.** Every pick is scored vs the screen, vs SPY, and vs
   its own written prediction. The edge is *measured*, never *assumed*.

**The distinction that unlocks it — verification ≠ conservatism.** Verification
asks "is this claim true?" Conservatism asks "is this edge proven?" Today's
Oracle uses a truth-gate (good) as a floor-mandate (bad), which kills honest
selection theses for the crime of being unproven — and so the A/B only ever
measures avoidance. The finest Oracle keeps the truth-gate and drops the
floor-mandate. Kill lies; test reads.

**Where the edge actually lives** (docs/house_view_llm_edge_2026-07-05.md): in
**reading text → signal** on names too small / weird / complex for sell-side or
quants, where the mispricing is structural (neglect, forced seller, complexity,
misclassification) and the barrier is one an LLM doesn't dissolve. The moat is
the *rotation*, not the position — camp where LLMs win, retreat as edges decay.

---

## The funnel — thousands → the few

Each stage is a *different kind of intelligence*, not just a tighter filter.
Counts are illustrative of the collapse, not targets.

### Stage 0 — The Field  ·  (~7,000 names + the filing firehose)
The universe is US-listed equities + ADRs **and the flow of new information**:
the EDGAR full-text stream (8-Ks, 13D/Gs, S-1/424Bs, proxies), earnings-call
transcripts, index-reconstitution events. Oracle watches the *flow*, not a
static list — most edges are born the day a document lands.

### Stage 1 — The Nets  ·  (~7,000 → ~400)
Multiple **orthogonal, blind** sourcing nets (multi-modal sweep — each net blind
to the others so nothing convex is left behind for lack of a net):
- **Structural-state** — below a countable floor (net-cash / net-net / tangible
  book) and asset-revaluation (land/resource below cost). *(built — the spine)*
- **Event** — forced sellers, spinoffs, index deletions, post-reorg stubs,
  tenders. *(built — forced_seller leg)*
- **Catalyst** — activist 13D, strategic reviews, management change, guidance
  resets. *(built — hard_catalyst leg, used by intersection)*
- **Text-anomaly (NEW — the real leap).** Nets no screen can build because they
  require *reading*:
  - **language-change detection** — this year's risk factors / MD&A / going-
    concern language vs last year's; the sentence that quietly changed.
  - **footnote archaeology** — buried segment economics, off-balance-sheet,
    related-party, a hidden asset or liability the headline metrics miss.
  - **narrative-gap** — where the market's *story* about a name diverges from
    what its primary documents actually say. This is the pure text→signal edge.
  - **orphan securities** — post-merger stubs, tracking stocks, dual-class and
    holdco/lookthrough discounts the tape misclassifies.

### Stage 2 — Triage  ·  (~400 → ~40)
A cheap, parallel LLM pass — dozens of lightweight agents, one paragraph each:
*"is there a there there?"* **Recall-preserving** — it kills obvious noise and
keeps anything with a plausible situation. Not deep; its only job is to protect
the deep stage's budget without discarding a live thesis.

### Stage 3 — The Dossier  ·  (~40 → ~15)  ·  THE EDGE
Per-name deep research, adversarial:
- **Primary-document read** — the last ~3 years of 10-Ks/10-Qs, every 8-K in
  window, the proxy, the transcripts. The LLM reads what the sell-side skips.
- **Thesis written for asymmetry** — *both* shapes allowed: floor-plays
  (bounded downside) **and** pure-selection reads (the edge is comprehension of
  a situation, no hard floor required).
- **Adversarial panel** — bull / bear / judge agents per name; the bear is
  prompted to *kill* it. Survives the refutation or it's cut.
- **Facts verified** — the four traps stay, but as a **truth** gate
  (primary-source-cited, not-merely-asserted, survives-goodwill, debt-full-stack,
  not-already-fired), *not* a floor requirement. Cite accession numbers.
- **Falsifiable prediction + typed kill** on every survivor.

### Stage 4 — The Book  ·  (~15 → the few)
Concentrated, conviction-weighted, **correlation-aware** (don't fund five
versions of one bet). Floor-hardness caps size where a floor exists; explicit
position discipline where the edge is a read. Concentration is the return lever;
the discipline is what makes it a bounded option, not a naked one.

### Stage 5 — The Verdict  ·  (grade everything)
**Two-arm A/B, graded separately** so we learn *which kind of intelligence pays*:
- **Arm A — the dossier book** (Arm B — the mechanical screen top-N).
- **Floor-plays vs selection-bets** tracked apart — is the lift in avoidance, in
  selection, or both?
- Each pick vs SPY and vs its own written prediction.
- Headline: **Oracle LLM-lift = A − B.** The number decides capital, not the story.

### Stage 6 — The Memory  ·  (compounding — what makes it *finest* over time)
- **Calibration by thesis-type** — track hit rate by *kind* of read
  (language-change, footnote, narrative-gap, floor, catalyst). Oracle learns
  which of its own instincts are real.
- **The belief file** — a living record of worldview, lessons, what decayed.
- **Rotation as the moat** — retreat from edges adoption has competed away;
  advance onto the capability frontier. The engine improves because it remembers.

---

## The roadmap — where we are → the Oracle

A genuine capability sequence; each phase is a prerequisite for the next.

- **Phase 0 — The Avoider (NOW).** Floor-gated. 7,000 → 1 (STHO). Proven-safe,
  but structurally can only demonstrate *avoidance* — it funds the names that
  need the least intelligence. The A/B is starved.
- **Phase 1 — Split the gate.** Verification ≠ floor-mandate. Selection theses
  pass the truth-gate without a mandatory hard floor. Two-arm A/B opens. *(This
  is the immediate change — turns Oracle from trap-avoider back into a picker
  whose edge is measured.)*
- **Phase 2 — The reading nets.** Build the text-anomaly sourcing (Stage 1
  NEW) — the pure text→signal edge no screen can replicate. The sourcing-side leap.
- **Phase 3 — The adversarial dossier.** Bull/bear/judge fan-out at scale
  (Stage 3), deep-read machinery on every finalist.
- **Phase 4 — The memory.** Calibration by thesis-type + belief file + rotation
  (Stage 6). Oracle starts compounding on its own track record.
- **Phase 5 — The Oracle.** Self-improving, knows its own edge, camps where LLMs
  win, funds the desirable few with conviction. The finest picker.

---

## The discipline (pioneer, not gambler)

The one line that separates this from "let the LLM buy whatever it likes":
**verify the facts, have courage about the thesis, grade honestly at the end.**
The measurement spine (Stages 5–6) is non-negotiable — it's what lets Oracle
take real swings at unproven selection edge *without* fooling itself. Paper first
(Oracle is pending_funding); a validated thesis-type earns capital and
concentration; a refuted one is cut on evidence, not assumed away at design time.

Avoidance-only violates *courage*. Funding lies violates *verification*. The
finest Oracle holds both.
