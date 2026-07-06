# Oracle event legs — full verification (2026-07-06)

Ran the forced_seller and hard_catalyst legs to completion the same way as the
neglect leg — one primary-source verifier per candidate, leg-matched briefs
(NAV-discount for the CEF/BDC tenders; live-catalyst + floor for the
strategic-review / activist names). This is the honest measure of whether the
*event* legs supply the catalyst-driven convexity the neglect leg structurally
can't.

## Result: the event legs are THIN. Neglect is Oracle's real edge.

| Leg | FUND | WATCH | KILL | Fundable rate |
|---|---|---|---|---|
| **neglect** (net-cash cohort) | 4 | 11 | 12 | ~15% |
| **forced_seller** (CEF/BDC tenders) | 1 (JOF) | 2 | 5 | ~12% |
| **hard_catalyst** (13D + strategic review) | **0** | **0** | **14** | **0%** |

**The neglect leg is where the fundable convex floors are.** The two event legs,
as built, produced exactly one fundable name between them (JOF) — and it was
already found. That is a strategically important, honest result: Oracle's edge is
**below-floor value (neglect)**, not event-driven catalysts.

## forced_seller — 1 FUND / 2 WATCH / 5 KILL

The SC TO-I form enumeration surfaces the wrong mechanism most of the time:

- **JOF (FUND)** — the archetype and the exception: a *recurring COMMON*
  conditional-tender-at-98%-NAV governor. Genuinely convex.
- **EVV, EFR (WATCH)** — real ~7-11% discounts, but their SC TO-I filings are
  **Auction-Preferred-Share (leverage) tenders, not common pull-to-NAV** — no
  mechanism closes the common discount; 30-40% leverage, soft loan-book NAV.
- **EVF (KILL)** — same preferred-tender-not-common problem, tiny/soft.
- **EIIA, PGIM, FRBP, PRIF (KILL)** — **non-traded** interval/BDC funds: you
  subscribe and are repurchased *at NAV*, so there is no listed market discount to
  capture. Broker-untradable. Un-actionable by construction.

**Lesson:** a CEF's SC TO-I is usually a *preferred/leverage* action or a
*non-traded fund's at-NAV repurchase* — not a common forced-buyer event. The
odd-lot/fund-tender family is as thin as its own spec warned ("~1%/yr ceiling,
opportunistic only"). JOF-style *recurring common conditional-tenders* are rare
and are the only convex sub-type.

## hard_catalyst — 0 FUND / 0 WATCH / 14 KILL

The strategic-review-8K keyword sweep + raw SC 13D enumeration is **structurally
mismatched** to Oracle's bounded-floor thesis. Every one of the 14 failed, in
five distinct ways:

1. **Keyword false positives** (5) — "strategic" matched routine capital-allocation
   or acquirer language: ZYME, LIF, WY, AIRT, JHX.
2. **Acquirer-side** (3) — the company is the *buyer*, not the target: JHX (AZEK),
   LIF (Nativo), BTU (walked from Anglo met-coal).
3. **Already concluded** (2) — EHAB (closed cash deal, delisted), NOTV
   (prepackaged Chapter 11, equity cancelled).
4. **Hermes's domain** (1) — GNK (a hostile all-cash tender, fully priced; the
   "13D/A" was actually a TO-T acquirer filing).
5. **No floor / distress** (3) — GWH (going concern), DAIC (death-spiral nano-cap),
   FWRD (covenant-tight levered stub), TXMD (inverted asymmetry, sole asset under
   lawsuit).

**None is fixable by a threshold.** The leg's two enumeration signals are each
individually too noisy:
- **SC 13D enumeration** catches acquirer TO-T filings (GNK) and passive stakes,
  not just friendly value-realization activists.
- **Strategic-review keywords** catch acquirer-side boilerplate, concluded deals,
  and distress "evaluating alternatives," not just live sale processes with a floor.

## Actions taken (build the machine, not just the picks)

1. **hard_catalyst leg DEMOTED to a signal, not a sourcing leg.** Raw 13D +
   strategic-review enumeration does not stand alone (measured 0/14). Annotated in
   `oracle/hard_catalyst_sourcing.py`. Its correct role is a **cross-reference**:
   an activist 13D or a live strategic review *on a name that already has a
   verified below-floor* (a neglect FUND/WATCH) is the real "floor + catalyst"
   convex combo — the catalyst overlays the floor, it does not substitute for it.
2. **forced_seller CEF-tender family annotated**: the SC TO-I enumeration must
   distinguish *common conditional-tenders* (JOF, convex) from *Auction-Preferred/
   leverage tenders* (EVV/EFR/EVF, not convex) and *non-traded at-NAV repurchases*
   (EIIA/PGIM/FRBP/PRIF, un-actionable). A tradability + common-vs-preferred filter
   is the tightening; noted as the next build.
3. **The book is unchanged** — 5 verified names (INVE, XBIT, SEER, LAB, JOF); the
   event-leg pass added no new fundable names, which is itself the finding.

## The strategic conclusion

Across all three legs and ~40 primary-source verifications: **Oracle's real,
repeatable edge is the neglect leg — below-floor value in small, uncovered names.**
The forced-seller leg yields the occasional JOF; the hard_catalyst leg's
STRATEGIC-REVIEW-KEYWORD half is measured too noisy to stand alone, while its
ACTIVIST-13D half is UNTESTED here (a data gap — see "Data-completeness" below) and
must not be written off. The right architecture going forward
is **neglect as the spine, with forced_seller and activist-13D as catalyst
OVERLAYS on already-floored names** — not as standalone nets. That is the
house-view thesis (camp on structural forced-seller/neglect; a catalyst is a
bonus on a floor, never a substitute for one), now measured.

## Data-completeness audit (2026-07-06) — a real gap on the 13D channel

Prompted by the "0 fundable" result looking suspicious. Checked the EDGAR daily
form index directly across five trading days. The parser is CORRECT and COMPLETE
(reads all ~5,000 data rows/day), but the environment's EDGAR is **missing the
activist-filing channel**:

| Form | filings/day | verdict |
|---|---|---|
| Form 4 (insider) | ~1,700–2,090 | realistic, complete |
| 8-K | ~235–324 | realistic, complete |
| 10-Q | 4–27 | realistic, complete |
| SC TO-I | 0–6 | thin but present (forced-seller CEF findings are valid) |
| **SC 13D** | **0** | **near-empty — data gap** |
| **SC 13D/A** | **0–1** | **near-empty — data gap** |
| SC 13G / 13G/A | 0 | empty |

**Correction to an overstatement.** The hard_catalyst "0 of 14" was **13 from the
strategic-review KEYWORD sweep + 1 from the 13D channel**. So:
- The **strategic-review keyword** finding (noisy, structurally mismatched) is
  ROBUST — the 8-K data is complete and 13 names really did fail.
- The **activist-13D** channel was **effectively UNTESTED** — with ~0 SC 13D in
  the environment's index, the net had almost nothing to enumerate, and the lone
  hit (GNK) was an acquirer TO-T, not a friendly activist. It is WRONG to conclude
  "activist-13D sourcing doesn't work." It remains the most promising untested
  catalyst channel and must be re-measured against live/complete EDGAR.

**What IS trustworthy (data-complete):** the NEGLECT + asset-revaluation legs run
on the Sharadar fundamentals panel (5,700 names with marketcap, 5,593 with SF1) —
complete; and every primary-source VERIFICATION read an actual, complete 10-Q/10-K.
So the book (5 verified names) and all KILL/WATCH verdicts stand on complete data.
The only measurement weakened by a data gap is the activist-13D overlay — flagged,
not trusted.
