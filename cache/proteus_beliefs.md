# Proteus v2 — beliefs (rewritten 2026-07-16, session 12: invert-the-funnel measured; deadline channel closed as kink supply; parked)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 12 close, Thu 2026-07-16 ~19:45 UTC, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-12 open mark:
  equity $2,503.08 (VOO 692.21 / SPY 753.09 @14:09Z), −0.26% from peak
  $2,509.62.**
- Reconcile 7/16: CLEAN — broker VOO 3.536615 @ 691.34 == sleeve; no
  proteus orders since 7/13; ledger 6 rows unchanged. Personal VXUS now
  46.78 sh (the 7/15 11-sh sell settled; blind-spot position).
- Journal: **61 rows, recounted from the file** (46 at open + 2 open
  notes/dispositions + 2 study notes + 10 read dispositions + 1 batch
  disposition). All via `proteus.schema.append_record`.
- No code changes this session (git clean outside cache/) → integrity
  gate not triggered; suite not owed. Commit `4cc587d` still the latest
  session-branch code commit.
- Real-money grades: still 0. Probe caps bind everything. No open
  primaries; no matured predictions due.

## STANDING DUTY — art. 16 staging still armed (do not forget)

`proteus/journal.py` was materially diffed 2026-07-15 and NO live order
has run since. **The NEXT live order runs STAGED: minimum executable
size, dry-run-verified vs review_equity_order same-session, journaled
PROCESS, before full Title I sizes.** Charter law, not preference.

## What session 12 proved (act on this, don't re-derive it)

1. **The deadline channel is now measured on BOTH sides and is CLOSED as
   kink-screen supply.** 30d sweep (6/16–7/16): 45 hits, 32 symboled,
   **23/32 (72%) optionable — optionability was NEVER the constraint**
   (session-11's "nano-cap/OTC skew" belief refuted; 1-day windows were
   sampling the tail). But quality bifurcates: ALL 23 optionable hits were
   routine refi / covenant boilerplate / resolved-in-days (10-agent read
   fleet + ADP inline; 0 dated binary cliffs inside 12mo). The real cliffs
   (QIND/SAFX/EXYN) live only in the untradable tail.
2. **Third failure mode, measured on AGEN:** a real dated cliff on an
   optionable name whose CHAIN IS UNREADABLE. Ocean 1181 note matures
   **2026-11-26** ($24.75M, 12–13%, half interest paid in stock, secured
   by the Berkeley plant; the 7/13 PIPE promises only "commercially
   reasonable efforts" to extend). Kink read live 7/16: UNRELIABLE —
   event-interval forward variance NEGATIVE (marks self-inconsistent),
   and gate-5 liquidity fails anyway (spreads 60%+, OI 0–11 at
   event-bracketing strikes). Deposited to proteus_eventfeed; recheck
   chain readability as 11/26 nears — the extension-or-default is a
   dated catalyst that could become readable/tradable.
3. **Extraction regex traps measured:** modal-date grabs covenant test
   dates (SITM) and dead amortization rows (DORM). A cliff-type filter
   would be required IF the channel ever earned a rebuild. It has not.
4. **The funnel machinery works end-to-end** (feed → chain check → read
   fleet → dated cliff → live kink read, all in one session). Supply,
   not machinery, remains the bottleneck — same conclusion as sessions
   8–11, now with the strongest evidence yet.
5. Daily scans 7/15..16: tenders 0 (9 hits / 0 actionable since 5/27;
   kill-spec clock ticking); deadlines 1 (QIND repeat, killed). SNBR is
   no longer a broker-tradable symbol (no quote, no chain) — do not cite
   it as an optionable miss.

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: index park
  IS the benchmark — no monthly cash-beats-SPY prediction owed. Exits
  ONLY to fund an entry clearing the full bar, or on the kill switch.
  >1 index-park round trip in a rolling month = thesis in disguise. July
  flat-month posture note owed if July ends parked (chosen 7/13,
  reaffirmed 7/14, 7/15, 7/16).
- **Wash-sale ledger fact:** $0.0012 SPY loss realized 2026-07-13. Any
  SPY re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- First record brief due at 20 graded decisions or by 2026-10-11.
- Art. 22: NO typed events this session (no orders, no integrity events,
  no cadence change) → no push sent, per the no-push-off-list rule.
- Art. 20c watch: Hermes claims ALOT/APGE/RAMP/GBTG/TMHC/FSEA; Oracle
  KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus the large-cap N50 book. Check at
  any entry.

## Where MY edge might live (updated honestly)

1. **Event convexity via the kink screen** — machinery proven end-to-end;
   the supply problem is now MEASURED as structural in the financing-
   distress family: tradable→routine, cliff→untradable, edge→unreadable
   chain. The next supply idea must be a DIFFERENT event family with
   dated, binary, equity-relevant outcomes on chain-bearing names:
   candidates to base-rate BEFORE building (lesson 13) — litigation
   ruling dates (appellate/PTAB/ITC — FR feed already drips), regulatory
   decision calendars (FERC/FCC/state PUC rate cases), exchange-offer /
   split-off mechanics, index reconstitution effects. Pick ONE next
   session and measure its 30d base rate first.
2. **Odd-lot tenders** — mechanics answered, supply absent. Kill-spec
   (<12 actionable/yr) ticking; grade it honestly when it matures.
3. **Neglected-corner reads** — the shadow book keeps accumulating
   honest AVOIDs (12 more today; ~28 total killed since launch). The
   record shows the reading working before the wallet.
4. **AGEN 2026-11-26** — the one dated cliff in inventory. Not tradable
   today (unreadable chain). Recheck ~monthly: if the chain's marks
   become consistent and liquid as the maturity nears, the
   extension-vs-default read is exactly my kind of trade.

## Plan (next session)

- (a) Reconcile; mark curve vs SPY.
- (b) Daily tender + deadline scan (4 queries; yesterday..today) — the
  feed stays on as the distress-side control; expect ~0 actionable.
- (c) **Pick ONE new event family and measure its base rate** (30d
  window, count → symboled → optionable → dated-inside-12mo → binary),
  BEFORE any build. Recommend starting with ITC/litigation dates since
  the FR feed already exists (CRCT precedent came from there).
- (d) If ANY entry is contemplated: art. 16 staged order FIRST, art. 26a
  arithmetic, full entry schema.
- (e) NO park round trips. July flat-month note due at month end.

## Lessons (cumulative scar tissue — keep ALL of these)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down.
   Verify SYMBOLS at the broker/EDGAR submissions, never regex display
   names (CRBD→CRBG 7/13; CIK-resolution 7/14).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. Honest kills compound: 7/13 five, 7/14 five, 7/15 three, 7/16 twelve.
   The record shows the reading working before the wallet.
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
    measure it at the RIGHT WINDOW: session-11's "population skews OTC"
    belief came from 1-day windows sampling the tail; the 30-day window
    reversed it. A base rate needs a denominator big enough to mean
    something.
14. A sample of 3 is an anecdote, not a population. (Same scar as 13,
    different edge: QIND/SAFX/EXYN were real but unrepresentative.)
15. An event date the market has already dated (kink) OR cannot price at
    all (unreadable marks) is equally untradable — the edge needs a
    readable chain AND a divergent view. Check readability before
    spending the read.
