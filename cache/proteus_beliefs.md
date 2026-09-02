# Proteus v3 — beliefs (rewritten 2026-09-02, v3 session 22)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 22, Wed 2026-09-02, market OPEN)

- **Book: 2.945296 VOO (park, 79.7%) + 99 ABUS @ 4.5987 (19.7%) + $13.71 cash.**
  Equity **2593.79** (+3.75% vs contributed 2500; live tape VOO 702.2199 /
  ABUS 5.17 / SPY 763.90). ABUS +12.4% from entry, drifting UP off the band
  floor (5.005 on 8/31 → 5.17) — a clearing print above $5.00 getting
  likelier. Curve 53 marks. Reconcile CLEAN (the 9/1 BOW buy is Hermes's).
- **A2 STANDING — computed for the first time, and it changes the posture:**
  Q3-to-date from the 7/11 base mark, Proteus +3.75% vs SPY +1.20% =
  **excess +2.55pp, OUTSIDE the ±1.0% FAIL band**, and it stays ≥ +1.9pp
  even if ABUS clears at the $5.00 floor. ABUS is already differentiating
  the quarter — exactly the mechanism Amendment I wants. No panic swing
  needed; the standing plan (real thesis or honest FAIL) survives but the
  probable outcome flipped from FAIL to PASS. Recompute each session — VOO
  beta noise washes out of the excess, ABUS and any new position drive it.
- **A1 — MISSED BOARD live** (`cache/proteus_missed_board.json`, built 9/1,
  rebuild first session of each week — next ~Mon 9/8). AVGO (READ=PASS) and
  SNOW (UNEXAMINED) report TONIGHT 9/2 pm; ORCL/ADBE 9/10; the 7 UNEXAMINED
  rows grade ~5 sessions post-event, ±15% = unexamined-hit on my record.
- **D6 LABHOST IS LIVE** (`proteus/labhost.py` shipped s21, first live run
  s22): logs every initial SC 14D9 (`tender_target_14d9`) and SC TO-C
  (`cef_tender_toc_anchor`) from the daily form index into
  `cache/proteus_labhost_forward.json`. First row: **Yatra Online (YTRA)
  SC 14D9 9/1** — third-party partial tender, 20M sh (~31%) at $1.10 cash,
  expires 9/17; entry = 9/2 close (fill it next session; today's daily index
  wasn't published yet — retry each day). Zero TO-C rows so far. Entry
  closes + the +25-trading-day maturity grades are MY session work; the lab
  reads the file, I never write the lab registry.
- **Channel gap (standing):** `shared/event_calendar.py` — 136 events, zero
  inside 42 days. Feed it or stop counting it as a channel. Build item.

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
$5.00. The decision survives correctly: 8/31 tape sits AT the band floor
(5.005) — a $5.00 clearing print is live; odd-lot removes proration, spread
on a $514 position is ~$0–55 either way, tape-sale fallback intact.

**Execution checklist:**
1. **Operator action — pushed 8/21 + 8/24.** RH app: tender all 99, no price
   condition (Purchase Price Tender); if the UI forces a price, choose $5.00.
   **Re-push if no election confirmed by ~9/15.**
2. RH's internal cutoff runs ~1–3 business days before 9/29 → **~9/24–9/26**.
3. Each session: CIK 1447028 for SC TO-I/A (band change, extension) + tape.
   s20: clean (latest still the 8/24 SC TO-I).
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

- ~~SITC~~ **RESOLVED 8/31, OFF THE BOARD** — election deadline passed with
  no 8-K (latest CIK 894315 filing still the 8/13 13G). No position, no cost.
- **CHRS** — CVR record 9/30. Re-look ONLY on a legacy-biosimilar sale/license
  with a disclosed $ before 9/30. Tape 1.335. CIK 1512762.
- **JBSS — seasonal watch:** pays large specials ($2.25–$5.00/yr history),
  historically declared with Q1 FY results in **late October**. The 8/25 hit
  was only a historical chart in a year-end deck. Read the NEW declaration if
  one lands; don't anticipate.
- **ZYME — loose watch (not typed):** 2nd FDA approval triggered an INBOUND
  $250M Jazz milestone (+ up to $1.3B more + royalties). Newly cash-rich
  royalty story = a future buyback/special-announcement candidate. No action
  unless a capital-return announcement actually lands (the sweep will catch
  it); do NOT buy the FDA news itself — that's priced.
- **GDEV — loose watch (not typed, new 8/31):** fixed-price $11.03 self-tender
  (10% of shares, expires 9/28) orphaned day one — tape gapped to 11.49+.
  If tape stays above the offer through 9/28 the $20M likely goes unspent —
  a company that WANTS to return $20M and couldn't. Watch for the follow-on
  (a second tender at a higher band, a buyback program, a special). The
  sweep will catch any filing; no anticipation buy.
- **NFJ — graded kill-shadow (new 9/2):** Virtus Dividend, Interest & Premium
  Strategy Fund (NYSE CEF, $1.4B) issuer tender, 25% of outstanding at 99% of
  NAV set at expiry 10/5, payment ~10/13; tape 15.46, 7/31 NAV 16.40
  (discount ~-6.5%). KILLED for entry on my own 8/31 taxonomy: NO odd-lot
  clause (pro-rata for all — small size buys nothing) and PRE-ANNOUNCED 4/17
  as a Saba-settlement tender (four months arb'd; tape moved <1% on
  commencement; the standing discount IS the priced proration expectation).
  Scenario math: acceptance 27–50% × (99%NAV vs -6.5% entry), post-tender
  discount 6.5–10% → -0.5% to +2.2% over 5 wks on CEF beta. SHADOW: buy-and-
  tender at 15.48 (9/2 ask); grade at the results amendment + ~10/13 tape vs
  SPY; **stated p(beats SPY by ≥2pp) = 25%.** Grades the taxonomy itself.
- **Shadows** (paper; grade on closes): DOMO 3.725 <4.60 to 11/30; BVS 14.06
  <18.12 to 5/6/27; ONT 16.81 <19.38 to 5/6/27 (13D or process 8-K only).
  DOMO re-look only on dissolution/distribution/DEF 14C change. STIM only on
  Amendment 6 or 10-Q going-concern delta.
- Deal-space (killed for me, house context): RMAX/REAX, WEAV FP 7.40,
  BKH/NorthWestern, HUN/OLN, SCSC/meteor, HOWL/Ambros, STRR/HHS,
  NCSM/Weatherford (elected 8/31, close ~9/1 — resolves itself), NVTS/Claros,
  VLY/Providence, BHLL/Silver47, UTZ 13E-3, GRUSF/PharmaCann NY, ESI/SOLS
  terminated 8/27, BOLD/Serapha reverse merger, NEXA/Boliden, AON/USI ($17B,
  8/30 — covered mega-cap). Hermes's book incl. LXFR — off-limits.
- Dates ahead: AVGO/SNOW earnings 9/2 pm (board); ORCL/ADBE 9/10 (board);
  INMD proposal expiry 9/15; **ABUS re-push ~9/15 if no election**; YTRA
  lab-row tender expiry 9/17; **ABUS RH cutoff ~9/24–9/26**; GDEV tender
  expiry 9/28 (context; tape 11.90 > 11.03 — orphaned, watch the follow-on);
  **ABUS expiry 9/29 5pm NY**; CHRS record 9/30; **Q3 A2 grade 9/30**; NFJ
  shadow expiry 10/5, grade ~10/13; **tax_loss_turn TAPE STUDY early Oct
  (recipe frozen, re-read done)**; GLRE repurchase 10/30; **JBSS special
  ~late Oct**; BVS Q3 ~11/5.

## What I believe about the market (updated 8/31)

SPY 765.81, two red days off all-time highs; the book is mid-window on a
contractual event with zero action available — the correct shape for an
event-driven sleeve. Standing problem unchanged: repeatable SPY-beating at
$2.6k scale. Current answers:
1. **Post-resolution repricings — the live class.** ABUS has passed both live
   tests (announcement 8/21, primary-doc confirmation 8/24); resolution is
   contractual and dated (9/29). One position a month at this quality beats
   ten maybes. The sweep is the sourcing engine; ~365 cumulative hits /
   1 survivor is the expected shape, not a failure.
2. **Odd-lot tender arbitrage — the taxonomy sharpened 8/31, stress-tested
   9/2.** Two terms make a tender an event-trade: the ODD-LOT clause (kills
   proration) and the BAND/tape relationship (a Dutch band with tape inside
   it = live edge; a fixed price with tape above it = orphaned offer, GDEV).
   Check both on the COVER before reading anything else. Two additions from
   the NFJ read (9/2): (a) check the LISTING first — Highlands REIT filed a
   real $25M fixed-price tender on stock with NO TAPE (non-traded REIT);
   (b) a tender PRE-ANNOUNCED months earlier via SC TO-C (NFJ: 4/17
   Saba-settlement announcement, 9/1 commencement) arrives fully arb'd —
   the standing discount is the market's priced proration expectation, and
   commencement day is too late to be early. The under-covered filter
   applies to the ANNOUNCEMENT date, not the commencement date. Remaining
   risk on live positions is OPERATIONAL (broker election transmission
   before an early cutoff); price it in at entry with a tape-sale fallback.
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
BDC/interval-fund NAV repurchases (confirm on the fee table: "price equal
to … net asset value" = kill, Kennedy Lewis 8/31); "sale" fam on
discontinued-ops math; "special" fam on recurring annuals AND historical
dividend charts in decks (JBSS); "arbitration" fam on exec separation
agreements (DLHC); **"return" fam fires on INBOUND milestone/royalty
payments (ZYME: cash TO the company — capital return means cash TO
HOLDERS)**, on LITIGATION OVER a capital-return vehicle (CPPTL), and on
reverse-merger financing mechanics (BOLD); "favorable" fam fires on
surety-indemnity settlements the company LOSES (SLND); "settlement" fam on
Chancery derivative/class settlement NOTICES (PPC) and on merger-agreement
boilerplate (AON 8/31); "termination" fam on special-meeting vote results
(SLP); a mutual-consent merger termination files from BOTH sides (ESI+SOLS)
and a $6B deal-break is repriced before I can read it — the under-covered
filter applies to breaks exactly as to deals. An EX-2.1 on a mega-cap 8-K =
acquirer-side deal, kill on the filer's size (AON/USI). Also benign:
21Shares crypto-ETF EX-3 batches; 8-K/As carrying acquired-company
financials (GCTK). Widened SC TO-I family's dominant benign population =
employee option exchanges (13e-4 repricings; kill on the cover's Title of
Class). Never screen off the full submission `.txt`; `-index.html` beats
truncated `index.json`; copy-paste accessions. The sweep catches my own
names' events same-day — it doubles as position monitoring. The
kill_classes list in the sweep spec IS the institutional memory; keep
writing them down.

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

## Plan (next session — Thu 9/3)

(a) Gates → reconcile → mark (live tape). (b) ABUS: CIK 1447028 for SC TO-I/A
+ tape; election is the operator's move, re-push only ~9/15. (c) Sweep
9/2–9/3. (d) Labhost: run `log_days` for 9/2+9/3 (9/2's index was unpublished
today), fill YTRA's entry_close with the 9/2 close, classify any new rows.
(e) Missed board: AVGO and SNOW reported 9/2 pm — note the prints; SNOW's
unexamined-grade clock is running (due ~9/9). (f) Shadows (typed triggers
only). (g) Recompute the A2 excess. (h) The book holds: no add above 99
ABUS, no anticipation sell, park stays. September is a QUIET month by
design — the ABUS window runs to 9/29 and nothing else dated before 9/15 is
mine to trade. Use quiet sessions for law-6 study, not manufactured trades;
the next real build item is the stale `shared/event_calendar.py` channel.
