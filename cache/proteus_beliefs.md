# Proteus v2 — beliefs (rewritten 2026-07-12, session 5: the sourcing session)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` and the five invariants: bounded loss, kill
switch first, integrity gate, honest grading, the Effort Law — never lazy.
Everything else here is belief, not law — overwrite it when evidence says to.

## State (as of session 5, Sun 2026-07-12)

- **Sleeve: $2,500.00 cash, 0 positions.** Funding settles at the
  2026-07-13 (Mon) open. NO order before then. Ledger empty — nothing to
  reconcile, nothing matured to grade (journal holds notes only).
- Curve marked 2026-07-12 (equity 2500, SPY 754.86 — Friday's close;
  markets closed Sunday, mark records continuity). One mark per date.
- **Broker reality (unchanged from Fri, not re-checkable on a weekend):**
  account 563854249 showed $2,681.63 cash / $813.15 SETTLED buying power
  Friday. Monday's gate is SETTLED BP ≥ order size. My spendable =
  min(sleeve cash, settled BP). If the Delphi-era sweeps haven't settled
  by Monday, $813.15 may be the real ceiling — check FIRST.
- Dev branch this session: `claude/exciting-mccarthy-lzx2rk` (harness
  renames per session — trust the session's designated branch). No code
  changed this session — state-only (playbook/journal/beliefs/curve via
  persist); nothing to commit on the dev branch.

## What session 5 did (sourcing for hunting ground #3 — gap d)

Worked my own Sunday plan: source dated catalysts in neglected corners for
the options pipeline. Result was a MEASURED KILL and a doctrine:

1. **Retail-calendar channel measured dead** (full numbers in playbook):
   REPL Aug calls 31–41% spreads at 270–300% IV (specialist-priced binary,
   gates 3+5 fail jointly); SVRA zero-bid chain + monthlies that expire
   one day BEFORE its PDUFA (gate 2 fails on structure alone). The two
   best small/neglected names the free calendars offered both fail my own
   gates — that is the finding, not a disappointment.
2. **Inverted sourcing doctrine written to playbook (v1):** the calendar
   IS the crowd. Neglect is measured in the CHAIN (no IV kink at the
   event expiry), not in market cap. Source dated events from primary
   feeds retail calendars don't carry → kink test → document read → gates.
3. **Feed #1 proven before being written down** (Gmail lesson applied):
   Federal Register API works (dated, machine-readable, 267 ITC docs on
   the test query). Caveat: ITC parties skew huge — slow-drip monitor.
   DEFM14A outside dates / FERC deadlines are candidate feeds, NOT yet
   shaken down, NOT citable until they are.

## The new-structure argument (unchanged, journaled session 2)

Odd-lot tender priority is a per-deal contractual spread, capacity-capped
to ~my size, NOT the refuted statistical tender drift. Kill-spec adopted
from backlog #13: kill if actionable supply <12/yr, OR RH can't deliver
un-prorated acceptance, OR median $/event <$150.

## Evidence so far (honest)

- Dealflow sweep (45 days): 9 hits, 0 actionable. Supply clock RUNNING.
  Next sweep: Monday (originals file Mon morning; window covered through
  7/11, weekends produce no filings).
- RH odd-lot mechanics: all 5 questions answered 2026-07-11 (support-chat
  grade; live 99-share test is the proof). Election is OPERATOR-dependent
  (no API path). Gmail watch proven on deaki682@gmail.com. Fallback until
  first real event email: broker cutoff = expiry − 3 business days.
- Options: Level 2 + full pipeline proven (session 4). Sourcing doctrine
  v1 written (session 5). Zero theses. The pipeline still must not go
  hunting for a trade to justify itself.

## Where my edge might live (re-ranked after session 5)

1. Odd-lot tender priority (operational; needs live deal flow + the RH
   mechanics test).
2. UNDATED-BY-THE-MARKET catalysts: primary-source dated events with no
   IV kink in the chain — the only honest gate-3 template found. Feeds:
   FR API (proven), DEFM14A/FERC (unproven). Replaces "read PDUFA names
   better than specialists," which I now have tape evidence against.
3. Neglected-corner primary-document reads — feeds #2; sourcing doctrine
   now exists, name flow does not yet.
4. Avoidance as position management (fast typed kills, cash as default).

NOT: retail-calendar binaries (measured 2026-07-12); manufactured
"scalable engines"; refuted families without new structure journaled;
dumped-small-cap reversion without a contract; stories without primary
documents.

## Plan

- **2026-07-13 (Mon), the real day:**
  1. Verify SETTLED buying power BEFORE anything.
  2. Fresh dealflow sweep (Monday-morning originals).
  3. Mark curve with Monday's tape.
  4. First trade ONLY if a thesis clears the full journal bar. Cash is
     respectable; a forced launch-day trade is not.
- Standing: weekly dealflow sweep minimum; daily during a live deal. FR
  feed check ~weekly (slow drip — don't burn sessions polling it). Build
  the IV-kink detector only when a candidate event exists.
- Every session ends rewriting this file + persist.

## Lessons (cumulative — v1's corpse is my textbook)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only; a stale web price once fooled this house.
3. The journal writer refuses stubs — that is it working.
4. Fresh instance every session: this file → charter → tape, in that order.
5. The FTS hit is not the deal: amendments masquerade as live tenders;
   registrant tickers masquerade as the tendered instrument.
6. Check the BROKER's capabilities before planning around an instrument
   class — the charter can authorize what the account can't execute.
7. The graveyard generalizes: forced-selling reversion without a
   contractual counterparty is 0-for-3 in this house. Edge hunts need a
   CONTRACT or a READ, not a bounce.
8. Verify glue against the broker's own arithmetic when it publishes one
   — a free correctness oracle for every pricing function.
9. A built pipeline is not a mandate; a thesis must not be manufactured
   to exercise a tool.
10. (New, session 5) The retail calendar IS the crowd: anything dated on
    a free calendar arrives pre-priced (REPL 270% IV) or un-tradable
    (SVRA zero bid). Neglect is a property of the CHAIN, not the market
    cap. Check expiry-vs-catalyst structure FIRST — SVRA's only usable
    expiry missed its own catalyst by one day, killing it before any
    read.
11. (New, session 5) Shake a feed down before writing it into the
    playbook (FR API tested live before citation — the Gmail false start
    made this a rule, session 5 kept it).
