# Proteus v2 — beliefs (rewritten 2026-07-14, session 10: feed #3 built and shaken down; parked, hunting supply)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 10 close, Tue 2026-07-14 ~15:30 UTC, market hours)

- **Sleeve: PARKED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash, ALL SETTLED as of today (staged-sell
  proceeds settled 7/14 per T+1). Equity $2,501.14 at the VOO 691.66 mark
  (15:06:52Z tape); peak 2501.14. SPY 752.44.**
- Reconcile 7/14: CLEAN — broker VOO 3.536615 @ 691.34 == sleeve; no new
  orders since the 3 of 7/13; ledger 6 rows. Account settled BP $237.12 ≥
  my $55 cash (the park consumed the rest; that is the design).
- Journal: 33 → 41 records today (session-open, build register, shakedown
  note, 5 feed-3 dispositions). NO orders placed today. Ledger unchanged.
- Suite: **1920 green** (1915 + 5 feed-3 extraction tests). Commit
  `b2f954e` (feed #3) on session dev branch — reaches main via the
  operator's PR flow like `19b71f1` did.
- Real-money grades: still 0. Probe caps bind everything. Matured
  predictions due: none (park carries no thesis; no open primaries).

## What today proved (act on this, don't re-derive it)

1. **Feed #3 (8-K financing deadlines) mechanics are PROVEN** —
   `eventfeed.scan_deadlines/enrich_deadline/extract_deadline_date`,
   register row feed3_8k_financing_deadlines, shakedown journaled.
   6 hits/10 days (~220/yr). Extraction verified EXACT against source
   (SMTC 2031-07-06 == the agreement's stated revolver maturity).
2. **But the first window's catalyst yield was ZERO.** The
   extended-maturity queries mostly surface healthy amend-and-extends
   (5-yr revolvers — never deposit these, noise). The distress residue
   (SAFX/XCF Global carries live Twain/GNCU forbearance arrangements) is
   real but its dated cliff lives in docs the queries don't match. Next
   iteration: query the forbearance agreements' OWN dated language
   ("forbear until", "forbearance period expires"); deposit judgment =
   only deadlines inside ~12 months are catalysts. Kill-spec clock runs
   from 7/14: 60 days of zero liquidity-pre-gate survivors → DEAD.
3. **Extraction lesson: first-date-in-window fails on 8-K prose** — the
   announcement date ("On July 10, 2026, the Company entered into...")
   leads every window. `_all_dates_near` (all dates per window) + strict
   post-filing filter + modal fixed it. The proxy extractors keep their
   first-date heuristic (cover pages lead with the meeting date).
4. **EDGAR FTS 500s intermittently** (twice today); retry-with-backoff at
   the call site clears it in 1-2 attempts. Don't patch shared/edgar.py
   for a transient.
5. Eventfeed refresh: +3 events (AVB/APGE merger votes 8/12 + 8/11, HUN
   outside date 2027-09-15; all CIK-resolved via EDGAR submissions API,
   HUN's extracted meeting date failed plausibility and was dropped).
   Note: APGE is a PERSONAL position in the account — blind-spot
   disclosed; no god claims it; merger votes never feed long options.

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: index park
  IS the benchmark — no monthly cash-beats-SPY prediction owed. Exits
  ONLY to fund an entry clearing the full bar, or on the kill switch.
  >1 index-park round trip in a rolling month = thesis in disguise.
  July flat-month note (if July ends parked): posture chosen consciously
  7/13, reaffirmed 7/14.
- **Tenders: 9 hits / 0 actionable since 5/27** (rescan 7/14: 0 new).
  Kill-spec (<12 actionable/yr) keeps ticking.
- **Wash-sale ledger fact:** $0.0012 SPY loss realized 2026-07-13. Any
  SPY re-entry before 2026-08-12 re-runs the art. 20b check. VOO park is
  a different ticker; gray area disclosed.
- Re-run art. 26a fresh at every order: spendable = min(sleeve cash,
  account settled BP minus other gods' pending deployments). Today:
  min(55.00, 237.12) = 55.00.
- First record brief due at 20 graded decisions or by 2026-10-11.
- No art. 22 typed events arose today (no orders, no drawdown crossing,
  no integrity stop, no cadence change, no collision, persist verified) —
  no push owed.

## Where MY edge might live (updated honestly)

1. **Event convexity via the kink screen** — machinery complete; supply
   still the missing piece. Feed #3 v1 skews to healthy refis; the v2
   iteration (forbearance-doc dated language) is the next build. FERC/
   state-PUC deliberately deferred (mega-cap skew, lower expected yield).
2. **Odd-lot tenders** — mechanics fully answered, waiting on supply.
3. **Neglected-corner reads** — CRCT precedent; keep accumulating honest
   AVOIDs.
4. **Avoidance is still the only measured-real LLM skill** — today it
   killed 5 more candidates (feed-3 first window) before a dollar moved.
   The record shows avoidance working; it does not yet show a positive
   edge. Do not confuse the two.

## Plan (next session)

- (a) Reconcile VOO; mark curve vs SPY.
- (b) Feed #3 v2: forbearance-deadline query iteration ("forbear until" /
  "forbearance period expires" phrases; SAFX's Twain forbearance doc is
  the test case — find its dated cliff via EDGAR company filings if it
  was ever filed). Build test already registered; this is tuning, not a
  new machine.
- (c) Daily tender + deadline scan (yesterday..today window) — cheap now,
  both feeds have retry-with-backoff.
- (d) Kink-screen any candidate that arrives with a <12mo deadline AND a
  live chain (bid-side liquidity pre-gate first, always).
- (e) NO park round trips. The next order should be a thesis entry or
  nothing.

## Lessons (cumulative scar tissue — keep ALL of these)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down.
   Never deposit an extracted date/symbol without a plausibility gate —
   and verify the SYMBOL at the broker/EDGAR submissions, never regex
   display names alone (CRBD→CRBG 7/13; CIK-resolution 7/14).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. The first honest kill (CRCT) is worth more to the record than a
   coin-flip first trade would have been. 7/13 added five; 7/14 five more.
6. Verify the record before trusting any summary of it — including mine.
   Counts are computations, never recollections.
7. Session containers are ephemeral and shallow-cloned: `git fetch
   --deepen` before reasoning about history; `pip install pytest numpy`
   before the suite (~1 min, then 1920 tests in ~4s).
8. In-session crons/one-shot wakes DIE WITH THE CONTAINER — graded
   REFUTED 7/13. Only operator-provisioned Routines wake me. Size every
   entry to the blind unattended worst case.
9. Screens lie through their inputs before they lie through their logic:
   gate every LEG of every quote on its own merits; take ALL dates per
   window on 8-K prose (first-date is announcement-date bias, 7/14).
10. RH dollar orders truncate at 6dp. Dry-run → place → verify-fill →
    ledger → sleeve, in that order, every time.
11. A feed's first live window is part of the build: feed #3 shipped
    working code AND the honest news that its v1 queries source the
    wrong population (healthy refis, not distress cliffs). Machinery
    that finds nothing tradable is only NOT-YET if you name the fix;
    the kill-spec clock keeps it honest (60 days).


## OPERATOR SITUATION NOTE — the shared pool grew (2026-07-14)

You already do this right (art. 26a: you read live broker BP, not sleeve
cash — today min(55.00, 237.12)=55.00). Two updates for tomorrow: (1) the
operator sold ~$930 of a personal holding (VXUS) at the 2026-07-14 close,
queued for the 7/15 open — after it fills, account buying power rises from
~$237 to ~$1,167. Re-run art. 26a fresh as always; the number just moved up.
(2) The other gods (Oracle/Hermes/Plutus) now share your discipline —
`shared.guards.spendable_buying_power(broker_bp)` is in their runbooks, so
the shared pool is no longer something only you guard. The pool is still
shared: your art. 26a "minus other gods' pending deployments" term matters
more now that there is real cash for two gods to want at once.
