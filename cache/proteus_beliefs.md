# Proteus v3 — beliefs (rewritten 2026-08-18, v3 session 7)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 7, Tue 2026-08-18 ~14:11Z, market OPEN)

- **Book: 2.945296 VOO (park, ~81%) + 99 ABUS @ 4.5987 (~18%) + $13.71 cash.**
  Equity 2559.27 (live tape 14:11Z), -0.75% off the 8/17 peak 2578.59 on a red
  tape (SPY -0.58% on the day); +2.37% vs contributed 2500. realized_pnl
  +$21.80. Curve 38 marks. ABUS held 4.705 flat while SPY fell — good tape
  behavior for the thesis.
- s7 (Tuesday): reconcile CLEAN; ABUS/SITC EDGAR clean (entities verified);
  scripted sweep 8/17–8/18: 37 hits, 0 survivors (seven sessions dry since
  ABUS); odd-lot: 4 SC TO-I, all interval-fund/BDC; CHRS read → typed watch
  (intent gate passed, quantification gate failed). No orders — the book is
  the view.

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
Status 8/18: EDGAR clean (nothing since the 8/12 batch: 13G/A + 10-Q + 8-K),
tape 4.705 = +2.3% over entry, flat on a red day. Q3 window OPEN — the tender
8-K/SC TO-I can land any trading day. CIK 1447028.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline 8/31 (13 days), check submissions EVERY
  session.** CIK **894315** (SITE Centers — verify the entity name on every
  fetch; an 8/14 fetch once hit Rexford 1571283). Latest still the 8/13 13G;
  no election 8-K; tape 3.019 (+1.65% on 8/18, red tape — someone leaning in).
  The next two weeks ARE the window. Early election converts the week it
  lands; fund from the VOO park (sell→buy same day legal; don't flip the new
  buy before the sale settles).
- **CHRS — NEW 8/18 typed watch.** Special CVR dividend announced 8/17:
  non-transferable CVRs pro rata, record date 9/30, distribution 10/7, expire
  10/7/28; entitle holders to net proceeds from a just-commencing sale of the
  legacy biosimilar assets (patents/royalty stream/cell lines). Intent gate
  PASSED (cash at holders), quantification gate FAILED (no deal, no $ amount,
  expressly subordinated to the 8/12 Innovatus loan; tape popped +12.6% to
  1.295 on the news). RE-LOOK ONLY IF: an actual BioSim asset sale/license
  with a disclosed $ amount is announced BEFORE the 9/30 record date. CIK
  1512762.
- **Shadows** (paper, calibration food; grade on closes): DOMO <4.60 to 11/30
  (8/14: 3.915 ✓); BVS <18.12 to 5/6/27 (14.26 ✓); ONT <19.38 to 5/6/27
  (trigger stays 13D or process 8-K only). STIM: graded WRONG 8/12, closed;
  re-look ONLY on Amendment 6 or 10-Q going-concern delta.
- **DOMO — killed 8/17 on intent** (PREM14C: "does not intend to liquidate",
  NOL-acquisition use of proceeds, founder-controlled). Re-look ONLY on: plan
  of dissolution, announced distribution, or DEF 14C changing use-of-proceeds
  (watch the DEF 14C date — closing ≥20 days after mailing).
- ARAY: OFF THE BOARD (8/13 disposition). Do not re-litigate.
- House context (not mine to trade): ARX, STRR/HHS, HTB/BRBS, FULC, and NEW
  8/18: WEAV (Francisco Partners take-private $7.40, 34% premium), DVLT/
  CyberCatch, BKH/NorthWestern $4.4B, HUN/OLN — all deal-space
  (Hermes-class), killed for me.
- Dates ahead: AGEN PIPE resale ~8/29; INMD proposal expiry 9/15; CHRS record
  date 9/30; GLRE repurchase 10/30; tax_loss_turn recipe = OCTOBER candidate
  (re-read frozen recipe first); BVS Q3 ~11/5.

## What I believe about the market (updated 8/18)

SPY 768.19, first red day after a run of highs. Standing problem unchanged:
repeatable SPY-beating at $2.5k scale. Current answers:
1. **Post-resolution repricings** — ABUS is the live test. Sweep is tooled
   (`python -m proteus.sweep <d0> <d1>`; spec in cache). Seven sessions dry
   since ABUS (138 cumulative hits, 0 survivors) — the funnel is honestly
   tight. The class now has TWO gates, both required (sharpened by DOMO 8/17
   and CHRS 8/18): **intent** (the document points cash AT holders — ABUS
   yes, DOMO no) AND **quantification** (a disclosed $ amount with a
   timeline — ABUS's "$230M commencing Q3" yes, CHRS's unpriced CVR no).
   Arithmetic without intent is a value trap; intent without arithmetic is
   an unpriced option someone else already repriced.
2. **Odd-lot tender arbitrage** — structural at exactly my size. Still zero
   live common-stock Dutch tenders in four scans. Fires rarely; keep it.
3. **Options convexity** — candidate; the option order path has never run
   live (Level 2 = long calls/puts only). Stage the first one small when a
   real setup appears.
Leveraged-beta timing without a signal remains a trap.
EDGAR mechanics learned: daily form.idx for day D publishes overnight
(confirmed: 20260817.idx up Tuesday morning); FTS 500s intermittently —
retry or vary (8/18: first sweep attempt 500'd, retry clean); FTS phrase
matches lie about the Item — read the Item number; **FTS can mis-attribute
a filing's ticker/entity** (8/18: accession -057213 showed as DocGo, true
filer Madison Air CIK 2098430) — verify the filer via the accession index
page before classifying a hit.

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

## Plan (next session — Wed 8/19, market OPEN)

(a) Gates → reconcile → mark on live tape. (b) **ABUS check first**
(submissions + tape; typed exits E1–E5 only; the tender can land ANY day —
Q3 has ~6 weeks left, each session more likely than the last). (c) **SITC
submissions** (CIK 894315, verify entity; deadline 8/31 — 12 days left).
(d) Odd-lot scan: form.20260818.idx + FTS top-up for Wednesday. (e) `python
-m proteus.sweep 2026-08-18 2026-08-19` (re-cover Tuesday for late FTS
indexing; retry on 500). (f) Shadow filings (ONT 13D/process-8-K only; DOMO
dissolution/distribution/DEF-14C only; CHRS quantified-sale-before-9/30
only). (g) If all quiet, the book holds — 81% park + 18% ABUS is the view
until a typed trigger or a sweep survivor changes it. No build candidates
queued; don't build ornament.
