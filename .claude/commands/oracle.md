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

## Standing posture (2026-07-06, operator directive — the proactivity default)

Oracle's job is to find the best asymmetric bets in the **whole universe**, not
to perfectly vet a handful the lenses happened to surface. Run every session in
**HUNT mode** by default:

- **SOURCE WIDE, every session — all THREE legs.** Run the unified sourcing pass
  (`python3 run_oracle_sourcing.py`) across the whole universe BEFORE working the
  lens net. It covers every why_mispriced type the gate can fund, so nothing
  convex is left behind for lack of a net:
  - **forced_seller** — form-enumerate price-insensitive SUPPLY events (issuer
    tenders, fund wind-downs, large-cap spinoffs) off EDGAR daily indexes
    (`oracle.forced_seller_sourcing`, measured 100% recall vs 12% keyword).
  - **hard_catalyst** — form-enumerate activist SC 13D / 13D-amendments +
    a strategic-review 8-K keyword supplement (`oracle.hard_catalyst_sourcing`);
    each 13D carries `requires_item4_read` (the index can't see a campaign).
  - **neglect** — screen the whole Sharadar fundamentals panel for names below a
    countable floor (net cash / net-net / tangible book) with no event to trip a
    form index (`oracle.neglect_screen`; FX-clean USD reporters, financials &
    mortgage-REITs excluded, cash-runway flagged). This is the family that
    produced 4 of 5 pre-rebuild names (ARVN/VTSI/ALCO/RNA) — the forced-seller
    net is blind to it.
  The four legacy lenses are a narrow, biased, ~zero-measured-alpha net; the
  durable convex edges live in these three structural families. Goal: coverage
  of thousands, not depth on forty.
- **MEASURED 2026-07-06 — NEGLECT is the spine; the event legs are OVERLAYS.** A
  full primary-source verification of all three legs (~40 names,
  docs/oracle_neglect_verification + oracle_event_legs_verification) found the
  fundable convex floors live in the **neglect** leg (4 FUND / 11 WATCH / 12 KILL).
  The **forced_seller** leg yields the rare JOF-style *recurring common
  conditional-tender* but its SC TO-I enumeration mostly surfaces
  preferred/leverage tenders and non-traded at-NAV funds (1 FUND / 2 WATCH / 5
  KILL). The **hard_catalyst** leg as a standalone net measured **0 fundable of
  14** — raw 13D + strategic-review keywords are too noisy (false positives,
  acquirer-side, concluded deals, Hermes-domain, floorless distress). So: source
  neglect as the spine, and use activist-13D / strategic-review / forced-seller
  as a **catalyst overlay by INTERSECTION** with an already-verified below-floor
  name. A catalyst is a bonus on a floor, NEVER a substitute for one.
- **DRIVE TO A VERIFIED PICK, not a list.** A candidate list is not a
  deliverable; a primary-source-**verified** dossier (or an honest kill) is.
  Push each promising name through `make_convex_dossier` → `verify_dossier` →
  `rank_fundable` to a decision — don't stop at "here are some names."
- **BOTH STAGES, ALWAYS.** Widen the net (sourcing) AND keep it honest (the
  four-trap verification gate). Sourcing without verification funds phantom
  floors (the 2026-07-06 XRN/SMHI/MNRO/GYRO kills); verification without
  sourcing just polishes forty names.
- **AMBITION WITH RIGOR.** Bias toward building and acting over hedging — but
  the verification gate is non-negotiable. Hunt hungrily; fund nothing unverified.
- **BUILD THE MACHINE, not just the picks.** When the sourcing or verification
  tooling has a gap, fix the tooling — a better engine compounds every future
  session; one pick doesn't. (Open engine work: a fund-vs-operating-company
  issuer-type filter to drop keyword false positives, and catching CEF/BDC
  tender *commencement* filings with runway rather than post-expiry results —
  see docs/oracle_sourcing_status_2026-07-06.md.)

## Session liturgy

0. **Hydrate.** `pantheon.hydrate()`.

0b. **Safety gates.** `kill_switch_active()` → liquidate (fresh-sleeve positions
   only, never the legacy hold) + stop. `is_live("oracle")` → if `ORACLE_LIVE`
   != `"true"`, PAPER MODE (compute + journal, place nothing, mutate nothing).
   **Funding gate:** load the fresh sleeve; if `pending_funding` is set, the
   reframed engine isn't funded — research + dossiers + paper A/B only, no
   orders. **Pre-trade:** `filter_broker_to_gods` (legacy names are personal =
   invisible) + `pre_trade_check` + `already_placed_today` before any order.

1. **Source WIDE first, lenses second (2026-07-06) — the THREE-leg pass.** The
   PRIMARY sourcing is the unified whole-universe sweep — run it every session:
   `python3 run_oracle_sourcing.py` runs all three why_mispriced legs and writes
   one combined `cache/oracle_sourced_candidates.json`:
   - **forced_seller** (`oracle.forced_seller_sourcing.sweep_by_form`) — issuer
     tenders / fund wind-downs / large-cap spinoffs, graveyard-excluded,
     Hermes-deduped, tradability-split.
   - **hard_catalyst** (`oracle.hard_catalyst_sourcing.sweep_by_form` +
     `sweep_strategic_review`) — activist 13D campaigns + strategic-review 8-Ks.
   - **neglect** (`oracle.neglect_screen.screen_panel`) — below-floor names from
     the Sharadar panel; needs the pulled data (`run_oracle_neglect_pull.py`
     refreshes `data/oracle_neglect/` quarterly with fresh fundamentals).
   THEN run the four legacy lenses (insider/13F/13D/quality) as a SECONDARY net —
   narrow, biased, ~zero-measured-alpha; the durable edges are in the three legs.
   Sourcing is a WIDE cheap net, not a decision; every candidate — swept or
   lensed — must EARN its slot through the convex-dossier + verification
   discipline (steps 2/2c). Record each candidate's `lens_score` purely as the
   Arm-B baseline input — never as the decision.
   *Known engine gaps to tighten (docs/oracle_sourcing_status_2026-07-06.md):* a
   fund-vs-operating-company issuer filter; catching CEF/BDC tender
   *commencement* (not post-expiry) filings; and an index-DELETION channel
   against S&P/Russell reconstitution data (a Form 25 is the wrong instrument —
   measured ~all noise, DEMOTED).

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

2c. **VERIFY against PRIMARY FILINGS before the book (2026-07-06, MANDATORY —
   the launch-gate lesson).** A dossier's self-reported `convex` flag is NOT
   enough to fund it. The 2026-07-06 launch gate killed 4 of 8 dossiers a
   fundamentals-API pass had waved through — XRN ("debt-free" missed a $653M
   credit line), MNRO (P/B<1 was 100% goodwill, tangible book NEGATIVE), SMHI
   ("$20 NAV" was an activist claim in NO filing, catalyst already fired), GYRO
   (a melting liquidation PROJECTION, not an audited NAV). Every one shared a
   shape a snapshot cannot see and a primary filing reveals. So for EACH name
   near the cut, pull the actual 10-K/10-Q/8-K (`shared.edgar`; deep-read
   subagents for a fan-out) and run
   `oracle.convex_dossier.verify_dossier(dossier, floor_basis=…,
   debt_reconciled_full_stack=…, catalyst_fired=…, book_survives_goodwill=…,
   primary_citations=[…], verdict=…)`. It runs the four traps, each a real kill:
   - **primary_source_cited** — a snapshot citation (Robinhood/Yahoo) is NOT a
     floor source; at least one real filing must back it (killed XRN).
   - **floor_not_merely_asserted** — `floor_basis` on the trust ladder
     `cash > net_net > transacting_asset > book > asserted`; an *asserted* NAV
     (activist appraisal, management projection) is not a floor (killed SMHI/GYRO).
   - **book_survives_goodwill** — for a book floor, tangible book (ex-goodwill)
     must still support it (killed MNRO).
   - **debt_reconciled_full_stack** — debt taken off the FULL liability stack,
     not one balance-sheet line (killed XRN).
   - **catalyst_not_already_fired** — the re-rating hasn't already happened.
   Verification RE-STAMPS `floor_hardness` from the true `floor_basis` (a
   self-reported "hard" on an asserted floor cannot survive), and only a name
   whose traps ALL pass with verdict keep/revise becomes `verified`. **Cite the
   accession numbers in the dossier.** A name that fails is retracted with its
   reason (the record keeps it, per docs; never silently drop).

3. **Select a CONVEX book (concentrated, conviction-weighted) — from VERIFIED
   names only.** Use `oracle.convex_dossier.rank_fundable(dossiers)` (NOT
   `rank_by_convexity`) — it returns only names that are BOTH convex AND
   primary-source-`verified`, best convexity first, so an unverified dossier
   (however good its self-reported numbers) structurally cannot receive capital.
   `rank_by_convexity` stays the pure-math research view; `rank_fundable` is the
   gated view money flows through. Take the few best; size within a per-name cap
   (concentration is the return lever — no equal 8-name cohort). Horizons are
   multi-month/patient, but a name must EARN its slot on risk-adjusted
   convexity, verified against filings — not on a signal or a raw multiple.

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
