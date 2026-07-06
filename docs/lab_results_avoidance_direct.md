# Lab results — `avoidance_direct` (mechanical precondition SUPPORTED, 2026-07-05)

**Verdict: mechanical precondition SUPPORTED — small and decaying, but real.**
Arm B (mechanical distress exclusion) beats Arm C (random exclusion) in-sample
AND in the holdout, non-isolated across k = 5/10/20%. The house's "avoidance is
the real edge" claim survives its first direct test; the forward LLM-vs-mechanical
A/B is now justified and open. Filed here to close a loose end: the backtest was
recorded in the lab registry same-day but this results doc and ledger row were
never written before the session ended.

Prereg: `docs/lab_prereg_avoidance_direct.md` (committed before data). Universe:
SMALL/MICRO PIT (achilles panel, survivorship-free Sharadar SEP; LARGE bucket
NOT yet tested — pending a separate bar pull, disclosed as a coverage gap, not
a survivorship issue). Distress composite: SF1 PIT-by-datekey (netinc/assets,
ncfo/assets, gp/assets, shares-outstanding dilution), monthly rebalance,
exclude the most-distressed top-k%, hold survivors EW, metric = survivors' EW
return minus the full-universe EW return ("avoidance alpha"). In-sample
≤2015-12-31 / holdout 2016+.

## What the mechanical arms (B vs C) showed

- **In-sample:** distress-exclusion avoidance-alpha strongly positive, t≈4,
  monotonic in k (bigger cut → bigger alpha), and beats the random-exclusion
  control (~0 by construction) at every k. n=192 monthly observations —
  well-powered.
- **Holdout (2016+):** same sign, still beats random at every k=5/10/20%
  (non-isolated), but the effect is **decaying** — roughly ~1%/yr and no
  longer independently significant at any single k (t≈1–1.5, n=118,
  underpowered for an effect this small at this n).
- The registry's single summary figure (mean avoidance alpha 0.163%/mo raw,
  shrunk to 0.148%/mo) carries `n=192`, which the bias checklist ties to the
  **in-sample** count ("n=192 in / 118 holdout") — so this number is most
  likely the in-sample average, not a holdout figure. **No precise holdout
  point estimate is recoverable from the registry** — only the qualitative
  description above (same-sign, beats random at every k, t≈1–1.5, ~1%/yr).
  Flagging this explicitly: an earlier version of this doc mislabeled this
  figure as "holdout-period average," which was wrong.

## Reading

1. **Mechanical avoidance clears its own bar** — the precondition test the
   prereg required before opening any LLM arm. This is the FIRST time the
   house has directly measured that excluding distressed names (not just
   picking winners) adds return, beyond the earlier informal reads (Achilles
   sold-ban, Nemesis veto).
2. **The decay from in-sample to holdout is the honest story, not a footnote.**
   t≈4 collapsing to t≈1–1.5 while staying same-sign at every k is exactly the
   capability-frontier decay pattern the prereg flagged (G2-weak: this is an
   information-processing edge, not a structural constraint, and gets arbitraged
   as it's noticed). The effect is real but small and shrinking — an overlay,
   not an engine.
3. **This measures ONLY the mechanical floor.** The headline question — does an
   LLM veto read deterioration better than a checklist (Arm A vs B)? — is
   untested here by design; it requires live forward reads.

## Reproducibility caveat (added on review)

`run_avoidance_direct.py` prints results to stdout only — it saves no results
file. This doc (and the registry entry it's built from) reflects a summary a
prior session typed into `cache/lab_registry.json`; neither that session's
raw per-cell output nor this one independently re-ran the backtest against
the achilles panel. The numbers above are only as reliable as that prior
recording. If this result is ever load-bearing for a capital decision, it
should be re-run from raw data with the per-k, per-window table saved to a
results JSON (as `gauntlet_v1`/`achilles_pead_gauntlet` did), not taken on
the registry's word alone.

## Consequence (pre-committed, applied)

Mechanical avoidance works → the forward A/B (Arm A LLM veto vs Arm B mechanical)
is now open per the prereg's pre-committed rule. Registry status: `forward_testing`
(started 2026-07-05). **As of this session, zero forward periods have been graded
and zero ghost positions are open** — the status was advanced in the registry but
the actual forward mechanics (LLM veto reads on a live universe, `shared.ghost`
paper entries under `features={"strategy": "avoidance_direct"}`) were never
bootstrapped. That bootstrap — pick a live universe, score it both ways (Arm A
LLM read vs Arm B mechanical distress screen), open the first graded period — is
the next concrete step and is flagged in the backlog for the next session that
has room to build it properly rather than rush it.
