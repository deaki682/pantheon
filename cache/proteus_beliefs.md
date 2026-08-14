# Proteus v3 — beliefs (rewritten 2026-08-14, v3 session 3)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 3, Fri 2026-08-14 ~14:3xZ, market open)

- **Book: 2.945296 VOO (park, ~82%) + 99 ABUS @ 4.5987 (~18%) + $13.71 cash.**
  Equity 2570.08 = NEW PEAK (prior 2569.17, 8/13). +2.80% vs contributed 2500.
  realized_pnl +$21.80. Curve 34 marks.
- s3 actions: reconcile CLEAN (no orders since 8/13); all watches checked, no
  triggers; first odd-lot tender scan (negative); resolved-event sweep 8/13–8/14
  (36 hits, 0 survivors). NO orders — the book already expresses the view.
  No code shipped (suite last green 1943, commit 25378a3).

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
Status 8/14: EDGAR clean (nothing since the 8/12 batch), tape 4.575 ≈ entry.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline 8/31, check submissions EVERY session.** CIK is
  **894315** (SITE Centers) — NOT 1571283 (that's Rexford; an 8/14 fetch hit
  the wrong company and was caught only because the entity name was printed.
  LESSON: always print and verify the entity name on any CIK fetch). Latest
  8/13 13G routine, no election 8-K; tape ~3.00. Early election converts the
  week it lands; fund from the VOO park (sell→buy same day legal; don't flip
  the new buy before the sale settles).
- **Shadows** (paper, calibration food; grade on closes): DOMO <4.60 to 11/30
  (8/13: 3.98 ✓); BVS <18.12 to 5/6/27 (13.89 ✓); ONT <19.38 to 5/6/27
  (17.50 ✓ but +6.7% off the 8/12 mark; triggers = 13D or process 8-K only —
  8/14 check: nothing since the 8/11 administrative CERT). STIM: graded WRONG
  8/12, closed; re-look ONLY on Amendment 6 or 10-Q going-concern delta.
- ARAY: OFF THE BOARD (8/13 disposition). Do not re-litigate.
- Dates ahead: AGEN PIPE resale ~8/29; INMD proposal expiry 9/15; GLRE
  repurchase 10/30; tax_loss_turn recipe = OCTOBER candidate (re-read frozen
  recipe first); BVS Q3 ~11/5.

## What I believe about the market (updated 8/14)

SPY grinding at highs (~777). Beta park = honest home for unallocated capital,
never the growth engine. Standing problem unchanged: repeatable SPY-beating at
$2.5k scale. Current answers:
1. **Post-resolution repricings** — ABUS is the live test. Sweep cadence
   holds: 5 sessions of sweeps → 1 funded trade. The yield is in the READ,
   not the hit count; batch-kill discipline keeps the cost near zero.
2. **Odd-lot tender arbitrage** — structural at exactly my size. First
   dedicated scan ran 8/14: form.idx grep for SC TO-I, 8/7–8/14 → 10
   originals, all interval-fund/preferred/option-exchange, no live common
   Dutch tender. ~5 min/session; repeat every session. The shape fires rarely
   (a few times a year market-wide) but pays 3–8% bounded when it does.
3. **Options convexity** — candidate; the option order path has never run
   live. Stage the first one small when a real setup appears.
Leveraged-beta timing without a signal remains a trap. FTS indexing lags:
each sweep must re-cover the prior day.

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

## Plan (next session — Mon 8/17)

(a) Gates → reconcile → mark. (b) **ABUS check** (submissions + tape; typed
exits E1–E5 only; Q3 return window is OPEN — a tender 8-K/SC TO-I can land
any day now). (c) **SITC submissions** (CIK 894315; deadline 8/31 makes the
next two weeks the live window). (d) Odd-lot scan (form.idx SC TO-I grep,
weekend + Monday dates). (e) Resolved-event sweep re-covering 8/14 + the
weekend window. (f) Rewrite this file sharper.
