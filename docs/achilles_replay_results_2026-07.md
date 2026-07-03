# Results: reaction-direction gate replay (Achilles/PEAD)

Graded 2026-07-03 per the frozen terms of
`docs/achilles_prereg_reaction_gate.md`. One shot, no re-cuts. This doc
is the permanent record; the full per-event table lives in the session
archive (`achilles_gate_results.json`).

## Population and sample

- Catalog: **23,688** Item 2.02 earnings 8-Ks across **8,006** issuers,
  2025-01-02 .. 2026-05-29, from EDGAR submissions records, 0 fetch errors.
- Sample: 600 events drawn with the pre-committed seed
  (`random.Random(20260703).sample`, population sorted by
  filed/CIK/symbol before the draw).
- Disposition: **293 graded** (137 rewarded, 156 sold),
  **262 excluded-lukewarm** (reaction between −3% and +3% — his gate
  doesn't trade those), **45 unpriceable** (42 symbols, reported below,
  none substituted).

## Headline (all-cap)

5-day excess return vs IWM, entry next open after the reaction day:

| Group | n | mean excess | t |
|---|---|---|---|
| Rewarded (reaction ≥ +3%) | 137 | **−0.60%** | −0.96 |
| Sold (reaction ≤ −3%) | 156 | **−1.60%** | **−2.27** |
| Spread (rewarded − sold) | | **+1.00%** | 1.07 |

**Verdict under the frozen rule: INCONCLUSIVE.** Validation required
rewarded-mean > 0 and spread t ≥ 2 — neither held. Formal refutation
required n ≥ 150 rewarded events; we graded 137.

## Pre-registered small/mid slice (his actual pond)

| Slice | Rewarded n / mean / t | Sold n / mean / t | Spread / t |
|---|---|---|---|
| Small/mid (<$10B) | 108 / **−0.86%** / −1.16 | 143 / −1.55% / −2.06 | +0.69% / 0.65 |
| — small (<$2B), exploratory | 70 / −1.01% / −1.01 | 107 / −1.88% / −2.12 | +0.87% / 0.65 |
| Large (≥$10B), complement | 28 / +0.87% / 0.92 | 10 / −1.07% / −0.68 | +1.93% / 1.05 |

Market caps are current (2026-07-03), not as-of event date — a disclosed
approximation. 4 graded events lacked cap data (ASNS, DRMAW, OWLTW,
SQFTW) and are absent from all slices.

## Plain reading

1. **The protective half of the gate is real.** Sold reports kept
   falling — another −1.6% vs IWM over the next five sessions (t −2.3),
   and the effect is at least as strong in small caps (−1.9%). "Never
   buy a sold report" is supported by this data.
2. **The long half did not show up.** Rewarded reports showed NO
   positive drift — slightly negative everywhere, including his own
   small/mid pond (−0.86%). In this unconditioned test, the day-one pop
   already contained the news.
3. What this could NOT test (stated in the prereg before results):
   beat-vs-miss conditioning (historical estimates unavailable), his
   confirming-signal stack, and his scoring curve. Achilles trades a
   narrower subset — *beats* with confirmations — than "any rewarded
   reaction." The drift may live in that subset. It demonstrably does
   not live in the broad reaction signal alone.

## Consequences (per the freeze)

- **No live-rule change.** His gates run as written this season — the
  prereg committed to that either way.
- The reaction gate's role should be understood as **risk filter, not
  alpha source**, until his live graded trades say otherwise. The
  earnings-season live season is now the test of whether
  beats + confirmations + small/mids finds the drift this broad replay
  did not.
- The −8% stop and the sold-report ban both point the right way; nothing
  here argues for loosening either.

## Unpriceable events (42 symbols, 45 events — reported, never replaced)

AGNCL, ALL-PI, APO-PA, AUB-PA, BSPK, BSTT, BTMWQ, BZAIW, CDR-PC,
CLDT-PA, ELLA, FBRT-PE, FDP, FGRS, FIISO, FMFG, GTN-A, HLTC, IAUX-WT,
INBP, LANDP, MBINL, NEWTH, PCG-PH, PEW-WT, RCD, RITM-PB, SATLW, SAY,
SILA, SMCIP, SOCGM, STLE, STT-PG, TBNRL, TLSIW, TPGXL, VREOF, WAL-PA,
WBHC, WRB-PH, XOM. Mostly preferred-share/warrant tickers and
delisted/OTC names the broker's historicals endpoint cannot resolve;
XOM and FDP are genuine data-source gaps at the broker (verified with
solo re-fetches), not join errors.
