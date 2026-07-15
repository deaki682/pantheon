# Proteus v2 — beliefs (rewritten 2026-07-15, session 11: journal-path trap found and fixed; feed3 v2 measured; parked)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 11 close, Wed 2026-07-15 ~14:45 UTC, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Equity $2,509.62 at the
  VOO 694.06 mark (14:11:27Z tape) — NEW PEAK. SPY 755.04.**
- Reconcile 7/15: CLEAN — broker VOO 3.536615 @ 691.34 == sleeve; no
  proteus orders since 7/13; ledger 6 rows (3 placed + 3 filled, by
  design). Operator PERSONAL VXUS sell (11 sh @ 85.00) filled at the 7/15
  open — blind-spot position, matches the 7/14 situation note; account BP
  should now be ~$1,167 but RE-READ IT LIVE at any order (art. 26a).
- Journal: **46 rows, RECOUNTED FROM THE FILE** (37 found at open + 2
  integrity/anomaly/session notes + 3 migrated + 2 dispositions + 4
  afternoon notes/dispositions). Ledger unchanged.
- Suite: **1924 green.** Commit `4cc587d` on session dev branch
  (journal-path fix + feed3 query) — reaches main via the operator's PR
  flow like `19b71f1`/`b2f954e` did.
- Real-money grades: still 0. Probe caps bind everything. No open
  primaries; no matured predictions due.

## STANDING DUTY — art. 16 staging armed (do not forget this)

`proteus/journal.py` (append_decision, on the order-path manifest) was
materially diffed 2026-07-15 (JOURNAL_PATH fix). **The NEXT live order
runs STAGED: minimum executable size, dry-run-verified against
review_equity_order in the same session, journaled as a PROCESS entry,
BEFORE full Title I sizes.** This is charter law, not a preference.

## What session 11 proved (act on this, don't re-derive it)

1. **The lost-entries mystery is SOLVED and FIXED.** journal.py's
   JOURNAL_PATH defaulted to the v1 ghost path; `append_decision(record)`
   with no explicit path silently wrote to an unpersisted stray file.
   Session 10's 3 narrative entries died that way; session 11's 3
   session-open notes did too (caught live, migrated same-session, stray
   deleted). Fix + regression test shipped (`4cc587d`). **Session code
   standard: write via `proteus.schema.append_record` (the art. 15 gate);
   it validates dispositions/grades too — `journal.append_decision`
   refuses action types the schema accepts.**
2. **Feed3 v2 measured, not guessed:** planned phrases "forbear until" /
   "forbearance period expires" = ZERO FTS hits/30d → NOT added. New query
   `"agrees to forbear"` = +1 hit/30d, surfaces agreement EXHIBITS the v1
   queries miss → ADDED. Systematic extraction gap identified: cliffs in
   agreement docs are RELATIVE dates ("sixty (60) days following the
   funding date") which absolute-date parsing cannot see. **Deliberately
   NOT built**: on 3 live cases (QIND, SAFX, EXYN) every dated cliff died
   at the LIQUIDITY gate, never at extraction — the feed3 population
   skews nano-cap/OTC with no chains. Build relative-date extraction ONLY
   if a chain-bearing candidate ever surfaces.
3. **SAFX new fact:** 7/08 ex10-1 is a NEW $750k bridge note, 10%,
   maturity ~60 days post-funding (~early-Sept 2026 cliff), Nasdaq
   delisting = event of default, 5M penalty shares. Real distress, real
   date, UNTRADABLE ($0.49, no chain). The Twain forbearance's own cliff
   is still undated in any filed doc.
4. **Repo anomaly flagged to operator (art. 22 push sent):** 7 commits
   authored "Claude" 2026-07-15 06:54–08:35Z on the session dev branch
   build "UnTraceable" (client-side photo EXIF stripper + $7 sales landing
   page). Not trading machinery, not journaled anywhere, not proteus:-
   prefixed, fails the build test. Content itself benign. NOT my work per
   the record; possibly the operator's own side project on the shared
   branch. Left untouched. If the operator says it's theirs, drop it; if
   not, it needs investigating (who authored it?).
5. Scans 7/14..15: tenders 0 (9 hits / 0 actionable since 5/27, kill-spec
   ticking); deadlines 2 (PLUR: EIB negotiation, no date yet — REVISIT on
   any dated amendment; QIND: real workout, dated 2028 terminus, OTC
   untradable). EDGAR FTS 500s persist intermittently; retry-with-backoff
   clears in 1–2 attempts (don't patch shared/edgar.py for a transient).

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: index park
  IS the benchmark — no monthly cash-beats-SPY prediction owed. Exits
  ONLY to fund an entry clearing the full bar, or on the kill switch.
  >1 index-park round trip in a rolling month = thesis in disguise. July
  flat-month note owed if July ends parked (posture chosen 7/13,
  reaffirmed 7/14 and 7/15).
- **Wash-sale ledger fact:** $0.0012 SPY loss realized 2026-07-13. Any
  SPY re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order: spendable = min(sleeve cash, account
  settled BP minus other gods' pending deployments). My cash: $54.9989.
- First record brief due at 20 graded decisions or by 2026-10-11.
- Art. 22 push SENT this session (batched: integrity event + fix, repo
  anomaly, session status). No orders placed; no other typed events.

## Where MY edge might live (updated honestly)

1. **Event convexity via the kink screen** — machinery complete; the
   supply problem is now sharper: feed3 finds real dated distress cliffs
   but in an untradable population. The next supply idea must source
   OPTIONABLE names first (screen the chain, then the filings — invert
   the funnel), or the kink screen starves. Think on this before
   building anything.
2. **Odd-lot tenders** — mechanics fully answered, waiting on supply.
   Kill-spec (<12 actionable/yr) ticking.
3. **Neglected-corner reads** — CRCT precedent; keep accumulating honest
   AVOIDs; the shadow book is where avoidance becomes evidence (art. 8).
4. **Avoidance is still the only measured-real LLM skill** — sessions
   10–11 killed 8 more candidates before a dollar moved. The record shows
   avoidance working; it does not yet show a positive edge.

## Plan (next session)

- (a) Reconcile VOO; mark curve vs SPY.
- (b) Daily tender + deadline scan (now 4 queries; yesterday..today).
- (c) **Invert-the-funnel study (no build yet):** take the optionable
  universe (names with listed chains) and ask which of THEM carry dated
  financing/deal cliffs inside 12 months — from the eventfeed store
  (AVB/APGE votes, HUN outside date) and any new deposits. That is where
  kink-screen supply must come from; feed3 keeps running as the
  distress-side control.
- (d) If ANY entry is contemplated: art. 16 staged order FIRST (see
  standing duty above), art. 26a arithmetic, full entry schema.
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
5. Honest kills compound: 7/13 five, 7/14 five, 7/15 three more (+SAFX
   follow-up). The record shows the reading working before the wallet.
6. Verify the record before trusting any summary of it — including mine.
   Counts are computations, never recollections. (Session 11 proved it:
   the "41 rows" belief was wrong twice over.)
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
    `schema.append_record`. A writer that RAISES on a valid record and a
    writer that silently writes to the WRONG FILE are different bugs; I
    had both in one module.
13. Measure a query's base rate BEFORE adding it to a feed. Two planned
    queries died in measurement today; one unplanned one earned its place.
