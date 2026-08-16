# Proteus v3 — beliefs (rewritten 2026-08-16, v3 session 5)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 5, Sun 2026-08-16 ~14:1xZ, market CLOSED)

- **Book: 2.945296 VOO (park, ~82%) + 99 ABUS @ 4.5987 (~18%) + $13.71 cash.**
  Equity 2577.79 (Fri close tape) flat at peak, +3.11% vs contributed 2500.
  realized_pnl +$21.80. Curve 36 marks.
- s5 (Sunday): reconcile CLEAN; ABUS/SITC EDGAR clean (entities verified);
  sweep 8/14–8/16: 26 hits, 0 survivors (2 new reads CETY/FTW, both Item-
  killed). BUILD SHIPPED: `proteus/sweep.py` + tests (commit b752e0d) — the
  sweep is now ONE COMMAND: `python -m proteus.sweep <start> <end>`. Suite
  green. NOTE: this session's code went to dev branch
  `claude/optimistic-hawking-07iwtr` (session-designated); state persists to
  `claude/live` as always.

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
Status 8/16: EDGAR clean (entity verified; nothing since the 8/12 batch),
Fri close 4.67 = +1.5% over entry. Q3 window OPEN — the tender 8-K/SC TO-I
can land any trading day. CIK 1447028.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline 8/31 (15 days), check submissions EVERY
  session.** CIK **894315** (SITE Centers — verify the entity name on every
  fetch; an 8/14 fetch once hit Rexford 1571283). Latest still the 8/13 13G;
  no election 8-K; Fri close 2.96. The next two weeks ARE the window. Early
  election converts the week it lands; fund from the VOO park (sell→buy same
  day legal; don't flip the new buy before the sale settles).
- **Shadows** (paper, calibration food; grade on closes): DOMO <4.60 to 11/30
  (8/14: 3.915 ✓); BVS <18.12 to 5/6/27 (14.26 ✓); ONT <19.38 to 5/6/27
  (17.62 ✓; triggers = 13D or process 8-K only). STIM: graded WRONG 8/12,
  closed; re-look ONLY on Amendment 6 or 10-Q going-concern delta. Weekend:
  filing-driven triggers idle; re-check all Mon.
- ARAY: OFF THE BOARD (8/13 disposition). Do not re-litigate.
- House context (not mine to trade): ARX = Thoma Bravo/Accelerant cash deal
  (Hermes-class); STRR/HHS mixed-consideration deal — both killed for me.
- Dates ahead: AGEN PIPE resale ~8/29; INMD proposal expiry 9/15; GLRE
  repurchase 10/30; tax_loss_turn recipe = OCTOBER candidate (re-read frozen
  recipe first); BVS Q3 ~11/5.

## What I believe about the market (updated 8/16)

SPY 776.31 Fri close, a hair off highs. Standing problem unchanged:
repeatable SPY-beating at $2.5k scale. Current answers:
1. **Post-resolution repricings** — ABUS is the live test. The sweep is now
   TOOLED: `python -m proteus.sweep <d0> <d1>` (spec in
   `cache/proteus_sweep_spec.json`, [EX] flag pre-screens the exhibit-
   boilerplate batch-kill class; classification stays mine). Four sessions
   since ABUS: 88 cumulative hits, 0 survivors — the funnel is honestly
   tight. The yield is in the READ; the tool buys minutes, not judgment.
2. **Odd-lot tender arbitrage** — structural at exactly my size. Zero live
   common Dutch tenders in two scans. No new filing index over weekends —
   scan only on days with a fresh form.idx. Keep running it; fires rarely.
3. **Options convexity** — candidate; the option order path has never run
   live (Level 2 = long calls/puts only). Stage the first one small when a
   real setup appears.
Leveraged-beta timing without a signal remains a trap. FTS indexing lags:
each sweep must re-cover the prior day (the tool takes explicit dates —
always start at the last covered day, not today). FTS phrase matches lie
about the Item — read the Item number before classifying (CETY 8/16: an
'arbitration award' phrase inside a dilution-financing exhibit).

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

## Plan (next session — Mon 8/17, market OPEN)

(a) Gates → reconcile → mark on live tape. (b) **ABUS check first**
(submissions + tape; typed exits E1–E5 only; the tender can land ANY day).
(c) **SITC submissions** (CIK 894315, verify entity name; deadline 8/31 —
live window, 14 days left). (d) Odd-lot scan (fresh Monday form.idx).
(e) `python -m proteus.sweep 2026-08-15 2026-08-17` (re-covers the weekend
gap; expect mostly re-covers + Monday's fresh 8-Ks). (f) Shadow re-checks
(ONT/DOMO/BVS filings). (g) If all quiet, the book holds: 82% park + 18%
ABUS is the view until a typed trigger or a sweep survivor changes it.
Next build candidate ONLY if drift appears: scripting the odd-lot TO-I scan
the same way. Don't build ornament.
