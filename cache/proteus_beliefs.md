# Proteus v3 — beliefs (written 2026-08-12, v3 session 1: LAUNCH)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` — one page: **make money**, six laws
(bounded loss; kill switch supreme; integrity of the record; total freedom
inside 1–3; show up and swing; get smarter every session). v2 is SCRAPPED —
its charter, directives, Kelly arithmetic, probe caps, calibration gates and
kill-spec clocks are VOID. `cache/proteus_v2_beliefs.md` holds the 37 lessons:
scar tissue to read (I re-read them today; they are good), never law.
`.claude/commands/proteus.md` carries the house physics (ledger, reconcile,
spendable = min(sleeve cash, BP − live gods' idle cash), persist, cadence).

## The charter in my own words

The operator fired the bureaucrat and kept the trader. I am scored on one
thing: the equity curve vs SPY. I may do anything long/bounded (stock, ETFs
incl. leveraged/inverse, long options, debit spreads, covered calls, CSPs,
defined-risk spreads), any size including all-in, no approval, no paper
apprenticeship. The price of that freedom is three hard walls (loss bounded at
$0, kill switch, honest record) and one duty: be invested, and get smarter
faster than my edges decay. Losing is priced in; paralysis is not.

## State (v3 session 1, Wed 2026-08-12 ~14:2xZ, market open)

- **Book: VOO 3.597332 sh (blended entry 696.9827) + cash $3.98. FULLY
  INVESTED.** Equity at mark 1: 2559.60 (VOO 710.42 / SPY 772.88), +2.38% vs
  contributed 2500, peak 2567.38 (8/5) stands. realized_pnl +$11.26.
- Session-1 actions: archived v2 (`proteus_v2_journal.jsonl` 155 rows,
  `proteus_v2_beliefs.md`, `proteus_v2_curve.json`, `proteus_v2_sleeve.json`);
  reconciled CLEAN (broker VOO == sleeve, zero foreign orders); **graded the
  STIM shadow WRONG as written** (8/11 official close 3.19 ≥ 2.98; foregone
  ~+$60 on the declined $199.23 at stated p 0.35 — the record's first honest
  WRONG; n=1, does not refute the v2 pricing read, but it is data that the
  declines lose their counterfactual sometimes); **bought $755 VOO** (fill
  1.062717 @ 710.4431, order `6a7c828a`) — idle-since-8/4 cash deployed to
  beta per law 5.
- Ledger/journal: journal now 159 rows (156 launch note, 157 STIM grade, 158
  trade line, 159 session note). Curve: 32 marks. No code shipped s1 — suite
  not triggered (last green: 1943 tests, commit `25378a3`).
- Wash-sale: the 7/13 SPY $5-probe loss window lapsed 8/12 — history. VOO has
  only gains realized. Clean.

## What I believe about the market today (honest, low-information)

I have NO researched macro view yet — v2 left me an event-corner map, not a
market view. Facts I trust: SPY grinding at highs (773 area, prior peak 8/5);
the house growth-hunt verdict says no scalable alpha at this size without a
real read (LEAN_ON_BETA); v2's 63 dispositions across 8+ full deep reads
measured that pre-event optionality in the neglected corner virtually never
offers a mispriced entry — the payable shapes are POST-resolution repricings
and they are RARE. So today the sleeve sits in beta while I build. Beta ties
SPY; it never beats it. **The standing problem of v3: find the repeatable
thing that beats SPY, at $2.5k scale, bounded-loss.** Candidate directions to
develop (next sessions, in order):
1. **Post-resolution event repricings** (SITC-class) — v2's one validated
   shape idea. Thin supply, but real. Keep the watches; take them when typed
   triggers fire, sized at conviction (no Kelly ceiling anymore).
2. **Defined-risk options convexity** — now lawful without probe caps. v2
   never got an honest fill; small-cap chains kept failing on spread. Look
   UP-cap: liquid mid/large-cap chains around dated events (earnings,
   FDA, rulings) where I can actually read the filing better than the tape.
   First option trade stages small; the OPTION order path has never run live.
3. **Leveraged-beta timing** is a trap without a signal — do NOT reach for
   SSO/UPRO "to beat SPY" absent a researched regime read. That is noise
   with extra variance, not intelligence.

## Inherited leads and dates (pursue on merit, drop on merit)

- **SITC — election deadline 8/31** (check EDGAR submissions EVERY session;
  early election converts the week it lands). The receiver's election is the
  information event (v2 lesson 30). If partner buys: p~0.75 shape, v2 sized
  ~$320; v3 may size bigger on conviction. Fund from the VOO park (cash
  account: sell→buy same day is legal; just don't flip the new buy before
  the sale settles).
- **ARAY — proxy re-look ~8/13** (tomorrow): judge ONLY vs v2 row-150 tests
  (claims-stack ≥ ~25% improvement, or dislocation ≤ ~0.20 with terms
  unchanged → probe; terms-as-filed at ≥ ~0.25 = walk). Tape 8/12: 0.276.
- **Shadow watches** (paper, zero cost, calibration food): DOMO <4.60 to
  11/30 (3.92); BVS <18.12 to 5/6/27 (13.59); ONT <19.38 to 5/6/27 (16.22,
  typed triggers only). STIM re-look ONLY on Amendment 6 or 10-Q
  going-concern delta + dislocation — never price.
- AGEN PIPE resale ~8/29; INMD proposal expiry 9/15; GLRE repurchase 10/30;
  tax_loss_turn recipe (v2 row 94) — an OCTOBER execution candidate, re-read
  the frozen recipe first; BVS Q3 ~11/5.
- feed3 / sweep machinery: v2's kill-spec clock died with v2. Verdict on
  merit: 29 days, zero survivors — the daily-sweep channel is a LOW-YIELD
  use of a session. Do not run it daily by habit; run event reads when a
  named date approaches. The eventfeed store (32 events) is reference.

## Standing mechanics (do these every session)

Gates (kill switch → pause → PROTEUS_LIVE) → reconcile fills vs ledger →
mark the curve (equity + SPY) → then trade/build/study at judgment → journal
one honest line per trade BEFORE the order → persist
(`pantheon.persist("proteus", files)`) + `mark_run` cadence. Art-26a
spendable before any buy; broker tape only for prices; RH dollar orders
truncate 6dp; book NET sell proceeds. Other gods' tickers OFF-LIMITS:
Hermes ALOT/APGE/RAMP/GBTG/FSEA/OGN, Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA +
frozen CXT/HDSN/J/PSN/VITL, Plutus N50 book when funded. Retired guard
sleeves (achilles $2k, delphi, midas) are HISTORY, not cash claims — exclude
from the spendable subtraction (verified 8/12: live claims hermes 664.56 +
oracle 449.94 + plutus 0 ≈ broker cash 1883.78 − ~$10 personal).

## Plan (next session)

(a) Gates → reconcile → mark. (b) **ARAY proxy check** (EDGAR submissions;
judge vs row-150 tests the day it lands). (c) **SITC submissions check**
(election converts the week it lands — this is the best sized entry on the
board). (d) Start v3's real work: pick direction 1 or 2 above and go deep —
one researched, sized position candidate by end of week beats ten shallow
sweeps. (e) Rewrite this file sharper than you found it.
