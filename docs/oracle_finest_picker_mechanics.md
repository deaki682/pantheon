# Oracle — how each stage works, if truly designed to find the best (2026-07-06)

Companion to `oracle_finest_picker_roadmap.md`. The roadmap is the *shape*; this
is the *mechanism* — how each of the seven funnel stages actually works in a
best-in-class build. Five cross-cutting principles run through all of it:

- **Recall early, precision late.** Nets maximize recall (form-enumeration, not
  keyword); precision is spent only on the survivors. Cheap to keep a name;
  expensive to fund one.
- **Recency is signal.** Most edges are born the day a document lands. Work the
  *arrival* of information, not a quarterly re-scan.
- **Adversarial ensembles.** A thesis that survives a *majority refute attempt*
  is robust; one that survives a single reviewer is not.
- **Measure by type, not just by return.** Grade *prediction accuracy* per
  thesis-type — a pick that rose for an unpredicted reason is luck, not skill.
- **Memory closes the loop.** Each stage feeds the next session's version of an
  earlier stage. That's what makes it sharpen instead of just run.

---

## Stage 0 — The Field  ·  the arrival monitor

**Input:** the whole US-listed universe + ADRs (~7,000), plus the EDGAR daily
firehose.

**How it works.** Two layers. (1) A persistent universe table — every common +
ADR keyed to its *final* ticker (Sharadar's law: `resolve_ticker` before any
fetch, or history returns nothing / the wrong recycled company), stamped with
sector / industry / marketcap / liquidity, refreshed quarterly. (2) On top, a
**filing firehose**: poll the EDGAR daily index every session, classify each new
filing by form into the streams that matter — 8-K (by Item code), SC 13D/G, S-1 /
424B, DEF 14A, 10-K/Q, Form 25 / 15 (deletion / deregistration). The unit of work
is *"what landed since last run,"* time-ordered, not "re-scan 7,000 balance
sheets." A mandatory `coverage_note` states what is KNOWN missing (foreign-only
filers, expert-market names, sub-threshold caps); delisted series are archived so
the next study doesn't re-hit the no-delisted-bars wall.

**Why this is best:** it's an *arrival* monitor. If you only re-screen quarterly
you're blind to the catalyst on the day it becomes fileable — which is the day it
matters most.

---

## Stage 1 — The Nets  ·  orthogonal, blind, recall-maximizing

**Input:** the field + firehose. **Output:** ~400 candidates, each tagged with
which net(s) caught it (a name caught by three nets ranks higher) and a raw score.

Each net is a **recall-maximizing enumerator**, not a precision filter — allowed
to be noisy because Stage 2 triages. The measured lesson: form-enumeration is
~100% recall vs ~12% for keyword search.

- **Structural-state net** *(built — the spine).* Runs the Sharadar panel; per
  name computes the floor ladder — net cash (cash + current marketable securities
  − total debt), NCAV (current assets − total liabilities), tangible book (equity
  − intangibles − goodwill) — and flags marketcap < floor × (1 − margin). Plus the
  asset-reval mirror (land / PP&E / resource at historical cost below likely
  market — the ALCO/FPH shape). Emits `floor_type`, `discount`, and soft-flags
  (dilution, investments-heavy, eroding book, crypto-shell, cost-overstates).
- **Event net** *(built — forced_seller).* Form-enumerates price-insensitive
  supply / structure events off the firehose: SC TO-I (tenders), Form 25/15
  (deletion / deregistration), spinoff Form 10, post-bankruptcy fresh-start
  emergence, CEF/BDC wind-downs. A mechanical reason a name is mispriced
  regardless of fundamentals.
- **Catalyst net** *(built — hard_catalyst, used by intersection).* Enumerates SC
  13D/13D-A (activist) + strategic-review / management-change (8-K Item 5.02) +
  guidance-reset 8-Ks. Each carries `requires_item4_read` — the index sees the
  *filing*, the LLM must read the *intent*. Intersect with a floor; never fund
  alone (measured 0/14 standalone).
- **Text-anomaly nets** *(NEW — the leap; nets no screen can build because they
  require reading).* Run on the *firehose slice* (names that just filed), which
  keeps the per-name cost tractable:
  - **language-change** — semantic-diff this filing's risk factors / MD&A /
    going-concern / critical-accounting sections against the same name's
    prior-year filing; surface where the *meaning* changed (a "substantial doubt"
    appearing or lifting, a risk quietly removed, a hedge added).
  - **footnote archaeology** — read the notes (segment, off-balance-sheet,
    related-party, contingencies, subsequent events) for a disclosed-but-unpriced
    asset/liability: a segment worth more than the whole company, a reserve about
    to release, an equity-method stake carried at zero.
  - **narrative-gap** — pull the market's *story* (news / analyst framing via
    search) and the *primary documents*, flag divergence: the tape prices a
    decline the filings don't support, or vice versa. The pure text→signal edge.
  - **orphan securities** — enumerate post-merger stubs, tracking stocks,
    dual-class and holdco / lookthrough structures the tape misclassifies or
    mis-sums.

---

## Stage 2 — Triage  ·  cheap, parallel, recall-preserving

**Input:** ~400 tagged candidates. **Output:** ~40 with a live question.

**How it works.** A fan-out of lightweight LLM agents — one per candidate (or
small batch) — each with a tight, cheap prompt: given the net-tag plus the one or
two key facts (the floor number, the filing snippet, the catalyst), answer in a
paragraph — *is there a plausible asymmetric situation here, yes/no, and the
single reason?* Returns structured `{keep, reason, open_question}`.

The bar is **"could a deep read find an edge?"** not "is this an edge?" It kills
only the obvious dead ends — negative-equity stubs (OPTU), China VIEs (HTT),
serial-dilution shells (RBNE), at-NAV funds, above-book covered names (SCHL) —
and passes everything with a live question, carrying that `open_question` forward
as the deep stage's assignment.

**Best-in-class detail:** the triage bar is **calibrated from Stage 6** — if a
net-tag has historically triaged to ~all kills (standalone hard_catalyst), its
bar auto-tightens. The cheap stage learns from the record.

---

## Stage 3 — The Dossier  ·  the edge (deep + adversarial)

**Input:** ~40 names each with an open question. **Output:** ~15 verified
dossiers (+ kept kills, with reasons).

**How it works — five moves per name:**

1. **Assemble the record.** Pull the last ~3 years of 10-K/10-Q, every 8-K in
   window, the latest proxy, recent transcripts (`shared.edgar` + search). A real
   document set, not a snapshot.
2. **The primary read.** An LLM analyst writes the thesis *against the documents*:
   the floor (if any) with its basis on the trust ladder (cash > net_net >
   transacting_asset > book > asserted), the `upside_x` with the **specific**
   re-rating path, the structural `why_mispriced`, the catalyst + date — every
   number cited to an accession. **Both shapes allowed:** bounded-floor OR
   pure-selection (edge = comprehension, no floor required).
3. **The adversarial panel.** Independent agents, distinct lenses: a **bear**
   prompted to *kill* it (find the phantom debt, the fired catalyst, the melting
   floor — the XRN/MNRO/GNK/BTU refutations); a **bull** steelmanning the upside;
   a **judge** who reads both + the documents and renders keep/revise/kill with a
   probability. Diversity over redundancy — each verifier hunts a *different*
   failure mode. Run the bear **3× (ensemble)**; survive a majority-refute or die.
4. **The truth-gate (verification, NOT a floor-mandate).** The four traps —
   primary-source-cited, floor-not-merely-asserted (only if a floor is claimed),
   book-survives-goodwill, debt-reconciled-full-stack, catalyst-not-already-fired.
   A selection thesis with no floor *skips the floor traps* but still must pass
   source-cited + not-already-fired + facts-reconciled. Kill lies, not unproven
   theses.
5. **The output.** A dossier with a falsifiable prediction, a typed
   `kill_condition`, `floor_hardness` (if any), conviction, `thesis_type`, and the
   graded verdict — accessions cited. Survivors go to the book; **kills are kept
   with reasons** (the dataset buys its decision once).

---

## Stage 4 — The Book  ·  conviction, bounded

**Input:** ~15 verified dossiers. **Output:** the funded few.

**How it works.**
- **Rank** by risk-adjusted conviction — `convexity_score` for floor-plays; a
  *selection-conviction* score for reads (expected re-rating × probability × the
  LLM's calibrated hit-rate for that `thesis_type`, from Stage 6).
- **Size** concentrated, conviction-weighted — no equal-weight cohort. Per-name
  cap scales with `floor_hardness` where a floor exists (hard 1.0 / medium 0.7 /
  soft 0.45 × the cap). Selection-bets without a floor get a **separate, tighter
  discipline** — a hard notional cap + the 25%-concentration `risk_ack` — because
  their downside isn't bounded by an asset.
- **Correlation guard.** Cluster the book by driver (sector / catalyst-type /
  macro factor) and cap cluster exposure — don't fund five coal names or five
  rate-sensitive REITs and call it diversified.
- **Preserve the floor/selection split** — a fixed initial sleeve share to each
  arm, so the experiment gets a real sample of *both* rather than the
  better-measured floor arm crowding out selection before it's tested.

Concentration is the return lever; hardness-scaled + correlation caps make it a
*bounded option*, not a naked one.

---

## Stage 5 — The Verdict  ·  measure prediction, not just return

**Input:** every candidate in the pool (funded and not). **Output:** the LLM-lift
number + its decomposition.

**How it works.**
- Record every candidate in the A/B with `lens_score`, `llm_selected`,
  conviction, floor/upside, `entry_price`, `spy_entry`, `thesis_type`.
- **Arm A** = the dossier book; **Arm B** = the mechanical screen top-N by
  `lens_score`, computed automatically so the comparison is honest.
- At each name's horizon or kill, grade the outcome vs entry, **vs SPY**, and **vs
  its own falsifiable prediction** (did the predicted catalyst fire? did the
  re-rating happen for the predicted reason?).
- **Decompose:** split every metric floor-plays vs selection-bets. Headline =
  Oracle LLM-lift = A − B; the decomposition says *where* the lift is —
  avoidance (Arm A killed the losers), selection (Arm A's picks rose), floor, or
  read. That's what tells us what to scale.
- **Statistical honesty:** shrink the mean (small-n), carry the multiple-testing
  count, report confidence not point estimates.

The gate that separates skill from luck: a pick that rose for a reason the
dossier *didn't* predict grades as luck, and the calibration must know the
difference.

---

## Stage 6 — The Memory  ·  the loop that compounds

**Input:** the graded record. **Output:** a sharper Stage 1–4 next session.

**How it works.**
- **Calibration table** — per `thesis_type` (language-change / footnote /
  narrative-gap / floor / catalyst / forced-seller): running hit-rate + average
  lift. Feeds back into Stage 2 (triage bar), Stage 3 (panel priors), Stage 4
  (selection-conviction score). Oracle learns which of its own reads are real.
- **The belief file** — a living prose record (the Proteus `beliefs.md` pattern):
  worldview, open theses, lessons from kills, what decayed. Read at the top of
  every session, updated at the bottom; Oracle's continuity across runs.
- **Rotation as the moat** — track each edge's decay; as a text-net's hit-rate
  erodes (adoption competes it away), down-weight it and hunt the next
  capability-frontier net. The house-view rotation, operationalized: the position
  isn't the moat, the rotation is.

Without Stage 6, Oracle is a static screener with an LLM bolted on. With it, the
pipeline is self-improving — next quarter's triage is smarter *because* of this
quarter's grades. That is the difference between a tool that runs and an
instrument that sharpens.
