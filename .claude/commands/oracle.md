# /oracle — deep-research convex engine (REFRAMED 2026-07-05)

**REFRAMED — read docs/oracle_reframe_2026-07-05.md first.** Oracle is no
longer an insider-signal factor god. Its mechanical spine was refuted (insider
clusters −6.4%/yr, quality lens the drag), so it is recast as what it actually
is: a **measured LLM deep-research convex engine.** The lenses are now just an
idea-sourcing net; the **dossier is the edge**, written for ASYMMETRY (bounded
floor + catalyst upside + structural mispricing) and GRADED against the screen
it came from. The book is **concentrated and conviction-weighted**, not an
equal 8-name cohort. Fail-safe: if any step breaks, skip and open a PR — never
silently patch.

## ⚠️ Legacy cohort — HELD, not managed (operator directive 2026-07-05)

The prior cohort `cohort-2026-06-29` (**CXT, HDSN, J, PSN, VITL**) is FROZEN and
HELD by the operator — do NOT sell, thesis-break-check, top up, or rebalance
them. The live state is left UNTOUCHED: `cache/oracle_sleeve.json` +
`cache/oracle_cohort.json` remain as the legacy snapshot (the green positions
stay exactly where they are). The reframed engine gets a **fresh sleeve when the
operator funds it** — until then it is `pending_funding` and runs research +
dossiers + paper A/B only, placing NO orders and never touching the legacy
names. At funding, the operator decides whether the legacy positions move to a
personal hold (removed from Oracle's ledger → invisible via
`filter_broker_to_gods`) or stay parked; the reframed book starts clean either
way. Every session: skip the legacy symbols — they are not the reframed engine's
to trade.

## Session liturgy

0. **Hydrate.** `pantheon.hydrate()`.

0b. **Safety gates.** `kill_switch_active()` → liquidate (fresh-sleeve positions
   only, never the legacy hold) + stop. `is_live("oracle")` → if `ORACLE_LIVE`
   != `"true"`, PAPER MODE (compute + journal, place nothing, mutate nothing).
   **Funding gate:** load the fresh sleeve; if `pending_funding` is set, the
   reframed engine isn't funded — research + dossiers + paper A/B only, no
   orders. **Pre-trade:** `filter_broker_to_gods` (legacy names are personal =
   invisible) + `pre_trade_check` + `already_placed_today` before any order.

1. **Idea-source (the lenses, demoted).** Run the lenses ONLY to surface
   candidates worth researching — insider clusters, 13F, 13D, quality
   prescreen, plus neglect signals (thin coverage, small size, forced-seller
   calendars). No mechanical scoring drives selection; this is a cheap net.
   Record each candidate's `lens_score` (the old mechanical number) purely as
   the Arm-B baseline input for the A/B — never as the decision.

2. **Deep dossiers (the new spec — the edge).** For candidates worth the work,
   write/refresh a dossier that ANSWERS, in writing (docs/oracle_reframe §"How
   dossiers are written now"):
   - **floor_pct** — what bounds the downside (asset/cash/liquidation floor);
     no identifiable floor → it's a growth gamble, not an Oracle name.
   - **upside_x** + the SPECIFIC path to the re-rating (magnitude, not "cheap").
   - **why_mispriced (structural, G2)** — neglect / forced seller / hard
     catalyst. "The market underappreciates quality" is refuted; cut it.
   - **catalyst + catalyst_date (contractual > forecast, G4)** — anchor to a
     hard event where possible.
   - **falsifiable prediction + typed kill_condition** (price_level / drawdown_pct
     / thesis_date / filing_event).
   - **adversarial paragraph** — "what does the disciplined house know that says
     this is a mistake?" If it reduces to a refuted trigger (insider/quality/
     cheap) or a base-rate violation with no reason, cut BEFORE the book.
   Build each via `oracle.convex_dossier.make_convex_dossier(...)` — the writer
   REFUSES a dossier without a floor, a structural `why_mispriced_type`
   (neglect/forced_seller/hard_catalyst), or a typed kill, and flags
   `dead_trigger_risk` if the thesis leans on a refuted signal. Also pass
   **`floor_hardness`** (`hard` = asset/net-cash · `medium` = book · `soft` =
   contingent/thin — a floor that might not hold is not a hard floor) and
   **`horizon_months`** (months to the re-rating). It derives
   `asymmetry_score = P(up)·(upside_x−1) − (1−P(up))·floor_pct` (raw expectancy)
   and the SELECTION metric `convexity_score` = annualized asymmetry ×
   floor-hardness weight — so a bounded near-certain win (the Tang/Concentra
   sub-net-cash shape) is not buried under a low-odds far-off multiple, and a
   hard floor outranks a hopeful one. `convex` now means "positive expectancy +
   a real (bounded) floor", NOT "big multiple". Use the deep-read machinery
   (extraction + adversarial refuter subagents) on any name near the cut.
   Persist to `cache/oracle_dossiers.json`.

3. **Select a CONVEX book (concentrated, conviction-weighted).**
   `oracle.convex_dossier.rank_by_convexity(dossiers)` orders by convexity_score
   (annualized asymmetry × floor-hardness) and drops non-convex names (negative
   expectancy / no real floor) automatically. Take the few best; size within a
   per-name cap (concentration is the return lever — no equal 8-name cohort).
   Horizons are multi-month/patient, but a name must EARN its slot on
   risk-adjusted convexity, not on a signal or a raw multiple.

4. **Record the A/B (measure the edge).** For EVERY candidate in the pool this
   round, `oracle.ab.record_selection(ab, round_id, date, candidates=[...])`
   with `lens_score`, `llm_selected` (did the dossier pick it), `conviction`,
   `floor_pct`, `upside_x`, `entry_price`, `spy_entry`, `catalyst`. The
   mechanical Arm-B baseline (top-N by lens_score) is computed automatically.
   This IS the experiment: the dossier book (Arm A) vs the screen (Arm B).

5. **Execute (fresh sleeve, live).** `pre_trade_check`, size within the per-name
   cap, place fractional-share orders, append `cache/oracle_ledger.jsonl`,
   update the sleeve with ACTUAL fills. Journal every decision (buy/hold/pass)
   with its thesis + typed kill.

6. **Tend + grade.** Each session: check every held name's typed kill_condition
   against current facts (a quote/filing) — fire it if triggered (the kill is a
   promise). At a name's horizon or exit, `oracle.ab.record_grade(...)` and,
   periodically, `oracle.ab.llm_lift(ab)` — **the headline: do the dossiers beat
   the screen?**

7. **Persist.** Sleeve + dossiers + ledger + curve + `cache/oracle_ab.json` +
   cadence → `pantheon.persist("oracle", ...)`.

## Kill conditions (the only exits — typed, promise-not-suggestion)

A held name exits ONLY on its journaled, typed kill firing, or a hard structural
break: **fraud** (SEC/fraud filing), **going_concern** (bankruptcy/going-concern
disclosure), **thesis_date** passed without the catalyst, **drawdown** ≥ its
`floor_pct` (arithmetic — executes immediately, no debate), **price_level** hit,
or a **filing_event** the kill named. A judgment-based break (fraud/
going_concern) gets ONE adversarial refuter before selling (is the "fraud" an
unconfirmed short report? is the going-concern language in the filing or a news
paraphrase?) — sell only if the break survives; journal either way. **Prohibited
exits:** "a new dossier scored higher", rank drift, "flat after 60 days",
sector-out-of-favor. Patience is the edge.

## The checkpoint

At ~20 graded names (or a date): **Oracle LLM-lift = Arm A (dossier) − Arm B
(screen).** Positive and material → the deep research is real alpha; Oracle
earns concentration + capital. Zero/negative → the dossiers are rationalization
and Oracle folds into Proteus. The numbers decide, not the narrative — the same
question Hermes asks on the event side, Oracle asks on the value/neglect side.

## Halt

- Circuit breaker (`sleeve.check_circuit_breakers` = "halt") → set halted, stop
  opening. Code error → log `cache/oracle_errors.jsonl`, OPEN A PR, do not
  auto-patch.
