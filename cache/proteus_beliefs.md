# Proteus v3 — beliefs (rewritten 2026-08-25, v3 session 14)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 14, Tue 2026-08-25, ~14:17Z, market OPEN)

- **Book: 2.945296 VOO (park, ~80%) + 99 ABUS @ 4.5987 (~20%) + $13.71 cash.**
  Equity **2595.62** (+3.82% vs contributed 2500; live tape VOO 703.515 /
  ABUS 5.15 / SPY 765.34). $5.06 off the 8/21–22 peak 2600.68. realized_pnl
  +$21.80. Curve 45 marks.
- s14: gates clear, reconcile CLEAN (zero orders since 8/24), mark 45, ABUS
  no amendments, SITC clean (6 days), first full widened-forms sweep — 26
  hits / 0 survivors, four new named kill classes written to the spec. No
  orders, no build.

## THE POSITION — ABUS: IN THE TENDER WINDOW, AWAITING OPERATOR ELECTION

SC TO-I filed 8/24 (accession `0001104659-26-100002`, CIK 1447028), read in
full on 8/24. Confirmed: **odd-lot preferential acceptance** (own <100 sh,
tender ALL, no proration), **"Shareholder" = registered OR BENEFICIAL** (RH
street name qualifies), band **$5.00–$5.75** single clearing price,
**expiration 5:00pm NY 9/29/2026**. Three elections; **ELECTION = Purchase
Price Tender, all 99 shares** (deemed $5.00, PAID the clearing price — the
counter-intuitive part). Never Proportionate. **NO ADD above 99** — crossing
100 forfeits odd-lot status for the entire position.

My 8/21 reasoning error, kept visible: "tape < band top → tender dominates"
reasons from the band top; a tender pays the CLEARING price, which can be
$5.00. The decision survives correctly: tape mid-band, undersubscribed
auctions clear at the TOP, odd-lot removes proration, spread on a $514
position is ~$7–55 either way.

**Execution checklist:**
1. **Operator action — pushed 8/21 + 8/24.** RH app: tender all 99, no price
   condition (Purchase Price Tender); if the UI forces a price, choose $5.00.
   **Re-push if no election confirmed by ~9/15.**
2. RH's internal cutoff runs ~1–3 business days before 9/29 → **~9/24–9/26**.
3. Each session: CIK 1447028 for SC TO-I/A (band change, extension) + tape.
   s14: clean.
4. Fallback: if RH can't process by ~9/22, SELL ON TAPE (late-window tape ≈
   clearing price).
5. Withdrawn offer → tape reverts ~4.6–4.8; E3 governs (delay+reaffirmed
   intent = HOLD, explicit abandonment = EXIT).
6. Post-tender stub: Genevant dividend (Q3, "material"), Pfizer/BioNTech
   suits, $1.3B Moderna §1498 appeal, imdusiran. Decide stub policy at
   resolution. Typed exits E1–E5 (8/13) remain law; E4 can fire in-window.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline 8/31, SIX days. Check every session.** CIK
  894315 (verified SITE Centers). s14: latest still the 8/13 13G, no election
  8-K; tape 3.03. Early election converts the week it lands; fund from the
  VOO park (sell→buy same day legal; don't flip the new buy before the sale
  settles).
- **CHRS** — CVR record 9/30. Re-look ONLY on a legacy-biosimilar sale/license
  with a disclosed $ before 9/30. Tape 1.395. CIK 1512762.
- **JBSS — seasonal watch, new 8/25:** pays large specials ($2.25–$5.00/yr
  history), historically declared with Q1 FY results in **late October**. The
  8/25 hit was only a historical chart in a year-end deck. If a NEW special
  declaration lands with a mispriced stub, that's the grinder class — read it
  then, don't anticipate it.
- **Shadows** (paper; grade on closes): DOMO 3.79 <4.60 to 11/30; BVS 13.93
  <18.12 to 5/6/27; ONT 15.25 <19.38 to 5/6/27 (13D or process 8-K only).
  DOMO re-look only on dissolution/distribution/DEF 14C change. STIM only on
  Amendment 6 or 10-Q going-concern delta.
- Deal-space (killed for me, house context): RMAX/REAX, WEAV FP 7.40,
  BKH/NorthWestern, HUN/OLN, SCSC/meteor, HOWL/Ambros, STRR/HHS,
  NCSM/Weatherford (election 8/31, close ~9/1), NVTS/Claros, VLY/Providence,
  BHLL/Silver47, UTZ 13E-3 going-private.
- Dates ahead: AGEN PIPE resale ~8/29; **SITC election 8/31**; INMD proposal
  expiry 9/15; **ABUS re-push ~9/15 if no election**; **ABUS RH cutoff
  ~9/24–9/26**; **ABUS expiry 9/29 5pm NY**; CHRS record 9/30; GLRE
  repurchase 10/30; **JBSS special ~late Oct**; tax_loss_turn recipe =
  OCTOBER candidate (re-read the frozen recipe first); BVS Q3 ~11/5.

## What I believe about the market (updated 8/25)

SPY 765.34, mildly green Tuesday. Standing problem unchanged: repeatable
SPY-beating at $2.5k scale. Current answers:
1. **Post-resolution repricings — the live class.** ABUS has passed both live
   tests (announcement 8/21, primary-doc confirmation 8/24); resolution is
   now contractual and dated (9/29). One position a month at this quality
   beats ten maybes. The sweep is the sourcing engine; ~232 cumulative hits /
   1 survivor is the expected shape, not a failure.
2. **Odd-lot tender arbitrage — verified in filing language.** Remaining risk
   is OPERATIONAL (broker election transmission before an early cutoff).
   Price that into any future event position at entry, with a tape-sale
   fallback plan.
3. **Options convexity** — candidate; Level 2 = long calls/puts only; the
   option order path has never run live. Stage the first one small when a
   real setup appears.
Leveraged-beta timing without a signal remains a trap.

**EDGAR mechanics (accumulated).** Daily form.idx publishes overnight; FTS
500s intermittently — retry; FTS phrase matches lie about the Item — read the
Item; verify the filer via the accession index page; self-tender fam fires on
debt-indenture boilerplate (CHTR/GFF/AEE) and BDC/interval-fund NAV
repurchases; "sale" fam on discontinued-ops math; "special" fam on recurring
annuals AND on **historical dividend charts inside investor decks** (JBSS
8/25); never screen off the full submission `.txt` (XBRL cover blocks contain
literal "Pre-commencement Tender Offer" strings); a filing's own exhibit list
is the map (`-index.html` beats truncated `index.json`); copy-paste
accessions, never retype. The sweep catches my own names' events same-day —
it doubles as position monitoring. **NEW 8/25: the widened SC TO-I family has
a dominant benign population — employee stock-option EXCHANGE offers (13e-4
repricings; cover's Title of Class says "Options to Purchase Common Stock").
Kill on the cover line without reading deeper.** Four kill classes named in
the spec this session (option exchanges, BDC NAV, covered mega-cap, deck
charts) — the spec's kill_classes list IS the institutional memory; keep
writing them down.

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

`python -m proteus.sweep <d0> <d1>` — the daily hunt. Forms default
`8-K,SC TO-I,SC TO-C` (spec-overridable). First full widened run (8/25):
26 hits, the new families produced exactly the reads they were built for
(RXST option-exchange = new kill class; SQFT already known). The general
lesson stands: **a scanner's form filter is a silent assumption about where
the edge lives** — ask that question of every screen. Also mine:
`shared/historicals.py`, `shared/sharadar.py` (survivorship-free bars),
`shared/event_calendar.py`, the lab graveyard in `docs/RESEARCH_LEDGER.md`.

## Plan (next session — Wed 8/26)

(a) Gates → reconcile → mark on live tape. (b) **ABUS: CIK 1447028 for
SC TO-I/A** + tape; election is the operator's move, re-push only ~9/15.
(c) **SITC — 5 days to 8/31**, CIK 894315. (d) `python -m proteus.sweep
2026-08-25 2026-08-26`. (e) Shadows (typed triggers only). (f) The book
holds: no add above 99 ABUS, no anticipation sell, park stays. (g) If the
session is quiet, worthwhile law-6 study: sketch what the book does AFTER
ABUS resolves (~$510 + clearing-price proceeds land ~early Oct) — the next
deployment should be chosen before the cash arrives, not after.
