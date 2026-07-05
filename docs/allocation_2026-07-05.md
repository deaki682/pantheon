# Portfolio allocation — the ~$19k rearrange (2026-07-05, operator directive)

The operator is liquidating the account to cash (manually, during Monday
2026-07-06's market) and redeploying once cash settles (**T+1 → Tuesday
2026-07-07**). This is the target structure the Tuesday god-sessions execute
against. Buying power is fluid until Monday's selling finishes, so **treat these
as targets that scale proportionally to actual settled cash**, not fixed dollars.

## Target allocation (on ~$19,000)

Per the portfolio mandate (docs/portfolio_mandate_2026-07-05.md): a growth book
headlined by the experiments, anchored by the proven engine, no dead cash.

| Sleeve | Target | % | Role / rationale |
|--------|--------|---|------------------|
| **Plutus** | ~$5,000 | 26% | **Growth anchor** — the only backtest-supported god (gauntlet_v2 net-issuance) AND large-cap equity, so it carries bull participation + a proven edge. The spine. |
| **Hermes** | $4,000 | 21% | **Headliner** — ARMED 2026-07-05; best-rated; the one uncorrelated diversifier; fastest LLM-lift verdict; contractual bounded floor. |
| **Proteus** | $4,000 | 21% | **Headliner** — live discretionary + seasonal PEAD; chases growth, can hold beta; bounded by the conscious-concentration gate + 40% breaker. |
| **Oracle (reframed)** | $3,000 | 16% | **Headliner** — convex deep-research, high ceiling. Deploys as it sources convex names (RNA/VTSI/ARVN/SMHI/ALCO + more); the rest waits in-sleeve. Per-name cap keeps it disciplined. |
| **Cash** | ~$1–2,000 | ~8% | **Operational buffer only** — not a strategic reserve. Growth mandate: no dead cash. |
| **Oracle legacy cohort** | ~$2,000 | (sep.) | CXT/HDSN/J/PSN/VITL, frozen/held. Hold-or-sell is the operator's Monday call. |

Experiments collectively headline (~58%); the proven engine anchors (~26%); cash
is a working buffer, not a fifth of the book. Fully deployed, growth-oriented,
still un-blow-up-able (every sleeve keeps its rails).

## If the legacy cohort is SOLD Monday
Its ~$2,000 does NOT sit in cash (growth mandate). Default: split into **Plutus
(the growth anchor) and Hermes (the armed headliner)**, or let Oracle absorb it
if it has sourced more convex names by then. Operator's call at execution.

## Tuesday execution sequence (only after cash settles)

1. **Reconcile.** Confirm actual settled buying power; scale the targets
   proportionally if it isn't ~$19k. No god buys with unsettled proceeds (T+1).
2. **Fund the sleeves** to target: Hermes already $4k; fund Plutus → ~$5k,
   Proteus → $4k, the reframed Oracle sleeve → $3k (clears its pending_funding).
3. **Each god deploys on its own session, within its sleeve + rails:**
   - `/hermes` — scan small/mid cash-merger targets, LLM break-risk read, buy Arm
     A (real), paper Arm B, log LLM-lift. Min-spread + per-deal cap + break-stop.
   - `/plutus` — first settled-cash rebalance into the net-issuance basket
     (deluxe stack; pure-N50 control tracked in parallel).
   - `/proteus` — one discretionary session; every position earns its place.
   - `/oracle` — enter the top convex names (RNA/VTSI/ARVN/SMHI/ALCO per the
     2026-07-05 bank), size within the per-name cap; seed the live A/B.
4. **Reserve stays in cash** until an A/B reports; then scale the winner.

## Disciplines that do not bend
- Every sleeve keeps its rails (per-name/per-deal caps, break-stops, 40%
  breakers, conscious-concentration gate). Account-level: `KILL_SWITCH` liquidates all.
- Oracle stays probe-size until LLM-lift is positive and material.
- The cash reserve is deployed by EVIDENCE (an A/B verdict), not impatience.
