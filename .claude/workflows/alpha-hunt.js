export const meta = {
  name: 'alpha-hunt',
  description: 'Standing adversarial alpha reconnaissance: domain fan-out -> graveyard-checked synthesis -> kill-attempt verification. The lab runs this every session (delta weekly, full quarterly).',
  whenToUse: 'Invoked by /lab each session (mode=delta weekly, mode=full quarterly or on operator request). Recon only — it never tests data, never ticks hypotheses_ever, never slugs. Survivors go to the backlog for the ratchet.',
  phases: [
    { title: 'Recon', detail: 'agents sweep the alpha landscape (full: 14 domains; delta: what changed since last hunt)' },
    { title: 'Synthesize', detail: 'dedupe, cross-check vs the repo graveyard, rank by the barriers framework' },
    { title: 'Verify', detail: 'adversarial kill-attempt per top candidate; only survivors reach the backlog' },
  ],
}

// ---- args: { mode: 'full' | 'delta', focus?: string } ----
const MODE = (args && args.mode) === 'full' ? 'full' : 'delta'
const FOCUS = (args && args.focus) ? `\nOPERATOR FOCUS THIS RUN: ${args.focus}` : ''

const REPO = '/home/user/pantheon'
// Every agent reads the LIVE house record from the repo — never a frozen summary.
// (Lesson from the 2026-07-05 run: a frozen context let synthesis miss a terminal
// refutation, ipo_lockup_reversion, that the repo record would have caught.)
const CTX = `You are hunting alpha-strategy candidates for Pantheon, a long-only US-equity book (~$19k) at Robinhood: ETFs ok (inverse ETFs express shorts), fractional shares ok; NO options, NO leverage, NO direct shorting, NO futures. Small size is an ADVANTAGE (capacity-constrained edges in-scope; scale-needing edges out).

MANDATORY FIRST STEP — read the live house record at ${REPO} before any judgment:
- docs/RESEARCH_LEDGER.md (every completed study + verdict — THE GRAVEYARD; anything refuted there is terminal),
- docs/house_view_llm_edge_2026-07-05.md (the barriers framework: avoid text-processing edges LLMs are dissolving; camp on structural forced-seller / capacity / patience / execution barriers; ride the capability frontier briefly),
- docs/RESEARCH_BACKLOG.md (already-queued items — those are known, not "missed"),
- cache/lab_registry.json if present (slug statuses; refuted slugs are terminal),
- CLAUDE.md "The Gods" (what is already live/tested: net-issuance+gross-prof+cash-op factors SUPPORTED; merger-arb, convex forced-seller value, discretionary, PEAD-in-test).

THE 5 GATES a candidate must pass: G1 tape (price-only = dead), G2 constraint (a NAMED forced counterparty + the document that binds them), G3 capacity-inversion (works small, not at scale), G4 arithmetic (contractual/mechanical payoff beats a forecast), G5 power (>=20 tradable events/12mo).

Your job: surface GENUINELY UNEXPLORED, DURABLE-or-FRONTIER, GATE-PASSING opportunities. Reject graveyard relabels and crowded text edges. Do REAL web research (2024-2026 evidence, decay checks). Be exhaustive within scope; be honest — an empty list beats an invented finding.${FOCUS}`

// Loose schema (lesson: an over-strict schema killed one verify agent via retry cap)
const RECON_SCHEMA = {
  type: 'object',
  properties: {
    domain: { type: 'string' },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          thesis: { type: 'string' },
          barrier_type: { type: 'string' },
          capacity_fit: { type: 'string' },
          likely_dead_or_known: { type: 'boolean' },
          gate_reads: { type: 'string' },
          score: { type: 'number', description: '0-5 unexplored-x-durable' },
          why_missed: { type: 'string' },
        },
        required: ['name', 'thesis', 'score'],
      },
    },
  },
  required: ['domain', 'candidates'],
}

const FULL_DOMAINS = [
  ['Structural forced-sellers', 'index recon flows, tax-loss selling, redemptions/gating, forced deleveraging, downgrade-forced sales, mandate exclusions, CEF liquidations'],
  ['Mergers & deals', 'cash/stock merger-arb variants, SPAC redemption floors, appraisal, busted deals, topping bids, collars, going-private'],
  ['Spinoffs & restructurings', 'spinoff PARENT drift, split-offs, rights offerings, Dutch/odd-lot tenders, stubs, exchange offers'],
  ['Distressed & capital structure', 'post-BK-emergence equity, fallen angels, distressed converts/preferreds, liquidations, NOL shells'],
  ['Unexplored fundamentals', 'intangible-adjusted value, capital-allocation quality, earnings-quality variants, net-payout, expectations gaps'],
  ['Text/document frontier', 'full-docket synthesis, call tone/evasion, 10-K language change, litigation reads, patents, FDA filings, 8-K exhibits, proxy reads'],
  ['Alternative data', 'satellite/foot-traffic, app/web traffic, shipping, card panels, job postings, supply-chain maps'],
  ['Microstructure & flow', 'ETF create/redeem dislocations, recon windows, gamma/pinning, lockups, short-interest mechanics, buyback windows'],
  ['Analyst & revisions', 'revision momentum, dispersion, PEAD variants, initiations, retail flows, options-implied sentiment'],
  ['International & niche vehicles', 'ADR discounts, CEF discount+catalyst, BDCs, REIT NAV gaps, royalty trusts, holdco discounts, dual listings'],
  ['Cross-asset carry & premia', 'commodity roll/carry, duration carry, FX carry via ETFs, VRP (NOTE: short-vol is anti-convex — flag, do not propose), term structure'],
  ['Insider, ownership & activism', 'insider LANGUAGE/context, 13D escalation outcomes, 13F de-crowding, ownership breadth, executive transitions'],
  ['Calendar & seasonality', 'turn-of-month, FOMC drift, rebalance dates, tax-January in micro-caps — only with a STRUCTURAL cause; most are G1-fail'],
  ['Frontier & agentic', 'multi-source cross-referencing, cross-document entity linking, regulatory-change anticipation, thematic emergence'],
]

const DELTA_DOMAINS = [
  ['What changed: events & filings', 'NEW since the last hunt (~7 days): announced deals, tenders with odd-lot carve-outs, index recon announcements, Ch.11 emergences, spinoff Form 10s, forced-seller situations. Concrete, dated, tradable-now candidates.'],
  ['What changed: market structure & regime', 'new dislocations this week: CEF discount blowouts, ADR gaps, sector forced rotation, vol regime shifts creating structural (not directional) opportunities.'],
  ['What changed: capability frontier', 'new model/tooling capabilities or newly-digitized data sources since the last hunt that open a processable-into-signal window the fleet is not exploiting yet.'],
  ['Decay watch on OUR live edges', `read the live A/B states at ${REPO} (cache/hermes_ab.json, cache/oracle_ab.json if present) + recent evidence on merger-arb spreads and small-cap value crowding: is any HOUSE edge showing decay/crowding that should trigger rotation?`],
]

const DOMAINS = MODE === 'full' ? FULL_DOMAINS : DELTA_DOMAINS

phase('Recon')
log(`alpha-hunt mode=${MODE}: ${DOMAINS.length} recon domains`)
const recon = await parallel(DOMAINS.map(([domain, scope]) => () =>
  agent(
    `${CTX}\n\nYOUR DOMAIN: **${domain}**\nScope: ${scope}\n\nRead the house record first, then sweep your domain. Return candidates with honest scores; flag known/dead ones (likely_dead_or_known=true).`,
    { label: `recon:${domain}`, phase: 'Recon', agentType: 'general-purpose', schema: RECON_SCHEMA }
  )
)).then(rs => rs.filter(Boolean))

const all = recon.flatMap(r => (r.candidates || []).map(c => ({ ...c, domain: r.domain })))
const promising = all.filter(c => !c.likely_dead_or_known && (c.score || 0) >= 3)
log(`Recon: ${all.length} mapped, ${promising.length} promising`)

phase('Synthesize')
const SYNTH_SCHEMA = {
  type: 'object',
  properties: {
    shortlist: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, thesis: { type: 'string' }, domain: { type: 'string' },
      barrier_type: { type: 'string' }, why_missed: { type: 'string' }, rank_score: { type: 'number' },
    }, required: ['name', 'thesis', 'rank_score'] } },
    landscape_note: { type: 'string' },
  },
  required: ['shortlist', 'landscape_note'],
}
const synth = promising.length === 0
  ? { shortlist: [], landscape_note: 'No promising candidates survived recon this run.' }
  : await agent(
      `${CTX}\n\nSynthesis: here are ${promising.length} recon candidates:\n${JSON.stringify(promising, null, 1)}\n\nDedupe; CROSS-CHECK EVERY ONE against the repo graveyard (docs/RESEARCH_LEDGER.md + lab registry — read them, do not trust the recon agents); reject relabels and already-queued backlog items unless the recon adds something material. Rank survivors (durability > frontier > rest; G-gates; capacity-fit; LLM-reader fit). Return top <=8 + an honest landscape_note (fertile vs barren, biggest miss).`,
      { label: 'synthesize', phase: 'Synthesize', schema: SYNTH_SCHEMA }
    )

phase('Verify')
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    verdict: { type: 'string', enum: ['GOD_CANDIDATE', 'LAB_HYPOTHESIS', 'REJECT'] },
    note: { type: 'string' },
    next_step: { type: 'string' },
    gate_summary: { type: 'string' },
  },
  required: ['name', 'verdict', 'note'],
}
const top = (synth.shortlist || []).slice(0, 8)
const verified = top.length === 0 ? [] : await parallel(top.map(c => () =>
  agent(
    `${CTX}\n\nAdversarially VERIFY (try to KILL) this candidate:\n${JSON.stringify(c, null, 1)}\n\nRead the repo record yourself (ledger, registry, backlog). Real web research on decay/crowding. Walk G1-G5 concretely. Is capacity real for ~$19k long-only no-options? Verdict: GOD_CANDIDATE (survives everything), LAB_HYPOTHESIS (needs the ratchet), REJECT (dead/relabel/crowded/capacity-fail/already-queued). Default skeptical; give the concrete next step.`,
    { label: `verify:${c.name.slice(0, 40)}`, phase: 'Verify', agentType: 'general-purpose', schema: VERDICT_SCHEMA }
  )
)).then(vs => vs.filter(Boolean))

return {
  mode: MODE,
  domains: recon.length,
  mapped: all.length,
  promising: promising.length,
  landscape_note: synth.landscape_note,
  verified,
  god_candidates: verified.filter(v => v.verdict === 'GOD_CANDIDATE'),
  lab_hypotheses: verified.filter(v => v.verdict === 'LAB_HYPOTHESIS'),
  rejected: verified.filter(v => v.verdict === 'REJECT').map(v => ({ name: v.name, why: v.note.slice(0, 200) })),
}
