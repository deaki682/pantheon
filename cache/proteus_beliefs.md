# Proteus v2 — beliefs (rewritten 2026-07-23, session 17: DOMO/Progress asset-sale read — FIRST GRADABLE SHADOW on the record; declined at the tape)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 17, Thu 2026-07-23 ~14:10Z, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-17 mark:
  equity $2,462.50 (VOO 680.735 / SPY 740.52 @14:07Z), −1.88% from peak
  $2,509.62. No Title I ladder triggers (dd tier 0, computed in code).**
- Reconcile 7/23: CLEAN — broker VOO 3.536615 == sleeve; zero account
  orders by ANY god since 7/22 14:10Z; ledger 6 rows unchanged.
- Journal: **85 rows** after session 17 (81 + session-open/pre-read note
  + leg-1 note + leg-2 note + DOMO disposition; verified by `wc -l`).
  All via `proteus.schema.append_record` (which REFUSED my first
  malformed disposition — the schema works; field names are
  name/verdict/reason/shadow_primary/divergence).
- No code changes session 17 → integrity gate not triggered. My latest
  code commit still `4cc587d`.
- Real-money grades: 0. Probe caps bind everything. Calibration table
  empty, Kelly multiplier 0.25 (computed in code at session open).

## OPEN SHADOW PRIMARY — grade at maturity (do not lose this)

**DOMO gradable shadow (journal row 85, 2026-07-23) — the FIRST gradable
shadow in the record.** Declined a probe-long after a three-leg read
reversed the journaled pre-read live-leaning. Grading rule, as written:
if DOMO official close ≥ **$4.60** on any trading day 2026-07-24..
2026-11-30 → decline WRONG (hypothetical +$28.66 on 59.70 sh @ 4.12);
otherwise RIGHT (P&L marked at the 11/30 close vs 4.12). **Maturity:
first session on/after 2026-12-01.** Stated p(hit)=0.45, class
neglected_read, judgment document_read, tag SHADOW (feeds calibration
only, never unlocks ladders; at review, shadow+flat-month grades must
stay strictly fewer than half of counted n). Track DOMO's close daily
at reconcile — note that the ticker will be RENAMED pre-closing
(APA §8.2(f)); if the symbol changes, the grade follows the renamed
listing (same CIK 0001505952).

## STANDING DUTY — art. 16 staging still armed (do not forget)

`proteus/journal.py` was materially diffed 2026-07-15 and NO live order
has run since. **The NEXT live order runs STAGED: minimum executable
size, dry-run-verified vs review_equity_order same-session, journaled
PROCESS, before full Title I sizes.** Charter law, not preference.

## What session 17 did (act on this, don't re-derive it)

**Feed3 daily scan 7/22..23: 3 raw hits — the first since 7/14.** SAFX
(nano de-SPAC loan boilerplate) and PRGS (acquirer side) killed at
screen; **DOMO worked in full** (the kill-spec clock now has its first
worked candidate; feed3 matures ~9/12).

**The DOMO event, for reuse:** Domo sells substantially all assets to
Progress Software for $400M base (8-K 0001104659-26-085819; APA = PRGS
EX-2.1 acc 0001552781-26-000390). Signed 7/22 under lender forbearance
(6/12, ARR covenant breach, unwaived; forbearance ends at earliest of
no-close-by-11/30 or unrestricted cash < $10M). Written consent locked
within 1hr of signing (founder 76% vote, shares PLEDGED — foreclosure
is a termination path 9.1(c)(v)). Conditions: HSR + info statement
mailed ≥20 days pre-close + rename/de-DOMO the ticker. Earliest close
~mid/late Sept; outside date 11/30. Fee $13.5M one-way (Seller pays,
incl. lender-caused termination). Three-leg arithmetic (rows 82–85):
wire ≈ $243M; diluted ~52.5M shares; value ~$4.63 pre-leakage,
$4.15–4.45 after the retained stack — vs tape $4.11 (+30% on the day).
**No variant view: the tape priced it in a day. Declined; shadow set.**

**Recheck dates:** GLXZ/Evolution merger-break watch 2026-08-03; AGEN
chain-readability ~mid-Aug; DOMO shadow maturity 2026-12-01; feed3
kill-spec ~2026-09-12.

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: index park
  IS the benchmark — no monthly cash-beats-SPY prediction owed. Exits
  ONLY to fund an entry clearing the full bar, or on the kill switch.
  >1 index-park round trip in a rolling month = thesis in disguise.
  **July flat-month posture note owed at the 7/31 or 8/1 session.**
- **Kill-spec clocks: only ONE running — feed3** (7/14, 60d → matures
  ~9/12). Session 17 is the first session it surfaced a worked
  candidate (DOMO). Odd-lot: TRIPPED/DEAD 7/21. ITC family:
  measured-dead 7/20. No successor specs without new evidence (art. 12).
- Wash-sale ledger fact: $0.0012 SPY loss realized 2026-07-13. Any SPY
  re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- First record brief due at 20 graded decisions or by 2026-10-11.
- Art. 22: NO typed events session 17 (no orders, no cadence change, no
  drawdown crossing, no integrity stop, no collision — a declined
  candidate and a shadow are not on the typed list) → no push.
- Art. 20c watch: Hermes ALOT/APGE/RAMP/GBTG/TMHC/FSEA/OGN (checked
  7/23: closed[] empty — no break-stop exit; standing deal-break watch
  quiet); Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus the N50 book
  (monitoring-only until 2026Q3). DOMO unclaimed — verified at the
  disposition.

## Where MY edge might live (updated honestly)

1. **Neglected-corner reads + the shadow book** — now 33 dispositions
   + the FIRST GRADABLE shadow (DOMO). The lane keeps accumulating
   honest evidence; the DOMO read cost one session and produced a
   falsifiable, dated counterfactual instead of a thin-EV trade.
2. **Single-name event theses from the eventfeed inventory** — AGEN
   2026-11-26 financing cliff (recheck ~mid-Aug); INMD respondent-side
   ITC FD (12–18mo); deal-break reversion on Hermes break-stop exits
   (opportunistic lane, free sourcing). Theses, not channels.
3. **A NEW event family, base-rated first (lesson 13).** Dead/starved/
   demoted so far: deadlines (both sides), ITC channel, tenders +
   odd-lot, spinoff orphans and spin-mechanics, deal-break-as-channel,
   index additions (house), CEF tenders (house). Remaining unmeasured:
   tax-loss-selling calendar (backlog #21 — build the base rate in
   October, window Nov–Dec).
4. If nothing survives by feed3's maturity (~9/12), the honest posture
   per art. 21 is the park plus research — say so plainly in the record
   brief.

## Plan (next session)

- (a) Reconcile; mark curve vs SPY; **check DOMO's close vs the $4.60
  shadow line** (cheap daily check while the shadow is open).
- (b) Daily DEADLINE scan (yesterday..today). Check Hermes sleeve/ledger
  for any break-stop exit. GLXZ recheck due 8/3.
- (c) MAIN WORK candidates, in order: (i) **July flat-month posture note
  due 7/31 or 8/1** (index-park type: exempt from the cash-beats-SPY
  prediction; record why parked rather than hunting); (ii) AGEN
  chain-readability recheck ~mid-Aug — not yet; (iii) the deferred
  historical deal-break tape study — HEAVY, needs a full session +
  primary-doc population plan; (iv) calibration/registry plumbing for
  the record brief (due by 10/11).
- (d) If ANY entry is contemplated: art. 16 staged order FIRST, art. 26a
  arithmetic, full entry schema, art. 20c collision check.
- (e) NO park round trips.

## Lessons (cumulative scar tissue — keep ALL of these)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down.
   Verify SYMBOLS at the broker/EDGAR submissions, never regex display
   names (CRBD→CRBG 7/13; CIK-resolution 7/14).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. Honest kills compound: 32 dispositions through 7/22 + SAFX/PRGS
   killed-at-screen and the DOMO gradable decline 7/23. The record shows
   the reading working before the wallet.
6. Verify the record before trusting any summary of it — including mine.
   Counts are computations, never recollections.
7. Session containers are ephemeral and shallow-cloned: `git fetch
   --deepen` before reasoning about history; `pip install pytest numpy`
   before the suite (~1 min, then ~1924 tests in ~4s).
8. In-session crons/one-shot wakes DIE WITH THE CONTAINER — graded
   REFUTED 7/13. Only operator-provisioned Routines wake me. Size every
   entry to the blind unattended worst case.
9. Screens lie through their inputs before they lie through their logic:
   gate every LEG of every quote on its own merits; take ALL dates per
   window on 8-K prose.
10. RH dollar orders truncate at 6dp. Dry-run → place → verify-fill →
    ledger → sleeve, in that order, every time.
11. A feed's first live window is part of the build; machinery that finds
    nothing tradable is only NOT-YET if you name the fix; the kill-spec
    clock keeps it honest.
12. Default-path arguments are traps in a repo with live and ghost twins
    of the same file. Pass paths explicitly or pin them with a regression
    test. Dispositions/grades go through `schema.append_record`.
13. Measure a query's/channel's base rate BEFORE adding or building. And
    measure it at the RIGHT WINDOW: a base rate needs a denominator big
    enough to mean something.
14. A sample of 3 is an anecdote, not a population. (1-in-25 has a
    Wilson CI of 0.2–20% — read the full census of the high-precision
    channel instead of extrapolating the noisy one.)
15. An event date the market has already dated (kink) OR cannot price at
    all (unreadable marks) is equally untradable — the edge needs a
    readable chain AND a divergent view. Check readability before
    spending the read.
16. **A legal WIN can be a tape LOSS — on a SAMPLE (n=12, 7/20).** The
    market grades remedy SCOPE and economic substance, not the verdict.
17. Delisted names are invisible to broker historicals — build study
    populations from primary documents (FR/EDGAR), then resolve tickers
    as_of via Sharadar. Volume-check movers before believing an
    abnormal return (earnings contamination).
18. **A query hit is a MECHANISM CLAIM until the document says so.**
    Count mechanisms, never keywords — and classify by reading, not by
    form type (~96% of termination-phrase hits were boilerplate).
19. **Journal corrections are APPENDED, never edited.** No de-minimis
    exception.
20. **A refutation's own table can kill an adjacent idea for free.**
    Re-read the refutation's numbers at your horizon BEFORE designing
    any study on scorched-adjacent ground.
21. **Stub/deal math is share-count and cash-mechanics math (DOMO,
    7/23).** A naive stub discount computed from basic shares and
    headline debt was off by ~25 points: diluted shares ran 40M→52.5M
    (penny warrants to LENDERS, RSU engine, +1.9M in six weeks) and the
    APA's cash treatment (Buyer takes ALL cash, credits only $25M;
    Indebtedness defined to include LT deferred revenue, PTO, AP>$14M,
    PIK exit fees) moved the wire ~$25M. Read the Indebtedness
    definition and the cash-adjustment DIRECTION before believing any
    discount — and journal the pre-read leaning BEFORE the read so the
    reversal is gradable (that discipline just produced the record's
    first gradable shadow).
