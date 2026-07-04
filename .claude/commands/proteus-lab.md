# /proteus-lab — invent and test new strategies (paper only, bias-proofed)

The operator's mandate (2026-07-04): Proteus may come up with ENTIRELY
NEW or completely underutilized stock strategies and test them — under
the same discipline every house study runs on, with backtest bias held
in front of his face mechanically, not by memory. Engine:
`proteus/lab.py` — a validated writer that refuses hypothesis stubs,
un-preregistered backtests, unaddressed bias items, second cuts at the
same data, and early promotions.

**The lab is PAPER ONLY.** No broker orders, ever, from this skill. Lab
forward-test trades do NOT count toward the live book's 30-trade
checkpoint (prereg amendment #4). A strategy touches real money only
one way: after `validated`, Proteus may cite it in a live thesis in his
normal daily session, where every live-book rule still applies.

## Cadence

Weekends, once per week (`should_run("cache/proteus_cadence.json",
"lab", 7)` — Zeus dispatches it). Markets are closed; this is his deep
work. A lab session with no new hypothesis is fine — tending an open
forward test or honestly shelving a dead idea is work.

## The pipeline (one-way ratchet, enforced by `proteus/lab.py`)

    hypothesis -> preregistered -> backtested -> forward_testing -> validated
                       |               |                                |
                    shelved         refuted <---------------------------

## Session liturgy

0. **Hydrate.** `pantheon.hydrate()`. Load `lab = proteus.lab.load_lab()`.
   Read `docs/RESEARCH_LEDGER.md` FIRST — the graveyard of refuted
   "obvious" ideas is his best prior. Then read the lab: statuses of
   every strategy, `hypotheses_ever` (his own multiple-testing count).

1. **Tend before inventing.** Any strategy in `forward_testing` gets
   marked/graded first (see step 5). Any `backtested`+`supported`
   strategy not yet forward-testing gets its forward test started. Only
   then does he get to play with new ideas — the lab is a pipeline, not
   a pile of abandoned enthusiasms.

2. **Ideate (maybe).** Where genuinely new/underutilized edges live —
   his own runbook already names the terrain: forced flows and
   price-insensitive counterparties, structural calendars (index
   reconstitution mechanics, lockups, window-dressing), filing types
   and clauses nobody parses, closed-end discounts, post-bankruptcy and
   busted-instrument corners, microstructure. What does NOT qualify:
   anything the ledger already refuted (insider clusters as auto-buy,
   convergence multipliers, raw PEAD buy-side...) unless the hypothesis
   states specifically what is DIFFERENT this time. Register via
   `new_strategy(lab, slug=..., date=..., mechanism=..., who_loses=...,
   underutilized_because=..., falsifiable_claim=...)` — the writer
   refuses ideas that can't articulate why the edge exists, who is on
   the other side, and why it isn't already arbitraged away.

3. **Pre-register BEFORE data.** Write `docs/proteus_lab_prereg_<slug>.md`
   (population definition, metric + horizon, success criteria with
   thresholds, planned bias handling) and COMMIT IT to the repo before
   pulling a single price bar or filing — git history is the timestamp
   that proves "before." Then `preregister(lab, slug, date=...,
   prereg_doc="docs/proteus_lab_prereg_<slug>.md",
   population_definition=..., metric=..., success_criteria=...)`.

4. **Backtest — with the bias catechism as a hard gate.** Build the
   COMPLETE population the prereg defined (EDGAR full-index catalogs,
   `get_equity_historicals` bars — the same machinery every house study
   used; include the dead names or explain survivorship honestly).
   Compute the pre-registered metric. Then, and only then:
   `record_backtest(lab, slug, date=..., n=..., mean_excess=...,
   verdict="supported"|"refuted"|"inconclusive", bias_checklist={...},
   results_doc=...)`. The writer refuses the record unless ALL EIGHT
   bias items (`proteus.lab.BIAS_CHECKLIST`: survivorship, look_ahead,
   selection, multiple_testing, overfitting, costs_liquidity, regime,
   small_n) are addressed in writing, ≥60 chars each — "n/a" without a
   why is rejected. The multiple_testing item must cite
   `lab["hypotheses_ever"]`. Write
   `docs/proteus_lab_results_<slug>.md` and ADD A ROW to
   `docs/RESEARCH_LEDGER.md` — refuted and inconclusive get the same
   prominence as supported (house rule). One dataset, one decision,
   once: the writer refuses a second backtest on the same slug; a
   revised idea is a NEW slug with a fresh prereg.

5. **Forward test (the only road to validated).** A supported backtest
   is a licence to spend paper, not a result. `start_forward_test`,
   then run it via the shared ghost engine (paper positions in
   `cache/proteus_lab_ghost_ledger.json` /
   `cache/proteus_lab_ghost_curve.json`, `shared.ghost.open_entries`
   with `features={"strategy": slug}`, marked and graded at horizon
   with `grade_entries`). Each graded ghost trade's excess vs its SPY
   mirror goes in via `record_forward_grade`. `evaluate_forward` shows
   the running score (judged on the SHRUNK mean — small samples get no
   face value). At ≥20 grades, `conclude_forward` settles it:
   validated or refuted, arithmetic, no judgment call, no early call.
   The daily `/proteus` session tends open lab positions (mark, grade,
   record) so horizons don't rot between weekend lab sessions.

6. **Persist.** `mark_run("cache/proteus_cadence.json", "lab")`, then
   `pantheon.persist("proteus", {lab json, ghost ledger/curve, cadence})`.
   Prereg/results docs and ledger rows are committed to the code branch
   in the same session they're written.

## Hard rules

- NEVER a broker order from this skill; never a live-book mutation.
- NEVER pull data before the prereg doc is committed. If data was
  peeked, the slug is burned — register the honest variant as a new
  slug and say so in its prereg.
- `refuted` is terminal for the slug. Earning the idea back requires a
  new slug, a fresh prereg, and FRESH data (the ledger's own rule).
- A `validated` strategy is a tool, not an autopilot: live entries
  citing it still go through the full journal (thesis, prediction,
  typed kill condition) and every live safety gate. `live_citable(lab)`
  is the list; citing anything else as "the lab validated it" is a
  violation.
- Backtest support alone is never citable as validation in a live
  thesis — the ledger's standing finding is that in-sample support is
  where good ideas go to flatter themselves.
