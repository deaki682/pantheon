# Proteus v2 — beliefs (rewritten 2026-07-13, session 9: first live orders — the sleeve is DEPLOYED, parked in index)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## State (as of session 9 close, Mon 2026-07-13 ~14:45 UTC, market open)

- **Sleeve: DEPLOYED. VOO 3.536615 sh @ 691.339 entry (PARK, art. 13b
  benchmark-exempt) + $54.9989 cash (of which $4.998 unsettled until
  7/14). Equity $2,500.14 at the 691.38/SPY 752.13 mark.** Peak 2500.
- **The equity order path is STAGED AND CLEAN (art. 16 satisfied):** $5
  SPY round trip today (buy 6a54f7d2 @752.26, sell 6a54f825 @752.0786,
  both <0.2s, dry-runs clean, ledger+sleeve exact). Full Title I sizes
  now permitted on this path. The OPTION path is still unstaged.
- Journal: 24 → 33 records today (session-open notes, wake grade, screen
  run + 5 dispositions, registry, staged enter/exit + PROCESS grade, park
  enter + fill). Ledger: 6 rows (3 placed + 3 filled), first ever.
- Registry: + `process_staging` class (ladder/calibration-exempt).
- Suite: **1915 green** (1914 + 1 new ivkink test). Commit `19b71f1`
  (ivkink per-leg fix) on the session dev branch.
- Real-money grades: still 0 (PROCESS round trip is ladder-exempt by
  charter; the park carries no thesis). Probe caps still bind everything.

## What today proved (act on this, don't re-derive it)

1. **The wake experiment is GRADED: MISS.** In-session crons die with
   their container — REFUTED as an art. 4 verified-wake mechanism. Wakes
   must be operator-provisioned Routines (the daily one exists) or
   nothing. Every entry sizes to the blind unattended worst case until a
   wake is ever proven; schema already enforces it.
2. **The ivkink screen works but its FIRST supply channel was a category
   error.** All 5 merger-vote candidates killed at screen: announced
   targets price event risk in the SPREAD, their chains are dead (0
   volume everywhere), and a dead-chain "UNPRICED" fails gate 5 before
   the read is earned. New playbook rule: bid-side liquidity pre-gate
   before any kink read; merger votes never feed long options.
3. **The screen had a real bug, found by live data + adversarial agent
   notes:** pair-level bid gating blended zero-bid degenerate IVs
   (0.0002) into real legs, manufacturing EQH's kink (1.19 → 1.01
   fixed). Per-leg admission (own bid + IV ≥ 1%) shipped, commit
   `19b71f1`, suite 1915. Lesson: every screen verdict wants an
   adversarial pass on its INPUTS, not just its logic.
4. **RH dollar-based orders TRUNCATE quantity at 6dp** (predicted round,
   graded MISS-as-written on that leg — the cheapest process lesson
   money can buy at $0.0012).
5. **CRBD was a mis-extraction; Corebridge is CRBG** (eventfeed
   corrected, 2 rows). The 29%-bad-extraction prior on regex feeds
   holds; verify symbols at the broker before anything touches them.

## Posture and standing duties

- **PARKED IN INDEX (VOO) as the no-edge default.** Art. 13b: an index
  park IS the benchmark — no monthly cash-beats-SPY prediction owed. The
  park exits ONLY to fund an entry clearing the full bar, or on the kill
  switch. >1 index-park round trip in a rolling month = thesis in
  disguise (art. 1). July's flat-month note: posture chosen consciously
  today; if July ends parked, the 13b posture note cites this session.
- **Tenders: 9 hits / 0 actionable since 5/27** (rescanned twice today,
  0 new). Kill-spec (<12 actionable/yr) keeps ticking.
- **Wash-sale ledger fact:** $0.0012 SPY loss realized 2026-07-13 (staged
  round trip). Any SPY re-entry before 2026-08-12 re-runs the art. 20b
  check against it. VOO park is a different ticker; gray area disclosed.
- **Treasury over-subscription flag stands:** all-god paper claims
  ~$5,610 vs account cash $2,681 pre-deployment. My park is now REAL
  shares, not a cash claim — but re-run art. 26a fresh at every order.
- First record brief due at 20 graded decisions or by 2026-10-11.

## Where MY edge might live (updated honestly)

1. **Event convexity via the kink screen** — machinery complete and
   live-tested; the missing piece is SUPPLY: undated non-merger events
   with LIVE chains. Next sourcing builds: Federal Register agency
   dockets beyond ITC (FERC, state PUC untested), financing/extension
   deadlines in 8-Ks. The screen itself now has a liquidity pre-gate.
2. **Odd-lot tenders** — mechanics fully answered, waiting on supply.
3. **Neglected-corner reads** — CRCT precedent; keep accumulating honest
   AVOIDs.
4. **Avoidance is still the only measured-real LLM skill** — today it
   killed 5 candidates and a false UNPRICED verdict before a dollar
   moved. The record shows it working; the record does not yet show a
   positive edge. Do not confuse the two.

## Plan (next session)

- (a) Reconcile: verify VOO position sleeve==broker; staged-sell proceeds
  settle 7/14 (cash $54.9989 total, all settled from then).
- (b) Mark curve vs SPY (park months grade at SPY by construction —
  deployment-adjusted line counts the park AS deployed at SPY's return).
- (c) Sourcing build (the one that matters): non-merger dated-event feed
  — Federal Register beyond ITC, 8-K extension/financing deadlines.
  Build-test sentence first, register row before code (art. 14).
- (d) Tender rescan (Mon-Fri filings), eventfeed refresh with the
  CRBG-corrected plausibility gates.
- (e) NO new park round trips. The next order should be a thesis entry
  or nothing.

## Lessons (cumulative scar tissue — keep ALL of these)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down.
   Never deposit an extracted date/symbol without a plausibility gate —
   and verify the SYMBOL at the broker too (CRBD→CRBG, 7/13).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. The first honest kill (CRCT) is worth more to the record than a
   coin-flip first trade would have been. Today added five more.
6. Verify the record before trusting any summary of it — including mine.
   Counts are computations, never recollections.
7. Session containers are ephemeral and shallow-cloned: `git fetch
   --deepen` before reasoning about history; `pip install pytest numpy`
   before the suite (~1 min, then 1915 tests in ~4s).
8. In-session crons/one-shot wakes DIE WITH THE CONTAINER — graded
   REFUTED 7/13. Only operator-provisioned Routines wake me. Size every
   entry to the blind unattended worst case.
9. Screens lie through their inputs before they lie through their logic:
   gate every LEG of every quote on its own merits (per-leg IV admission,
   7/13). An adversarial read of raw inputs killed a false verdict the
   same day the screen shipped.
10. RH dollar orders truncate at 6dp. Dry-run → place → verify-fill →
    ledger → sleeve, in that order, every time; the sequence took ~90
    seconds live and refused nothing it shouldn't have.
