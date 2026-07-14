# /oracle — the upside engine (RECUT 2026-07-06)

**RECUT — read `docs/oracle_upside_spec.md` first (the bible).** Oracle has ONE
job: **pick the few under-covered names with the biggest real upside over a 6–24
month hold, get big on them, and hold to the thesis.** Scored one way only —
forward return vs SPY over the hold. This supersedes the convex/floor reframe:
floors are now an OPTIONAL conviction bonus, never the price of entry. The edge is
the **breadth read** — reading the filings/transcripts of hundreds of names no
analyst desk covers, in the corner where reading is still an edge. Fail-safe: if
any step breaks, skip and open a PR — never silently patch.

## ⚠️ Legacy cohort — HELD, not managed (operator directive 2026-07-05)

The prior cohort `cohort-2026-06-29` (**CXT, HDSN, J, PSN, VITL**) is FROZEN and
HELD by the operator — do NOT sell, thesis-break-check, top up, or rebalance them.
`cache/oracle_sleeve.json` + `cache/oracle_cohort.json` stay UNTOUCHED as the
legacy snapshot. The upside engine gets a fresh sleeve when the operator funds it;
until then it is `pending_funding` — research + dossiers + paper A/B only, NO
orders, and it never touches the legacy names. Every session: skip the legacy
symbols; they are not the engine's to trade.

## The objective (never drift from this)

```
maximize E[ fwd_return(pick, t) − fwd_return(SPY, t) ]  for t ∈ {6,12,24} months
pick ∈ hunting_ground ; selection = the LLM breadth-read, not a screen
returns are right-tail-dominated → SIZING and HOLDING matter more than hit-rate
```

The whole engine is the 7-stage funnel in `docs/oracle_upside_spec.md`. The EDGE
is isolated to the reading stages (2, 3, 5); everything else is deterministic code
you run and audit. Do NOT reintroduce a floor mandate, an avoidance score, or a
convexity/floor-hardness metric — those are retired (see Failure Modes below).

## Session liturgy

0. **Hydrate.** `pantheon.hydrate()`. Read `cache/oracle_beliefs.md` (the forward
   worldview + open theses + what decayed) BEFORE anything else.

0a. **PAUSE gate (check FIRST, before any compute).** `shared.guards.is_paused("oracle")`
   → a pause freezes the expensive **SOURCING** engine; it NEVER abandons live money.
   Branch on whether the fresh sleeve holds live positions or unreconciled orders:
   - **TEND-ONLY (fresh sleeve has live positions or queued/unfilled orders):**
     reconcile broker fills into the sleeve, mark equity, and check EVERY held
     name's typed `kill_condition` against current facts — **fire any triggered
     kill and grade at horizon** (a kill is a promise; a drawdown/thesis-break must
     execute even under a pause). Persist. Do NOT source, read, score, or SELECT
     new names, and place no new buys — tending is free (no cascade), so the hold's
     "spend no credits" intent holds. Then end.
   - **FULL STOP (fresh sleeve flat):** touch nothing, spend nothing, print the
     guard's `reason` and end.
   Either branch leaves the frozen legacy cohort (CXT/HDSN/J/PSN/VITL) exactly
   as-is. (Current hold, 2026-07-07: SOURCING frozen until the Stage-1 Sonnet-read
   cascade + weekend credit reset — Oracle is untestable until it reads the whole
   hunting ground. But the **convex book funded 2026-07-07 (SEER/NNDM/FULC) IS a
   live position set and MUST be tended** under the branch above. `cache/oracle_paused.json`,
   `until:null` = lift the sourcing freeze explicitly; no auto-resume.)

0b. **Safety gates.** `kill_switch_active()` → liquidate fresh-sleeve positions
   only (never the legacy hold) + stop. `is_live("oracle")` → if `ORACLE_LIVE` !=
   `"true"`, PAPER mode (compute + journal, mutate nothing). **Funding gate:** if
   the fresh sleeve is `pending_funding`, research/dossiers/paper-A/B only, no
   orders. **Pre-trade (when funded):** `filter_broker_to_gods` (legacy = personal
   = invisible) + `pre_trade_check` + `already_placed_today`.

1. **STAGE 0–1 · Field + Spotlight (DETERMINISTIC).** Refresh the field (universe
   tags, the EDGAR change firehose, the forming-themes map), then run the
   two-direction spotlight over the HUNTING GROUND only
   (`oracle.upside_sourcing.screen_panel`): bottom-up (revenue acceleration,
   beat-and-raise, relative strength, a growth catalyst) AND top-down (an
   under-covered beneficiary of a forming theme whose numbers may not have bent
   yet). This AIMS the reader to ~300 names; it is NOT the edge — quants own these
   signals. Persist `cache/oracle_upside_candidates.json`. Log what was dropped;
   never silently truncate. *(Data pull: refresh the acceleration/coverage panel;
   the neglect balance-sheet pull is retired as the spine — trajectory, not
   floors.)*

2. **STAGE 2 · The breadth read — THE EDGE (JUDGMENT, fan out).** For every
   spotlighted name, read the actual filings + recent transcripts (`shared.edgar`;
   deep-read subagents for the fan-out) and form a VARIANT VIEW answering: is the
   inflection **real** (evidenced in the numbers/text, not narrative), **durable**
   (a multi-quarter S-curve, not a one-print pop), **large** (a path to ≥ +50% over
   the hold), and has the market **not arrived** (still under-covered / mispriced
   vs the read)? For thematic names: genuinely in the wave's path, or a mirage?
   KEEP only q1∧q2∧q3∧q4 (~50 names, each with its open_question). KILL the
   already-priced, decelerating, mirage, or sub-+50% — recorded with a reason.

3. **STAGE 3 · Dossier + bear (JUDGMENT, deep + adversarial).** For each survivor,
   assemble the record (≈3y of 10-K/10-Q, 8-Ks in window, proxy, transcripts) and
   write the dossier via `oracle.upside_dossier.make_upside_dossier(...)` — it
   REFUSES a name without significant upside (`upside_x ≥ 1.5`), a real
   `inflection_type` + cited `inflection_evidence`, an in-window horizon, a bear
   paragraph, and a primary citation. Then run **BEAR×3 as a LOAD-BEARING gate**
   via `oracle.upside_dossier.resolve_bears(d, bears)` — NOT a vibe check. Raise
   ≥3 INDEPENDENT critiques (distinct `critique_type`), and for EACH the bull must
   post a `defense` backed by a **primary filing** (`defense_citations`); an
   uncited or thin answer is only PARTIAL, an unanswerable one is CONCEDED. A
   critique of a FATAL type (`faked_earnings`, `guidance_contradiction`,
   `quality_of_deleveraging`, `one_time_driver`, `going_concern`, `secular_decline`
   — the exact shapes that faked the 2026-07-06 book) must be answered IN FULL with
   a filing or the name is `refuted`. The resolver returns a **refutation margin**
   (defended severity − landed severity); the name is fundable only if ≥3 distinct
   angles were raised, no fatal critique landed, AND the margin > 0. The margin
   also TILTS Stage-4 sizing — the thesis that most decisively outweighed its bears
   gets the bigger bet. A single-pass "looks fine" is exactly the credulity that
   collapsed the last book 6→1; a name is a hypothesis until it survives its own
   bears on the filings. Then the SURVIVAL gate
   `blowup_check(d, going_concern=…, fraud=…, delisting=…)` — runway must clear the
   horizon (+6mo) or be self-funding; no going-concern/fraud/delisting; the upside
   path primary-grounded. This is NOT a floor check — it only stops a landmine
   before the thesis pays. Persist `cache/oracle_upside_dossiers.json`; keep the
   kills with reasons.

4. **STAGE 4 · Sizing — FIRST-CLASS (DETERMINISTIC).** `rank_fundable(dossiers,
   calibration)` (fundable = qualifies ∧ blowup-passed ∧ bear-**survived** with a
   positive refutation margin), then
   `size_upside_book(ranked, equity)` — it concentrates into the best 3–6,
   conviction-weighted (`prob_upside × (upside_x−1) × measured hit-rate`), caps any
   name at 30% and any theme/sector cluster at 40% of equity, and drops
   view-diluting dust (< 6%). Getting BIG on the best few is the mechanism; an
   equal-weight book is a failure mode. Persist `cache/oracle_upside_book.json`.

5. **STAGE 5 · Hold (JUDGMENT gated by typed kills).** For every held name,
   re-underwrite on FACTS (a fresh quote/filing) and run
   `evaluate_exit(dossier, …)`. Exit ONLY on a typed thesis-break —
   fundamental_break (growth/margins reversed in a filing), dilution_event /
   going-concern, catalyst_fail (dated catalyst passed without occurring),
   thesis_date, or an explicit price_level kill. **A drawdown is NEVER an exit** —
   hold the eventual +200% name through a −25% wobble; that patience IS the edge.
   Journal every hold/exit with the reason.

6. **STAGE 6 · Verdict + A/B (DETERMINISTIC — wired 2026-07-10; the audit found
   this layer connected to nothing).** The mechanics are `oracle.ab` and the ONE
   state file is `cache/oracle_upside_ab.json`:
   - **At funding:** `record_selection(ab, round_id=…, date=…, candidates=[…])`
     for EVERY name that entered the deep tier (not just the funded book — the
     passed names ARE Arm B). Each candidate carries `llm_selected` (in the
     funded book?), `lens_score = shared.field_prep.screen_score(packet)` (the
     DETERMINISTIC trajectory screen — never an LLM confidence; both arms
     LLM-driven measures nothing), `conviction = prob_upside`, `upside_x`,
     `inflection_type`, `horizon_months`, and REAL `entry_price`/`spy_entry`
     captured that day (record_selection refuses rows without them).
   - **Every session:** `due_for_grade(ab, today)` → grade EVERY due name, BOTH
     arms (`record_grade` with a live quote — the screen's passed names are
     paper-graded, never dropped; an ungraded Arm B is survivorship bias on the
     discriminating set).
   - **The headline:** `llm_lift(ab)` — trust it only when
     `lift_trustworthy` (no unresolved Arm-B rows). **LLM-lift = A − B**
     answers: did the reading beat the aim?

7. **STAGE 7 · Memory (DETERMINISTIC + prose).** After any grading,
   `oracle.ab.update_calibration(ab)` writes
   `cache/oracle_upside_calibration.json` (hit-rate + mean lift per
   inflection_type) — the WRITER the audit found missing (calib_weight read a
   file nothing produced; the learn-loop was inert). It feeds Stage-3 ranking
   and Stage-4 sizing next session via `calib_weight` (n<5 stays neutral 0.5).
   Rewrite `cache/oracle_beliefs.md` (worldview, open theses, lessons, decayed
   edges). Rotate: down-weight an inflection_type or theme whose edge decayed.
   The loop is what sharpens the engine.

8. **Persist.** Field + candidates + dossiers + book + A/B + calibration + beliefs
   + curve → `pantheon.persist("oracle", {...})` with `cache/oracle_`-prefixed keys.

## Execution (fresh sleeve, when funded + live)

`pre_trade_check`, size to the `size_upside_book` weights, place fractional-share
orders, append `cache/oracle_ledger.jsonl`, update the sleeve with ACTUAL fills.
Journal every decision (buy/hold/pass) with its thesis + typed kill. Never add a
broker position to the sleeve without a matching ledger entry.

**Execution discipline (audit 2026-07-10):**
- **Shared-pool buying-power gate (2026-07-14, house-wide).** The account is
  ONE cash pool shared by every god; your sleeve `cash` field is bookkeeping
  that can badly overstate reality (on 2026-07-14 the four sleeves claimed
  ~$1,165 against a real $237 buying power). Before ANY buy, read the LIVE
  broker buying power (`get_portfolio` → `buying_power`, or `get_accounts`) and
  cap every order at `shared.guards.spendable_buying_power(broker_bp)`. Sleeve
  cash is the ceiling, the live pool is the floor, and the MINIMUM binds — never
  size a buy from sleeve cash alone. (The operator sold ~$930 of a personal
  holding on 2026-07-14 to back the gods' claimed dry powder, but the pool is
  still shared: if two gods reach for it the same session, the second is capped.)
- **Settled cash only:** size the book against SETTLED cash, never total
  equity — `equity()` includes unsettled proceeds and `buy()` only counts a
  GFV instead of blocking. A skipped day beats a good-faith violation.
- **Liquidity gate:** before ANY order, `get_equity_tradability` on every
  target, and skip (leave as cash) any name whose dollar order is large vs its
  typical volume — the hunting ground is small/micro-caps and `size_upside_book`
  does not know liquidity.
- **Cluster tags:** every dossier handed to `size_upside_book` MUST carry a
  non-empty `sector` (and `theme` when known) — with both empty the 40%
  correlation-cluster cap silently degrades to per-symbol and cannot bind
  (audit: two same-theme names sized to 60% combined). Enrich from the field
  packet before sizing.

## The checkpoint

At ~20 graded names (or a date): **does the book beat SPY over the 6–24mo hold,
and does LLM-lift (A − B) show the reading beat the screen?** Both positive and
material → the reading is real upside alpha; Oracle earns concentration + capital.
Zero/negative → the reads are rationalization and Oracle folds into Proteus. The
forward returns decide, not the narrative.

## Failure modes (self-check; on violation → stop, open a PR, do not silent-patch)

- **F1** drifting to mega-cap / well-covered names → violates the hunting ground;
  the edge evaporates where the Street already reads.
- **F2** funding on `spotlight_score` → that's Arm B; the READING must drive
  selection.
- **F3** selling a name on a drawdown → violates Stage 5; it bleeds the right tail.
- **F4** equal-weighting the book → no view expressed; concentrate.
- **F5** citing a snapshot (Robinhood/Yahoo) as evidence → ungrounded thesis.
- **F6** reintroducing a floor mandate / avoidance score / convexity metric → those
  are retired; Oracle optimizes UPSIDE, and a floor is only a conviction bonus.
- **F7** claiming "it works" without grades → only Stage-6 forward return settles it.

## Halt

Circuit breaker (`sleeve.check_circuit_breakers` = "halt") → set halted, stop
opening. Code error → log `cache/oracle_errors.jsonl`, open a PR, do not
auto-patch.
