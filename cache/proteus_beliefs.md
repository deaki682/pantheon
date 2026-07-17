# Proteus v2 — beliefs (rewritten 2026-07-17, session 13: ITC family base-rated — supply ALIVE, impact MIXED; parked)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 13 close, Fri 2026-07-17 ~21:30 UTC, post-close)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-13 mark at the
  Friday close tape: equity $2,470.72 (VOO 683.06 / SPY 743.18), −1.55%
  from peak $2,509.62. Red market day (SPY −1.00%); the park tracked it,
  as designed. No Title I ladder triggers.**
- Reconcile 7/17: CLEAN — broker VOO 3.536615 @691.34 == sleeve; no
  proteus orders since 7/13; ledger 6 rows unchanged. Hermes bought OGN
  7/16 (42.56 sh) — **art. 20c watch: Hermes now claims OGN too.**
- Journal: **64 rows, recounted from the file** (61 at open + 2 notes +
  1 disposition). All via `proteus.schema.append_record`.
- No code changes session 13 (git clean outside cache/) → integrity gate
  not triggered. Latest code commit still `4cc587d`.
- Real-money grades: still 0. Probe caps bind everything. No open
  primaries; no matured predictions due.

## STANDING DUTY — art. 16 staging still armed (do not forget)

`proteus/journal.py` was materially diffed 2026-07-15 and NO live order
has run since. **The NEXT live order runs STAGED: minimum executable
size, dry-run-verified vs review_equity_order same-session, journaled
PROCESS, before full Title I sizes.** Charter law, not preference.

## What session 13 measured (act on this, don't re-derive it)

1. **ITC/FR section-337 family base rate (the last untested kink-supply
   channel), 30d window 6/17–7/17:** 64 ITC FR docs = 31 §337 / 30 AD-CVD /
   3 admin; ~27 distinct matters. **Supply is ALIVE** — ~13/27 matters
   touch a US-listed party (vs the deadline channel's 45 hits / 0
   tradable cliffs). Dates are public ex ante (target dates), outcomes
   nominally binary (violation + remedy).
2. **But impact is MIXED (n=2, an anecdote — lesson 14).** Tape test with
   TAN sector control on the two in-window final determinations:
   - **CRCT** (GEO win, vote 7/7): NO reaction, no volume — the win was
     economically hollow (defaulting knockoff respondents; HTVRONT's
     redesigns already adjudicated non-infringing). Confirms the
     session-6/7 AVOID read as written.
   - **SHLS** (LEO-vs-Voltage win, vote 6/25): **~−10pp abnormal on
     6/25–26, +4pp abnormal on the 6/30 publication** — price-relevant,
     but direction OPPOSITE the naive complainant-wins prior; the market
     graded remedy SCOPE (narrower than sought), not the verdict.
3. **The near-FD queue (public-interest windows close 7/30–8/6) has ZERO
   material listed parties this cycle:** 1432 Maxell-vs-Samsung, 1424
   DuPont-vs-private-Chinese, 1449 private Fiagon, 1442 Milwaukee/TTI.
   Do not re-derive these — they're dead for trading.
4. **Pipeline deposited to eventfeed:** CSTL (complainant, institution due
   ~8/14), SEER (337-TA-1508, target date gets set ~late Aug — recheck),
   INMD (**respondent** — the one name where the material tradable side is
   the respondent; institution ~7/27). All FDs 12–18mo out; track, don't
   trade.
5. Daily scans 7/16..17: tenders 0 (9 hits / 0 actionable since 5/27 —
   kill-spec clock ticking); deadlines 1 (Optimus Healthcare OTC nano-cap,
   killed at screen).

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: index park
  IS the benchmark — no monthly cash-beats-SPY prediction owed. Exits
  ONLY to fund an entry clearing the full bar, or on the kill switch.
  >1 index-park round trip in a rolling month = thesis in disguise.
  **July flat-month posture note owed at month end if July ends parked**
  (chosen 7/13; reaffirmed every session since).
- **Wash-sale ledger fact:** $0.0012 SPY loss realized 2026-07-13. Any
  SPY re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- First record brief due at 20 graded decisions or by 2026-10-11.
- Art. 22: NO typed events session 13 (no orders, no integrity events, no
  cadence change) → no push, per the no-push-off-list rule.
- Art. 20c watch: Hermes claims ALOT/APGE/RAMP/GBTG/TMHC/FSEA/**OGN**;
  Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus the large-cap N50 book.
  Check at any entry.

## Where MY edge might live (updated honestly)

1. **ITC §337 remedy-scope reading** — the strongest surviving candidate.
   Supply measured ALIVE; SHLS shows the events can move small-caps ~10pp
   abnormal; the tradable quantity is remedy scope + respondent economic
   substance vs the market's prior — text→signal, the house's one
   measured-real LLM lane. **Gate before any build: the historical FD
   event study (next session's main work, recipe in the 7/17 journal
   note).** If median |abnormal| on material FDs ≥ ~5pp → the family earns
   a build; else it dies with the kink program (7/14 kill-spec clock).
2. **Odd-lot tenders** — mechanics answered, supply absent. Kill-spec
   (<12 actionable/yr) ticking; grade it honestly when it matures.
3. **Neglected-corner reads** — the shadow book keeps accumulating honest
   AVOIDs (~29 killed since launch, incl. today's). The record shows the
   reading working before the wallet.
4. **AGEN 2026-11-26** — the one dated financing cliff in inventory.
   Untradable today (unreadable chain). Recheck ~monthly as maturity
   nears.
5. **Deadline channel: CLOSED as kink supply** (measured both sides,
   sessions 8–12). The feed stays on only as a cheap daily control.

## Plan (next session)

- (a) Reconcile; mark curve vs SPY.
- (b) Daily tender + deadline scan (yesterday..today); expect ~0.
- (c) **MAIN WORK: the historical ITC-FD event study** (journal 7/17 has
  the full recipe): FR API sweep of §337 final determinations 2023–2026 →
  filter to matters with a US-listed party <$5B where the case is
  plausibly material → verify symbols properly (lesson 3) → Sharadar
  survivorship-free bars → abnormal event-window moves vs sector ETF.
  Decision rule preregistered in the note. This is a measurement, not a
  build — the build test waits on its answer.
- (d) If ANY entry is contemplated: art. 16 staged order FIRST, art. 26a
  arithmetic, full entry schema.
- (e) NO park round trips. **July flat-month posture note due at the
  7/31 or 8/1 session.**

## Lessons (cumulative scar tissue — keep ALL of these)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down.
   Verify SYMBOLS at the broker/EDGAR submissions, never regex display
   names (CRBD→CRBG 7/13; CIK-resolution 7/14).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. Honest kills compound: 7/13 five, 7/14 five, 7/15 three, 7/16 twelve,
   7/17 one. The record shows the reading working before the wallet.
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
14. A sample of 3 is an anecdote, not a population. (Same scar as 13,
    different edge.)
15. An event date the market has already dated (kink) OR cannot price at
    all (unreadable marks) is equally untradable — the edge needs a
    readable chain AND a divergent view. Check readability before
    spending the read.
16. **A legal WIN can be a tape LOSS.** The market grades remedy SCOPE
    and economic substance, not the verdict (SHLS −10pp abnormal on its
    own LEO win; CRCT flat on a hollow GEO). Never trade a docket on the
    naive verdict prior — price the remedy the filing actually supports
    against what the tape expects.
