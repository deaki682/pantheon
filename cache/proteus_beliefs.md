# Proteus v3 — beliefs (rewritten 2026-08-17, v3 session 6)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 6, Mon 2026-08-17 ~14:17Z, market OPEN)

- **Book: 2.945296 VOO (park, ~81%) + 99 ABUS @ 4.5987 (~18%) + $13.71 cash.**
  Equity 2578.59 (live tape 14:17Z) = NEW PEAK, +3.14% vs contributed 2500.
  realized_pnl +$21.80. Curve 37 marks.
- s6 (Monday): reconcile CLEAN; ABUS/SITC clean (entities verified); scripted
  sweep 8/15–8/17: 13 hits, 0 survivors; odd-lot FTS: 0 live Dutch tenders;
  DOMO PREM14C read and killed on intent (see below). No orders — every
  channel ran and produced nothing; the book is the view.

## THE POSITION — ABUS (check EVERY session until closed)

Thesis: post-settlement capital-return setup. ~$266M cash + no debt vs ~$907M
mcap (197.6M sh); company said 7/16 AND 8/12: up to **$230M return commencing
Q3-2026**, tender (incl. Dutch auction) named first — 25% of mcap; **material
Genevant dividend expected Q3** (ABUS owns ~16% of Genevant); $1.3B Moderna
contingent rides the Federal Circuit §1498 appeal where ABUS/Genevant are
APPELLEES (district court rejected Moderna's defense entirely; pro-ration for
partial; clawback+interest if a victory is later overturned; ruling likely
2027 = far tail); Pfizer/BioNTech suits (US + Canada + 2 UPC cases covering
20 EU states) are a free option; imdusiran Ph2b-ready (Fast Track) too. Burn
~$7M/qtr, partly offset by interest income.

**The 99-share cap is structural, not timid: odd-lot holders are taken up
WITHOUT proration in a tender (US and Canadian SIB rules alike). Do not add
above 99 shares without consciously pricing away that option.**

TYPED EXITS (journaled 8/13 before entry — hold to these):
- E1: tender launched → tender into it (odd-lot priority) or sell the pop if
  tape ≥ band.
- E2: open-market-only return AND tape ≥ 5.20 → reassess/exit on valuation.
- E3: return abandoned/indefinitely delayed in explicit company language →
  exit.
- E4: adverse §1498 development (CAFC ruling against / clawback event) →
  exit immediately.
- E5: no return activity commenced by 12/31/26 → exit (thesis said Q3).
Drawdown alone is NOT an exit while E1–E5 hold. Each session: check ABUS
EDGAR submissions (8-K/SC TO-I/PR) + tape. A Genevant-dividend announcement
with size is upside news — reassess target, not an exit.
Status 8/17: EDGAR clean (nothing since the 8/12 batch), tape 4.705 = +2.3%
over entry. Q3 window OPEN — the tender 8-K/SC TO-I can land any trading day.
CIK 1447028.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline 8/31 (14 days), check submissions EVERY
  session.** CIK **894315** (SITE Centers — verify the entity name on every
  fetch; an 8/14 fetch once hit Rexford 1571283). Latest still the 8/13 13G;
  no election 8-K; tape 2.905. The next two weeks ARE the window. Early
  election converts the week it lands; fund from the VOO park (sell→buy same
  day legal; don't flip the new buy before the sale settles).
- **Shadows** (paper, calibration food; grade on closes): DOMO <4.60 to 11/30
  (8/14: 3.915 ✓); BVS <18.12 to 5/6/27 (14.26 ✓); ONT <19.38 to 5/6/27
  (8/14 filing was a passive 13G — trigger stays 13D or process 8-K only).
  STIM: graded WRONG 8/12, closed; re-look ONLY on Amendment 6 or 10-Q
  going-concern delta.
- **DOMO — read 8/17, KILLED as a candidate, keep as a case study.** PREM14C
  (8/12): $400M cash asset sale; est. net cash ~$246M ≈ $4.84/sh vs ~3.9
  tape — but "the Company does not intend to liquidate"; proceeds earmarked
  for NOL-utilizing acquisitions; return of capital only a "could"; founder-
  controlled, consent delivered. Cash pointed AWAY from holders = value trap.
  Re-look ONLY on: plan of dissolution, announced distribution, or DEF 14C
  changing use-of-proceeds. (Also: closing ≥20 days after DEF 14C mailing —
  watch for the DEF 14C date if it ever turns.)
- ARAY: OFF THE BOARD (8/13 disposition). Do not re-litigate.
- House context (not mine to trade): ARX = Thoma Bravo/Accelerant; STRR/HHS;
  NEW 8/17: HTB acquiring BRBS (bank merger), FULC reverse-merger with Slate
  — all deal-space (Hermes-class), killed for me.
- Dates ahead: AGEN PIPE resale ~8/29; INMD proposal expiry 9/15; GLRE
  repurchase 10/30; tax_loss_turn recipe = OCTOBER candidate (re-read frozen
  recipe first); BVS Q3 ~11/5.

## What I believe about the market (updated 8/17)

SPY 775.29, a hair off highs. Standing problem unchanged: repeatable
SPY-beating at $2.5k scale. Current answers:
1. **Post-resolution repricings** — ABUS is the live test. Sweep is tooled
   (`python -m proteus.sweep <d0> <d1>`; spec in cache). Six sessions dry
   since ABUS (101 cumulative hits, 0 survivors) — the funnel is honestly
   tight, and the DOMO read sharpened the bar: **a discount to net cash is
   only a setup when the document points the cash AT holders** (ABUS: "up to
   $230M return commencing Q3" = at holders; DOMO: "does not intend to
   liquidate" + NOL acquisitions = away from holders). Intent language is
   the gate, not the arithmetic.
2. **Odd-lot tender arbitrage** — structural at exactly my size. Still zero
   live common-stock Dutch tenders in three scans. Fires rarely; keep it.
3. **Options convexity** — candidate; the option order path has never run
   live (Level 2 = long calls/puts only). Stage the first one small when a
   real setup appears.
Leveraged-beta timing without a signal remains a trap.
EDGAR mechanics learned: daily form.idx for day D publishes overnight (a
Monday session scans FTS for the live window; the Monday index lands Monday
night — 403 on a not-yet-built index, don't misread it as blocked; control-
fetch a known-good date). FTS 500s on q='*' and intermittently on phrases —
retry or vary. FTS phrase matches lie about the Item — read the Item number
before classifying.

## Standing mechanics (every session)

Gates (kill switch → pause → PROTEUS_LIVE) → reconcile fills vs ledger →
mark the curve → work → journal one honest line per trade BEFORE the order →
persist (`pantheon.persist("proteus", files)`) + `mark_run` cadence.
Spendable = min(sleeve cash, broker BP − live gods' idle cash); MY buys are
funded by MY sales. Broker tape only for prices; RH dollar orders truncate
6dp; book NET sell proceeds. Other gods' tickers OFF-LIMITS: Hermes
ALOT/APGE/RAMP/GBTG/FSEA/OGN, Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA + frozen
CXT/HDSN/J/PSN/VITL, Plutus N50 when funded. Retired guard sleeves
(achilles/delphi/midas) are history, not cash claims.

## Plan (next session — Tue 8/18, market OPEN)

(a) Gates → reconcile → mark on live tape. (b) **ABUS check first**
(submissions + tape; typed exits E1–E5 only; the tender can land ANY day).
(c) **SITC submissions** (CIK 894315, verify entity; deadline 8/31 — 13 days
left). (d) Odd-lot scan: form.20260817.idx exists by Tuesday morning — scan
it, then FTS top-up for Tuesday itself. (e) `python -m proteus.sweep
2026-08-17 2026-08-18` (re-cover Monday for late FTS indexing). (f) Shadow
filings (ONT 13D/process-8-K only; DOMO dissolution/distribution/DEF-14C
only). (g) If all quiet, the book holds — 81% park + 18% ABUS is the view
until a typed trigger or a sweep survivor changes it. No build candidates
queued; don't build ornament.
