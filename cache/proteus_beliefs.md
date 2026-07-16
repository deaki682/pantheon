# Proteus v2 — beliefs (rewritten 2026-07-16, session 12: invert-the-funnel measured; kink-screen supply starved from BOTH directions; parked)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 12 close, Thu 2026-07-16 ~15:45 UTC, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Equity $2,503.47 at the
  VOO 692.32 mark (15:07Z tape); SPY 753.18. Peak $2,509.62 stands
  (drawdown −0.25%, no ladder event).**
- Reconcile 7/16: CLEAN — broker VOO 3.536615 @ 691.34 == sleeve; zero
  proteus orders since 7/13; ledger 6 rows unchanged.
- Journal: **54 rows, RECOUNTED FROM THE FILE** (46 at open + 1 session
  note + 6 dispositions + 1 study note). All writes went through
  `proteus.schema.append_record` (the art. 15 gate) — it refused two
  malformed drafts correctly before accepting (the gate works).
- Real-money grades: still 0. No open primaries; no matured predictions
  due. No orders placed s12; no code shipped s12 (suite run not required —
  integrity gate binds self-modifications only).
- Eventfeed store: 20 events (added QIND financing_deadline 2028-01-15,
  installments from 2026-07-30, source_url cited; OTC untradable —
  deposited for the record).

## STANDING DUTY — art. 16 staging armed (do not forget this)

`proteus/journal.py` (append_decision, on the order-path manifest) was
materially diffed 2026-07-15 (JOURNAL_PATH fix). **The NEXT live order
runs STAGED: minimum executable size, dry-run-verified against
review_equity_order in the same session, journaled as a PROCESS entry,
BEFORE full Title I sizes.** This is charter law, not a preference.

## What session 12 measured (act on this, don't re-derive it)

1. **The inverted funnel WORKS as machinery, and its answer is bearish
   for the kink screen.** Method proven cheap: FTS channel → broker quote
   gate (kills OTC/inactive, 20 symbols/call) → chain gate
   (`get_option_chains`, 1 call/name, kills ~80% pre-read) → document
   read → dated-cliff gate. Measured this window:
   - `"Item 2.04"` 8-K/30d: 32 hits (12 CMBS noise), 8 corporate tickers,
     3 chain-bearing (AMC/AXTI/DAIO), **0 forward-dated cliffs** — Item
     2.04 is BACKWARD-looking by construction (reports triggers already
     fired), and partly a post-M&A artifact (ASRT/CWAN/SEM inactive =
     completed deals' change-of-control accelerations).
   - Going-concern 10-Q/K/14d: 23 hits, 1 chain-bearing (BZAI), 0 dated
     (burn-rate cliffs have no date to straddle).
   - `"springing maturity"` 8-K/30d measured per lesson 13 BEFORE adding:
     9 hits, 7 tickers, 100% listed/optionable (BV/CAR/GLIBA/OII/PBH/
     SITM/SMTC) — verified read (CAR 7/01) shows routine-refi protective
     boilerplate, spring dates relative and years out. **Query DECLINED.**
     Near-dated springs live in EXISTING cap structures (10-K
     cross-sectional read = heavier build, doubtful edge vs credit desks).
2. **Kink-screen supply is now measured starved from BOTH directions:**
   distress-first (feed3) → dated but untradable; optionable-first →
   tradable but undated-or-resolved. Kill-spec clock (from 7/14: 60 days
   of zero liquidity-pre-gate survivors → DEAD) ticked another day with
   zero survivors. Do not build for this ground without a NEW sourcing
   idea that names where forward-dated + optionable events actually live
   (candidates untested: Federal Register/ITC decision dates on listed
   names — the fr_itc plumbing exists; Nasdaq compliance-deadline 8-Ks).
3. **Broker gates surface M&A corpses:** `get_equity_quotes` 400s with
   `inactive_instruments` on acquired/delisted names — a free
   is-this-still-alive gate. And batch quotes silently DROP symbols they
   can't serve (11 of 18 returned; the missing 3 were the inactive ones,
   surfaced only when queried alone) — never assume a missing symbol is
   an error in your list; query it alone before concluding.
4. Daily scan 7/15..16: tenders 0 (kill-spec ticking, 0 actionable since
   5/27); deadlines 1 = QIND second forbearance (RB Capital, $1.675M / 19
   installments 7/30/26→1/15/28) — read, deposited, killed at the same
   liquidity gate as every prior QIND hit.
5. Side observations from the study tape (NOT theses, NOT worked):
   NVVE −54% intraday on 7/16; AXTI −12% same day with an InP/AI story
   and an undated $49M redemption overhang. Neither has a divergence
   view; neither was leaned live. If either ever earns a read it starts
   from zero at the full entry bar.

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: index park
  IS the benchmark — no monthly cash-beats-SPY prediction owed. Exits
  ONLY to fund an entry clearing the full bar, or on the kill switch.
  >1 index-park round trip in a rolling month = thesis in disguise. July
  flat-month note owed if July ends parked (posture chosen 7/13,
  reaffirmed 7/14, 7/15, 7/16).
- **Wash-sale ledger fact:** $0.0012 SPY loss realized 2026-07-13. Any
  SPY re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order: spendable = min(sleeve cash, account
  settled BP minus other gods' pending deployments). My cash: $54.9989.
- First record brief due at 20 graded decisions or by 2026-10-11.
- **Repo anomaly (from s11, still open):** 7 non-proteus "UnTraceable"
  commits on the session dev branch, flagged to operator via art. 22 push
  7/15. No operator response seen by s12. Left untouched; not mine.
- No art. 22 typed events arose in s12 (no orders, no drawdown crossing,
  no cadence change, no integrity events) — no push owed.

## Where MY edge might live (updated honestly)

1. **Event convexity via the kink screen** — machinery complete, supply
   MEASURED STARVED from both funnel directions (see above). On the
   clock. The only paths left: (a) regulatory-date channels (FR/ITC on
   listed names, plumbing exists, base rate unmeasured), (b) let the
   kill-spec fire on schedule and fold the machinery. Measure (a) before
   any further effort here.
2. **Odd-lot tenders** — mechanics fully answered, waiting on supply.
   Kill-spec (<12 actionable/yr) ticking; 0 actionable since 5/27.
3. **Neglected-corner reads** — CRCT precedent; keep accumulating honest
   AVOIDs; the shadow book is where avoidance becomes evidence (art. 8).
4. **Avoidance is still the only measured-real LLM skill** — s12 killed
   6 more at the gates before a dollar moved (QIND, AXTI, AMC, DAIO,
   BZAI, CAR). The record shows the reading working; it does not yet
   show a positive edge.

## Plan (next session)

- (a) Reconcile VOO; mark curve vs SPY.
- (b) Daily tender + deadline scan (4 queries; yesterday..today).
- (c) **Measure the FR/ITC channel base rate** (the last untested kink
  supply): `eventfeed.fr_itc_recent` — how many dated decisions/30d, how
  many on listed+optionable names? One session, measurement only; the
  result decides whether the kink ground lives to its kill-spec date or
  dies early by evidence.
- (d) If ANY entry is contemplated: art. 16 staged order FIRST (standing
  duty above), art. 26a arithmetic, full entry schema.
- (e) NO park round trips. July flat-month posture note comes due at
  month end if still parked.

## Lessons (cumulative scar tissue — keep ALL of these)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down.
   Verify SYMBOLS at the broker/EDGAR submissions, never regex display
   names (CRBD→CRBG 7/13; CIK-resolution 7/14).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. Honest kills compound: 7/13 five, 7/14 five, 7/15 three, 7/16 six.
   The record shows the reading working before the wallet.
6. Verify the record before trusting any summary of it — including mine.
   Counts are computations, never recollections.
7. Session containers are ephemeral and shallow-cloned: `git fetch
   --deepen` before reasoning about history; `pip install pytest numpy`
   before the suite (~1 min, then 1924 tests in ~4s).
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
12. **Default-path arguments are traps in a repo with live and ghost
    twins of the same file.** Pass paths explicitly or pin them with a
    regression test. And: `journal.append_decision` validates only
    enter|exit|note — dispositions/grades go through
    `schema.append_record`.
13. Measure a query's base rate BEFORE adding it to a feed — and verify
    ONE hit by reading it before believing the base rate means what you
    think (s12: springing-maturity's 9 listed hits were all routine-refi
    boilerplate; the count lied about the content).
14. Batch quote calls silently drop symbols they can't serve; a missing
    symbol is a FINDING (often a delisted/acquired corpse), not a typo —
    re-query it alone. `inactive_instruments` is a free M&A-corpse
    detector.
