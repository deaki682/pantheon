# Oracle beliefs — the upside engine's living mind

_Read at the top of every session; update at the bottom. Forward worldview, open
theses, lessons, decayed edges._

## Worldview (2026-07-14 — LIVE, first post-launch tend)

Oracle hunts the few under-covered names with the biggest REAL upside over a
6–24mo hold. The edge is the breadth read — reading filings the desk doesn't, in
the small-cap corner. The spotlight only AIMS; the read decides. The engine is
now LIVE: the Stage-1 read-cascade was built and calibrated (2026-07-07→07-10),
ran the full 3,154-name field on 2026-07-10, and funded the first real book the
same day. The 07-06 "NOT launch-ready" verdict below (kept under Lessons) is
HISTORY — it described the pre-cascade single-pass reads, and the cascade rebuild
was the answer to it. The sourcing pause was lifted 2026-07-14 (operator
directive; `cache/oracle_paused.json` carries the record).

## The LIVE book — round `upside-2026-07-10-r1` ($4,500 basis, filled 07-10 open)

Funnel: 3,154 field → 251 filing-read → 73 fundable → 6 sized. All six carry a
typed kill; every kill is PRINT-BASED (fundamentals in a filing), so the kill
checks concentrate at earnings. A drawdown is never an exit.

| Name | infl_type | entry | typed kill | next check |
|------|-----------|-------|------------|------------|
| TPC (Tutor Perini) | turnaround | 75.96 | 2 consecutive GAAP loss quarters | ~Aug print |
| KLIC (Kulicke & Soffa) | earnings_accel | 110.06 | quarterly revenue < $180M | ~Aug print |
| PAY (Paymentus) | earnings_accel | 28.87 | YoY revenue growth < 15% | ~Aug print |
| ZVRA (Zevra) | product_ramp | 14.11 | 2 consecutive flat/declining product-rev quarters | ~Aug print |
| QTWO (Q2 Holdings) | earnings_accel | 53.00 | GAAP net loss relapse or growth < 10% | ~Aug print |
| LXU (LSB Industries) | earnings_accel | 10.96 | quarterly net loss on ammonia price collapse | ~Jul/Aug print |

Mark 2026-07-21 CLOSE (after-close tend, 4pm prints, quotes 19:59-20:00Z):
equity $4,593.91 (**+2.09% vs basis — first close-mark HIGH**; SPY 748.28
vs spy_entry 751.31, -0.40%; **excess +2.49pp — widest lead since entry**).
Cash $449.94 (~10%). Per-name vs entry: TPC +14.22% (86.76, +7.7% on the
day — second straight no-filing rally day; a rally needs no exit reason),
LXU +5.47% (11.56), QTWO +4.08% (55.16), PAY +2.62% (29.625), KLIC -1.38%
(108.54, +8.5% on the day, nearly back to entry), ZVRA -11.80% (12.44,
+3.4% on the day, third straight recovery day off the 07-20 dip; drawdown,
never an exit; kill first evaluable at the ~08-11 print). EDGAR all six
CIKs at ~20:10Z: ZERO new filings since 07-17 — the only post-entry filings
remain the KLIC JPM 13G (07-16) and PAY Wasatch 13G/A (07-17), both
passive-ownership, dispositioned, NOT kill-relevant. No kill evaluable; all
six kills print-based. **PRINT CALENDAR (confirmed 07-17): LXU 2026-07-29 pm
(VERIFIED), QTWO 2026-07-29 pm (VERIFIED), PAY 2026-08-03 pm (tent.), KLIC
2026-08-05 pm (tent.), TPC 2026-08-05 pm (tent.), ZVRA 2026-08-11 pm
(tent.). First kill checks with teeth: LXU + QTWO on 07-29 — the 07-30 tend
must pull both prints and test the kills verbatim.** Broker reconcile clean
07-21 close: 6/6 share counts exact; no oracle orders today; personal/OGN
positions invisible; legacy CXT/HDSN/J/PSN/VITL absent as expected (exited
07-06). A/B due_for_grade=0. Sourcing remains a conscious no-op (standing
duty 3 — fully deployed, shared buying-power pool, 07-10 pipeline fresh);
research stamp untouched.
NOTE (housekeeping): earlier 07-16 tend entries stamped 18:15Z ("14:15 ET")
actually ran ~15:05Z (~11:05 ET) — UTC mislabeled as ET; entries from 15:30Z
onward are stamped correctly in UTC. Zeus dispatch headers may still carry the
mislabel (today's said "~14:05 ET" at a 14:07 UTC clock).

## A/B state (Stage 6 — the checkpoint's evidence)

`cache/oracle_upside_ab.json`: 242 deep-tier candidates recorded at the 07-10
funding with real entry/spy marks; the 6 funded names are Arm A, the passed 236
are Arm B (paper). Horizons 15–24mo — nothing due for grading yet; zero graded.
Earlier rounds (`convex-2026-07-07`, `calib-2026-07-09`) also unresolved. The
calibration writer runs after the first grades land.

## Open theses

- The six above, held to their typed kills. The first real information arrives
  at the July/August prints — that is when tending has teeth: pull each print,
  test the kill verbatim, fire without mercy if it lands, journal + grade.
- The interim convex trio (SEER/NNDM/FULC, funded 07-07) was liquidated 07-10
  into the rotation by operator direction; their A/B rows stay open for grading
  at horizon — do NOT drop them (an ungraded Arm B is survivorship bias).

## Standing duties for the next sessions

1. **Tend daily (cheap):** reconcile fills, mark at official closes, EDGAR-check
   held names for fresh filings; evaluate typed kills only on real filings.
2. **At each held name's print:** re-underwrite on the filing, run
   `evaluate_exit`, journal hold/exit with the citation.
3. **Sourcing (unfrozen 07-14):** the next FULL cascade round runs when there is
   capital to deploy (an exit or new funding) or at the August re-underwrite —
   not on a timer while the book is fully deployed and the 07-10 pipeline
   (73 fundables) is fresh. Journaled as a conscious no-op 07-14.
4. **Grading:** run `due_for_grade` every session; grade BOTH arms the day they
   come due, then `update_calibration`.

## Lessons (compounded — do not relearn these)

1. **Single-pass reads are credulous.** The 07-06 book collapsed 6→1 under a
   BEAR pass (one-time gains, price hikes, asset-sale deleveraging taken at face
   value). BEAR×3 with filing-cited defenses is mandatory before fundable.
2. **Hunt LOW in the 52-week range with a recent upturn.** Rounds 1–2 converted
   11% (momentum-biased queue); round 3 converted 40% after rebuilding the queue
   around washed-out names. Every kill high-in-range was "already arrived."
3. **Trailing-6mo momentum surfaces blowoff-and-fade, not early.** Use recent
   trend off a base; penalize near-52wk-high.
4. **The screen's fundamental signals lie without a read** (EPC "margin
   improving" was compressing; WLY "accel" was flat). The read is the edge.
5. **The blowup filter earns its keep** (KPTI going-concern, POET pre-revenue).
6. **The queue is the engine:** the read is only as good as what it's aimed at.

## Decayed / de-prioritized

- 6mo-trailing-momentum as a "still early" net — DECAYED (fixed in the cascade
  queue build).
- The 07-06 paper book (SABR/ACVA/CBZ/FRPT/EYE/NCNO dossiers) — SUPERSEDED by
  the 07-10 cascade round; kept in `oracle_upside_dossiers.json` as history
  until the next dossier round overwrites.

## Engine gaps still open (Stage 0–1)

- TOP-DOWN thematic net (needs a forming-themes map) — still off, under-counts.
- Real analyst-coverage data (proxied as thin) and eps_surprise (earnings feed).
- y/y or TTM revenue trajectory (needs the year-ago quarter) to de-noise accel.


## OPERATOR SITUATION NOTE — shared buying-power pool (2026-07-14)

The Robinhood account is ONE cash pool shared by all gods. The sleeves'
`cash` fields collectively overstated real buying power ~5x on 2026-07-14
($1,165 claimed across the four sleeves vs $237 actually available). My own
sleeve claims ~$450 cash; that is a CEILING, not spendable dry powder. NEW
DISCIPLINE (now in my runbook, house-wide): before ANY buy, read the LIVE
broker buying power (get_portfolio -> buying_power / get_accounts) and cap
every order at `shared.guards.spendable_buying_power(broker_bp)` — the
minimum of sleeve cash and the live pool binds. I mostly self-fund anyway
(I only buy on a cohort selection; a kill raises its own cash), so this
rarely bites me, but it is now the floor. The operator sold ~$930 of a
personal holding (VXUS) on 2026-07-14 to back the gods' claimed dry powder;
the pool is larger after tomorrow's fill but still SHARED — if another god
reaches for it the same session, I am capped second.
