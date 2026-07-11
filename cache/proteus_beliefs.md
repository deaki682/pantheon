# Proteus v2 — beliefs (rewritten 2026-07-11, session 4: the build session)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` and the five invariants: bounded loss, kill
switch first, integrity gate, honest grading, the Effort Law — never lazy.
Everything else here is belief, not law — overwrite it when evidence says to.

## State (as of session 4, Sat 2026-07-11 ~10:30 ET)

- **Sleeve: $2,500.00 cash, 0 positions.** Funding settles at the
  2026-07-13 (Mon) open. NO order before then. Journal has one note
  (session 4 build record); ledger empty — nothing to reconcile or grade.
  Curve marked 2026-07-11 (equity 2500, SPY 754.86); one mark per date —
  next mark Monday.
- **Broker reality (unchanged from session 3, not re-checked Sat — markets
  closed, sweeps can't settle on a weekend):** account 563854249 showed
  $2,681.63 cash / $813.15 SETTLED buying power Friday. Monday's gate is
  SETTLED BP ≥ order size. My spendable = min(sleeve cash, settled BP).
- Dev branch this session: `claude/exciting-mccarthy-8z8iuh` (harness
  renames per session — trust the session's designated branch, not this
  note). Options build commit: `a8c2938`, pushed. House code flows to main
  via operator-merged PRs; my last session's dealflow commit `4ac9a35` is
  on this same branch lineage.

## What session 4 did (the queued build debt — DONE)

**Options BUILD PRECONDITION cleared (playbook updated with evidence):**

1. `proteus/options.py` — OptionPosition/ClosedOptionTrade, OCC symbols,
   spread_pct / breakeven_move_pct / contract_mid / priced_read glue.
   Priced-move math NOT reimplemented — calls catalyst.expectations.
2. Sleeve: `option_positions` (keyed by OCC, deliberately OUT of
   `positions` so guards' equity-share map never sees a contract),
   enter_option/exit_option/expired_options, max_loss = net debit computed
   AT ENTRY (invariant 1 by construction), kill-switch liquidation covers
   options, concentration gate refactored to cover option debits and to
   demand live marks when ANY position (equity or option) is open.
3. Journal: `instrument="option"` entries validated mechanically against
   playbook gates — long-only, catalyst+14d expiry buffer, dollars ==
   contracts×premium×100 == max_loss, edge_arithmetic ≥ 80 chars showing
   the numbers. Option EXITS may record premium 0.0 (worthless expiry is
   a gradeable outcome, not a malformed price); equities keep strict >0.
4. Shakedown on REAL broker data: SPY Sep-18 755 straddle fetched;
   priced_read breakeven == broker's break_even_price (776.42, exact);
   `review_option_order` dry-run on 563854249 returned order_checks
   (broker itself flags OPTION_WIDE_BID_ASK_SPREAD — mirrors my gate 5),
   fees (~$0.04/contract/side, OCC+ORF — immaterial at my size but real),
   collateral, greeks. NO order placed.
5. Integrity gate: full suite 1808 passed (had to `pip install numpy
   requests pytest` into system python3 — the `pytest` binary here is a
   uv-isolated tool missing repo deps; run `python3 -m pytest`).

Hunting ground #2 (long-option convexity) is now EXECUTABLE end to end:
accounting, validation, pricing glue, order path — all proven. What it
does NOT have is a thesis. The remaining gap is sourcing (playbook
gap d): dated catalysts in neglected corners where my read of primary
docs diverges from the chain's price. That is research, not plumbing.

## The new-structure argument (unchanged, journaled session 2)

Odd-lot tender priority is a per-deal contractual spread, capacity-capped
to ~my size, NOT the refuted statistical tender drift. Kill-spec adopted
from backlog #13: kill if actionable supply <12/yr, OR RH can't deliver
un-prorated acceptance, OR median $/event <$150.

## Evidence so far (honest)

- Dealflow sweep (45 days): 9 hits, 0 actionable. Supply clock RUNNING
  (~7 weeks scanned, 0 actionable; kill-spec accrues with every empty
  sweep). Next sweep: Monday pre-open (originals file Mon morning).
- Robinhood odd-lot pass-through: UNKNOWN (playbook Q1–Q5) — answered
  only by one live 99-share test. OPERATOR DEPENDENCY stands: tender
  election has no API path; operator submits in-app. Notify EARLY.
- Options: Level 2 approved + full pipeline proven (this session). Zero
  option theses yet — the pipeline must not go hunting for a trade to
  justify itself. A built tool is not a mandate to use it.

## Where my edge might live (ranking unchanged)

1. Odd-lot tender priority (operational; needs live deal flow + the RH
   mechanics test).
2. Bounded-loss convexity via LONG options — pipeline COMPLETE; blocked
   only on a real thesis clearing all 7 playbook gates.
3. Neglected-corner primary-document reads (frontier window per
   house-view) — feeds #2 and is the sourcing gap (d).
4. Avoidance as position management (fast typed kills, cash as default).

NOT: manufactured "scalable engines"; refuted families without new
structure journaled; dumped-small-cap reversion without a contract;
stories without primary documents.

## Plan

- **2026-07-12 (Sun):** No forced work. Only genuinely useful candidate:
  start sourcing for hunting ground #3 (pick 1–2 neglected names with a
  DATED catalyst inside ~90 days and read the primary docs; that feeds
  gate 1–3 arithmetic if a thesis emerges). Skipping honestly is fine.
- **2026-07-13 (Mon), the real day:**
  1. Verify SETTLED buying power BEFORE anything.
  2. Fresh dealflow sweep (Monday-morning originals).
  3. Mark curve with Monday's tape.
  4. First trade ONLY if a thesis clears the full journal bar. Cash is
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
6. Check the BROKER's capabilities before planning around an instrument
   class — the charter can authorize what the account can't execute.
7. The graveyard generalizes: forced-selling reversion without a
   contractual counterparty is 0-for-3 in this house, worst in the
   smallest names. Edge hunts need a CONTRACT or a READ, not a bounce.
8. (New, session 4) Verify glue against the broker's own arithmetic when
   it publishes one (my breakeven vs its break_even_price) — a free
   correctness oracle for every pricing function I ever write.
9. (New, session 4) A built pipeline is not a mandate. The tool exists so
   the thesis can move fast when it arrives — not so a thesis gets
   manufactured to exercise the tool.
