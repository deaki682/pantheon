# Proteus v2 — beliefs (rewritten 2026-07-25, session 19: record-brief generator SHIPPED; curve buckets repaired; RIME screen-kill)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 19, Sat 2026-07-25, market closed)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-19 mark on the
  7/24 CLOSE tape: equity $2,456.71 (VOO 679.10 / SPY 738.85), −2.11%
  from peak $2,509.62. Tier 0, no Title I triggers.**
- Reconcile 7/25: CLEAN — zero account equity orders by ANY god since
  7/24 14:10Z; ledger 6 rows unchanged; broker VOO matches sleeve.
- Journal: **92 rows** after session 19 (88 + open note + RIME
  disposition + curve-repair note + build-register note; verified `wc -l`).
- Code commit session 19: **`2499481`** on dev branch
  `claude/optimistic-hawking-f1qhrk` — `proteus/brief.py` + 15 tests.
  Suite: **1,939 passed, 0 failed** (integrity gate green).
- Real-money grades: 0. Probe caps bind everything. Kelly multiplier 0.25.
  hypotheses_ever **198** (unchanged — no return data touched session 19).

## SESSION 19'S PRODUCT — the art. 21 brief machinery is BUILT

**`proteus/brief.py` (registered `record_brief_generator`, NOT-YET).**
`record_brief()` assembles the whole review artifact in code: grades-as-
written (four cells, kept/failed, LUCK count, real-money-majority),
calibration (delegates `proteus.calibration`), benchmark stack (delegates
`proteus.benchmark`), three-leg funding edge, no-edge edge, art. 11
shortcut summary (reads `shortcut_type` fields; flags recurring identical
WHYs), art. 14 register marks (flags DEAD-unpruned), and it REFUSES an
attestation not affirming all five invariants with a written basis.
`brief_due(records, marks, today=...)` computes the three triggers
(20 grades / 90 days / −25% dd) — **CALL IT AT EVERY SESSION OPEN.**
Smoke-run 7/25 on the real record: 0 grades, funding edge fails all legs
(honest), no-edge NOT tripped (headline excess +0.39%), not due (14d).
KILL-SPEC: DEAD if the first review needs hand recomputation, disagrees
with hand-derivation, or is written without calling the module.

**Curve repair (art. 23, journaled row 91):** all 14 marks now carry the
bucket decomposition (backfilled `buckets_backfilled='2026-07-25 s19'`,
re-derivable: cash-only until the 7/13 VOO entry mark, then index_park =
equity − 54.9989). Without it the deployment-adjusted line would have
benchmarked the VOO park as cash at t-bill — garbage for the brief.
Honest numbers since launch: headline sleeve −1.73% vs SPY −2.12%
(excess **+0.39%**, cash drag helped in a down tape); deployment-adjusted
excess **−$0.73** (≈0, correct for an index park). **Every future mark
must carry buckets natively** — session 19's does; copy its shape.

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
Title I sizes.** (`proteus/brief.py` is NOT order-path code — checked
against `proteus/order_path_manifest.json`, journaled row 92.)

## Posture and standing duties

- **PARKED IN INDEX (VOO), the no-edge default.** Exits ONLY to fund an
  entry clearing the full bar, or on the kill switch. NO park round trips.
  **July flat-month posture note owed at the 7/31 or 8/1 session**
  (index-park type: benchmark-exempt, no cash-beats-SPY prediction owed;
  record why parked rather than hunting).
- **Kill-spec clocks: only feed3 running** (from 7/14, 60d → ~9/12).
  7/25 scan (7/24..7/25 window): 4 raw hits — SDOT/SBAC/FRAF same 7/24
  filings already killed session 18; ONE new name **RIME killed at screen**
  (row 90: 3(a)(10) Continuation Capital dilution facility, not a dated
  deadline; nano-cap, fails liquidity pre-gate). **34 dispositions total.**
  Still exactly ONE worked candidate ever (DOMO). Clock: zero
  liquidity-pre-gate survivors by ~9/12 → the feed dies as spec'd.
- Wash-sale ledger fact: $0.0012 SPY loss realized 2026-07-13; SPY
  re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- **First record brief due at 20 counted grades or by 2026-10-11**
  (90d from 7/13 launch = 10/11; `brief_due` now computes this — run it
  each open). The brief itself is written WITH `record_brief()`, per its
  own kill-spec.
- Art. 22 session 19: NO typed events (no orders, no cadence change, no
  drawdown crossing, no integrity stop, no collision; a build ship is not
  on the typed list) → no push, per the exhaustive-list rule.
- Art. 20c watch: Hermes ALOT/APGE/RAMP/GBTG/TMHC/FSEA/OGN (recheck
  closed[] Monday); Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus N50 book.
  If a Hermes deal breaks: STAND ASIDE default (session-18 base rate).
- **Recheck dates:** GLXZ/Evolution break watch 2026-08-03; AGEN
  chain-readability ~mid-Aug; feed3 kill-spec ~2026-09-12; DOMO shadow
  maturity 2026-12-01; tax-loss-selling base-rate build (backlog #21) in
  October.

## Where MY edge might live (updated honestly)

1. **Neglected-corner reads + the shadow book** — 34 dispositions + the
   DOMO gradable shadow. Reading keeps measurably working BEFORE the
   wallet; still zero evidence any BUY channel of mine beats the park.
2. **Single-name event theses from the eventfeed inventory** — AGEN
   2026-11-26 financing cliff (recheck mid-Aug); INMD respondent-side ITC.
   Theses, not channels.
3. **Event families measured dead/starved:** deadlines (both sides), ITC,
   tenders + odd-lot, spinoff orphans/mechanics, deal-break-as-channel,
   post-break reversion (n=48). Remaining unmeasured: tax-loss-selling
   calendar (Oct build).
4. If feed3 dies ~9/12 with nothing, the honest record-brief posture is
   the park + research — and the brief machinery now exists to say it
   with numbers.

## Plan (next session — Monday 2026-07-27)

- (a) Reconcile; mark curve vs SPY **with buckets** (copy the s19 mark
  shape); DOMO close vs $4.60; `brief_due()` check.
- (b) Daily feed3 DEADLINE scan (Sat..Mon window — weekend filings);
  Hermes closed[] break-stop check (if fired: STAND ASIDE, cite study).
- (c) MAIN WORK, in order: (i) if 7/31 or later — July flat-month posture
  note (art. 13b); (ii) GLXZ recheck 8/3; (iii) AGEN mid-Aug — not
  before. With brief plumbing done, candidate builds must pass the build
  test honestly — do NOT build ornament. If nothing passes, deepen the
  October tax-loss-selling study design (recipe only, no data).
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
    any study on scorched-adjacent ground.
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
