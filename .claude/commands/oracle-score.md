# /oracle-score — DEPRECATED, disabled 2026-07-04

**This command is disabled and must not be used.** It predates the
cohort model (implemented 2026-06-29) and ran a score-rotation trade
path — incumbent-vs-challenger scoring, `rotation_decision`,
`exit_signal` bull_hit/bear_hit trims — that directly contradicts
Oracle's current strategy. `oracle.md`/`CLAUDE.md` define Oracle as
buy-and-hold-to-thesis-break and explicitly list "a new dossier scored
higher" and "rank drift of any kind" as PROHIBITED exit reasons. This
command's own header claim ("runs steps 7-12 of /oracle") is also
false under the current runbook — those steps are research,
calibration-only rescoring, and cohort logic, none of which perform
rotation.

Found via the 2026-07-04 LLM integration audit
(`docs/pantheon_llm_integration_audit_2026-07.md`, finding #1, HIGH
severity, CONFIRMED): if this command were ever invoked against the
live cohort, it would place real broker orders (`ORACLE_LIVE=true`)
that violate the strategy's core discipline.

## Steps

1. **Refuse to run.** Print: "`/oracle-score` is deprecated and
   disabled — Oracle runs exclusively via `/oracle` (cohort model).
   See docs/pantheon_llm_integration_audit_2026-07.md finding #1."
   Take no other action. Do not load state, do not compute rotation
   decisions, do not place orders.

Use `/oracle` for the full cycle (research → cohort logic → thesis-
break checks → journal → persist) or `/oracle-research` for a
dossiers-only accumulation pass. Neither performs rotation on an
active cohort.
