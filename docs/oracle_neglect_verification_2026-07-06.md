# Oracle neglect leg — full cohort verification (2026-07-06)

The precision stage run to completion on the neglect leg's core cohort. This is
the "best of thousands" question answered with primary-source evidence, not a
ranked list: of the whole-universe below-floor screen, **how many names are
genuinely fundable hard-floor convex bets once you read the actual filings?**

## Method

The neglect screen surfaced 323 below-floor names. Triaged to the strongest
convex family — **below net cash, US-domiciled, ≥10% screen discount** (27 names
incl. INVE/MED verified earlier) — then ran **one primary-source verifier per
name in parallel**: each read the actual 10-Q/10-K, reconciled the share count,
separated real debt from leases, checked for preferred/minority claims and active
ATM dilution, and returned a four-trap FUND/WATCH/KILL verdict.

## Result: 4 FUND · 11 WATCH · 12 KILL

**The headline number: ~15% of the net-cash sub-cohort (4 of 27) — roughly 1% of
the raw 323-name screen — are genuinely fundable.** That is the honest measure of
how much real signal the screen carries, and it is exactly why the two-stage
machine exists: the screen alone would have "bought" a dozen traps.

### FUND — verified hard floor + margin of safety (added to the book)

| Ticker | Price | True disc. | Why it clears |
|---|---|---|---|
| **XBIT** | $2.30 | ~37% (25% FD) | $115.5M cash, zero debt/leases/preferred, all options OTM; *recurring* capital-return history (2 tenders + special dividend). Melts ~$36M/yr. |
| **SEER** | $2.02 | 25-49% | $219.5M liquid net cash vs $111M cap, *buying back stock*; screen understated it (missed $52.8M LT Treasuries). Poison pill caps takeover. |
| **LAB** | $0.91 | ~20% FD | $526M net cash vs $356M cap; feared Casdin/Viking preferred *already converted* (no senior stack); post-SomaScan divestiture. |
| **INVE** | $2.61 | ~29% FD | $124.5M cash, zero debt, post-divestiture cash box (verified earlier). |

All four are **bounded-floor value bets, not conviction catalyst plays** — every
one has a hard, primary-source-verified debt-free floor, but the floor *melts*
(clinical/tools burn) and the catalyst is undated. Sized accordingly. Book now
holds **5 verified names** (these four + JOF, the forced-seller CEF), ranked by
convexity: INVE ≈ XBIT > SEER > LAB > JOF.

### KILL — the discount was an artifact (12)

The screen's deep discounts were, on inspection, mostly illusions — and the
*kinds* of illusion are the systematic lessons:

- **Stale share count** — FTH (preferred converted 6/2026, 1.34M→25.78M sh; trades at a *premium*).
- **Holdco phantom** — FBIO ("$203M net cash" is total equity; one-time PRV windfall behind $85.7M senior preferred + $40M minority + $98M payables → common claim ~zero).
- **Gross-cash / basic-share double count** — RNA (22% *premium* FD), ARVN, AMWL (priced off Class A only → 4-6% premium).
- **Liability the screen ignored** — FLNA (former Cassava; a binding $32.75M securities settlement → 33% premium), MED (leases mislabeled as debt).
- **Crypto/illiquid "cash"** — CYPH (91% Zcash, halved last quarter), AIFA (China structured notes + $20M *defaulted* loans → hard net cash −$33.5M).
- **Dilution-financed / melting floor** — TPET (100% fresh ATM proceeds under an open $65M ATM), MSAI ($60M ATM, 6× cap), LIDR (serial ATM ~doubled the count), LPCN ($50M ATM below NCAV).

### WATCH — real cash, but the floor melts / no catalyst / discount thin (11)

KTTA (62% below, verified — but burns with no catalyst + listing risk), PHUN
(~54% below a hard floor — but new CEO + $200M shelf), PXLW (China sub sold, clean
$55M — but melts 33%/yr), RVP (real 27-31% — but founder poison pill makes cash
*unreachable*), VGAS (symmetric NCI, ~20% real — but pre-revenue melt + sponsor
take-under), KROS (clean $281M — but ~10% disc, tender already fired), FULC (live
Leerink strategic review — but ~10% FD + reverse-merger-away risk), PEW/MYPS/ARVN
(discount evaporates fully-diluted), NNDM (thin ~13%, pile under M&A threat,
guarded only by a live Murchinson proxy fight, EGM 7/31).

## Systematic screen lessons (feed back into the coverage stage)

The verification pass exposed the recurring ways a raw net-cash screen lies —
each now a known correction the precision read applies, and candidates for
tightening the screen itself:

1. **Stale share count** post-conversion/reverse-split (the marketcap vendor lags): FTH, MSAI, FLNA.
2. **Basic vs fully-diluted / multi-class**: ARVN, AMWL, KROS — pre-funded warrants and second share classes erase the discount.
3. **`debt` includes leases** (documented earlier): MED.
4. **Senior claims the screen can't see**: holdco minority interests (FBIO, AMWL, PXLW pre-sale), senior preferred liquidation prefs, binding litigation settlements (FLNA).
5. **"Cash/investments" that isn't hard cash**: crypto treasuries (CYPH), China structured notes + defaulted loans (AIFA), volatile equity stakes (NNDM).
6. **Dilution-financed floors**: an open ATM below NCAV means the "floor" is being sold into the market (TPET, MSAI, LIDR, LPCN).

None of these is fixable by loosening or tightening a threshold — they require
reading the filing. That is the two-stage thesis, now measured: **coverage is a
generous net; the primary-source gate is what turns it into a book, and it says
NO ~85% of the time.**

## Recorded

- `cache/oracle_convex_dossiers.json` — INVE, XBIT, SEER, LAB added (pool now 5 verified: + JOF). Persisted to `claude/live`.
- `cache/oracle_ab.json` — all four logged as fresh-launch A/B selections.
- `cache/oracle_neglect_verification_2026-07-06.json` — the full 27-name verdict audit trail.
