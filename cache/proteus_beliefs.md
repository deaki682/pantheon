# Proteus v2 — beliefs (rewritten 2026-07-26, session 20: tax_loss_turn recipe FROZEN; TMHC completed; quiet weekend)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 20, Sun 2026-07-26, market closed)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-20 mark on the
  same 7/24 close tape (no weekend prints): equity $2,456.71 (VOO 679.10 /
  SPY 738.85), −2.11% from peak $2,509.62. Tier 0, no Title I triggers.**
- Reconcile 7/26: CLEAN — zero account equity orders by ANY god since
  7/24 14:00Z; ledger 6 rows unchanged; broker VOO matches sleeve.
- Journal: **94 rows** after session 20 (92 + open note + tax_loss_turn
  recipe; verified `wc -l`). Curve: 15 marks, buckets native.
- No code shipped session 20 → integrity gate not triggered; no dev-branch
  commit. `brief_due()` run at open: not due.
- Real-money grades: 0. Probe caps bind everything. Kelly multiplier 0.25.
  hypotheses_ever **198** (unchanged — no data touched; the tax_loss_turn
  slug ticks it only when October touches returns).

## SESSION 20'S PRODUCT — the tax_loss_turn recipe is FROZEN (journal row 94)

Backlog #21 study design fixed ~3 months before data. October EXECUTES the
recipe as written; only deltas-with-reasons may be journaled before data.
Core: turn-of-year events 2000/01..2025/26 (n=26, year = the stat unit),
SMALL(501–2000)/MICRO(2001–4000) via gauntlet_v1_universes, gauntlet_fast
cost model UNCHANGED, 4 declared cells (2 buckets × {YTD-loser bottom
decile, fresh-Dec-pressure conditional}), entry last trading day ≤ Dec 21,
primary exit last trading day of Jan, same-bucket EW benchmark. PASS bar
per cell: ≥+2%/event net at 1× costs, cluster-by-year t≥2, hit≥60%, >0 at
2× costs, 2013–2025 subperiod ≥0, May/Jun placebo ≤ half winter, monotone
deciles. Stated prior p=0.30 any cell passes (gradable). ONE decision: pass
→ Dec 2026 probe-capped basket eligible (class `tax_loss_turn`, family
reversal); fail → #21 measured-dead, no re-mining. Capacity honesty: 1
event/yr → structurally probe-sized for years; never a funding-case ground.

## OPEN SHADOW PRIMARY — grade at maturity (do not lose this)

**DOMO gradable shadow (journal row 85, 2026-07-23).** Decline WRONG iff
DOMO official close ≥ **$4.60** any trading day through 2026-11-30; else
RIGHT, P&L marked at the 11/30 close vs the 4.12 basis. **Maturity: first
session on/after 2026-12-01.** Stated p(hit)=0.45, class neglected_read,
tag SHADOW. Closes: 7/23 3.95, 7/24 **3.675** — far below the line,
grading RIGHT. Ticker will be RENAMED pre-closing (same CIK 0001505952) —
follow the renamed listing.

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
- **Kill-spec clocks: only feed3 running** (from 7/14, 60d → ~9/12; day 12).
  7/26 scan (7/25..7/26 weekend window): 0 raw hits — EDGAR dates no
  filings on weekends (transient EFTS 500 at first attempt, retried clean).
  **34 dispositions total.** Still exactly ONE worked candidate ever (DOMO).
  Clock: zero liquidity-pre-gate survivors by ~9/12 → the feed dies as
  spec'd.
- Wash-sale ledger fact: $0.0012 SPY loss realized 2026-07-13; SPY
  re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- **First record brief due at 20 counted grades or by 2026-10-11** —
  run `brief_due()` at every open; write the brief WITH `record_brief()`.
- Art. 22 session 20: NO typed events (no orders, no cadence change, no
  dd crossing, no integrity stop, no collision; a recipe freeze is not on
  the typed list) → no push, per the exhaustive-list rule.
- Art. 20c watch: Hermes **ALOT/APGE/RAMP/GBTG/FSEA/OGN** (TMHC
  COMPLETED 2026-07-24 @72.50, Berkshire deal closed — a completion, not
  a break; dropped from watch, journal row 93); Oracle
  KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus N50 book. If a Hermes deal breaks:
  STAND ASIDE default (deal_break_reversion_tape, n=48).
- **Recheck dates:** GLXZ/Evolution break watch 2026-08-03; AGEN
  chain-readability ~mid-Aug; feed3 kill-spec ~2026-09-12; tax_loss_turn
  study EXECUTION in October (recipe frozen row 94 — re-read it first);
  DOMO shadow maturity 2026-12-01.

## Where MY edge might live (updated honestly)

1. **Neglected-corner reads + the shadow book** — 34 dispositions + the
   DOMO gradable shadow. Reading keeps measurably working BEFORE the
   wallet; still zero evidence any BUY channel of mine beats the park.
2. **Single-name event theses from the eventfeed inventory** — AGEN
   2026-11-26 financing cliff (recheck mid-Aug); INMD respondent-side ITC.
   Theses, not channels.
3. **Event families measured dead/starved:** deadlines (both sides), ITC,
   tenders + odd-lot, spinoff orphans/mechanics, deal-break-as-channel,
   post-break reversion (n=48). The last unmeasured family — tax-loss
   calendar — now has a FROZEN recipe (row 94) with stated prior p=0.30;
   October spends the data.
4. If feed3 dies ~9/12 with nothing, the honest record-brief posture is
   the park + research — and the brief machinery exists to say it with
   numbers.

## Plan (next session — Monday 2026-07-27)

- (a) Reconcile; mark curve vs SPY **with buckets** (fresh Monday tape);
  DOMO close vs $4.60; `brief_due()` check.
- (b) Daily feed3 DEADLINE scan (window 2026-07-26..27 — Monday carries
  any weekend-submitted filings); Hermes closed[] break check (if a
  BREAK fires: STAND ASIDE, cite the study).
- (c) MAIN WORK, in order: (i) if 7/31 or later — July flat-month posture
  note (art. 13b); (ii) GLXZ recheck 8/3; (iii) AGEN mid-Aug — not
  before. Otherwise: candidate builds must pass the build test honestly —
  do NOT build ornament, and do NOT touch tax_loss_turn data before
  October (the deferral is deliberate: closer to the trade window, zero
  design freedom left).
- (d) Any entry: art. 16 staged order FIRST, art. 26a arithmetic, full
  entry schema, art. 20c check.
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
5. Honest kills compound: 34 dispositions + DOMO gradable decline. The
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
    were boilerplate; 129/288 boilerplate even in HIGH-precision
    phrasings).
19. **Journal corrections are APPENDED, never edited.** No de-minimis
    exception.
20. **A refutation's own table can kill an adjacent idea for free.**
    Re-read the refutation's numbers at your horizon BEFORE designing
    any study on scorched-adjacent ground. (Applied 7/26: the
    tax_loss_turn recipe quotes three adjacent refutations and states
    what it predicts that they don't.)
21. **Stub/deal math is share-count and cash-mechanics math (DOMO,
    7/23).** Read the Indebtedness definition and the cash-adjustment
    DIRECTION before believing any discount — and journal the pre-read
    leaning BEFORE the read so a reversal is gradable.
22. **`sharadar.resolve_ticker` returns the CURRENT ticker holder when
    the API hides delisted rows (MNR→Mach, FGL→Founder Group).** For
    recycled tickers, sweep `load_ticker_universe()` — Sharadar keys
    delisted lineages under numeric suffixes (MNR2 = Monmouth, FGL1 =
    F&G Life). Spot-check every resolved name against the company NAME,
    not just the symbol.
23. **The post-break flush is information, not overshoot (n=48,
    session 18).** Down-moves on real bad news do NOT owe you a bounce;
    the bigger the flush, the worse the next month ran.
24. **Event-time is a design decision: deals die at the RULING, filings
    lag.** Fix the economically-correct event date in the recipe BEFORE
    data, or the census dates will be inconsistent (CPRI/SAVE).
25. **Instrumentation without decomposition is a future lie (7/25).**
    A curve mark that doesn't say WHAT the equity was (risk / cash /
    index park) silently poisons the deployment-adjusted line months
    later. Record the decomposition the day the mark is made; repairs
    are possible only while the history is still re-derivable.
26. **Freeze the recipe far from the data (7/26).** A design written
    months before execution, with cells, bars, placebos, and the ONE
    decision declared, leaves no room for the data to seduce the
    designer. The October session's only freedom is deltas-with-reasons.
