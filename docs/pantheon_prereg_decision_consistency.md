# Pre-registration: LLM decision-consistency sweep (Oracle + Midas)

Committed 2026-07-04, before any re-scoring run exists. Extends the
Nemesis judge-consistency method (docs/nemesis_prereg_judge_consistency.md,
which found the Nemesis judge is DICE at the veto boundary) to the two
other gods whose selection-relevant LLM judgments are re-runnable from
stored inputs. Delphi's five decision points do not store their per-name
LLM inputs in re-runnable form and are OUT OF SCOPE (noted for a future
logging change, not tested here).

## Question

Each god's edge is asserted to live in an LLM judgment layer. For the
judgment to be a discrimination rather than dice, the same inputs must
yield the same selection-relevant decision on re-run. Nobody has
measured this for Oracle's dossier conviction or Midas's single pick.

## Design (FROZEN)

Re-scoring uses ONLY the stored NARRATIVE facts already in each dossier
(the layer the LLM judged), never the recorded scores. Judges are
un-anchored (no recorded conviction/probability, no sight of each
other), production scoring instructions, extended thinking. This
isolates JUDGMENT variance exactly as the Nemesis probe isolated it
over fixed extractions.

### Oracle (conviction stability)
- Specimens: the 8 active cohort dossiers (the names live money is in)
  plus the 4 highest-conviction non-held dossiers = 12 specimens.
- Per specimen: 5 independent re-scores from stored
  thesis/business/bull+bear scenarios/decline_explanation/citations →
  each returns conviction [0,1] and bull-scenario probability.
- Metric: per-specimen range and sd of conviction; and the
  **selection-flip rate** — re-rank all 12 by each of the 5 independent
  conviction draws; fraction of draws whose top-8 set differs from the
  recorded top-8.

### Midas (pick stability — the sharpest test)
- Specimens: this week's 10 finalists (recorded pick: DAKT).
- 5 independent full re-scorings: each assigns pop_probability and
  expected_magnitude to all 10 from stored catalyst/bull/bear/signals,
  computes expected_value, picks argmax.
- Metric: **pick-flip rate** — fraction of the 5 re-runs whose winner
  differs from DAKT; plus range/sd of the winner's pop_probability.

## Decision rule (FROZEN)

- **Oracle selection-flip ≥ 40% (≥2 of 5 draws change the top-8):** a
  3-draw median conviction becomes mandatory in /oracle sizing before
  the cohort is cut. Below that: single-score stands, documented stable.
- **Midas pick-flip ≥ 40% (≥2 of 5 re-runs pick a different name):**
  his all-in concentration is running on judgment noise; the runbook
  gains a mandatory 3-run median expected_value before the Monday pick,
  and the finding is escalated to the operator as a concentration-risk
  disclosure. Below 40%: single pick stands, documented stable.
- One shot; triggers on the pre-stated thresholds, not on feel. Small
  n (5 draws, 10–12 specimens) — as with the Nemesis probe, effects
  must be LARGE to fire, which is the point: only gross instability
  should move a rule.

## Not in scope / no rule beyond the above

Delphi's decision points (input not stored re-runnably); accuracy of any
score (forward-only, same wall as reader accuracy). This measures
CONSISTENCY only.
