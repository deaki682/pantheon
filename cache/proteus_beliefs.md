# Proteus v2 — beliefs (rewritten 2026-07-11, session 3: the reading session)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` and the five invariants: bounded loss, kill
switch first, integrity gate, honest grading, the Effort Law — never lazy.
Everything else here is belief, not law — overwrite it when evidence says to.

## State (as of session 3, Sat 2026-07-11 ~01:10 ET)

- **Sleeve: $2,500.00 cash, 0 positions.** Funding settles at the
  2026-07-13 (Mon) open. NO order before then. Journal empty, ledger
  empty — nothing to reconcile or grade yet. Curve marked 2026-07-11
  (equity 2500, SPY 754.86); one mark per date, not re-marked this session.
- Session cadence note: sessions 1–3 all ran within ~90 min of each other
  (Fri ~23:47 ET → Sat ~01:10 ET). Fine for launch week; if the daily
  Routine keeps firing this densely I should tune my own schedule
  (house physics: my cadence is mine) rather than burn tokens on no-ops.
- **Broker reality check (session 3):** account 563854249 shows $2,681.63
  cash but only **$813.15 settled buying power** — the retiring-god sweeps
  haven't settled. Monday's gate is SETTLED BP ≥ order size, not cash.
  My spendable = min(sleeve cash, account settled BP) — shared account.
- **BLOCKER FLAGGED: no options approval.** `option_level` on the agentic
  account is EMPTY. Hunting ground #2 (bounded-loss convexity) is not
  executable until the OPERATOR applies for options approval at RH.
  Notified 2026-07-11. Stock-only expressions unaffected.
- Code note: dealflow scanner commit `4ac9a35` is pushed on the session
  dev branch (`claude/exciting-mccarthy-jdij0u`; the branch name in
  session 2's note is stale — harness renames per session). House code
  flows to main via operator-merged PRs.

## What session 3 did (no positions to tend, so: pay down debt)

1. **Effort Law debt CLEARED:** read `docs/RESEARCH_BACKLOG.md`,
   `docs/RESEARCH_LEDGER.md`, and `docs/house_view_llm_edge_2026-07-05.md`
   END TO END (previously only grepped). Nothing contradicts my ranking.
   Key extractions for my book:
   - The tender-family refutations (TO-I −1.81% t−3.91; TO-C replication
     t−5.34; 14D-9 precise null; operating self-tenders −1.82%) are ALL
     statistical all-holders entries at filing/announcement anchors. My
     odd-lot structure (contractual priority acceptance, Rule 13e-4(f)(3)/
     14d-8) is a different mechanism — backlog #13 holds it as an open
     LAB_HYPOTHESIS with the kill-spec I run under. No new-evidence
     journaling needed; the refutations don't reach it.
   - The graveyard's strongest repeated pattern: **dumped-small-cap
     reversion keeps failing with the small/illiquid subset WORST**
     (spinoff_orphans −9.3%, ipo_lockup −10.4%, PEAD 18/18 negative).
     Prior for me: never buy "it fell on forced selling, it'll bounce"
     without a CONTRACT on the other side.
   - Every mechanical BUY trigger the house tested ≈ 0-to-negative;
     every AVOIDANCE rule measured real. Confirms hunting ground #4.
   - House-view: camp on structural constraint + capacity + patience;
     my capacity-capped odd-lot hunt and primary-doc reads sit exactly
     in the durable-barrier corner. Frontier windows (full-docket
     synthesis, agentic cross-referencing) = my hunting ground #3.
2. **Playbook started** (`cache/proteus_playbook.md`): options-convexity
   entry checklist (7 gates, dormant until approval), odd-lot broker-
   mechanics questions (the 5 unknowns kill-condition #2 turns on),
   settled-cash discipline.
3. **Dealflow re-scan SKIPPED — written WHY (Effort Law shortcut rule):**
   session 2's sweep ran ~00:20 ET Sat, after EDGAR's Friday acceptance
   window closed (22:00 ET Fri); it is now ~01:10 ET Sat. Zero new
   filings can exist. Re-running would be frequency theater, not effort.
   Next sweep: Monday pre-open (originals filed Mon morning).

## The new-structure argument (unchanged, journaled session 2)

Odd-lot tender priority is a per-deal contractual spread, capacity-capped
to ~my size, NOT the refuted statistical tender drift. Kill-spec adopted
from backlog #13: kill if actionable supply <12/yr, OR RH can't deliver
un-prorated acceptance, OR median $/event <$150.

## Evidence so far (honest)

- First sweep (45 days): 9 hits, 0 actionable (amendments, non-traded
  instruments, expired). Supply clock is RUNNING — the <12/yr kill
  condition accrues evidence with every empty sweep. ~7 weeks of window
  scanned, 0 actionable; if this rate holds to ~12–16 weeks of forward
  originals-at-filing coverage, supply-kill starts looking live.
- Robinhood odd-lot pass-through: UNKNOWN (playbook Q1–Q5) — one live
  99-share test on the first real deal answers it.
- Options approval: MISSING at broker (operator action required).

## Where my edge might live (ranking updated for the blocker)

1. Odd-lot tender priority (operational; needs live deal flow + the RH
   mechanics test).
2. Neglected-corner primary-document reads (frontier window per
   house-view; was #3 — promoted while options are blocked).
3. Bounded-loss convexity (options) — BLOCKED at broker until operator
   applies; checklist ready in the playbook.
4. Avoidance as position management (fast typed kills, cash as default).

NOT: manufactured "scalable engines"; refuted families without new
structure journaled; dumped-small-cap reversion without a contract;
stories without primary documents.

## Plan

- **2026-07-12 (Sun):** Only if genuinely useful work exists — candidate:
  scope hunting ground #2's stock-only substitute (deep primary-doc read
  on 1–2 neglected names from a fresh angle) OR skip the session honestly.
  No EDGAR filings on weekends; no forced work.
- **2026-07-13 (Mon), the real day:**
  1. Verify SETTLED buying power BEFORE anything ($813 Friday; sweeps
     must settle).
  2. Fresh dealflow sweep (Monday-morning originals).
  3. First trade ONLY if a thesis clears the full journal bar. Cash is
     respectable; a forced launch-day trade is not.
- Standing: every session ends rewriting this file + persist. Weekly
  dealflow sweep minimum; daily during a live deal.

## Lessons (cumulative — v1's corpse is my textbook)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only; a stale web price once fooled this house.
3. The journal writer refuses stubs — that is it working.
4. Fresh instance every session: this file → charter → tape, in that order.
5. The FTS hit is not the deal: amendments masquerade as live tenders;
   registrant tickers masquerade as the tendered instrument. Read WHICH
   instrument and WHICH filing stage before any excitement.
6. (New, session 3) Check the BROKER's capabilities before planning
   around an instrument class — the charter can authorize what the
   account can't execute. Constitution ≠ plumbing.
7. (New, session 3) The graveyard generalizes: forced-selling reversion
   without a contractual counterparty is 0-for-3 in this house, worst in
   the smallest names. My edge hunts must have a CONTRACT or a READ, not
   a bounce.
