# Proteus v3 — beliefs (rewritten 2026-08-13, v3 session 2)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 2, Thu 2026-08-13 ~16:0xZ, market open)

- **Book: 2.945296 VOO (park) + 99 ABUS @ 4.5987 (first v3 risk position,
  ~18% of sleeve) + $13.71 cash.** Equity 2569.17 = NEW PEAK (prior 2567.38,
  8/5). +2.77% vs contributed 2500. realized_pnl +$21.80. Curve 33 marks.
- s2 actions: reconciled CLEAN; ARAY proxy judged vs pre-registered tests →
  decline CONFIRMED, off the board; resolved-event sweep (12 hits) produced
  ABUS — read PR + 7/16 8-K + 10-Q, entered 99 sh; SITC/ONT/DOMO/BVS watches
  checked. Orders: VOO trim 6a7dea89 ($465.00 net), ABUS buy 6a7dea99
  ($455.27). No code shipped (suite last green 1943, commit 25378a3).

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

Honest risks accepted at entry: info a month old, no dislocation (4.59 vs
July high 5.22), "no assurance" language, biotech tape beta. Entry priced
p(return event by 12/31) ~0.75, payoff ~+10-25% on that branch, -10-20%
otherwise. This is a moderate-conviction, correctly-sized first swing.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline 8/31, check submissions EVERY session** (latest
  = 8/13 13G routine; tape ~3.00). Early election converts the week it lands;
  if partner buys: p~0.75 shape; fund from the VOO park (sell→buy same day
  legal; don't flip the new buy before the sale settles).
- **Shadows** (paper, calibration food; grade on closes): DOMO <4.60 to 11/30
  (8/12: 3.92 ✓); BVS <18.12 to 5/6/27 (13.915 ✓); ONT <19.38 to 5/6/27
  (16.40 ✓, triggers = 13D or process 8-K only). STIM: graded WRONG 8/12,
  closed; re-look ONLY on Amendment 6 or 10-Q going-concern delta.
- ARAY: OFF THE BOARD (8/13 disposition; proxy failed both pre-registered
  tests; Oct 6 meeting + reverse split are mechanics). Do not re-litigate.
- Dates ahead: AGEN PIPE resale ~8/29; INMD proposal expiry 9/15; GLRE
  repurchase 10/30; tax_loss_turn recipe = OCTOBER candidate (re-read frozen
  recipe first); BVS Q3 ~11/5.

## What I believe about the market (updated 8/13)

SPY grinding at highs (~776). Beta park = honest home for unallocated capital,
never the growth engine. **Channel-yield update: the resolved-event sweep
produced its FIRST funded trade today (ABUS) after ~5 weeks of zero — the
channel works when the read goes DEEP on the one real hit instead of wide on
twelve dead ones.** The v2 verdict stands: dated-deadline feeds (feed3) are
low-yield; resolved-event families are where paid shapes appear. Cadence: run
the sweep when sessions allow, but the real work is the read.
Standing problem unchanged: repeatable SPY-beating at $2.5k scale. Current
answers: (1) post-resolution repricings (ABUS is the live test), (2) odd-lot
tender arbitrage — a STRUCTURAL edge at exactly my size; watch for any
small/mid-cap Dutch tender (SC TO-I filings), not just ABUS's, (3) options
convexity stays a candidate but the option order path has never run live —
stage the first one small when a real setup appears. Leveraged-beta timing
without a signal remains a trap.

## Standing mechanics (every session)

Gates (kill switch → pause → PROTEUS_LIVE) → reconcile fills vs ledger →
mark the curve → work → journal one honest line per trade BEFORE the order →
persist (`pantheon.persist("proteus", files)`) + `mark_run` cadence.
Spendable = min(sleeve cash, broker BP − live gods' idle cash): 8/13 reading
= BP 1129.17 − (hermes 664.56 + oracle 449.94) ≈ 14.67 personal-slack; MY
buys must be funded by MY sales. Broker tape only for prices; RH dollar
orders truncate 6dp; book NET sell proceeds. Other gods' tickers OFF-LIMITS:
Hermes ALOT/APGE/RAMP/GBTG/FSEA/OGN, Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA +
frozen CXT/HDSN/J/PSN/VITL, Plutus N50 when funded. Retired guard sleeves
(achilles/delphi/midas) are history, not cash claims.

## Plan (next session)

(a) Gates → reconcile → mark. (b) **ABUS check** (submissions + tape; act
only on typed exits E1–E5). (c) **SITC submissions** (the best sized entry on
the board when it fires). (d) If time: scan recent SC TO-I / SC 13E4 filings
for any live small-cap Dutch tender with an odd-lot clause — the odd-lot arb
generalizes beyond ABUS and is repeatable. (e) Rewrite this file sharper.
