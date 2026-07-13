# Proteus v2 — beliefs (rewritten 2026-07-13, session 7: the law becomes code)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL by the
operator 2026-07-13** — plus the five invariants: bounded loss, kill switch
first, integrity gate, honest grading, the Effort Law. Everything else here
is belief — overwrite it the moment the evidence says to.

## State (as of session 7, Mon 2026-07-13 ~04:00 ET, second pre-open wake)

- **Sleeve: $2,500.00 cash, 0 positions — settled and live.** Spendable =
  min(sleeve $2,500, account BP $2,681.63) = $2,500 (verified session 6
  pre-open). Zero orders ever placed; ledger empty; reconcile trivially
  clean. Curve marked for 7/13 by session 6 (SPY ref 754.95, official 7/10
  settled close; overnight ~750.6).
- Journal: 9 records — 7 notes, 1 disposition (CRCT avoid), 1 record-audit
  note. 0 predictions outstanding, 0 grades due. (Session 6's "7 notes"
  line was a MISCOUNT — the audit note in the journal has the git proof;
  the real count was 4, nothing was ever lost.)
- **The clobber incident is closed:** operator-side stale-copy overwrite of
  this file was caught and restored same hour (state commit 01157e3). I
  deepened the shallow clone and verified the journal untouched. The vault
  held. Lesson reinforced: verify record integrity BEFORE building.

## The law is now machine-enforced (session 7's build)

Charter v2.1's effectivity clause required the machine artifacts BEFORE my
first post-ratification entry. **They shipped this session — the entry path
is UNBLOCKED:**

1. **`proteus/schema.py`** — the art. 15 ENTRY SCHEMA. One gate:
   `schema.append_record(record, EntryContext(...))`. It re-derives and
   refuses mechanically: Title I caps (25%/60%, halved below −25% peak),
   probe size (10% until class has 3 real grades), quarter-Kelly on worst
   case, the honesty floors (equity ≥50% notional; index ≥20%×leverage;
   merger = deal-break; option = debit), park whitelist (SPY/VOO/VTI-class
   + SGOV-class ONLY, no thesis by design), staged orders (art. 16),
   grade cells (derived from the two axes, never chosen), dispositions
   (art. 8), exit tax character (art. 20b), spendable arithmetic
   (art. 26a), handoff solo-fallbacks (art. 25). It calls the ghost
   journal's `validate_decision` FIRST — the operator-owned floor tests
   pin that layer; the schema only ever adds refusals.
2. **`proteus/registry.py`** + `cache/proteus_registry.json` — controlled
   taxonomies. 3 classes: `odd_lot_tender` (capacity-capped),
   `event_convexity`, `neglected_read`. 5 failure modes, 4 judgment types.
   New tags need a why-no-existing line; reclassification is append-only
   mapping, and the calibration counter follows the chain.
3. **`proteus/calibration.py`** — art. 10 in code. Ladder counters (real
   money, non-shadow, wc ≥1% equity only), the Kelly multiplier movement
   rule DEFINED ONCE (0.25 until 20 real grades; then 0.5 only if
   aggregate |stated_p − realized| ≤ 0.10; never higher), drawdown tiers.
4. **`proteus/benchmark.py`** — art. 23 defined once, never re-fit:
   headline sleeve-vs-SPY + deployment-adjusted excess (risk and index
   parks benched at SPY; cash/T-bill parks at the T-bill rate, default
   assumption 4% — reviews pass the live rate).
5. **`proteus/builds.py`** + `cache/proteus_build_register.json` — art. 14.
   7 machines registered (3 retro: tender scanner, eventfeed, options
   plumbing — each now carries its kill-spec in the register).
6. **`proteus/order_path_manifest.json`** — art. 16's material-rewrite
   surface, 25 entries. Any diff touching a listed function ⇒ first live
   use is STAGED (minimum size, dry-run-verified, PROCESS-typed).

Suite: **1903 green** (was 1847; +56 mine), floor file untouched, exit 0.

**STALE-DOCTRINE WARNING for tomorrow's me:** `proteus/sleeve.py` still
carries v1's "no per-position cap / all-in allowed" comment block
(CONCENTRATION_ACK_PCT). That right is REPEALED (art. 1 — my own
proposal). The schema binds upstream, so the code is safe, but the comment
lies; update it on the next sleeve.py touch (it's on the order-path
manifest, so that touch triggers staged deployment — batch it with a real
change).

## How to place my first real entry (the checklist is now executable)

Build `EntryContext` from the live book + registry + journal:
`class_real_grades`/`total_real_grades` from `calibration`, open worst
cases from the sleeve, `first_in_family=True` until a class has its
ledger-check row, `kelly_multiplier=cal.allowed_kelly_multiplier(journal)`.
Every duty the schema wants is a field; the refusal message lists what's
missing. At current zero grades: any single entry's worst case ≤ 10% of
equity (probe) AND ≤ 0.25×Kelly×equity — for a 60/40 coin at 2:1 payoff
that's ≤ $250 worst case on the $2,500 sleeve. That is the LAW working,
not timidity: concentration is earned by grades.

## Where MY edge might live (unchanged; supply-starved but honest)

1. **Odd-lot tenders** — 9 hits / 0 actionable since 5/27 (kill-spec: <12
   actionable/yr). EDGAR weekend rescan session 6 found nothing new.
   Patience — but the kill-spec is a promise, and the register now holds it.
2. **Event convexity** — 13 upcoming dated events in the feed (OGN 7/23
   vote, IPCX 7/28, EQH+CRBD 7/30, AXTA 8/5, MDV 8/10, RAMP 8/17, LPSN
   8/20; outside dates into 12/26). Missing piece: the **ATM-IV kink
   detector** — needs market-hours quotes (overnight IVs are stale).
3. **Neglected-corner reads** — CRCT was the first live rep (read → killed
   for the documented right reason; disposition row now in the journal).
4. **Avoidance as the measured-real skill** — accumulate it in the shadow
   book (art. 8), never inflate a base-rate decline into a fake divergence.

## Plan (next market-hours session)

- (a) Build + test the **IV-kink detector** on the nearest stored events
  (OGN, IPCX, EQH/CRBD). Register it in the build register FIRST (art. 14
  — sentence, observable, kill-spec: it must aim at a priced_move_read
  entry, and if no kink read ever survives the document read to an entry
  or gradable shadow in two review periods, prune it).
- (b) Rescan tenders (Monday filings land during market hours).
- (c) Mark curve on live tape; verify spendable against settled BP before
  any first order.
- (d) If an entry clears the gates, it must ALSO clear art. 4: a typed
  kill condition firing between sessions needs a **verified wake** or the
  unattended worst case prices it. My cadence is pre-open ephemeral
  containers — I have NO verified intraday wake today. Until I build one
  (`create_trigger` shakedown, art. 4's 30-day re-verify), every entry is
  sized to the blind unattended worst case. Journal that at entry.
- Charter duties running in the background: first record brief at 20
  graded decisions or 90 days from ratification (2026-10-11 at the
  latest), art. 13b flat-month posture note due if July ends flat
  (it will — write the cash-park-vs-SPY prediction or park in an index
  fund deliberately).

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
   mine.** Session 6 said "7 notes"; git said 4. The count is a computation
   (art. 10's spirit), never a recollection.
7. Session containers are ephemeral and shallow-cloned: `git fetch
   --deepen` before reasoning about state history; `pip install pytest
   numpy` before the suite (~1 min, then 1903 tests in ~6s).
