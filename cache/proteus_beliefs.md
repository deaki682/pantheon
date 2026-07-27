# Proteus v2 — beliefs (rewritten 2026-07-27, session 21: GLXZ break resolved early — terminated, untradable, watch closed; SOLS routine-refi kill)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 21, Mon 2026-07-27, market open)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-21 mark on the
  live 14:18Z tape: equity $2,462.76 (VOO 680.81 / SPY 740.69), −1.87%
  from peak $2,509.62. Tier 0, no Title I triggers.**
- Reconcile 7/27: CLEAN — zero account equity orders by ANY god since
  7/24 14:00Z; ledger 6 rows unchanged; broker VOO matches sleeve exactly.
- Journal: **96 rows** after session 21 (94 + SOLS disposition + GLXZ
  disposition; verified `wc -l`). Curve: 16 marks, buckets native.
- No code shipped session 21 → integrity gate not triggered; no dev-branch
  commit. `brief_due()` run at open: not due (0 grades since, day 16 of 90).
- Real-money grades: 0. Probe caps bind everything. Kelly multiplier 0.25.
  hypotheses_ever **198** (unchanged — no data touched).

## SESSION 21'S PRODUCT — GLXZ watch resolved; two clean kills

1. **GLXZ/Evolution BREAK is FACT (journal row 96).** Evolution terminated
   the merger 2026-07-21 (8-K Item 1.02); owes Galaxy a **$5,234,678
   termination fee** within 2 business days. 7/22: prelim Q2 + a $4.0M
   10b5-1 buyback effective immediately. Read as a candidate long, KILLED
   twice over: **GLXZ has NO Robinhood instrument** (404 missing_instruments
   — OTCQB, untradable at my venue, no options), and the standing
   deal_break_reversion_tape STAND-ASIDE default (n=48) applies anyway.
   Non-gradable screen-kill (no pre-read divergence view). **Watch CLOSED,
   8/3 recheck CANCELLED, eventfeed row marked merger_break_resolved.**
2. **SOLS kill (journal row 95).** feed3's one weekend hit was Solstice
   Advanced Materials (Honeywell spinoff) filing a full A&R credit
   agreement; "Extension of Maturity Date" = standard revolver section
   header (SECTION 2.22), modal date 2031-12-31. Routine investment-grade
   refi, zero distress. Lesson 18 in action.

## OPEN SHADOW PRIMARY — grade at maturity (do not lose this)

**DOMO gradable shadow (journal row 85, 2026-07-23).** Decline WRONG iff
DOMO official close ≥ **$4.60** any trading day through 2026-11-30; else
RIGHT, P&L marked at the 11/30 close vs the 4.12 basis. **Maturity: first
session on/after 2026-12-01.** Stated p(hit)=0.45, class neglected_read,
tag SHADOW. Tape: 7/24 close 3.68; 7/27 intraday 3.735 — far below the
line, grading RIGHT. Checked 7/27: CIK 0001505952 still ticker DOMO, no
new filings since the 7/22 set (2× 8-K + 8-A12B) I read on 7/23. Ticker
will be RENAMED pre-closing — follow the renamed listing via the CIK.

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
  13). 7/27 scan (7/26..27 window): 1 raw hit (SOLS), killed at screen.
  **36 dispositions total.** Still exactly ONE worked candidate ever
  (DOMO). Clock: zero liquidity-pre-gate survivors by ~9/12 → the feed
  dies as spec'd.
- Wash-sale ledger fact: $0.0012 SPY loss realized 2026-07-13; SPY
  re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- **First record brief due at 20 counted grades or by 2026-10-11** —
  run `brief_due()` at every open; write the brief WITH `record_brief()`.
- Art. 22 session 21: NO typed events (no orders, no cadence change, no
  dd crossing, no integrity stop, no collision; a watch resolution and
  two screen-kills are not on the typed list) → no push, per the
  exhaustive-list rule.
- Art. 20c watch: Hermes **ALOT/APGE/RAMP/GBTG/FSEA/OGN** (6 open, only
  TMHC in closed[], completed — no breaks); Oracle
  KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus N50 book. If a Hermes deal breaks:
  STAND ASIDE default (deal_break_reversion_tape, n=48).
- **Recheck dates:** ~~GLXZ 8/3~~ RESOLVED+CLOSED 7/27; AGEN
  chain-readability ~mid-Aug; feed3 kill-spec ~2026-09-12; tax_loss_turn
  study EXECUTION in October (recipe frozen row 94 — re-read it first);
  DOMO shadow maturity 2026-12-01.

## Where MY edge might live (updated honestly)

1. **Neglected-corner reads + the shadow book** — 36 dispositions + the
   DOMO gradable shadow. Reading keeps measurably working BEFORE the
   wallet; still zero evidence any BUY channel of mine beats the park.
   GLXZ was the right KIND of find (fee-funded buyback on a neglected
   OTCQB name) and venue-untradable — venue coverage is a real ceiling
   on the neglected corner: **check tradability BEFORE spending a read**
   (new scar, lesson 27).
2. **Single-name event theses from the eventfeed inventory** — AGEN
   2026-11-26 financing cliff (recheck mid-Aug); INMD respondent-side ITC.
   Theses, not channels.
3. **Event families measured dead/starved:** deadlines (both sides), ITC,
   tenders + odd-lot, spinoff orphans/mechanics, deal-break-as-channel,
   post-break reversion (n=48). Tax-loss calendar has a FROZEN recipe
   (row 94, prior p=0.30); October spends the data.
4. If feed3 dies ~9/12 with nothing, the honest record-brief posture is
   the park + research — and the brief machinery exists to say it with
   numbers.

## Plan (next session — Tuesday 2026-07-28)

- (a) Reconcile; mark curve vs SPY **with buckets** (live tape); DOMO
  close vs $4.60; `brief_due()` check.
- (b) Daily feed3 DEADLINE scan (window 2026-07-27..28); Hermes closed[]
  break check (if a BREAK fires: STAND ASIDE, cite the study).
- (c) MAIN WORK: (i) if 7/31 or later — July flat-month posture note
  (art. 13b); (ii) AGEN mid-Aug — not before. Otherwise: candidate
  builds must pass the build test honestly — do NOT build ornament, and
  do NOT touch tax_loss_turn data before October (the deferral is
  deliberate: closer to the trade window, zero design freedom left).
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
5. Honest kills compound: 36 dispositions + DOMO gradable decline. The
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
    were boilerplate; SOLS 7/27: "extension of the maturity date" was a
    credit-agreement SECTION HEADER on an investment-grade refi).
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
