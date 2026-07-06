# ORACLE_UPSIDE — the machine spec (2026-07-06, the bible)

This supersedes the convex/floor reframe as Oracle's operating definition. Oracle
is a **stock picker with one job: choose the few under-covered names with the
biggest real upside over a 6–24 month hold, get big on them, and hold to the
thesis.** Scored one way only — forward return vs SPY over the hold. No floor
term, no avoidance term, no Sharpe term. Floors, if present, are a conviction
bonus, never the price of entry.

Governance note: this is a **conscious reframe of Oracle's selection objective**,
not a new god (no new scaffolding). The legacy cohort (CXT/HDSN/J/PSN/VITL)
stays FROZEN and untouched; the reframed engine is `pending_funding`, paper-only,
places no orders. Prior floor-centric docs (`oracle_reframe_2026-07-05`,
`oracle_finest_picker_roadmap/mechanics`, the `convex_dossier` gate) are
SUPERSEDED for selection and retained only as history / the blowup-filter lineage.

---

## 0. OBJECTIVE
```
maximize  E[ fwd_return(pick, t) − fwd_return(SPY, t) ]   for t ∈ {6,12,24} months
where     pick ∈ hunting_ground
          selection_signal = LLM breadth-read (not a screen)
          returns are right-tail-dominated → optimize SIZING + HOLDING, not hit-rate
```

## 1. GLOBAL INVARIANTS
```
I1  hunting_ground := (mcap ∈ [1e8, 3e9] AND analyst_coverage ≤ 4)
                      OR special_situation ∈ {spinoff, post_reorg, ipo<18mo}   (mcap_upper→5e9)
I2  reject a thesis that reduces to {cheap, undervalued, below_book, insider_bought, quality}
    — cheapness is not a reason a stock rises; these are the value-trap tells
I3  horizon_months ∈ [6, 24]
I4  every KEEP carries its open_question forward (what the next stage must resolve)
I5  every KILL is recorded with a reason (never silent-drop; the dataset decides once)
I6  paper-only until funded (pending_funding): place no orders, mutate no live sleeve,
    never touch the frozen legacy cohort
```

## 2. STATE / ARTIFACTS  (all under cache/, persisted to claude/live)
```
cache/oracle_upside_field.json      universe + firehose + themes  (Stage 0)
cache/oracle_upside_candidates.json spotlight survivors           (Stage 1)
cache/oracle_upside_dossiers.json   UpsideDossier[]               (Stage 2–3)
cache/oracle_upside_book.json       funded book (weights, kills)  (Stage 4)
cache/oracle_upside_ab.json         A/B: reading vs spotlight     (Stage 6)
cache/oracle_upside_calibration.json inflection_type → hit_rate   (Stage 7)
cache/oracle_beliefs.md             forward worldview (read@start, write@end)
```

## 3. STAGE CONTRACTS  (READS → OP[mode] → KEEP/KILL → EMITS)

```
STAGE 0  FIELD                                   [DETERMINISTIC]
  build universe (mcap/coverage/trajectory tags); classify EDGAR firehose by
  form+item; build themes (sector waves forming|peaking). No selection.

STAGE 1  SPOTLIGHT   ~7000 → ~300                 [DETERMINISTIC]
  over hunting_ground ONLY, run two screen families that AIM the reader:
    bottom_up = accel(rev,margin,eps) ∨ beat_and_raise ∨ rel_strength ∨ growth_catalyst
    top_down  = under_covered beneficiary of a forming theme (numbers need NOT have bent yet)
  KEEP iff (bottom_up ∨ top_down) ∧ I1 ∧ ¬I2_obvious
  EMITS candidates(spotlight_score). NOT the edge — quants own these signals.

STAGE 2  BREADTH READ   ~300 → ~50   *** THE EDGE ***   [JUDGMENT, fan-out]
  read each name's filings/transcripts; form a VARIANT VIEW answering:
    q1 inflection REAL (evidenced, not narrative)?   q2 DURABLE (S-curve not one pop)?
    q3 LARGE (path ≥ +50% over hold)?                q4 market NOT arrived (still under-covered)?
    [thematic] genuinely in the wave's path, or a mirage?
  KEEP iff q1∧q2∧q3∧q4 ; KILL iff already_priced ∨ decelerating ∨ mirage ∨ upside<50%
  EDGE = breadth: hundreds of deep reads of names no desk covers, before coverage prices them.

STAGE 3  DOSSIER + BEAR   ~50 → ~12               [JUDGMENT, deep + adversarial×3]
  write UpsideDossier (§4); BEAR×3 attack (already_priced? decelerating? dilution? theme stalling?);
  run blowup_filter (§6.3).
  KEEP iff dossier.qualifies (§5) ∧ survives_majority_bear ∧ ¬blowup.
  EMITS dossiers ranked by rank_key (§5).

STAGE 4  SIZING   ~12 → 3–6   *** FIRST-CLASS ***  [DETERMINISTIC]
  weight_i ∝ conviction_i · (upside_x_i − 1) · calib_hit_rate(type_i);
  concentrate top 3–6; enforce §6.2 caps + correlation-cluster cap;
  drop any name < min_meaningful (0.06). EMITS book.

STAGE 5  HOLD   (per session, held names)         [JUDGMENT gated by typed kills]
  re-underwrite on FACTS only; EXIT iff a typed thesis_break fires (§6.1);
  HOLD otherwise. DRAWDOWN ALONE IS NEVER AN EXIT — this is where the right tail is protected.

STAGE 6  VERDICT   (6/12/24mo marks or exit)      [DETERMINISTIC]
  grade fwd_return(pick) − fwd_return(SPY); record vs own prediction;
  A = book return, B = spotlight top-N → LLM_lift = A − B (did the READING beat the AIM?).

STAGE 7  MEMORY                                   [DETERMINISTIC + prose]
  calibration[type] ← grades; rewrite beliefs; rotate (down-weight decayed types/themes).
  Feeds Stage 3 rank + Stage 4 sizing next session — the loop that sharpens the engine.
```

## 4. UpsideDossier SCHEMA  (typed; writer REFUSES on violation)
```
sym                 str
business            str
thesis              str  len≥120   the variant view: what the 6–24mo hold holds that consensus underweights
inflection_type     enum{earnings_accel, margin_turn, product_ramp, demand_shift,
                         adoption_s_curve, capital_return, turnaround, thematic_rerate}
inflection_evidence str  len≥40    SPECIFIC number/fact the trajectory is bending; cite a filing
upside_x            float ≥ 1.5    6–24mo target multiple (REQUIRED — the mandate)
prob_upside         float ∈[0,1]   also used as conviction in sizing
downside_pct        float ∈(0,1]   loss if wrong; for E[·] only — NOT gated small, NOT a floor
catalyst            str            what makes the market SEE it
catalyst_date       iso|""         prefer within [now, now+horizon]
horizon_months      float ∈[6,24]
runway_months       float|"self_funding"   survival input (§6.3)
falsifiable_pred    str  len≥20
prediction_date     iso
kill_condition      str
kill_type           enum{price_level, fundamental_break, dilution_event, thesis_date, filing_event}
kill_value          any (typed to kill_type)
adversarial         str  len≥60    the bear case, stated
citations           [primary]      SEC/accession/form-code; a snapshot is NOT a citation
current_price, spy_price, sector, coverage, recent_runup_pct, lens_score(A/B baseline only)
floor_pct           float|None     OPTIONAL downside floor → conviction bonus, never required
```

## 5. SCORING
```
expected_return  = prob_upside·(upside_x − 1) − (1 − prob_upside)·downside_pct
annualized_er    = expected_return · (12 / clamp(horizon_months, 6, 24))
calib_weight(t)  = calibration[t].hit_rate    (0.5 if n<5)
rank_key         = annualized_er · calib_weight(inflection_type)             (DESC)

qualifies iff upside_x ≥ 1.5 ∧ expected_return > 0 ∧ horizon ∈ [6,24]
            ∧ recent_runup_pct < 0.50 (not already run)
is_fundable iff qualifies ∧ blowup_checked ∧ ¬blowup ∧ bear_verdict ≠ refuted
```
No convexity_score, no floor_hardness weight, no floor requirement. Upside
magnitude is REWARDED, not penalized.

## 6. PREDICATES
```
6.1 EXIT (Stage 5) — exit iff ANY typed break; else HOLD
    fundamental_break : growth decelerated below thesis OR margins reversed (from a FILING)
    dilution_event    : dilutive raise beyond thesis OR going-concern raise
    catalyst_fail     : catalyst_date passed AND catalyst did not occur
    thesis_date       : horizon reached without the predicted re-rating
    price_level       : only if named in kill_value (rare; theses held through vol)
    NOT exits: drawdown, red day, rank drift, sector-out-of-favor, boredom

6.2 SIZING caps (Stage 4)
    concentrate 3–6 names; a top name may reach ~30% w/ explicit risk_ack
    min_meaningful ≥ 6% of book else drop (no view-diluting dust)
    correlation cluster: Σ weight per {theme|sector|macro_driver} ≤ 40%

6.3 BLOWUP filter (replaces floor verification) — ¬blowup iff ALL pass
    survives_to_thesis : runway_months ≥ horizon_months + 6  OR  "self_funding"
    no_going_concern   : no audited substantial-doubt language
    no_fraud           : no SEC action / credible fraud
    no_delisting       : no active deficiency / Form 25
    primary_grounded   : inflection_evidence + upside path cite real filings, not vibes
    Purpose: don't step on a landmine BEFORE the thesis pays. A survival gate, not a floor.
```

## 7. REASONING / EXECUTION BOUNDARY
```
DETERMINISTIC (code): Stages 0,1,4,6,7 ; all §5 arithmetic ; §6.2, §6.3 checks
JUDGMENT (LLM read — the edge): Stage 2 variant view ; Stage 3 dossier+bear ; Stage 5 re-underwrite
→ the edge is ISOLATED to reading; everything around it is deterministic and auditable.
```

## 8. FAILURE MODES  (self-check; on violation → stop, open PR, do not silent-patch)
```
F1 drift to mega-cap / covered names  → violates I1; the edge evaporates there
F2 fund on spotlight_score            → that's Arm B; the READING must drive selection
F3 sell a name on drawdown            → violates Stage-5 invariant; bleeds the right tail
F4 equal-weight the book              → violates §6.2; no view expressed
F5 cite a snapshot as evidence        → violates §4; ungrounded thesis
F6 claim "best" without grades        → only Stage-6 forward return settles it
```
