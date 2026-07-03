# LLM integration audit: every decision surface, all five gods

Run 2026-07-04. Not a pre-registered study (no statistical trigger) —
a systematic sweep for defects, each independently adversarially
verified before being reported. 28 agents (5 find + 23 verify), full
data: `docs/data_llm_integration_audit_2026-07.json`.

Method: one finder per god, reading its runbook + Python scaffolding
against the failure taxonomy this weekend built reactively (silent-
empty, schema-stub, anchoring-leakage, model-effort-mismatch,
swallowed-error, coverage-gap, prompt-defect). Every claimed defect
then got an independent skeptic instructed to default to
FALSE_POSITIVE and confirm only by reading the code itself.

**23 findings, 17 CONFIRMED, 6 FALSE_POSITIVE** (the skeptics did their
job — real false positives, listed at the bottom).

## HIGH severity — live-trading-relevant, need a decision before Monday

**1. `/oracle-score` runs the rotation trade path the cohort model
explicitly forbids.** `oracle-score.md` calls
`oracle.positioning.rotation_decision` (challenger ≥1.25x incumbent →
rotate) and `oracle.exits.exit_signal` (bull_hit → TRIM,
bear_hit → REVIEW), then places broker orders. But `oracle.md`/CLAUDE.md
define Oracle as buy-and-hold-to-thesis-break, and explicitly list
"rank drift" and "a new dossier scored higher" as PROHIBITED exits.
`/oracle-score`'s own header claims to run "steps 7-12 of /oracle" —
those steps are research/rescore/cohort-logic, not rotation. **If this
skill is ever invoked against the live cohort, it places real trades
that violate the strategy's core discipline.** `ORACLE_LIVE=true`.

**2. Midas's runbook contradicts its own architecture, citing a signal
his own study refuted.** The mechanical pick uses the convergence
score — but this weekend's pre-registered convergence test REFUTED the
multiplier (2+ signals scored *worse*, wrong direction;
`docs/midas_convergence_results_2026-07.md`). The runbook's closing
note still says the EV judgment "carries the decision," which is false
per `pick_winner()`'s own docstring (the finding that saved us from a
false alarm on 2026-07-04). Two separate defects compounding: docs
that don't match code, and a mechanical score now known-refuted still
driving the all-in pick.

**3. Midas's stale-signal freshness gate fails OPEN.** When a
historicals fetch fails or returns too few bars,
`midas/prescan.py`'s freshness check defaults to KEEP rather than
DROP — a failed fetch is indistinguishable from a fresh, undigested
signal. A dead/stale signal can pass silently into the all-in weekly
pick.

**4. Oracle's dossier validator has no prose gate.** `thesis` and
`business` are stored as free strings with zero length check —
`validate_dossier()` checks symbol/citations/ratings/scenarios/price
but never reads `thesis` or `business` content. A dossier with
`thesis=""` validates and ranks purely on scenario math. This is the
exact RNA stub-extraction failure class from 2026-07-03 — except
Nemesis was FIXED (`_PROSE_FIELDS`, `_MIN_PROSE=20`) and Oracle never
got the analogous gate. Directly exposed: the annual 8-name cohort
selection, "where Oracle's entire annual risk concentrates."

**5. Delphi's decision-log validator accepts a date-only stub.**
`REQUIRED_FIELDS = ("date",)` — a record of `{"date": "..."}` passes
despite the module's own docstring claiming it "refuses anything but
a proper record." `override_summary()` then backfills missing
override/weight fields as 0, which reads as "no overrides happened"
rather than "the field was never populated" — the two are
indistinguishable in the audit trail the override budgets depend on.

## MEDIUM severity

- Oracle: `insider_tier` defaults to `"full"` (1.0x, the MOST
  favorable sizing weight) when omitted — a flattering default,
  opposite of the hostile-default convention used elsewhere (Nemesis:
  incentive 0.0, garbage 1.0 by default).
- Oracle: broker price/52w-high divergence is "mandatory... rejects
  on >5% divergence" per the runbook, but degrades to a warning in
  code when the fields are simply omitted.
- Delphi: `breadth` computes % above moving-average over only the
  successfully-fetched subset — no coverage floor, so a partial data
  outage silently shrinks the sample rather than failing loud.
- Delphi: stated override budgets and weight/risk bounds are
  honor-system only — no Python clamp enforces the "max 2 holds,"
  "max 3 vetoes" limits the runbook describes.
- Midas: convergence-count treats correlated signals from a SINGLE
  event (e.g. an earnings beat that also trips a volume anomaly) as
  independent channels, inflating the multiplier tier.
- Achilles: LLM-attached confirming signals (revenue beat, guidance
  raised, squeeze, insider pre-buy) default False with no defined
  fetch method — "not found" and "not checked" are the same bit.
- Achilles: scoring trusts the caller for surprise direction/presence
  — `None` surprise scores as MAX; a miss scores via `abs()` (a -50%
  miss and a +50% beat currently score identically).
- Nemesis: `validate()` never requires `pro_forma_notes` or
  `post_spin_insider_activity` populated — 2 of the 5 mandated
  judgment fields can be empty and still pass.
- Nemesis: the revision judge is shown the PRIOR recorded scores and
  told to "justify each delta against" them — anchoring, precisely
  when new documents are supposed to force an independent re-read
  (the OCTV re-read case this was meant to guard).

## LOW severity

- Oracle: citation gate accepts non-empty placeholder strings (no
  format/URL check).
- Delphi: `load_decisions` silently discards corrupt JSONL lines
  despite its docstring claiming it counts them.
- Nemesis: only the primary judge is mandated to use extended
  thinking; the two refuters and the (now-mandatory) 3-judge panel
  have no reasoning-effort floor specified.

## False positives (skeptic caught these — reported for completeness)

Delphi's exit-candidate N/A handling, Midas's default-tradeable
assumption, Achilles' close-vs-open reaction timing and its parse-
failure basket handling, and two Nemesis claims (insider-silence
reconciliation wording, verdict-default interaction with the v2 veto)
were all investigated and found to not actually occur as claimed, or
to be already handled correctly elsewhere in the pipeline.

## Recommendation

No code has been changed by this audit — findings only, per the
standing "never silently patch" discipline for anything touching live
paths. Items 1–3 sit directly on money that trades Monday and warrant
an explicit decision before then: **deprecate/gate `/oracle-score`
against an active cohort, fix Midas's fail-open freshness default, and
reconcile the Midas runbook's claim against its own refuted signal.**
Items 4–5 (prose gate, decision-log stub) are structural and worth
fixing on the same footing as the Nemesis fixes they mirror, on
whatever timeline the operator prefers.
