# Proteus v2 — beliefs (rewritten 2026-07-11, session 2: the scanner build)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` and the five invariants: bounded loss, kill
switch first, integrity gate, honest grading, the Effort Law — never lazy.
Everything else here is belief, not law — overwrite it when evidence says to.

## State (as of session 2, Sat 2026-07-11 ~00:30 ET)

- **Sleeve: $2,500.00 cash, 0 positions.** Funding settles at the
  2026-07-13 (Mon) open. NO order before then. Journal empty (no
  position-changing decisions yet). Curve marked 2026-07-11 (equity 2500,
  SPY 754.86). v1 archived at `cache/proteus_v1_*`.
- Session 1 (launch + shakedown ALL PASS) ran ~23:47 ET Fri; this session
  ran ~00:20 ET Sat — the build day planned for Sunday was pulled forward.
- **Code note:** the harness pins my commits to a session dev branch
  (`claude/laughing-newton-wdrg2r`, pushed; commit `proteus: odd-lot
  tender deal-flow scanner`, suite 1783 green). House code flows to main
  via operator-merged PRs — the charter's "commits to main" is satisfied
  through that mechanism, not by me pushing main directly.

## What I built (session 2)

**`proteus/dealflow.py` + `tests/test_proteus_dealflow.py` (33 tests).**
The odd-lot tender scanner — hunting ground #1 made operational:
- EDGAR FTS sweep (SC TO-I / TO-T / 14D9 × odd-lot phrases) → dedupe →
  `fetch_offer_text` walks index.json to the substantive Offer-to-Purchase
  exhibit (primary docs are often 2-page cover shells — learned live) →
  `enrich` extracts odd-lot priority clause, fixed/Dutch price, expiration,
  condition flags → `economics` computes conservative 99-share spread with
  worst-case-at-entry = full cost basis.
- **The scanner AIMS the read.** Extraction is heuristic; the filing is the
  only authority before a journal entry or order. Both live reads this
  session proved why (below).
- State: `cache/proteus_dealflow.json` (candidates + read_verdicts +
  supply_log).

## The new-structure argument (journaled here, per house physics)

The ledger closed the tender FAMILY at *statistical, all-holders,
filing-anchor* entries (TO-I anchor −1.81% t −3.91; operating self-tenders
−1.82%; 14D-9 residual precise null; TO-C replication t −5.34). My hunt is
a DIFFERENT structure: **contractual odd-lot priority** (Rule 13e-4(f)(3) /
14d-8) — <100-share holders who tender all shares are accepted ahead of
proration. Not average drift; a per-deal spread whose acceptance is
contractual, capacity-capped to almost exactly my size. Backlog #13 frames
it with a kill-spec I adopt: **kill if actionable supply <12/yr, or the
broker can't deliver un-prorated acceptance, or median $/event <$150.**
(Backlog's "~1%/yr of book" ceiling was for the house book; on $2,500,
$150/event ≈ 6% — the capacity cap IS my edge.)

## Evidence so far (honest)

- First sweep (45 days): **9 hits, 0 actionable.** EXFY = amendment/final
  results (deal done); PRIF = tender for NON-traded common at NAV (listed
  tickers were the registrant's preferreds — read the instrument, not the
  name); rest non-traded funds/expired/OTC-risky. Supply logged in
  `proteus_dealflow.json`.
- Lesson: FTS surfaces amendments; the forward log must catch ORIGINALS at
  filing. A ~weekly sweep is enough (tenders run 20+ business days) but
  entry timing near expiry matters (buy late = less deal-break exposure,
  same guaranteed acceptance — subject to the guaranteed-delivery/odd-lot
  cutoff read from the filing).
- Unknown to verify before first trade: **does Robinhood pass through
  odd-lot tender instructions un-prorated?** This is kill-condition #2 and
  it can only be answered by ONE small live test on a real deal.

## Where my edge might live (unchanged ranking)

1. Odd-lot tender priority (now operational — needs live deal flow).
2. Bounded-loss convexity (options) on catalysts I've read primary docs for.
3. Neglected-corner primary-document reads (short-dated structural residue).
4. Avoidance as position management (fast typed kills, cash as default).

NOT: manufactured "scalable engines", refuted families without new
structure journaled, stories without primary documents.

## Plan

- **2026-07-12 (Sun):** (a) Read `docs/RESEARCH_BACKLOG.md` end-to-end
  (only grepped it so far — Effort Law debt). (b) Re-run the dealflow scan
  (new filings post Fri close unlikely but cheap to check Sat/Sun). (c)
  Draft the entry checklist for hunting ground #2 (options convexity):
  what a journal-clearing options thesis must contain — IV vs my read,
  defined max loss, dated catalyst, typed kill. (d) Verify broker option
  approval level + odd-lot tender mechanics questions written down.
- **2026-07-13 (Mon):** Verify $2,500 settled buying power BEFORE anything.
  Fresh dealflow scan (originals filed Mon morning). First trade ONLY if a
  thesis clears the full journal bar. Cash is respectable; a forced
  launch-day trade is not.
- Standing: every session ends rewriting this file + persist. Weekly
  dealflow sweep minimum; daily during a live deal.

## Lessons (cumulative — v1's corpse is my textbook)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only; a stale web price once fooled this house.
3. The journal writer refuses stubs — that is it working.
4. Fresh instance every session: this file → charter → tape, in that order.
5. (New, session 2) The FTS hit is not the deal: amendments masquerade as
   live tenders; registrant tickers masquerade as the tendered instrument.
   Read WHICH instrument and WHICH filing stage before any excitement.
