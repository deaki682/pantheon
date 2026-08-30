# Proteus v3 — beliefs (rewritten 2026-08-30, v3 session 19)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 19, Sun 2026-08-30, market CLOSED — weekend)

- **Book: 2.945296 VOO (park, ~80%) + 99 ABUS @ 4.5987 (~20%) + $13.71 cash.**
  Equity **2597.13** (+3.89% vs contributed 2500; Fri 8/28 close tape VOO
  707.22 / ABUS 5.055 / SPY 769.39), −$13.58 off the 8/28 intraday peak.
  realized_pnl +$21.80. Curve 50 marks.
- s19 (Sunday, minimal by design per the s18 plan): gates clear; reconcile
  CLEAN (zero orders since Sat; broker == sleeve exact); mark 50 on Friday
  close (unchanged, closed tape); sweep SKIPPED (EDGAR files nothing
  Sat/Sun — Monday covers 8/29–8/31); no orders. LAW-6: **tax_loss_turn
  pipeline PRE-FLIGHT green** — `shared.gauntlet_fast` imports + its 12
  tests pass, sharadar/historicals import clean, NASDAQ_DATA_LINK_API_KEY
  present, frozen recipe row (v2 journal row 94) intact. The early-Oct
  study has zero missing plumbing.
- s18: ABUS no amendments; SITC clean (MONDAY 8/31 resolves the watch);
  sweep 27 hits / 0 survivors (~358 cumulative / 1); tax_loss_turn recipe
  re-read DONE — see below.

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
$5.00. The decision survives correctly: tape mid-band (~5.06–5.20),
undersubscribed auctions clear at the TOP, odd-lot removes proration, spread
on a $514 position is ~$7–55 either way.

**Execution checklist:**
1. **Operator action — pushed 8/21 + 8/24.** RH app: tender all 99, no price
   condition (Purchase Price Tender); if the UI forces a price, choose $5.00.
   **Re-push if no election confirmed by ~9/15.**
2. RH's internal cutoff runs ~1–3 business days before 9/29 → **~9/24–9/26**.
3. Each session: CIK 1447028 for SC TO-I/A (band change, extension) + tape.
   s18: clean (latest still the 8/24 SC TO-I).
4. Fallback: if RH can't process by ~9/22, SELL ON TAPE (late-window tape ≈
   clearing price).
5. Withdrawn offer → tape reverts ~4.6–4.8; E3 governs (delay+reaffirmed
   intent = HOLD, explicit abandonment = EXIT).
6. Post-tender stub: Genevant dividend (Q3, "material"), Pfizer/BioNTech
   suits, $1.3B Moderna §1498 appeal, imdusiran. Decide stub policy at
   resolution. Typed exits E1–E5 (8/13) remain law; E4 can fire in-window.

## Post-ABUS deployment (decided 8/26; tax_loss_turn re-read DONE 8/29)

Resolution ~9/29; proceeds ~$495–570 (clearing price 5.00–5.75 × 99) land
~early Oct, T+2-ish after acceptance, plus any stub decision. **Default rule:
proceeds sweep to the VOO park the day they settle UNLESS a live typed event
exists that week.** Never hold idle cash waiting for a hypothetical. October's
scheduled candidates, in priority order:
1. **A sweep survivor** — steady-state arrival is ~1/month at current funnel
   quality; a live post-resolution repricing beats everything else.
2. **tax_loss_turn TAPE STUDY — recipe re-read DONE 8/29, EXECUTE early Oct.**
   The frozen v2 recipe (v2 journal row 94) is a preregistered historical
   study, not a trade: Sharadar survivorship-free panel, 26 turn-of-year
   events 2000/01–2025/26, 4 decision cells (SMALL rank 501–2000 / MICRO
   2001–4000 × bottom-decile-YTD / fresh-Dec-pressure), entry last trading
   day ≤ Dec 21, exit last trading day of Jan, benchmark same-bucket EW.
   PASS BAR (all required): mean net excess ≥ +2.0%/event, cluster-by-year
   t ≥ 2.0, hit ≥ 60% of years, mean > 0 at 2× costs, 2013–2025 subperiod
   ≥ 0, May/Jun placebo ≤ half the winter mean, monotone in loser depth.
   Prior p=0.30 any cell passes; MICRO-at-2×-costs the likeliest death.
   DECISION (declared, one dataset one decision): a passing cell → a Dec 2026
   basket ELIGIBLE in that cell's bucket — ~20 names, ~20% of sleeve (~$520,
   ~$26/name fractional; the ABUS proceeds map onto it exactly); no passing
   cell → backlog #21 measured-dead, family SHELVED, no re-mining. The
   recipe stays FROZEN as written — v3 freedom changes sizing law, not study
   integrity. Compute-only; reuses gauntlet_fast + SEP pipeline; zero new
   data purchases.
3. **JBSS special declaration** (~late Oct, with Q1 FY results) — read the
   actual declaration for a mispriced stub; don't anticipate.
The park is the floor of this decision tree, not a member of it.

## Watches (typed triggers only — price alone never fires)

- **SITC — election deadline MONDAY 8/31. Monday's session resolves it.** CIK
  894315 (verified SITE Centers). s18: latest still the 8/13 13G, no election
  8-K; tape 3.00. Early election converts the week it lands; fund from the
  VOO park (sell→buy same day legal; don't flip the new buy before the sale
  settles). **If Monday 8/31 passes with no 8-K, the watch comes OFF the
  board** — journal the removal.
- **CHRS** — CVR record 9/30. Re-look ONLY on a legacy-biosimilar sale/license
  with a disclosed $ before 9/30. Tape 1.41. CIK 1512762.
- **JBSS — seasonal watch:** pays large specials ($2.25–$5.00/yr history),
  historically declared with Q1 FY results in **late October**. The 8/25 hit
  was only a historical chart in a year-end deck. Read the NEW declaration if
  one lands; don't anticipate.
- **ZYME — loose watch (not typed):** 2nd FDA approval triggered an INBOUND
  $250M Jazz milestone (+ up to $1.3B more + royalties). Newly cash-rich
  royalty story = a future buyback/special-announcement candidate. No action
  unless a capital-return announcement actually lands (the sweep will catch
  it); do NOT buy the FDA news itself — that's priced.
- **Shadows** (paper; grade on closes): DOMO 3.86 <4.60 to 11/30; BVS 13.845
  <18.12 to 5/6/27; ONT 17.04 <19.38 to 5/6/27 (13D or process 8-K only).
  DOMO re-look only on dissolution/distribution/DEF 14C change. STIM only on
  Amendment 6 or 10-Q going-concern delta.
- Deal-space (killed for me, house context): RMAX/REAX, WEAV FP 7.40,
  BKH/NorthWestern, HUN/OLN, SCSC/meteor, HOWL/Ambros, STRR/HHS,
  NCSM/Weatherford (election 8/31, close ~9/1), NVTS/Claros, VLY/Providence,
  BHLL/Silver47, UTZ 13E-3, GRUSF/PharmaCann NY, ESI/SOLS terminated 8/27,
  BOLD/Serapha reverse merger (amended 8/28), NEXA/Boliden. Hermes's book
  incl. LXFR (8/28) — off-limits.
- Dates ahead: **SITC election 8/31 (MONDAY)**; INMD proposal expiry 9/15;
  **ABUS re-push ~9/15 if no election**; **ABUS RH cutoff ~9/24–9/26**;
  **ABUS expiry 9/29 5pm NY**; CHRS record 9/30; **tax_loss_turn TAPE STUDY
  early Oct (recipe frozen, re-read done)**; GLRE repurchase 10/30; **JBSS
  special ~late Oct**; BVS Q3 ~11/5.

## What I believe about the market (updated 8/29)

SPY 769.39, one red Friday off all-time highs; the book is mid-window on a
contractual event with zero action available — the correct shape for an
event-driven sleeve. Standing problem unchanged: repeatable SPY-beating at
$2.6k scale. Current answers:
1. **Post-resolution repricings — the live class.** ABUS has passed both live
   tests (announcement 8/21, primary-doc confirmation 8/24); resolution is
   contractual and dated (9/29). One position a month at this quality beats
   ten maybes. The sweep is the sourcing engine; ~358 cumulative hits /
   1 survivor is the expected shape, not a failure.
2. **Odd-lot tender arbitrage — verified in filing language.** Remaining risk
   is OPERATIONAL (broker election transmission before an early cutoff).
   Price that into any future event position at entry, with a tape-sale
   fallback plan.
3. **Calendar-seasonal forced sellers — the October question.** tax_loss_turn
   is the first non-filing forced-seller lens (the sweep is blind to flows
   with no EDGAR trail). The study will answer it with preregistered rigor;
   the prior is honest (p=0.30) because the January effect is the most
   published anomaly in finance.
4. **Options convexity** — candidate; Level 2 = long calls/puts only; the
   option order path has never run live. Stage the first one small when a
   real setup appears.
Leveraged-beta timing without a signal remains a trap.

**EDGAR mechanics (accumulated).** Daily form.idx publishes overnight; FTS
500s intermittently — retry (the sweep now retries 5xx); FTS phrase matches
lie about the Item — read the Item; verify the filer via the accession index
page (URL form: `/Archives/edgar/data/<CIK>/<nodash>/<dashed>-index.htm`);
self-tender fam fires on debt-indenture boilerplate (CHTR/GFF/AEE) and
BDC/interval-fund NAV repurchases; "sale" fam on discontinued-ops math;
"special" fam on recurring annuals AND historical dividend charts in decks
(JBSS); "arbitration" fam on exec separation agreements (DLHC); **"return"
fam fires on INBOUND milestone/royalty payments (ZYME: cash TO the company —
capital return means cash TO HOLDERS)**, on LITIGATION OVER a capital-return
vehicle (CPPTL), and on reverse-merger financing mechanics (BOLD 8/28);
"favorable" fam fires on surety-indemnity settlements the company LOSES
(SLND); "settlement" fam on Chancery derivative/class settlement NOTICES
(PPC 8/28 — and a $10B covered name is priced regardless); "termination" fam
on special-meeting vote results (SLP 8/28); a mutual-consent merger
termination files from BOTH sides (ESI+SOLS, one event two accessions) and a
$6B deal-break is repriced before I can read it — the under-covered filter
applies to breaks exactly as to deals. Also benign: 21Shares crypto-ETF EX-3
batches; 8-K/As carrying acquired-company financials (GCTK/Lokahi).
Widened SC TO-I family's dominant benign population = employee option
exchanges (13e-4 repricings; kill on the cover's Title of Class). Never
screen off the full submission `.txt`; `-index.html` beats truncated
`index.json`; copy-paste accessions. The sweep catches my own names' events
same-day — it doubles as position monitoring. The kill_classes list in the
sweep spec IS the institutional memory; keep writing them down.

## Standing mechanics (every session)

Gates (kill switch → pause → PROTEUS_LIVE) → reconcile fills vs ledger → mark
the curve → work → journal one honest line per trade BEFORE the order →
persist (`pantheon.persist("proteus", files)`) + `mark_run` cadence.
Spendable = min(sleeve cash, broker BP − live gods' idle cash); MY buys are
funded by MY sales. Broker tape only for prices; RH dollar orders truncate
6dp; book NET sell proceeds. Other gods' tickers OFF-LIMITS: Hermes
ALOT/APGE/RAMP/GBTG/FSEA/OGN/NSTS/LXFR, Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA +
frozen CXT/HDSN/J/PSN/VITL, Plutus N50 when funded. Retired guard sleeves
(achilles/delphi/midas) are history, not cash claims. Journal a routine line
EVERY session.

## The toolchain I own (law 6 — know what you already built)

`python -m proteus.sweep <d0> <d1>` — the daily hunt. Forms default
`8-K,SC TO-I,SC TO-C` (spec-overridable). Per-family fetch retries EDGAR
FTS's intermittent 5xx (4 tries, bounded backoff; 4xx raise). The general
lesson stands: **a scanner's form filter is a silent assumption about where
the edge lives** — ask that question of every screen. Also mine:
`shared/historicals.py`, `shared/sharadar.py` (survivorship-free bars),
`shared/event_calendar.py`, the lab graveyard in `docs/RESEARCH_LEDGER.md`.

## Plan (next session — Mon 8/31; Sunday physics DONE s19)

THE REAL SESSION IS MONDAY 8/31:
(a) Gates → reconcile → mark (live tape). (b) **SITC — 8/31 IS THE DEADLINE.**
CIK 894315: election 8-K → convert per the watch (fund from the park,
sell→buy same day, don't flip before settlement); no 8-K by Monday's session
→ THE WATCH COMES OFF THE BOARD, journal the removal. (c) ABUS: CIK 1447028
for SC TO-I/A + tape; election is the operator's move, re-push only ~9/15.
(d) Sweep the gap 8/29–8/31 (Monday covers the weekend; nothing new files
Sat/Sun). (e) NCSM/Weatherford close ~9/1 — deal-space context only, not
mine. (f) Shadows (typed triggers only). (g) The book holds: no add above 99
ABUS, no anticipation sell, park stays. Dates ahead: INMD proposal expiry
9/15; ABUS re-push ~9/15; ABUS RH cutoff ~9/24–9/26; ABUS expiry 9/29 5pm
NY; CHRS record 9/30; tax_loss_turn TAPE STUDY early Oct (recipe frozen,
re-read DONE 8/29); GLRE repurchase 10/30; JBSS special ~late Oct; BVS Q3
~11/5.
