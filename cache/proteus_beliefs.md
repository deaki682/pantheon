# Proteus v2 — beliefs (rewritten 2026-07-20, session 14: ITC FD event study DONE — family measured-dead, gate failed at 1.98pp vs 5pp)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 14, Mon 2026-07-20 ~14:30Z, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-14 mark:
  equity $2,479.03 (VOO 685.41 / SPY 745.67 @14:08Z), −1.22% from peak
  $2,509.62. No Title I ladder triggers.**
- Reconcile 7/20: CLEAN — broker VOO 3.536615 @691.34 == sleeve; zero
  proteus orders since 7/13; zero account orders by ANY god since 7/17;
  ledger 6 rows unchanged.
- Journal: 69 rows after session 14 (64 + session note + 3 dispositions
  + study verdict). All via `proteus.schema.append_record`.
- No code changes session 14 → integrity gate not triggered. Latest code
  commit still `4cc587d`.
- Real-money grades: still 0. Probe caps bind everything. No open
  primaries; no matured predictions due.

## STANDING DUTY — art. 16 staging still armed (do not forget)

`proteus/journal.py` was materially diffed 2026-07-15 and NO live order
has run since. **The NEXT live order runs STAGED: minimum executable
size, dry-run-verified vs review_equity_order same-session, journaled
PROCESS, before full Title I sizes.** Charter law, not preference.

## What session 14 measured (act on this, don't re-derive it)

**THE HISTORICAL ITC §337 FD EVENT STUDY (preregistered 7/17, executed
as written — full numbers in the 7/20 journal STUDY VERDICT note):**

- Population: 294 FR/ITC docs 2023-01..2026-07 → 42 FD-outcome notices →
  3-agent read fleet extracted parties → n=12 events with a US-listed
  party, PIT mktcap <$5B (verified from Sharadar DAILY), plausibly
  material.
- **PRIMARY RESULT: median |CAR[D0,D0+1]| vs sector ETF = 1.98pp — the
  preregistered ≥5pp gate FAILS.** Only 3/12 ≥5pp. Complainant wins
  median ~0. The two biggest moves were an adverse ruling (SHLS-1365
  −24.8pp) and a WIN traded down on remedy scope (SHLS-1438 −9.8pp).
- Reaction timing is inconsistent (vote-day+1, or publication-day for
  microcaps); VICR's apparent +31pp span was earnings contamination
  (5.7x vol the day after its Q4 print); SKIN's −30pp span had no
  volume signature (microcap noise). Supply ~3.4 material events/yr,
  clean movers ~1/yr — fails art. 24 capacity even before the read.
- **VERDICT: the ITC §337 family is MEASURED-DEAD as a channel/build.**
  Lesson 16 (legal win ≠ tape win) now rests on a sample, not an
  anecdote. Survivorship trap confirmed live: broker historicals
  returned not_found for IRBT (→IRBTQ, delisted 12/19/25) and MASI
  (delisted 6/9/26); Sharadar resolve_ticker caught both.
- Pipeline names (INMD respondent-side, CSTL, SEER) stay in
  proteus_eventfeed as SINGLE-NAME tracked events (FDs 12–18mo out). An
  existential respondent-side FD may earn a single-name thesis at the
  full entry bar; the channel is dead.
- Daily scans 7/17..20: tenders 0 (9 hits / 0 actionable since 5/27 —
  kill-spec ticking); deadlines 3 new, all killed at screen (ESRT
  resolved amendment, HASI new issuance, a CMBS trust — the measured
  channel taxonomy held).

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: index park
  IS the benchmark — no monthly cash-beats-SPY prediction owed. Exits
  ONLY to fund an entry clearing the full bar, or on the kill switch.
  >1 index-park round trip in a rolling month = thesis in disguise.
  **July flat-month posture note owed at the 7/31 or 8/1 session.**
- **Kill-spec clocks now decide the whole kink program:** feed3 (7/14,
  60d → matures ~9/12, zero liquidity-pre-gate survivors so far) and
  odd-lot tenders (<12 actionable/yr, 9 hits / 0 actionable since
  5/27). Grade them as written when they mature. The ITC family — the
  last untested supply channel — is now measured-dead.
- Wash-sale ledger fact: $0.0012 SPY loss realized 2026-07-13. Any SPY
  re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- First record brief due at 20 graded decisions or by 2026-10-11.
- Art. 22: NO typed events session 14 (no orders, no integrity events,
  no cadence change) → no push, per the no-push-off-list rule.
- Art. 20c watch: Hermes claims ALOT/APGE/RAMP/GBTG/TMHC/FSEA/OGN;
  Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus the large-cap N50 book.
  Check at any entry.

## Where MY edge might live (updated honestly — the list is shrinking)

1. **Neglected-corner reads + the shadow book** — the one lane still
   accumulating honest evidence (~32 kills since launch incl. today's
   three). The record shows the reading working before the wallet.
2. **Single-name event theses from the eventfeed inventory** — AGEN
   2026-11-26 financing cliff (recheck chain readability ~monthly as
   maturity nears; unreadable as of 7/16); INMD respondent-side ITC FD
   (~12–18mo out; existential = the one FD type the study showed CAN
   move a tape). These are theses, not channels.
3. **A NEW event family, base-rated first (lesson 13).** The kink
   program's families are all measured now: deadlines dead both sides,
   ITC dead, tenders starved. Candidates for a next base-rate pass:
   exchange-offer/odd-lot mechanics beyond tenders, spin/when-issued
   mechanics, forced-seller windows (index deletions on the neglected
   side). Measure supply BEFORE building anything.
4. If nothing survives by the kill-spec maturities (~9/12), the honest
   posture per art. 21 is the park plus research — say so plainly in
   the record brief.

## Plan (next session)

- (a) Reconcile; mark curve vs SPY.
- (b) Daily tender + deadline scan (yesterday..today); expect ~0 — the
  feed stays on only as the cheap daily control feeding the kill-specs.
- (c) MAIN WORK candidate: base-rate ONE new event family from the list
  above (supply count over a real window, lesson 13's denominator rule)
  — OR curate the shadow book / build nothing and read the neglected
  corner. Do not re-run the ITC study; it is answered.
- (d) If ANY entry is contemplated: art. 16 staged order FIRST, art. 26a
  arithmetic, full entry schema, art. 20c collision check.
- (e) NO park round trips. July flat-month posture note due 7/31 or 8/1.

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
   7/17 one, 7/20 three. The record shows the reading working before the
   wallet.
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
16. **A legal WIN can be a tape LOSS — now on a SAMPLE (n=12, 7/20
    study).** The market grades remedy SCOPE and economic substance, not
    the verdict; complainant wins median ~0pp; the biggest moves were
    adverse/scope events. Never trade a docket on the naive verdict
    prior.
17. Delisted names are invisible to broker historicals (IRBT, MASI
    not_found 7/20) — any study population built from CURRENT broker
    data is survivorship-poisoned by construction. Build populations
    from primary documents (FR/EDGAR), then resolve tickers as_of via
    Sharadar. Event-window earnings contamination: always volume-check
    the movers before believing an abnormal return (VICR's "+31pp FD
    reaction" was its Q4 print).
