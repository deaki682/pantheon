# Oracle: neglect-screen hardening + catalyst overlay (2026-07-06)

Two follow-ups to the full three-leg verification, both dividends of the ~40
primary-source reads: (1) fold the systematic screen-lies back into the coverage
stage; (2) build the floor+catalyst intersection the event-leg verdict pointed to.

## 1. Neglect-screen hardening

The 27-name verification catalogued the recurring ways a raw net-cash screen
lies. The ones that are STRUCTURAL and COMPUTABLE at the coverage stage are now
gated or flagged in `oracle/neglect_screen.py`; the ones that inherently need the
filing read are documented as precision-stage, honestly.

**Now excluded at the screen (structural disqualifiers):**
- **China/Hong Kong domicile** (`EXCLUDE_LOCATIONS`) — the floor cash carries
  VIE/reachability/governance/fraud risk that makes the discount un-actionable.
  Dropped the ~39 clearly China/HK-*located* names.
- **Crypto/digital-asset treasuries** (`CRYPTO_NAME_MARKERS`) — the "cash" is a
  volatile mark-to-market coin pile, not a hard floor (CYPH's was 91% Zcash).
  Caught by name marker.

**Now flagged (not excluded — the precision read decides):**
- **`investments_heavy`** — when `investmentsc` is >60% of the liquid pile, the
  "cash" may be crypto / structured notes / private stakes / marked securities
  needing a liquidity read. This is the defense-in-depth that catches **AIFA**
  (a China operating shell registered at a US address, so the location gate
  misses it) — its floor is 92% investments, flagged for verification.
- **`recent_dilution`** — shares grew >20% QoQ (from consecutive SF1 quarters) ⇒
  an active ATM/conversion is melting the per-share floor (the TPET/MSAI shape).

**Result:** 323 → **280** candidates, each now carrying quality flags
(34 investments_heavy, 12 recent_dilution, 131 eroding). Cleaner net, same
generous coverage philosophy — the flags guide the precision queue, they don't
prejudge.

**Documented as PRECISION-ONLY (not screenable from Sharadar structured data):**
stale share counts from *post-quarter* conversions/splits (FTH/MSAI/FLNA — vendor
lag, needs the 10-Q cover page); senior preferred / minority interests / holdco
structure (FBIO/AMWL/PXLW — Sharadar SF1 doesn't break these out); multi-class
fully-diluted counts (ARVN/AMWL/KROS pre-funded warrants); binding litigation
reserves (FLNA); open ATMs / going-concern language (filing text); and the
`debt`-includes-leases generosity (MED). The screen catches the structural
disqualifiers; the four-trap gate owns the rest. That is the two-stage thesis.

## 2. Catalyst overlay — floor + catalyst by intersection

Per the event-leg verdict (a catalyst is a bonus on a floor, never a substitute),
`run_oracle_catalyst_overlay.py` intersects the neglect below-floor names with
value-realization catalysts, from two sources:
1. **Form-enumerated SC 13D / 13D-A subjects** over the window (the automated,
   100%-recall net) — sparse in this environment's EDGAR (1 subject), but the
   machine is correct and populates against live EDGAR.
2. **Curated live catalysts** surfaced by the verification pass (a strategic
   review, a proxy fight) that the daily-index 13D enumeration doesn't capture.

**Output — the 2 genuine floor+catalyst leads in Oracle's universe right now:**

| Ticker | Floor | Catalyst |
|---|---|---|
| **NNDM** | net cash, ~26% below | LIVE Murchinson activist proxy fight (DEFC14A; EGM 2026-07-31) opposing a cash-consuming biotech-pivot M&A |
| **FULC** | net cash, ~22% below | LIVE Leerink strategic-alternatives review (engaged 2026-05-31 after an 85% RIF) |

Both were verified **WATCH** on floor-thinness in the neglect pass — but the LIVE
catalyst is what makes them the most interesting non-FUND names: a floor that
something is *actively working to unlock*, unlike a value trap (RVP's founder
poison-pill) or a floorless catalyst (the 14 hard_catalyst kills). They are
**priority-watch leads**, not yet book positions — the caveat is real (NNDM's
pile could be spent on the very M&A the activist opposes; FULC could reverse-merge
the cash away), so each needs the four-trap gate + an Item-4/process read before
funding. Recorded to `cache/oracle_catalyst_overlay.json`.

**The standing use:** run the overlay every session; a neglect FUND/WATCH that
picks up a fresh friendly 13D or a strategic-review announcement is the strongest
convex shape Oracle can build — promote it from watch to a dossier when the
catalyst turns the thin floor into a forced re-rating.
