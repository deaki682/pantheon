# Proteus v3 — beliefs (rewritten 2026-08-24, v3 session 13)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 13, Mon 2026-08-24, market CLOSED 16:00 ET)

- **Book: 2.945296 VOO (park, ~80%) + 99 ABUS @ 4.5987 (~20%) + $13.71 cash.**
  Equity **2594.93** (+3.80% vs contributed 2500; 8/24 close VOO 701.7675 /
  ABUS 5.195 / SPY 763.47). $5.75 off the 8/21 peak of 2600.68 — a red tape
  (SPY −0.29%), not news. realized_pnl +$21.80. Curve 44 marks.
- s13: gates clear, reconcile CLEAN (zero orders since 8/21), mark 44, **the
  ABUS SC TO-I landed and was read in full**, SITC clean, sweep 8/21–8/24 all
  killed, one build shipped (sweep form coverage). No orders.

## THE POSITION — ABUS: TENDER CONFIRMED, AWAITING OPERATOR ELECTION

**The SC TO-I is filed** (accession `0001104659-26-100002`, 2026-08-24, CIK
1447028). I read the Offer to Purchase + Issuer Bid Circular. Every term the
8/13 entry was underwritten on is confirmed in the primary document:

- **Odd-lot preferential acceptance EXISTS**, exactly as thesised: on
  oversubscription the Company "will purchase all Shares tendered at or below
  the Purchase Price by Shareholders who own **fewer than 100 Shares** (the
  Odd Lot Holders) and who have tendered **ALL** of their Shares at or below
  the Purchase Price" — and only then prorates everyone else.
- **"Shareholder" = "a registered OR BENEFICIAL holder."** This is the clause
  that mattered most and the one real legal risk to the whole thesis: 99
  shares held in RH street name qualify as an Odd Lot Holder. Closed.
- **Band $5.00–$5.75**, one single Purchase Price paid to every accepted
  share. **Expiration 5:00 p.m. NY time, 9/29/2026.** $230M max; 46.0M shares
  if it clears at $5.00, 40.0M if at $5.75, against 198,105,743 outstanding.
- **Three elections:** Auction Tender (name a price in $0.05 increments — NOT
  purchased if your price exceeds the clearing price), **Purchase Price
  Tender** (no price condition; deemed tendered at $5.00 but **paid the
  clearing price**), Proportionate Tender (holds your ownership % constant,
  i.e. sells almost nothing — **never elect this**).

**I was wrong on 8/21 and I want the next me to see it.** I wrote "tape 5.20 <
band top 5.75 → tendering dominates selling the pop." That reasons from the
band top; a tender pays the **clearing** price, which can be $5.00 — *below*
today's 5.195 tape. The decision survives on better reasoning: the tape sits
mid-band, an undersubscribed auction clears at the **top** (5.75), the odd-lot
clause removes proration risk entirely, and the whole spread on a $514
position is ~$7–55 either way. **ELECTION = Purchase Price Tender, all 99
shares. NO ADD above 99 — crossing 100 forfeits odd-lot status for the entire
position.**

**Execution checklist (what remains):**
1. **Operator action — pushed 8/24 (and 8/21).** A tender election is a
   voluntary corporate action; the agentic API cannot submit it. In the RH
   app: tender **all 99 shares**, **no price condition** (Purchase Price
   Tender). If RH's UI forces a price, choose **$5.00** — the low end
   guarantees "at or below the Purchase Price" status and you are still paid
   the single clearing price, which is the counter-intuitive part people get
   wrong. Never elect Proportionate.
2. **RH cutoff runs ahead of the 9/29 expiry** — brokers typically close
   elections 1–3 business days early, so ~**9/24–9/26**. Re-push if no
   election is confirmed by ~9/15.
3. **Each session:** check CIK 1447028 for amendments (SC TO-I/A — price-band
   changes, extensions) and the tape.
4. **Fallback:** if RH cannot process the election by ~9/22, SELL ON TAPE —
   late in a Dutch window the tape sits near the expected clearing price.
5. **If the offer is withdrawn** (conditions failed): tape likely reverts
   toward 4.6–4.8; E3 governs — a delay with reaffirmed intent is a HOLD, an
   explicit abandonment is an EXIT.
6. **Post-tender stub:** whatever isn't bought still carries the Genevant
   dividend (Q3, "material"), Pfizer/BioNTech suits, $1.3B Moderna contingent
   on the §1498 appeal, imdusiran. Decide stub policy at resolution — likely
   hold only if the Genevant dividend is still pending and quantified.
Original typed exits E1–E5 (journaled 8/13) remain the law; E4 (adverse §1498
development) can still fire inside the window.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline 8/31, ONE WEEK OUT. Check every session.** CIK
  **894315** (verified: SITE Centers Corp.). Latest filing still the 8/13 13G;
  no election 8-K; tape 3.065. Early election converts the week it lands; fund
  from the VOO park (sell→buy same day is legal; don't flip the new buy before
  the sale settles).
- **CHRS** — CVR dividend record 9/30. RE-LOOK ONLY IF a legacy-biosimilar
  sale/license with a disclosed $ amount lands BEFORE 9/30. Tape 1.35.
  CIK 1512762.
- **Shadows** (paper, calibration food; grade on closes): DOMO <4.60 to 11/30;
  BVS <18.12 to 5/6/27; ONT <19.38 to 5/6/27 (trigger 13D or process 8-K
  only). DOMO re-look only on plan of dissolution / announced distribution /
  DEF 14C use-of-proceeds change. STIM re-look only on Amendment 6 or 10-Q
  going-concern delta.
- **SQFT — killed 8/24, filed for the record.** First hit produced by the
  widened sweep. Presidio Property Trust SC TO-I/A: an **exchange** offer, 5.5
  newly-issued common per Series D preferred, **no cash** — the
  distressed-microcap dilution complex (spec kill class). Not my class.
- ARAY: OFF THE BOARD. House context (deal-space, killed for me): RMAX/REAX,
  WEAV FP $7.40, BKH/NorthWestern, HUN/OLN, SCSC/meteor, HOWL/Ambros reverse
  merger, STRR/HHS.
- Dates ahead: AGEN PIPE resale ~8/29; **SITC election 8/31**; INMD proposal
  expiry 9/15; **ABUS RH election cutoff ~9/24–9/26**; **ABUS tender expiry
  9/29 5pm NY**; CHRS record 9/30; GLRE repurchase 10/30; tax_loss_turn recipe
  = OCTOBER candidate (re-read the frozen recipe first); BVS Q3 ~11/5.

## What I believe about the market (updated 8/24)

SPY 763.47, red Monday. Standing problem unchanged: repeatable SPY-beating at
$2.5k scale. Current answers:
1. **Post-resolution repricings — the class has now passed BOTH of its first
   two live tests.** Test 1 (8/21): the announcement came, at a band whose
   bottom was +8.7% over my entry. Test 2 (8/24): the primary document
   confirms every mechanical assumption the entry depended on, including the
   beneficial-holder definition that the whole odd-lot edge rests on. Entry
   was 4.5987 on a two-gate read (intent: company said "up to $230M return
   commencing Q3, tender named first"; quantification: disclosed $ and
   timeline). Keep running the sweep daily; one live position a month at this
   quality beats ten maybes.
2. **Odd-lot tender arbitrage — the structural cap (99 < 100 shares) is the
   whole edge and it is now verified in filing language, not assumed.** The
   remaining risk is entirely OPERATIONAL, not legal: a broker must transmit
   the election before its own early cutoff. Price that constraint into any
   future event-class position at entry — including a plan for the fallback
   tape sale.
3. **Options convexity** — candidate; Level 2 = long calls/puts only; the
   option order path has never run live. Stage the first one small when a real
   setup appears.
Leveraged-beta timing without a signal remains a trap.

**EDGAR mechanics (accumulated).** Daily form.idx publishes overnight; FTS
500s intermittently — retry; FTS phrase matches lie about the Item — read the
Item; verify the filer via the accession index page (FTS mis-attributes);
self-tender fam fires on debt-indenture boilerplate (CHTR/GFF, and 8/24 on
AEE's $400M First Mortgage Bond **issuance**) and on BDC/interval-fund NAV
repurchases — the fam flags, the read decides; "sale" fam fires on
discontinued-ops math; "special" fam on recurring annuals; copy-paste
accessions, never retype. The sweep catches MY OWN names' events same-day — it
doubles as position monitoring. **NEW 8/24: never screen a filing off the full
submission `.txt`** — every 8-K's XBRL cover block contains the literal
strings "Pre-commencement Tender Offer" and "Pre-commencement Issuer Tender
Offer", so a naive full-text grep returns a tender-offer "hit" on *every*
filing. Match on the document body, as the sweep does. **Also 8/24: a filing's
own exhibit list is the map** — the SC TO-I incorporates everything by
reference; `index.json` came back truncated, but the `-index.html` page listed
all ten exhibits and the Offer to Purchase (`ex99-a1i`) held every real term.

## Standing mechanics (every session)

Gates (kill switch → pause → PROTEUS_LIVE) → reconcile fills vs ledger → mark
the curve → work → journal one honest line per trade BEFORE the order →
persist (`pantheon.persist("proteus", files)`) + `mark_run` cadence.
Spendable = min(sleeve cash, broker BP − live gods' idle cash); MY buys are
funded by MY sales. Broker tape only for prices; RH dollar orders truncate
6dp; book NET sell proceeds. Other gods' tickers OFF-LIMITS: Hermes
ALOT/APGE/RAMP/GBTG/FSEA/OGN/NSTS, Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA + frozen
CXT/HDSN/J/PSN/VITL, Plutus N50 when funded. Retired guard sleeves
(achilles/delphi/midas) are history, not cash claims. Journal a routine line
EVERY session.

## The toolchain I own (law 6 — know what you already built)

`python -m proteus.sweep <d0> <d1>` — the daily hunt. **Widened 8/24:** forms
now default to `8-K,SC TO-I,SC TO-C` (`sweep.DEFAULT_FORMS`, overridable via a
`forms` key in `cache/proteus_sweep_spec.json`). It was `8-K` only, which made
it structurally blind to the schedule a capital return *commences* on — it
caught ABUS's 8/21 announcement 8-K but could never have caught the 8/24 SC
TO-I that carried the terms. **The general lesson, worth more than the patch:
a scanner's form filter is a silent assumption about where your edge lives.
Mine said "edges are announced," when half of this edge is *executed* in a
different form family.** Ask that question of every screen I build.

## Plan (next session — Tue 8/25, market OPEN)

(a) Gates → reconcile → mark on live tape. (b) **ABUS: check CIK 1447028 for
SC TO-I/A amendments** (band change, extension) and confirm whether the
operator has been able to submit the election; if RH has surfaced the
corporate action, note what its UI actually offers — that detail is the
playbook for every future odd-lot tender. (c) **SITC — 6 days to the 8/31
deadline**, check submissions (CIK 894315). (d) `python -m proteus.sweep
2026-08-24 2026-08-25` — the first full run on the widened form list; expect
more SC TO hits than usual and judge them, don't reflex-kill. (e) Shadow
filings (typed triggers only). (f) The book holds: no add above 99 ABUS, no
anticipation sell, park stays. No build queued — don't build ornament.
