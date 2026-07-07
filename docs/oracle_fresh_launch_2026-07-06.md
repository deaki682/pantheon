# Oracle — fresh launch from scratch (2026-07-06, operator directive)

After the 2026-07-06 launch-gate diligence rebuilt Oracle into a two-stage
machine (whole-universe forced-seller **sourcing** + primary-source
**verification gate**), the operator directed a clean reset: **forget all prior
dossier choices and start fresh under the new rules.** This is NOT a buy-launch —
Oracle stays `pending_funding`. The purpose is to **tee up VERIFIED choices for
when funding lands**, built correctly from the first name.

## What was reset

- **The convex dossier pool** — all 9 prior dossiers cleared: the 4 deep-read
  survivors (RNA, ARVN, VTSI, ALCO), BOLD, and the 4 launch-gate kills (XRN,
  SMHI, MNRO, GYRO). Archived to
  `cache/oracle_convex_dossiers_archive_pre_reset_2026_07_06.json`.
- **The A/B pending selections** — 4 unresolved, unfunded selections cleared
  (none were graded, so no real LLM-lift data is lost). Archived to
  `cache/oracle_ab_archive_pre_reset_2026_07_06.json`. The A/B structure is kept;
  new selections accrue from verified fresh-launch dossiers.

## What was deliberately preserved (resetting these would be wrong)

- **The operator-held legacy cohort** (CXT/HDSN/J/PSN/VITL) in
  `oracle_sleeve.json` / `oracle_cohort.json` — frozen personal holds, never the
  reframed engine's to trade. Untouched.
- **The graveyard + RESEARCH_LEDGER** — forgetting what is already refuted would
  be catastrophic (we'd re-test dead ideas). The learning from the 4 kills lives
  on structurally in the verification gate's four traps and the ledger, so
  clearing the dossiers loses no knowledge.
- **The lens caches** (insider/13F/13D/prescreener/screen) — raw sourcing
  inputs, not choices.
- **The new machine** — `oracle.forced_seller_sourcing` (coverage) and
  `verify_dossier`/`rank_fundable` (precision), plus the HUNT posture in
  `oracle.md`.

## The fresh-launch process (how choices get teed up now)

Per the standing posture, every candidate is built correctly from scratch:

1. **Source WIDE.** Run the forced-seller sweep across the whole EDGAR universe
   (widen the window/families beyond the narrow first pass — see
   `oracle_sourcing_status_2026-07-06.md`). Tonight's first sweep already
   surfaced **JOF** (Japan Smaller Capitalization Fund — a listed CEF at a real
   ~10.5% sub-NAV discount with a recurring discount-triggered tender) as the one
   genuine lead; it carries forward as the first fresh name to dossier because it
   is the NEW machine's output, not an old choice.
2. **Dossier + VERIFY.** Each promising lead → `make_convex_dossier` →
   `verify_dossier` (four traps, primary-source-cited) → only `verified` names
   enter the pool. `rank_fundable` returns the book order.
3. **Record the A/B** on every candidate (Arm A dossier vs Arm B screen).

Until a name clears `verify_dossier`, `rank_fundable` returns nothing — which is
correct. The fresh pool starts empty and fills only with verified choices, ready
for the operator to fund.
