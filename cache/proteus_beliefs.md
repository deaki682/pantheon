# Proteus v2 — beliefs (rewritten 2026-07-13, session 8: launch-day pre-open — the screen is built, the wake is in the air)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL by the
operator 2026-07-13** — plus the five invariants: bounded loss, kill switch
first, integrity gate, honest grading, the Effort Law. Everything else here
is belief — overwrite it the moment the evidence says to.

## State (as of session 8, Mon 2026-07-13 ~04:45 ET, pre-open)

- **Sleeve: $2,500.00 cash, 0 positions — settled and live.** Verified at
  the broker THIS session: buying_power $2,681.63 settled, pending_deposits
  0, zero agentic orders ever. Spendable = min($2,500, $2,681.63) = $2,500,
  art. 26a run with **no deployment signal found** in any other god's files
  (Hermes FROZEN since 7/7 with sell-side trims queued; Plutus
  monitoring-only until 2026Q3, sleeve cash 0; Oracle upside pending
  funding; Achilles retired treasury guard $2,000).
- **FLAGGED, on the journal:** the treasury is over-subscribed on paper —
  all-god sleeve-cash claims ~$5,610 vs account cash $2,681.63. My $2,500
  is covered TODAY; if another god deploys first I go BP-BLOCKED (art.
  26a/22l handle it at that order). Re-run the arithmetic at EVERY order.
- Journal: 13 records (9 prior + 4 this session). 1 ancillary mechanics
  prediction OUTSTANDING (the wake experiment, grades by market close
  today). 0 trade grades due. Ledger still empty.
- Curve: 7/13 pre-open row exists (session 6). Mark the LIVE row at the
  market-hours wake.
- Suite: **1914 green** (pre-change baseline 1902 + exactly my 12; session
  7's "1903" was a beliefs-prose miscount — journaled; counts are
  computations, never recollections).

## In the air RIGHT NOW (grade or act on these first)

1. **One-shot in-session cron `27b2c108` fires 14:07 UTC (10:07 ET) today**
   — the art. 4 verified-wake shakedown, leg 1. Journaled mechanics
   prediction: it fires by 14:30 UTC and pulls live option quotes. If it
   fired and you are the woken turn: journal the result, then run the
   market-hours leg (kink reads → tender rescan → live curve mark →
   spendable re-check). If you are a LATER session and no shakedown-result
   journal line exists: **the wake never fired — grade the prediction MISS
   as written**, journal that the in-session cron mechanism is refuted for
   ephemeral containers, and pursue operator-provisioned Routines for art.
   4 wakes instead. Until a wake is verified end-to-end, every entry sizes
   to the blind unattended worst case.
2. **IV-kink detector is BUILT and waiting for live IV** —
   `proteus/ivkink.py` (commit aeb6d58; register row `ivkink_detector`
   with kill-spec written first). Flow: `get_option_chains` → ATM
   instruments per expiry → `get_option_quotes` → `point_from_quotes`
   (gates: zero-bid, far-strike, missing-IV) → `kink_read`. Verdicts:
   PRICED (kink ratio ≥ 1.25) = drop; UNPRICED = document read earned;
   UNRELIABLE = refuse. MARKET-HOURS quotes only (art. 19). Nearest
   targets: OGN vote 7/23, IPCX 7/28, EQH+CRBD 7/30, AXTA 8/5.
3. **Tenders: 9 hits / 0 actionable since 5/27** (Mon pre-open rescan: 0
   new). Kill-spec (<12 actionable/yr) keeps ticking honestly.

## The law is machine-enforced (session 7's build — unchanged)

Every position-changing journal line goes through
`proteus.schema.append_record(record, EntryContext(...))`. At zero grades
the tightest caps bind: probe worst case ≤ 10% of equity ($250) AND
quarter-Kelly on worst case AND 25%/60% ceilings; honesty floors (equity
wc ≥ 50% notional → single-name notional ≤ $500; index ≥ 20%×leverage;
merger = deal-break; option = full debit). Parks (SPY/VOO/VTI/SGOV-class
only) are cap-exempt, worst-case-honest. Context comes from
`proteus.calibration` counters + the sleeve as it IS. Staged first use
(art. 16) for anything touching `proteus/order_path_manifest.json` — the
ivkink module is NOT on it (screen only).

**STALE-DOCTRINE WARNING (still open):** `proteus/sleeve.py` carries v1's
"no per-position cap / all-in" comment block. Repealed by art. 1. Schema
binds upstream so it's safe; fix the comment on the next sleeve.py touch
(that touch IS staged per the manifest — batch it with a real change).

## Where MY edge might live (unchanged; supply-starved but honest)

1. **Odd-lot tenders** — mechanics answered (playbook Q1–Q5), Gmail watch
   proven, election is an OPERATOR HANDOFF (no API path; art. 25 solo
   fallback required). Waiting on supply.
2. **Event convexity** — the funnel is now complete end-to-end: eventfeed
   (proven) → ivkink screen (built, unproven on live IV) → document read
   (proven, CRCT) → 7 gates → schema. What's missing is only a LIVE
   UNPRICED verdict.
3. **Neglected-corner reads** — CRCT disposition on record; keep
   accumulating honest AVOIDs (art. 8 — never inflate a base-rate decline).
4. **Avoidance is the one measured-real LLM skill.** The shadow book is
   where it becomes evidence.

## Plan (this wake, or next session if the wake fails)

- (a) Grade the wake experiment as written (fires/doesn't by close today).
- (b) Run ivkink live on OGN/IPCX/EQH/CRBD/AXTA. Journal every verdict
  (PRICED verdicts are dispositions too — killed_at_screen rows if
  individually worked). UNPRICED → document read → 7 gates → maybe the
  first entry. **First live order note:** the equity/option order paths
  have never placed a live order — art. 16 staged deployment applies to
  their first live use (minimum size, dry-run comparison, PROCESS-typed).
- (c) Rescan tenders during market hours (Monday filings land 06:00+ ET).
- (d) Mark the curve on live tape; re-run art. 26a before any order.
- (e) July flat-month duty (art. 13b): if July ends flat/majority-cash —
  it will unless an entry lands — write the posture note: cash park
  predicts beating SPY over the following month (graded), or park in an
  index fund deliberately (exempt). Decide consciously, not by drift.
- (f) First record brief due at 20 graded decisions or by 2026-10-11.

## Lessons (cumulative scar tissue)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down
   (Gmail, 7/11). Never deposit an extracted date without a plausibility
   gate — 29% of raw extractions were wrong (7/13).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. The first honest kill (CRCT) is worth more to the record than a
   coin-flip first trade would have been.
6. **Verify the record before trusting any summary of it — including
   mine.** Two beliefs miscounts in two sessions ("7 notes" s6, "1903
   tests" s7); both caught by computing. The journal itself has never been
   wrong — prose counts are where lies creep in. Compute, then write.
7. Session containers are ephemeral and shallow-cloned: `git fetch
   --deepen` before reasoning about state history; `pip install pytest
   numpy` before the suite (~1 min, then 1914 tests in ~4s).
8. In-session crons are session-only and unproven for my containers —
   treat every self-scheduled wake as an EXPERIMENT until one fires and
   works end-to-end (that's what leg 1 is testing today).
