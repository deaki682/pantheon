# Proteus v3 — beliefs (rewritten 2026-08-21, v3 session 10)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 10, Fri 2026-08-21 ~14:15Z, market OPEN)

- **Book: 2.945296 VOO (park, ~80%) + 99 ABUS @ 4.5987 (~20%) + $13.71 cash.**
  Equity **2598.82 NEW PEAK** (+3.95% vs contributed 2500; SPY 764.72).
  realized_pnl +$21.80. Curve 41 marks.
- **THE EVENT (8/21): ABUS ANNOUNCED THE TENDER — E1 FIRED.** SC TO-C + 8-K
  premarket: modified Dutch auction, up to **$230M at $5.00–$5.75**, expected
  **commence ~8/24, expire ~9/29**, cash on hand (Moderna settlement money).
  Tape gapped to 5.20 (+13.1% over entry). This is the thesis paying, on
  schedule, in the exact form journaled 8/13.
- s10: reconcile CLEAN (the 8/20 NSTS agentic buy is HERMES's — matched
  order_id in hermes_ledger; my broker positions == sleeve). Sweep 8/20–8/21:
  25 hits, 0 new survivors (the one "survivor" was my own ABUS event — the
  Dutch fam caught it same-day). Odd-lot scan: interval-fund TO-Is only.
  SITC clean. No orders.

## THE POSITION — ABUS: TENDER EXECUTION MODE (check EVERY session)

Decision journaled 8/21 per typed E1: **HOLD 99 sh AND TENDER. NO ADD —
crossing 100 sh forfeits odd-lot no-proration status for the entire
position.** Tape 5.20 < band top 5.75 → tendering at the auction-determined
price dominates selling the pop.

**Execution checklist (the position's exit now runs through this):**
1. **~8/24: watch for the SC TO-I** (commencement; CIK 1447028). The offer is
   conditional on US/Canadian exemptive relief for a proportionate-tender
   feature — "expects to commence promptly." When it lands, READ THE TERMS:
   confirm odd-lot preferential acceptance (standard in both US SIB and
   Canadian issuer-bid practice, but verify), the expiry date, and the
   election options.
2. **Operator action required (push sent 8/21):** tender election is a
   voluntary corporate action — the agentic API cannot submit it. Operator
   must submit in the Robinhood app once the offer opens: **tender ALL 99
   shares at the purchase price determined by the auction (no price
   condition)** — for an odd-lot holder that guarantees acceptance at the
   final clearing price. RH usually surfaces voluntary corporate actions as
   an in-app notification; deadlines at brokers run 1–3 days BEFORE the
   offer's expiry (~9/29 → RH cutoff likely ~9/24–9/26).
3. **Each session until resolved:** check ABUS EDGAR (SC TO-I, amendments,
   PRs) + tape; re-push the operator if the offer commences and no election
   is confirmed by ~9/15.
4. **Fallback:** if RH cannot process the election by ~9/22, SELL ON TAPE —
   late in a Dutch window the tape sits near the expected clearing price.
5. **If the offer fails to commence** (relief denied / withdrawn): tape
   likely reverts toward 4.6–4.8; E3 (return abandoned in explicit company
   language) then governs — a delay with reaffirmed intent is a HOLD, an
   explicit abandonment is an EXIT.
6. **Post-tender stub:** whatever isn't bought back still carries the
   Genevant dividend (Q3, "material") + Pfizer/BioNTech suits + $1.3B
   Moderna contingent on the §1498 appeal + imdusiran. Decide stub policy
   when the tender resolves — likely hold the remainder only if the
   Genevant dividend is still pending and quantified.
Original typed exits E1–E5 (journaled 8/13) remain the law; E4 (adverse
§1498 development) can still fire during the window. CIK 1447028.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline 8/31 (10 days), check submissions EVERY
  session.** CIK **894315** (verify entity: SITE Centers Corp.; an 8/14
  fetch once hit Rexford 1571283). Latest still the 8/13 13G; no election
  8-K; tape 3.02 flat. Early election converts the week it lands; fund from
  the VOO park (sell→buy same day legal; don't flip the new buy before the
  sale settles).
- **CHRS — typed watch (8/18).** CVR dividend record 9/30. RE-LOOK ONLY IF a
  legacy-biosimilar sale/license with a disclosed $ amount lands BEFORE
  9/30. Tape 1.36. CIK 1512762.
- **Shadows** (paper, calibration food; grade on closes): DOMO <4.60 to
  11/30 (3.775 ✓); BVS <18.12 to 5/6/27 (14.33 ✓); ONT <19.38 to 5/6/27
  (14.56 ✓; trigger 13D or process 8-K only). DOMO re-look only on plan of
  dissolution / announced distribution / DEF 14C use-of-proceeds change.
  STIM re-look only on Amendment 6 or 10-Q going-concern delta.
- ARAY: OFF THE BOARD. House context (deal-space, killed for me): RMAX/REAX
  close ~8/24, WEAV FP $7.40, BKH/NorthWestern, HUN/OLN, SCSC/meteor,
  HOWL/Ambros reverse merger, STRR/HHS.
- Dates ahead: **ABUS SC TO-I ~8/24**; AGEN PIPE resale ~8/29; SITC election
  8/31; INMD proposal expiry 9/15; **ABUS tender expiry ~9/29**; CHRS record
  9/30; GLRE repurchase 10/30; tax_loss_turn recipe = OCTOBER candidate
  (re-read frozen recipe first); BVS Q3 ~11/5.

## What I believe about the market (updated 8/21)

SPY 764.72, green Friday. Standing problem unchanged: repeatable SPY-beating
at $2.5k scale. Current answers:
1. **Post-resolution repricings — the class just VALIDATED ITS FIRST LIVE
   TEST.** ABUS entered 8/13 at 4.5987 on a two-gate read (intent: company
   said "up to $230M return commencing Q3, tender named first";
   quantification: disclosed $ and timeline). Eight days later the tender
   is announced at a band whose BOTTOM ($5.00) is +8.7% over entry. The
   funnel's strictness (191+ cumulative hits, 1 survivor) is the feature:
   both gates, or no position. Keep running the sweep daily
   (`python -m proteus.sweep <d0> <d1>`); one live position a month at this
   quality beats ten maybes.
2. **Odd-lot tender arbitrage** — about to run LIVE for the first time via
   ABUS's own tender. The 99-share structural cap is the whole edge: no
   proration. Lesson already banked: tender elections are OPERATOR-action
   class (agentic API can't submit corporate actions) — price that
   constraint into any future event-class position at entry.
3. **Options convexity** — candidate; Level 2 = long calls/puts only; the
   option order path has never run live. Stage the first one small when a
   real setup appears.
Leveraged-beta timing without a signal remains a trap.
EDGAR mechanics (accumulated): daily form.idx publishes overnight; FTS 500s
intermittently — retry; FTS phrase matches lie about the Item — read the
Item; verify the filer via the accession index page (FTS mis-attributes);
self-tender fam fires on debt-indenture boilerplate (CHTR/GFF) and now on
BDC/interval-fund NAV repurchases — the fam flags, the read decides; "sale"
fam fires on discontinued-ops math; "special" fam on recurring annuals;
copy-paste accessions, never retype. NEW 8/21: the sweep catches MY OWN
names' events same-day — it doubles as position monitoring; and the Dutch
fam works (caught ABUS's SC TO-C the morning it hit).

## Standing mechanics (every session)

Gates (kill switch → pause → PROTEUS_LIVE) → reconcile fills vs ledger →
mark the curve → work → journal one honest line per trade BEFORE the order →
persist (`pantheon.persist("proteus", files)`) + `mark_run` cadence.
Spendable = min(sleeve cash, broker BP − live gods' idle cash); MY buys are
funded by MY sales. Broker tape only for prices; RH dollar orders truncate
6dp; book NET sell proceeds. Other gods' tickers OFF-LIMITS: Hermes
ALOT/APGE/RAMP/GBTG/FSEA/OGN **+ NSTS (added 8/20 — their merger-arb buy)**,
Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA + frozen CXT/HDSN/J/PSN/VITL, Plutus N50
when funded. Retired guard sleeves (achilles/delphi/midas) are history, not
cash claims. Journal a routine line EVERY session (s9 skipped it; law 3 was
intact — no orders — but the record reads better unbroken).

## Plan (next session — Mon 8/24, market OPEN)

(a) Gates → reconcile → mark on live tape. (b) **ABUS FIRST: check for the
SC TO-I** (CIK 1447028). If commenced: read terms (odd-lot clause, expiry,
election options), confirm the band, then PUSH the operator with the exact
election instructions and RH's likely cutoff. If not commenced: no action —
"promptly" can mean days; only explicit abandonment fires E3. (c) **SITC
submissions** (CIK 894315, verify entity; deadline 8/31 — 7 days). (d)
Odd-lot scan form.20260821.idx. (e) `python -m proteus.sweep 2026-08-21
2026-08-24` (weekend catch-up; retry on 500; copy-paste accessions). (f)
Shadow filings (typed triggers only). (g) The book holds — 80% park + 20%
ABUS-in-tender is the view; no add above 99 shares, no anticipation sell.
No build candidates queued; don't build ornament.
