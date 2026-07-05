# Portfolio allocation — the ~$19k rearrange (2026-07-05, operator directive)

The operator is liquidating the account to cash (manually, during Monday
2026-07-06's market) and redeploying once cash settles (**T+1 → Tuesday
2026-07-07**). This is the target structure the Tuesday god-sessions execute
against. Buying power is fluid until Monday's selling finishes, so **treat these
as targets that scale proportionally to actual settled cash**, not fixed dollars.

## Target allocation (on ~$19,000)

| Sleeve | Target | % | Rationale |
|--------|--------|---|-----------|
| **Hermes** | $4,000 | 21% | ARMED 2026-07-05. Best-rated god; the one uncorrelated diversifier (merger-arb ≈ deal-completion, not market direction); fastest clean LLM-lift verdict; contractual bounded floor. |
| **Plutus** | $4,000 | 21% | The only backtest-supported god (gauntlet_v2 net-issuance, two-regime + 2× cost). The proven anchor. |
| **Proteus** | $3,000 | 16% | Live discretionary + the seasonal PEAD release valve. High variance, now bounded by the conscious-concentration gate + 40% breaker. |
| **Oracle (reframed)** | $2,000 | 11% | Convex deep-research. Probe-size and GATED — the reframe's own rule: fund small until the dossiers beat the screen (LLM-lift), then concentrate + scale. |
| **Oracle legacy cohort** | ~$2,000 | 11% | CXT/HDSN/J/PSN/VITL, frozen/held. Hold-or-sell is the operator's Monday call. |
| **Cash reserve** | $4,000 | 21% | Dry powder EARMARKED to scale into the first god whose A/B validates — the reward side of the self-improving allocation. Not idle; not yet earned. |

Anchor on the two strongest (Hermes + Plutus = 42%); meaningful-but-gated stakes
to the high-ceiling unproven engines (Proteus, Oracle); a reserve to reward
proven edges. Every sleeve is bounded (rails), so full deployment still cannot
blow up the account.

## If the legacy cohort is SOLD Monday
Its ~$2,000 folds into the **cash reserve → ~$6,000 (32%)**. Default: hold as
reward-powder; do NOT force-deploy into unproven gods just because it's free.
Alternative (operator's call): split into Hermes/Plutus, the two strongest.

## Tuesday execution sequence (only after cash settles)

1. **Reconcile.** Confirm actual settled buying power; scale the targets
   proportionally if it isn't ~$19k. No god buys with unsettled proceeds (T+1).
2. **Fund the sleeves** to target: Hermes already $4k; top Plutus → $4k, Proteus
   → $3k, fund the reframed Oracle sleeve → $2k (clears its pending_funding).
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
