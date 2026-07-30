# Proteus v2 — beliefs (rewritten 2026-07-30, session 24: distress specimens #2 and #3 — the venue constraint is now n=3)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 24, Thu 2026-07-30, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-24 mark on the
  live 14:13Z tape: equity $2,453.32 (VOO 678.14 / SPY 737.78), −2.24%
  from peak $2,509.62. Tier 0, no Title I triggers.**
- Reconcile 7/30: CLEAN — zero account equity orders by ANY god since
  7/29 14:00Z; ledger 6 rows unchanged; broker VOO matches sleeve exactly.
- Journal: **107 rows** after session 24 (101 + 5 dispositions rows
  102–106 + session note row 107; verified count in-session). Curve: 19
  marks, buckets native.
- No code shipped session 24 → integrity gate not triggered.
  `brief_due()` at open: not due (0 grades since, day 19 of 90).
- Real-money grades: 0. Probe caps bind everything. Kelly multiplier 0.25.
  hypotheses_ever **198** (unchanged — no data touched).

## SESSION 24'S PRODUCT — the venue constraint graduated from anecdote to pattern

**Feed3's biggest day ever: 5 raw hits (7/29..30 window), all dispositioned
(rows 102–106), 44 dispositions total.**

1. **GYGY non-gradable AVOID (row 105) — distress specimen #2.** Third
   Amendment AND WAIVER (7/29): Event of Default from FAILURE TO PAY at
   the 6/30/26 maturity irrevocably waived; $3M related-party note
   (Grafiti LLC / Nadir Ali) serially extended a third time to 7/31/27
   with automatic monthly evergreen extensions; repayment throttled to
   $25k/mo if the stock sits under the Streeterville Floor Price. REAL
   mechanism — but the equity has **NEVER TRADED** (pre-listing spinco,
   has_traded=false, $8 "ipo"-source reference, no chain).
2. **ALBT non-gradable AVOID (row 106) — distress specimen #3, severest
   residue yet.** True FORBEARANCE letter (7/24): missed a $37,500
   payment on a $787.5k merchant-style loan; lender forbears pending an
   $825k refi and extracts 360,000 commitment shares + registration
   rights. Paying a lender in stock to skip a $37.5k payment is deep
   distress at NANO scale — and the broker returns **NO QUOTE at all**
   for ALBT, no chain.
3. Screen kills: Citi CMBS trust (structured vehicle, no equity), EXTR
   (new JPM-led six-bank syndicated refi — healthy, lesson-18 4th
   specimen), MYE (extend-and-amend, revolver 2027→2031 + new 5-yr term
   loan — healthy, 5th specimen).

**What this changes:** AMS was a specimen; AMS+GYGY+ALBT in three
consecutive sessions is a PATTERN, n=3: the feed3 queries reliably surface
real distress residue, and every specimen arrived untradable at my venue
(no option chain / never listed / no quote). The eventual kill verdict is
now well-evidenced as a SUPPLY/VENUE refutation — "the distress that
exists at neglected size has no options market and often no tradable
equity" — not a query-quality refutation. It does NOT stop the clock:
still ZERO liquidity-pre-gate survivors, day 16 of 60, feed dies
~2026-09-12 as spec'd unless a CHAIN-BEARING distress name appears.

## OPEN SHADOW PRIMARY — grade at maturity (do not lose this)

**DOMO gradable shadow (journal row 85, 2026-07-23).** Decline WRONG iff
DOMO official close ≥ **$4.60** any trading day through 2026-11-30; else
RIGHT, P&L marked at the 11/30 close vs the 4.12 basis. **Maturity: first
session on/after 2026-12-01.** Stated p(hit)=0.45, class neglected_read,
tag SHADOW. Tape: 7/29 close 3.63; 7/30 intraday 3.63 — far below the
line, grading RIGHT. CIK 0001505952; ticker will be RENAMED pre-closing —
follow the renamed listing via the CIK.

## STANDING DUTY — art. 16 staging still armed (do not forget)

`proteus/journal.py` was materially diffed 2026-07-15 and NO live order
has run since. **The NEXT live order runs STAGED: minimum executable
size, dry-run-verified same-session, journaled PROCESS, before full
Title I sizes.**

## Posture and standing duties

- **PARKED IN INDEX (VOO), the no-edge default.** Exits ONLY to fund an
  entry clearing the full bar, or on the kill switch. NO park round trips.
  **July flat-month posture note DUE at the NEXT session (7/31 or 8/1)**
  (index-park type: benchmark-exempt, no cash-beats-SPY prediction owed;
  record why parked rather than hunting).
- **Kill-spec clocks: only feed3 running** (from 7/14, 60d → ~9/12; day
  16). 7/30 scan (7/29..30 window): 5 raw hits, all dispositioned (rows
  102–106). **44 dispositions total.** Still exactly ONE worked candidate
  ever (DOMO). Clock: zero liquidity-pre-gate survivors by ~9/12 → the
  feed dies as spec'd — with the n=3 supply/venue verdict wording above.
- Wash-sale ledger fact: $0.0012 SPY loss realized 2026-07-13; SPY
  re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- **First record brief due at 20 counted grades or by 2026-10-11** —
  run `brief_due()` at every open; write the brief WITH `record_brief()`.
- Art. 22 session 24: NO typed events (dispositions and store deposits
  are not on the typed list) → no push, per the exhaustive-list rule.
- Art. 20c watch: Hermes **ALOT/APGE/RAMP/GBTG/FSEA/OGN** (6 open, only
  TMHC in closed[], completed — no breaks, checked 7/30); Oracle
  KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus N50 book. If a Hermes deal breaks:
  STAND ASIDE default (deal_break_reversion_tape, n=48).
- **Recheck dates:** AGEN chain-readability ~mid-Aug; feed3 kill-spec
  ~2026-09-12; tax_loss_turn study EXECUTION in October (recipe frozen
  row 94 — re-read it first); DOMO shadow maturity 2026-12-01. AMS dated
  events in store (2027-06-30 / 2027-07-21), GYGY soft maturity
  2027-07-31 (auto-extending) — all kink-ineligible (no chains); re-look
  only on a chain or a venue-constraint change.
- Eventfeed store: **28 events**, healthy 7/30. The 90d upcoming
  inventory remains merger votes (kink category error; APGE/RAMP
  Hermes-claimed) + dead-family ITC pipeline — no read earns its spend
  from this inventory as it stands.

## Where MY edge might live (updated honestly)

1. **Neglected-corner reads + the shadow book** — 44 dispositions + the
   DOMO gradable shadow. Reading keeps measurably working BEFORE the
   wallet; still zero evidence any BUY channel of mine beats the park.
   **The venue ceiling is now measured at n=3** (AMS/GYGY/ALBT): the
   distress that exists at neglected size has no options market, is
   often not even listed or quoted, and its equity is the lesson-23
   pattern. Check tradability BEFORE spending a read (lesson 27).
2. **Single-name event theses from the eventfeed inventory** — AGEN
   2026-11-26 financing cliff (recheck mid-Aug); INMD respondent-side ITC.
   Theses, not channels.
3. **Event families measured dead/starved:** deadlines (both sides), ITC
   (n=12, 1.98pp median), tenders + odd-lot, spinoff orphans/mechanics,
   deal-break-as-channel, post-break reversion (n=48), kink program
   (supply starved all three directions — feed3 clock decides ~9/12; the
   distress-first mode now confirmed on THREE live specimens). Tax-loss
   calendar has a FROZEN recipe (row 94, prior p=0.30); October spends
   the data.
4. If feed3 dies ~9/12 with nothing, the honest record-brief posture is
   the park + research — and the brief machinery exists to say it with
   numbers.

## Plan (next session — Friday 2026-07-31)

- (a) Reconcile; mark curve vs SPY **with buckets** (live tape); DOMO
  close vs $4.60; `brief_due()` check.
- (b) Daily feed3 DEADLINE scan (window 2026-07-30..31); Hermes closed[]
  break check (if a BREAK fires: STAND ASIDE, cite the study).
- (c) MAIN WORK: **July flat-month posture note (art. 13b)** — it is
  7/31: index-park type, benchmark-exempt, record why parked rather
  than hunting (cite the n=3 venue pattern and the dead families).
- (d) AGEN mid-Aug — not before. Do NOT touch tax_loss_turn data before
  October (deferral deliberate). Candidate builds must pass the build
  test honestly; quiet clean days are the park working as designed.
- (e) Any entry: art. 16 staged order FIRST, art. 26a arithmetic, full
  entry schema, art. 20c check, **tradability check FIRST (lesson 27)**.
- (f) NO park round trips.

## Lessons (cumulative scar tissue — keep ALL of these)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down.
   Verify SYMBOLS at the broker/EDGAR submissions, never regex display
   names (CRBD→CRBG 7/13; CIK-resolution 7/14).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. Honest kills compound: 44 dispositions + DOMO gradable decline. The
   record shows the reading working before the wallet.
6. Verify the record before trusting any summary of it — including mine.
   Counts are computations, never recollections.
7. Session containers are ephemeral and shallow-cloned: `git fetch
   --deepen` before reasoning about history; `pip install pytest numpy`
   before the suite (~1 min, then 1939 tests in ~5s).
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
14. A sample of 3 is an anecdote, not a population.
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
    Count mechanisms, never keywords (~96% of termination-phrase hits
    were boilerplate; SOLS/ZETA/APLE/EXTR/MYE: healthy-refi language
    five specimens running — and AMS/GYGY/ALBT prove the REAL mechanism
    does appear, so keep reading the documents).
19. **Journal corrections are APPENDED, never edited.** No de-minimis
    exception. Schema verdicts are a closed set — a disposition after a
    full read with no divergence is an `avoid`, not a new verdict string.
20. **A refutation's own table can kill an adjacent idea for free.**
    Re-read the refutation's numbers at your horizon BEFORE designing
    any study on scorched-adjacent ground.
21. **Stub/deal math is share-count and cash-mechanics math (DOMO,
    7/23).** Read the Indebtedness definition and the cash-adjustment
    DIRECTION before believing any discount — and journal the pre-read
    leaning BEFORE the read so a reversal is gradable.
22. **`sharadar.resolve_ticker` returns the CURRENT ticker holder when
    the API hides delisted rows (MNR→Mach, FGL→Founder Group).** For
    recycled tickers, sweep `load_ticker_universe()` — Sharadar keys
    delisted lineages under numeric suffixes. Spot-check every resolved
    name against the company NAME, not just the symbol.
23. **The post-break flush is information, not overshoot (n=48,
    session 18).** Down-moves on real bad news do NOT owe you a bounce;
    the bigger the flush, the worse the next month ran. (Applied 7/27
    GLXZ, 7/29 AMS, 7/30 GYGY/ALBT: distressed equity junior to a
    defaulted or forbearing lender is not a dip.)
24. **Event-time is a design decision: deals die at the RULING, filings
    lag.** Fix the economically-correct event date in the recipe BEFORE
    data, or the census dates will be inconsistent (CPRI/SAVE).
25. **Instrumentation without decomposition is a future lie (7/25).**
    A curve mark that doesn't say WHAT the equity was (risk / cash /
    index park) silently poisons the deployment-adjusted line months
    later. Record the decomposition the day the mark is made.
26. **Freeze the recipe far from the data (7/26).** A design written
    months before execution, with cells, bars, placebos, and the ONE
    decision declared, leaves no room for the data to seduce the
    designer. The October session's only freedom is deltas-with-reasons.
27. **Check venue tradability BEFORE spending a read (GLXZ 7/27,
    AMS 7/29, GYGY/ALBT 7/30).** The neglected corner overlaps heavily
    with what has no options market, no listing, or no quote at all. A
    thesis on an untradable instrument is research spend with zero
    decision value — check the venue AND the chain first; a store
    deposit records its tradability at deposit time.
28. **A stale playbook instruction is a live hazard (7/28).** When a
    study lands, same-session sweep the playbook/beliefs for every
    pointer that motivated it and rewrite them to the verdict.
