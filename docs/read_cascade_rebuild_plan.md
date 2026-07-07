# Read-Cascade Rebuild — status & weekend plan (2026-07-07)

**Read this before touching Oracle or Proteus's read path.** It is the durable
record of the rebuild a chat session cannot remember. Built 2026-07-07; the paid
phase waits for the operator's week's-end credit reset.

## Why the rebuild exists — the "sliver problem"

Oracle and Proteus both had the same flaw: a no-edge numeric filter chose an
arbitrary ~50-name sliver out of thousands, and the expensive LLM read only ever
saw that sliver. The filter had no edge, so the read was aimed by noise. The fix:
**the filter IS a read.** A cheap recall-first triage tier reads the WHOLE field;
only survivors reach the expensive deep tier + the god's adversarial gate. No name
is dropped by a coin flip — every name is read, or logged as skipped-for-budget.

## What is built (all on `main`, tested, zero credits spent)

| File | Role |
|------|------|
| `shared/read_cascade.py` | The machine. `run_cascade(packets, lens, model_read, budget)`. Model is an INJECTED seam → the whole pipeline tests for zero tokens. `plan_tier`/`apply_tier` are the shared primitives. `estimate_cost` dry-run. `build_packet`. |
| `oracle/lens.py` | Oracle's two tiers: Sonnet triage → Opus deep, wired to `resolve_bears` (BEAR×3) + `blowup_check`. Symbol authoritative from the packet. Never Haiku (calibration proved it kills real inflections). |
| `proteus/lens.py` | Proteus's two tiers: Sonnet triage → Opus deep, wired to `assess_case` (narrative gap, primary-confirmed numbers, triangulation, ≥2-hop trail). |
| `shared/field_prep.py` | On-disk Sharadar → packets. `ORACLE_FIELD` (under-covered small/mid non-financial, ≤$20B) vs `WHOLE_MARKET` (Proteus). Exclusions are a parameter. Reconciles the SF1-dollars vs marketcap-millions unit gap in ONE place. |
| `run_field_prep.py` | gz I/O around field_prep. Writes `cache/{oracle,proteus}_field_packets.json`. FREE to run. |
| `shared/read_runner.py` | Production read path. `CascadeRunner` runs the cascade STEPWISE so the session fans a tier out to subagents (a Python `model_read` can't). Shares primitives with `run_cascade` → parity-tested, can't diverge. `write_batch`/`read_answers` (Workflow handoff), `dict_reader` (penny-run bridge). |
| `run_cascade_estimate.py` | Dry-run cost on the real field. FREE. |

Tests: 41 new (harness, lenses, field-prep, runner incl. run_cascade↔runner parity
and packet-conservation). Full suite 1749 passed. Merged via PR #31 (Phase 0 batch
predecessor) and **PR #32** (this foundation).

## Measured field & cost (on-disk data as_of 2026-07-02)

- Oracle field: **3,154 packets**; Proteus: **4,649 packets**.
- Calibration slice (150 names): **~0.69M tokens/god** — trivial.
- Full field (the CAP under a budget, not the bill): Oracle 14.7M, Proteus 21.6M.

## The weekend sequence (each step gates the next) — DO THIS AFTER THE CREDIT RESET

1. **Refresh the field (free).** Re-pull Sharadar fundamentals/marketcaps if stale
   (the neglect pull + daily mcap), then `python3 run_field_prep.py`. Re-price with
   `python3 run_cascade_estimate.py`.
2. **Penny smoke test (cents).** Build a `CascadeRunner` over ~5 hand-picked packets,
   do the reads yourself (or `dict_reader`), drive `next_batch()`/`submit()` to a
   `result()`. Prove the wiring end-to-end on real reads. NOT measuring edge yet.
3. **Calibration + GO/NO-GO (~0.7M tok/god).** Run the ~150-name slice through the
   real cascade (triage via Sonnet subagents, deep via Opus subagents). The gate
   question: **does the read (Arm A) beat the screen (Arm B)?** Wire the survivors
   through the existing A/B (`oracle.ab` / Proteus's journal). GO only if the read
   shows a real lift; NO-GO → do not spend on the full field, rethink the lens.
4. **Full field → book (14.7M/21.6M cap).** Only on GO. Run the whole field under a
   token budget; the deep tier binds. Size the survivors into the book via the
   existing sizing (`size_upside_book` / Proteus sizing).
5. **Un-pause.** Oracle and Proteus are PAUSED (`cache/{oracle,proteus}_paused.json`,
   `until:null` = hold-until-manually-lifted). Lift the pause only when the book is
   real. Then Proteus runs the same harness with `WHOLE_MARKET`.

## Current live/paused state (as of 2026-07-07)

- **PAUSED:** Oracle, Proteus (`shared.guards.is_paused` reads the paused files;
  Zeus skips them). They stay paused until step 5.
- **LIVE:** Plutus (net-issuance deluxe, ~$4,900 book, quarter-gated — monitoring
  only until 2026Q3 / 2026-09-30; residual over-funding already swept to treasury,
  cash $0, 47 positions). Hermes (merger-arb LLM A/B, ~$4,000, ALOT/Arcline position
  filled; read pinned to Opus). Zeus dispatches /hermes + /plutus on schedule.
- Model tiers: triage=Sonnet, deep=Opus. Haiku ruled out by calibration.

## Design invariant to preserve

The credit-expensive thing (measuring edge) is the ONLY thing that spends credits,
and it sits behind the calibration go/no-go. Everything else — routing, budget,
gating, coverage, dedup, the gates — is proven free. Never let a harness change
skip the stubbed-read tests; a harness bug must never cost a real run.
