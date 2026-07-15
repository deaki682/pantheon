# B2B micro-tool niche hunt — findings (validated-demand hunt)

Five parallel research passes, each with one rule: **no niche survives without evidence** — a real
product charging real money (proven willingness-to-pay) + operators actually complaining (pain) + a
check that no good *free* tool already kills it. Scores are 1–5 (5 = best risk-adjusted opening).

## The meta-finding
**"Boring mandatory compliance document" is the most-mined vein in micro-SaaS, not an underserved one.**
Nearly every niche had either a free tool (often free because a government portal or an incumbent gives
it away to own the network) or a cheap entrenched player already in the slot. The moat can't be "I built
the doc well." Survivors all had a *structural* reason incumbents can't take the position: a fresh law,
a privacy wedge cloud players can't copy without killing their own model, or fragmentation free tools
don't cover.

## Shortlist (survivors)
| Score | Niche | Why it survived | The catch |
|---|---|---|---|
| **4** | **Local-first superbill generator** (cash-pay/OON clinicians; IBCLC beachhead) | WTP proven (Superbilled $15/mo, Reimbursify $99/mo, Mentaya ~5%/claim); **no-cloud→no-BAA→pay-once** wedge unoccupied & un-copyable by subscription incumbents; perfect fit for our offline+license stack; low maintenance | Incumbents also track claims; nobody's proven WTP for the *stripped private one-time* version → **the thing the landing test resolves** |
| **4** | Tip-pool / "tronc" allocation (restaurants/bars/salons) | Fresh law forces it (UK 2024 + US 2025); money-movement = sticky/recurring; UK incumbents prove money; US self-serve gap | Real backend SaaS near pay/taxes — not our client-side stack; more build/maintenance/liability; WTP is estimate-based |
| **4** | Process-server affidavit generator | Rejected affidavit = no payment (tight money linkage); state/county fragmentation defeats free single-jurisdiction PDFs; incumbents charge $25–50/affidavit or gate behind $49–99/mo suites | Small buyer slice (solo/occasional); per-county form maintenance |
| **3.5** | IBCLC lactation superbill + insurance-appeal helper | ACA mandates coverage yet IBCLCs stuck OON; denials repeat 3–4×; no IBCLC-specific tool → ideal **beachhead for the superbill** | Small population (but passionate, unserved) |
| **3** | HVAC/R refrigerant logs (EPA 608 / AIM Act) | 2026 rule 3×'s mandated population; single federal ruleset (low maintenance); strongest "done by hand" signal | Being land-grabbed now — you'd be entrant #9 |
| **3** | Restaurant HACCP / temp logs · food-truck permit tracker · septic inspection · pool/spa chemical logs · labor-law posters | Each mandatory + real WTP | Each blocked: HACCP moving to hardware; food-truck = one-time buyers + hyperlocal rules; septic/well = free mandatory state portals + county-form treadmill; pool = free templates + $2/pool incumbent; posters = physical-fulfillment moat |

## Kills (well-served or free — do not build)
- **All of construction** — certified payroll (free DOL WH-347 tool + CertifiedPayrollPro $49/mo), AIA
  pay apps (PayAppPro $7.99, free Excel templates), lien waivers (Levelset free + legal-liability
  treadmill), COI tracking (bcs free ≤25, Certificial free ≤5, funded incumbents above), change orders
  (free templates + generic e-sign + Extracker free). Territory = pass.
- **Micro-professions** — notaries ($9–12/mo, happy users), home inspectors (Spectora just consolidated),
  PIs, bail bondsmen, court reporters — all served cheap. Tax §7216 consent (3/5) bundled by suites.
- **Skilled trades** — fire/NFPA (10+ funded incumbents + free Joyfill), pest (GorillaDesk $49/mo + free
  university apps), gas/electrical CP12/EICR (free generator w/ 10k+ engineers), chimney (ChimSpect
  $135–450/mo), well-water (free state portals + free lab reports). Elevator inspection is the *most
  under-competed* but tiny TAM (ElevateLog already there).
- **Health/wellness** — gym waivers (WaiverForever free), massage SOAP (Noterro/ClinicSense), med-spa
  consent (HIPAA-storage, can't go client-side), vet certs, standalone Good Faith Estimate (free
  templates — but a good *bundle* sweetener).

## Proven-money patterns (from IndieHackers / Acquire.com / Flippa)
- Vertical ops tool for ONE unsexy trade at ~$75/mo recurs well (niche kitchen-appliance CRM $6.7k MRR /
  89 customers; MassageBook $60k MRR). Domain specificity is the moat, not features.
- Compliance docs work in two shapes: one-time **kits $149–449**, or recurring **renewal/deadline
  trackers $15–25/mo with near-zero churn**. The tracker wins for a solo.
- "Law says you must" = forced adoption, and incumbents are often *physical* (labor posters ship paper)
  or *enterprise* — leaving a software-only SMB gap.
- Money-movement / daily-workflow embedding lowers churn (highest MRRs are inside the money or the daily
  routine).
- Boring low-churn tools sell at ~3.9x profit on Acquire.com — a real exit, not just income.

## Decision
Bet: **local-first superbill, IBCLC beachhead.** Best fit for our proven capability, proven-adjacent WTP,
a structural (not cosmetic) privacy moat, low maintenance, and a sharp beachhead that solves discovery.
**Validate before building** — see `OUTREACH.md`. The exact WTP for the stripped/private/one-time version
is the one open question, and the landing test answers it for the price of a domain.
