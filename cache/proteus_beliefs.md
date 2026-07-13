# Proteus v2 — beliefs (rewritten 2026-07-13, session 6: launch day)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` and the five invariants: bounded loss, kill
switch first, integrity gate, honest grading, the Effort Law. Everything
else here is belief — overwrite it the moment the evidence says to.

## State (as of session 6, Mon 2026-07-13 pre-open)

- **Sleeve: $2,500.00 cash, 0 positions — SETTLED and live.** Confirmed
  pre-open 7/13: account BP $2,681.63 = cash; my spendable =
  min(sleeve $2,500, account BP) = $2,500. First live order is permitted
  from today's open. I chose NOT to trade today: nothing cleared the bar.
  Cash is a deliberate position, not a failure. SPY ref: 754.95 (official
  7/10 settled close; overnight tape ~750.6, i.e. Monday looks red).
- Reconcile 7/13: zero agentic orders, empty ledger, clean.
- Journal: 7 notes, 0 predictions outstanding, 0 grades due.

## The machine so far (what exists and works)

1. **Tender/odd-lot scanner** (`proteus/dealflow.py`) — RUNNING. Supply
   so far: 9 hits / **0 actionable** since 5/27 (kill-spec: <12
   actionable/yr kills the ground). The listed-company odd-lot tender is
   RARE; most SC TO-I hits are non-traded BDC/interval funds. Patience,
   not force — but watch that kill-spec honestly.
2. **Event feed** (`proteus/eventfeed.py`, built session 6) — RUNNING.
   Two proven primary feeds: FR/ITC §337 (slow drip) and EDGAR DEFM14A
   vote/outside dates. 15 events stored, **13 upcoming** in
   `cache/proteus_eventfeed.json` (OGN 7/23 vote, IPCX 7/28, EQH+CRBD
   7/30, AXTA 8/5, MDV 8/10, RAMP 8/17, LPSN 8/20 votes; GBTG 11/2,
   AMRX 11/17, LPSN 12/5, EQH/CRBD 12/26 outside dates). CAVEAT: regexes
   mis-extract (6/21 raw were provably wrong — plausibility filter now
   drops those); the store AIMS the read, the document is the authority.
3. **Options plumbing** (`proteus/options.py`) — VERIFIED, unused. Level 2
   only: long calls/puts, CSPs, covered calls. No spreads (Level 3).
4. **Journal/sleeve/guards** — shakedown-proven at launch.

## What session 6 taught (grade the process, not just trades)

- **The avoidance pipeline works end-to-end.** FR feed → CRCT (Cricut GEO
  win, ITC vote 7/7) → tape flat (the 7/7 dip was just the $0.10 ex-div)
  → full FR read → thesis KILLED in the primary document: the GEO covers
  one design patent (EasyPress housing); the real competitor (HTVRONT)
  was adjudicated non-infringing on redesigns and keeps importing. The
  market's shrug was right. First live proof the read can say NO for the
  documented right reason. Ledger row it echoes: every avoidance rule the
  house measured was real; every buy trigger alone was noise.
- **Extraction is not reading.** The LPSN outside date is BOTH 10/21
  (initial) and 12/5 (auto-extended) — the modal regex found the tail
  date, the first-hit regex found the headline one; only the document
  explains. Never journal a feed date without the read.
- **Environment note:** the session container needs
  `pip install pytest numpy` before the suite runs (two-env split;
  requests lives in the main python). ~1 min, then 1829 tests in ~5s.

## Where MY edge might live (unchanged hypotheses, one demoted)

1. **Odd-lot tenders** — alive but supply-starved (0 actionable in 7
   weeks). The 99-share mechanics test awaits the first real deal.
2. **Bounded-loss convexity on primary-source dated events** — the event
   feed now supplies candidates; the missing piece is the **ATM-IV kink
   detector** (build next market-hours session; overnight IVs are stale).
   Then: no-kink + verified date → document read → 7 gates.
3. **Neglected-corner document reads** — CRCT was the first live rep. The
   corner was efficient this time; keep testing, keep killing honestly.
4. **Avoidance as position management** — proven in-process this session.

## Plan (next sessions)

- **Next market-hours session:** (a) build + test the IV-kink detector on
  the 13 stored events, starting with the nearest votes (OGN 7/23,
  IPCX 7/28, EQH/CRBD 7/30); (b) rescan tenders for Monday filings;
  (c) mark curve on live tape. If the operator's daily Routine stays
  pre-open, the kink read must use previous-close IVs consistently —
  fine for a term-STRUCTURE comparison, weak for levels; say so in any
  journal entry that uses it.
- **Standing cadence gap (flag to operator when material):** sessions
  fire pre-open from an ephemeral container; I cannot reliably self-wake
  intraday. Costless while flat. The day I hold a position with a dated
  kill condition, I need either a market-hours Routine or an operator-
  owned trigger — journal it at entry, don't discover it at the kill.
- **Discipline reminders for tomorrow's me:** run the kill-switch check
  first; reconcile before anything; the bar for trade #1 stays at full
  height — the record starts at the first entry, and LUCK is a grade.

## Lessons (cumulative scar tissue)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down
   (Gmail, 7/11). Corollary from 7/13: never deposit an extracted date
   without a plausibility gate — 29% of raw extractions were wrong.
4. A session that skips reading this file, the charter, and the ledger
   is a dumber god.
5. The first honest kill (CRCT) is worth more to the record than a
   coin-flip first trade would have been.
