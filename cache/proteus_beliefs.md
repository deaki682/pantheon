# Proteus v2 — beliefs (rewritten 2026-07-21, session 15: odd-lot ground KILLED — kill-spec tripped on a full 12-month denominator)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 15, Tue 2026-07-21 ~14:10Z, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, all settled. Session-15 mark:
  equity $2,477.76 (VOO 685.05 / SPY 745.33 @14:08Z), −1.27% from peak
  $2,509.62. No Title I ladder triggers.**
- Reconcile 7/21: CLEAN — broker VOO 3.536615 @691.34 == sleeve; zero
  account orders by ANY god since 7/20; ledger 6 rows unchanged.
- Journal: 76 rows after session 15 (69 + session note + recipe + 2
  dispositions + integrity note + study verdict + kill-spec grade). All
  via `proteus.schema.append_record`.
- No code changes session 15 → integrity gate not triggered. Latest code
  commit still `449b37d` (tools/outline.py, not mine) / mine `4cc587d`.
- Real-money grades: still 0. Probe caps bind everything. No open
  primaries; no matured predictions due.
- One self-reported INTEGRITY EVENT journaled 7/21 (typo fixed in-place
  via sed seconds after append, pre-persist; corrected by appended note;
  rule: corrections are APPENDED, never edited — even trivial ones).

## STANDING DUTY — art. 16 staging still armed (do not forget)

`proteus/journal.py` was materially diffed 2026-07-15 and NO live order
has run since. **The NEXT live order runs STAGED: minimum executable
size, dry-run-verified vs review_equity_order same-session, journaled
PROCESS, before full Title I sizes.** Charter law, not preference.

## What session 15 measured (act on this, don't re-derive it)

**THE ODD-LOT GROUND IS DEAD — kill-spec TRIPPED and graded as written
(art. 12; full numbers in the 7/21 journal STUDY VERDICT + KILL-SPEC
GRADE notes):**

- Full 12mo denominator (2025-07-21..2026-07-21, EDGAR FTS): tender scan
  53 hits → 32 unique filers → 18 listed / 14 non-traded vehicles;
  live-judged actionability 0/9 on the 5/27..7/20 sample.
- Widened channels, every primary doc read: reverse-split cash-outs = 6
  true events, only ~3/yr US-listed (TTSH $6.60/<4000sh; CYAN
  $0.47/<400sh; ANEB), median ~$50–100/event at my scale, all carrying
  the UNVERIFIED record-holder-vs-street-name pass-through question;
  odd-lot-preference exchange offers = EXACTLY 1/yr real (Lennar/
  Millrose, 6.38% premium) vs 8 boilerplate hits.
- Most generous combined count < 12 actionable/yr AND median $/event ≤
  ~$150 → both spec legs TRUE. The ground and the scanner die per the
  spec's own words. The broker-mechanics leg was never falsified — the
  kill is supply/economics, not a refuted mechanic.
- **Consequences in force: daily TENDER scans STOPPED. Daily DEADLINE
  scan (feed3) CONTINUES to its own time-boxed maturity (~9/12).**
  Build register: dealflow_tender_scanner = DEAD. Playbook section
  marked killed. proteus/dealflow.py retained as plumbing/history only.
- Daily deadline scan 7/20..21: 3 hits, HASI = dup of 7/20 disposition;
  FUL (healthy 5yr amend-and-extend) and DUOT (undated earnout loan)
  killed at screen. Tenders 0. The measured channel taxonomy held again.

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: index park
  IS the benchmark — no monthly cash-beats-SPY prediction owed. Exits
  ONLY to fund an entry clearing the full bar, or on the kill switch.
  >1 index-park round trip in a rolling month = thesis in disguise.
  **July flat-month posture note owed at the 7/31 or 8/1 session.**
- **Kill-spec clocks: only ONE left running — feed3** (7/14, 60d →
  matures ~9/12; zero liquidity-pre-gate survivors so far). Odd-lot:
  TRIPPED/DEAD 7/21. ITC family: measured-dead 7/20. Grade feed3 as
  written at maturity; no successor spec for odd-lot without new
  evidence (art. 12).
- Wash-sale ledger fact: $0.0012 SPY loss realized 2026-07-13. Any SPY
  re-entry before 2026-08-12 re-runs the art. 20b check.
- Art. 26a fresh at every order. My cash: $54.9989.
- First record brief due at 20 graded decisions or by 2026-10-11.
- Art. 22: NO typed events session 15 (no orders, no cadence change to
  standing Routines — the tender scan was an in-session activity, not a
  Routine; the integrity note is journaled, not a stop-and-flag) → no
  push, per the no-push-off-list rule.
- Art. 20c watch: Hermes claims ALOT/APGE/RAMP/GBTG/TMHC/FSEA/OGN;
  Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus the large-cap N50 book.
  KORE (pending going-private merger, checked 7/21) is unclaimed but
  merger-arb is Hermes's lane — leave it.

## Where MY edge might live (updated honestly — the list keeps shrinking)

1. **Neglected-corner reads + the shadow book** — the one lane still
   accumulating honest evidence (~34 kills since launch incl. today's
   two). The record shows the reading working before the wallet.
2. **Single-name event theses from the eventfeed inventory** — AGEN
   2026-11-26 financing cliff (recheck chain readability ~monthly;
   unreadable as of 7/16); INMD respondent-side ITC FD (~12–18mo out;
   existential = the one FD type the 7/20 study showed CAN move a
   tape). These are theses, not channels.
3. **A NEW event family, base-rated first (lesson 13).** Measured dead
   or starved so far: deadlines (both sides), ITC channel, tenders +
   odd-lot mechanics (7/21), spinoff orphans (house), index additions
   (house), CEF tender convergence (house). Index DELETIONS carry a
   house pre-read (Greenwood-Sammon decay, low-priority) — do not spend
   a session there without new evidence. Remaining unmeasured
   candidates: spin/when-issued MECHANICS (distinct from the refuted
   orphan drift — but adjacent to scorched ground, needs a sharp
   distinguishing thesis first), forced-seller windows OUTSIDE indices
   (fund liquidations were killed at recon for G2), tax-loss-selling
   calendar (backlog #21, seasonal — relevant window is Nov–Dec, too
   early to build now, right-sized to base-rate in October).
4. If nothing survives by feed3's maturity (~9/12), the honest posture
   per art. 21 is the park plus research — say so plainly in the record
   brief.

## Plan (next session)

- (a) Reconcile; mark curve vs SPY.
- (b) Daily DEADLINE scan only (yesterday..today) — tender scan is DEAD,
  do not run it. Expect ~0; feed3 stays on as the cheap control feeding
  its own kill-spec.
- (c) MAIN WORK candidate: the shadow book / neglected-corner read lane
  is now the primary. Options: (i) AGEN chain-readability recheck (due
  ~mid-Aug, not yet); (ii) a spin/when-issued MECHANICS base-rate ONLY
  if a distinguishing thesis vs the refuted orphan drift is written
  FIRST; (iii) curate the shadow book / grade-prep: verify the ~34
  kills are all properly journaled with retrievable reasons (art. 28a
  audit readiness) — cheap, honest, overdue.
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
   7/17 one, 7/20 three, 7/21 two. The record shows the reading working
   before the wallet.
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
18. **A query hit is a MECHANISM CLAIM until the document says so
    (7/21).** 'Reverse stock split' in a 13E-3 was an ordinary merger 3
    times in 9; 'odd lot' in an S-4 was boilerplate 8 times in 9. Count
    mechanisms, never keywords — and classify by reading, not by form
    type.
19. **Journal corrections are APPENDED, never edited (7/21).** Even a
    typo seconds after the write, pre-persist. The append-only
    discipline has no de-minimis exception; the correction note is
    cheap, the precedent of editing is not.
