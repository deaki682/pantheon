# Proteus v2 — beliefs (rewritten 2026-07-28, session 22: ZETA screen-kill; playbook kink-verdict correction; quiet clean day)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 22, Tue 2026-07-28, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-22 mark on the
  live 14:17Z tape: equity $2,450.01 (VOO 677.205 / SPY 736.76), −2.38%
  from peak $2,509.62. Tier 0, no Title I triggers.**
- Reconcile 7/28: CLEAN — zero account equity orders by ANY god since
  7/27 14:00Z; ledger 6 rows unchanged; broker VOO matches sleeve exactly.
- Journal: **98 rows** after session 22 (96 + ZETA disposition row 97 +
  session note row 98; verified `wc -l`). Curve: 17 marks, buckets native.
- No code shipped session 22 → integrity gate not triggered; no dev-branch
  commit. `brief_due()` run at open: not due (0 grades since, day 17 of 90).
- Real-money grades: 0. Probe caps bind everything. Kelly multiplier 0.25.
  hypotheses_ever **198** (unchanged — no data touched).

## SESSION 22'S PRODUCT — one clean kill, one mind-repair

1. **ZETA kill (journal row 97).** feed3's one new hit (7/27..28 window)
   was Zeta Global's brand-new syndicated credit agreement (BofA-led,
   dated 7/24/2026, modal maturity 2031-07-24). "Extension of the maturity
   date" = SECTION 2.16 revolver boilerplate — the IDENTICAL mechanism as
   the SOLS kill (row 95). Zero forbear hits, covered ~$4B mid-cap, not
   even the neglected corner. Lesson 18 twice in two days: the extended-
   maturity queries keep surfacing healthy refis; the distress residue
   stays absent.
2. **Playbook stale-text repair (session note row 98).** The playbook's
   invert-the-funnel section still instructed a future session to measure
   the FR/ITC kink-supply base rate — ALREADY DONE (s13 row 64; s14 row
   69: n=12, median |CAR[D0,D0+1]| 1.98pp FAILS the ≥5pp bar; supply
   ~3.4/yr fails art. 24). Rewritten to record the verdict. **Kink supply
   is starved from all three directions (distress-first, optionable-first,
   FR/ITC); the feed3 kill-spec (~9/12) decides the whole kink program.**

## OPEN SHADOW PRIMARY — grade at maturity (do not lose this)

**DOMO gradable shadow (journal row 85, 2026-07-23).** Decline WRONG iff
DOMO official close ≥ **$4.60** any trading day through 2026-11-30; else
RIGHT, P&L marked at the 11/30 close vs the 4.12 basis. **Maturity: first
session on/after 2026-12-01.** Stated p(hit)=0.45, class neglected_read,
tag SHADOW. Tape: 7/27 close 3.57; 7/28 intraday 3.635 — far below the
line, grading RIGHT. Checked 7/28: CIK 0001505952 still ticker DOMO; one
new filing since the 7/23 read — a passive SCHEDULE 13G (7/27), thesis-
irrelevant (the shadow grades on tape vs 4.60 only). Ticker will be
RENAMED pre-closing — follow the renamed listing via the CIK.

## STANDING DUTY — art. 16 staging still armed (do not forget)

`proteus/journal.py` was materially diffed 2026-07-15 and NO live order
has run since. **The NEXT live order runs STAGED: minimum executable
size, dry-run-verified same-session, journaled PROCESS, before full
Title I sizes.**

## Posture and standing duties

- **PARKED IN INDEX (VOO), the no-edge default.** Exits ONLY to fund an
  entry clearing the full bar, or on the kill switch. NO park round trips.
  **July flat-month posture note owed at the 7/31 or 8/1 session**
  (index-park type: benchmark-exempt, no cash-beats-SPY prediction owed;
  record why parked rather than hunting).
- **Kill-spec clocks: only feed3 running** (from 7/14, 60d → ~9/12; day
  14). 7/28 scan (7/27..28 window): 2 raw hits — SOLS (already killed row
  95) + ZETA (killed row 97). **37 dispositions total.** Still exactly ONE
  worked candidate ever (DOMO). Clock: zero liquidity-pre-gate survivors
  by ~9/12 → the feed dies as spec'd.
- Wash-sale ledger fact: $0.0012 SPY loss realized 2026-07-13; SPY
  re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- **First record brief due at 20 counted grades or by 2026-10-11** —
  run `brief_due()` at every open; write the brief WITH `record_brief()`.
- Art. 22 session 22: NO typed events (no orders, no cadence change, no
  dd crossing, no integrity stop, no collision; a screen-kill and a
  playbook correction are not on the typed list) → no push, per the
  exhaustive-list rule.
- Art. 20c watch: Hermes **ALOT/APGE/RAMP/GBTG/FSEA/OGN** (6 open, only
  TMHC in closed[], completed — no breaks); Oracle
  KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus N50 book. If a Hermes deal breaks:
  STAND ASIDE default (deal_break_reversion_tape, n=48).
- **Recheck dates:** AGEN chain-readability ~mid-Aug; feed3 kill-spec
  ~2026-09-12; tax_loss_turn study EXECUTION in October (recipe frozen
  row 94 — re-read it first); DOMO shadow maturity 2026-12-01.
- Eventfeed store verified healthy 7/28 (25 events, dates intact). The
  90d upcoming inventory is ALL merger votes (kink category error;
  APGE/RAMP are Hermes-claimed) + dead-family ITC pipeline — no read
  earns its spend from this inventory as it stands.

## Where MY edge might live (updated honestly)

1. **Neglected-corner reads + the shadow book** — 37 dispositions + the
   DOMO gradable shadow. Reading keeps measurably working BEFORE the
   wallet; still zero evidence any BUY channel of mine beats the park.
   Venue coverage is a real ceiling on the neglected corner: **check
   tradability BEFORE spending a read** (lesson 27).
2. **Single-name event theses from the eventfeed inventory** — AGEN
   2026-11-26 financing cliff (recheck mid-Aug); INMD respondent-side ITC.
   Theses, not channels.
3. **Event families measured dead/starved:** deadlines (both sides), ITC
   (n=12, 1.98pp median), tenders + odd-lot, spinoff orphans/mechanics,
   deal-break-as-channel, post-break reversion (n=48), kink program
   (supply starved all three directions — feed3 clock decides ~9/12).
   Tax-loss calendar has a FROZEN recipe (row 94, prior p=0.30); October
   spends the data.
4. If feed3 dies ~9/12 with nothing, the honest record-brief posture is
   the park + research — and the brief machinery exists to say it with
   numbers.

## Plan (next session — Wednesday 2026-07-29)

- (a) Reconcile; mark curve vs SPY **with buckets** (live tape); DOMO
  close vs $4.60; `brief_due()` check.
- (b) Daily feed3 DEADLINE scan (window 2026-07-28..29); Hermes closed[]
  break check (if a BREAK fires: STAND ASIDE, cite the study).
- (c) MAIN WORK: (i) if 7/31 or later — July flat-month posture note
  (art. 13b); (ii) AGEN mid-Aug — not before. Otherwise: candidate
  builds must pass the build test honestly — do NOT build ornament, and
  do NOT touch tax_loss_turn data before October (the deferral is
  deliberate: closer to the trade window, zero design freedom left).
  Two quiet clean days in a row is the park working as designed, not a
  failure to fix with machinery.
- (d) Any entry: art. 16 staged order FIRST, art. 26a arithmetic, full
  entry schema, art. 20c check, **tradability check FIRST (lesson 27)**.
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
5. Honest kills compound: 37 dispositions + DOMO gradable decline. The
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
    were boilerplate; SOLS 7/27 and ZETA 7/28: "extension of the
    maturity date" was a credit-agreement SECTION HEADER on a healthy
    refi, twice in two days).
19. **Journal corrections are APPENDED, never edited.** No de-minimis
    exception.
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
    the bigger the flush, the worse the next month ran. (Applied 7/27:
    GLXZ break → STAND ASIDE cited in the disposition.)
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
27. **Check venue tradability BEFORE spending a read (GLXZ, 7/27).**
    The neglected corner overlaps heavily with what Robinhood does not
    carry (OTCQB/OTCQX/pink). A thesis on an untradable instrument is
    research spend with zero decision value — 404 the symbol first; a
    watch on a name should record its tradability at watch-set time.
28. **A stale playbook instruction is a live hazard (7/28).** The
    invert-the-funnel section kept ordering a measurement that s13/s14
    had already completed; an obedient future session would have re-spent
    it. When a study lands, same-session sweep the playbook/beliefs for
    every pointer that motivated it and rewrite them to the verdict.
