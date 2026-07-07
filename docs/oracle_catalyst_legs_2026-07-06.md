# Oracle catalyst legs — full sweep + gauntlet (2026-07-06)

The fresh blind Oracle run produced **1 FUND (STHO) / WATCH tier** from the
NEGLECT + asset-revaluation legs. This is the companion sweep of the two EVENT
legs the runbook mandates every session — **forced_seller** and
**hard_catalyst** — plus the **catalyst-overlay intersection**. The measured
prior going in (docs/oracle_event_legs_verification_2026-07-06.md): the event
legs are OVERLAYS on a floor, not standalone nets (forced_seller 1/8 fundable,
hard_catalyst 0/14). This session re-confirmed it, at full form-enumeration
recall, on a live window.

**Window:** 2026-04-06 .. 2026-07-06. **Sourcing:** `run_oracle_sourcing.py`
(counts `forced_seller_tradable=21, hard_catalyst_tradable=1,
hard_catalyst_review=13, neglect=280`) + `run_oracle_catalyst_overlay.py`.

## Result: ZERO new FUND. STHO remains the single FUND.

### 1. Catalyst-overlay intersection (floor ∩ catalyst) — the runbook's primary use
- **forced_seller ∩ neglect-below-floor = 0.** None of the 21 tender names sits
  below a countable floor.
- **hard_catalyst (GNK) ∩ neglect = 0.** GNK is not below a balance-sheet floor
  (activists target undervalued-vs-earnings-power, a different mispricing).
- **strategic_review ∩ neglect = 1 → BTU** (only intersection; gauntleted below → KILL).
- **form-enumerated SC 13D ∩ neglect floors = 0** — the environment's EDGAR
  daily-index 13D channel is a data desert (1 distinct SC 13D subject in the
  whole window). Machine is correct; the pond is empty here.
- **curated live-catalyst ∩ floor = NNDM, FULC** — both already VERIFIED **WATCH**
  from the prior pass (thin/eroding floors; governance-only or reverse-merge-away
  risk). No change.

### 2. forced_seller tradable (21) — triage: 0 fundable
The SC TO-I net surfaces exactly what it was measured to surface — funds,
preferred, warrants, and administrative buybacks, not neglected floors:
- **Preferred:** NHPAP, PRIF-PL, GPUS-PD — not common.
- **Warrants:** ZCARW, RCKTW — not common.
- **CEF/BDC at-NAV tenders:** EIIA, EVV, EFR, EVF, PGIM, FRBP — tender at NAV,
  arb-thin, no operating floor. (JOF, the known recurring-common-conditional-tender
  CEF, was already surfaced/verified — the rare good shape, no change.)
- **Foreign F-shares:** LAAOF (Li Auto), BCDRF (Santander) — unreachable.
- **Megacap odd-lot:** V (Visa) — administrative, no floor thesis.
- **Operating-company issuer tenders, quick-triaged on a fundamentals pull — all above/without a floor:**
  - SCHL (Scholastic) $990M, P/B 1.16, profitable — routine buyback, no floor.
  - EXFY (Expensify) $171M, P/B 1.18, cash-burning — above book.
  - RGNX (REGENXBIO) $749M, **P/B 32.5** — clinical biotech, no book.
  - OPTU (Optimum/Altice) $466M, **P/B −0.11** — negative equity, insolvent stub.
  - RBNE (Robin Energy) $4.9M, P/B 0.10 — **Panagiotidis serial-dilution shipping
    shell**, −97% YTD (the dilution trap the screen flags).
  - HTT (High Templar, ex-Qudian) $413M, P/B 0.25 — **China VIE, unreachable floor.**

### 3. hard_catalyst GNK (Genco Shipping) — gauntlet → KILL
The "activist 13D" (19 filings) is **Diana Shipping (DSX)** running a **hostile,
below-NAV all-cash tender at $24.80** — a TO-T to seize control, NOT a friendly
value-realization campaign. Genco's board rejected it; **shareholders re-elected
all six directors (~90% of non-Diana shares) at the 2026-06-18 meeting** — the
raid was DEFEATED. Stock is pinned at the dead bid (~$24.77 ≈ NAV), having run
$13.55→$27.25 as the bid emerged. Floor is cycle-peak vessel NAV (SOFT; peers
trade ~20% below NAV absent a deal). **Traps #3 (hostile TO-T) + #4 (catalyst
fired) + soft cyclical floor.** Accessions: 13D `0001104659-23-130212`; amend
cluster `0001104659-26-054931`..`-079410`; Q1-26 8-K `000114036126019316`.

### 4. strategic_review BTU (Peabody Energy) — gauntlet → KILL
The `strategic_review` keyword hit is **deal-termination noise on a DEAD deal** —
the Anglo American steelmaking-coal acquisition, **terminated Aug 2025** after the
March 2025 Moranbah North (Centurion) ignition triggered a MAC. **No sale,
breakup, going-private, or activist self-review of BTU exists** — the 8-K's
"value creation" text is capital-return boilerplate. The "22% below tangible
book" floor is **92% net PP&E** — coal mines at cost on a company **currently
losing money** (PE −22.67), with **$878.6M reclamation/ARO** off the face stack;
`commodity_dependent` + `cost_overstates` both fire → floor melts in the thermal
decline. Catalyst already fired AND reversed: $30.68→$41.14 (Mar 2026)→$22.66,
a full round-trip. **SOFT floor, no catalyst, heavily covered.** Accessions:
FY2025 10-K `0001064728-26-000006`; Anglo termination 8-K `0001064728-25-000122`.

## The lesson (crystallized)

Floors are everywhere — the panel screened **280 names below a countable floor**.
Catalysts that are simultaneously **real, friendly, dated, AND sitting on a hard
floor** are vanishingly rare: run at full recall on a live quarter, the two event
legs + the overlay produced **not one fundable intersection.** The event net's
job is to catch the rare floor-with-a-live-unlock (the STHO/JOF shape), not to
manufacture theses from catalysts alone. This is why NEGLECT is the spine and the
event legs are overlays-by-intersection — reconfirmed, not just asserted.

**Book unchanged: 1 FUND (STHO) / WATCH tier. No orders (Oracle pending_funding).**
