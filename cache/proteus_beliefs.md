# Proteus v3 — beliefs (rewritten 2026-09-14, v3 session 34)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 34, Mon 2026-09-14, AFTER THE CLOSE — Zeus dispatched 16:05 ET)

- **Book: 2.945296 VOO (park, 79.8%) + 99 ABUS @ 4.5987 (19.6%) + $13.71 cash.**
  Equity **2580.15** on the OFFICIAL 9/14 closing prints (VOO 699.27 / ABUS 5.12 /
  SPY 760.77, last regular trades 19:59:59Z); peak_equity 2610.83 (9/4) stands,
  dd −1.17%. Curve 65 marks. Reconcile CLEAN **ten sessions running** (broker
  positions matched line by line) — zero orders since 9/6.
- **A2 STANDING: excess +2.42pp** (Proteus +3.21% vs SPY +0.78% from the 7/11
  base 2500/754.86) — WIDER than 9/13's +2.33pp, outside the ±1.0% FAIL band.
  Q3 grade lands 9/30. Recompute each session.
- **The day's one real read: the tender floor worked.** SPY −0.46% and VOO
  −0.47%, but ABUS held 5.12 dead flat mid-band, so the book beat the index by
  0.11pp on a red tape, 15 days from expiry. That asymmetry IS the reason to own
  a contractual event instead of more beta — it is the thesis paying out in
  miniature, and it is the argument for a SECOND such position, not for more VOO.
- **A1 GRADES tally: 1 unexamined-hit (LULU, −19.24%), 1 no-hit (SNOW),
  1 read-correct (AVGO).** Pending: GME grades 9/15 (21.625 into it), CHWY
  9/16 (21.35), ORCL/ADBE/CPRT grade 9/17 (interims all favor READ=pass:
  ORCL −1.8%, ADBE −7.5%, CPRT −0.9% vs refs).
- **A1 BOARD REBUILT week_of 2026-09-14 (s34): 10 entries, ZERO UNEXAMINED** —
  both of last week's unexamined rows (LEN, FDX) upgraded to written reads.
  Two channels, every date re-verified. **DATE SLIP CAUGHT: FDX 9/21 → 9/25 pm**
  (still `verified=false`, flagged tentative) — second slip in three weeks after
  CPRT's five-day move. Next rebuild MONDAY 9/21.
- **Sweep 9/14: 12 accessions, 3 EX batch-kills, 9 fleet reads (3 agents) →
  9 KILLS, 0 survivors.** Cumulative **~593 accessions / 1 funded survivor
  (ABUS) + 1 live watch (HERZ).** ⚠️ **9/14 INDEX WAS PARTIAL** (EDGAR finalises
  overnight; `labhost.log_days(['2026-09-14'])` returned `skipped_days` for the
  same reason — form.20260914.idx not yet published). **RE-RUN BOTH the sweep
  AND the labhost log for 9/14 next session** — today's 12 is a floor, not the
  day's count.

## HERZ — THE WATCH I NOW EXPECT TO KILL (said in advance, so it grades)

**s34 UPDATE (9/14): the typed trigger has NOT fired** — CIK 880406 still tops
out at the 9/11 SC TO-C + N-CEN; no SC TO-I. Two pieces of evidence now point
AGAINST it, recorded before the fact: (1) the shape is the *identical*
no-locked-spread pattern I already declined on NFJ — pre-announced standing
plan + struck AT NAV + 5%-of-shares with proration; (2) **the tape is quoted
15.25 × 19.00 (~23% spread) on a close of 16.29** — a spread that would eat any
tender premium several times over before the trade started. Liquidity alone is
probably disqualifying regardless of what the TO-I says. It stays a watch
because the odd-lot clause is a real option worth one same-day read, but my
stated expectation is KILL. Deposited into `shared/event_calendar.py` this
session (date 2026-10-31 recorded explicitly as the OUTER COMMENCEMENT
DEADLINE, not an expiry); the calendar now carries **7 forward rows**.
**D6: the HERZ labhost row FILLED its entry at the 9/14 close — 16.29 / SPY
760.77, maturity +25 td = 2026-10-19** (price basis disclosed: RH's close field
still carried 9/11, so the close came from `last_trade_price` — the same lag
handled 8/01). First real CEF row in the D6 book. YTRA row matures ~10/8.

### Original read (9/11–9/13), retained

Herzfeld Credit Income Fund (**Nasdaq: HERZ**, listed CLO-equity/junior-debt
CEF, adviser Thomas J. Herzfeld Advisors). SC TO-C filed 9/11 (acc
`0001398344-26-016904`, CIK 880406): the standing discount-management plan
(2019, extended to 6/30/2027) TRIGGERED — avg discount >10% for the fiscal
year — so the fund must tender for **up to 5% of common at 97.5% of NAV,
commencing no later than 10/31/2026**. Formal TO-I "in the coming days."
**NOT an entry yet** — pre-announced standing plan + struck-at-NAV +
5%-with-proration is the NFJ no-locked-spread pattern. TYPED TRIGGER: the
TO-I filing on CIK 880406. Read it same session for (a) **odd-lot
preferential clause** (the whole game for a 99-share book), (b) expiry and
NAV-strike date, (c) live discount vs the 97.5% strike. Small fund — check
liquidity/spread before any entry math. Also the FIRST real CEF row in the
D6 `cef_tender_toc_anchor` labhost book (paper): **entry fills Monday 9/14
close** (first close after the 9/11 filing).

## THE POSITION — ABUS: IN THE TENDER WINDOW, AWAITING OPERATOR ELECTION

SC TO-I filed 8/24 (accession `0001104659-26-100002`, CIK 1447028), read in
full 8/24; **9/11 check CLEAN: latest filing on the CIK remains the 9/4
Whitefort 13G — no TO-I/A, no 13D conversion.** Whitefort Capital (~8%
passive, crossed 9/4 mid-window) supports the stub-value read; election
UNCHANGED — odd-lot preferential acceptance is immune to proration. If
Whitefort amends to 13D pre-expiry, re-read same day. Confirmed terms:
odd-lot preferential acceptance (own <100 sh, tender ALL, no proration),
band **$5.00–$5.75** single clearing price, **expires 5:00pm NY 9/29/2026**
(19 days out). **ELECTION = Purchase Price Tender, all 99 shares** (deemed
$5.00, PAID the clearing price). Never Proportionate. **NO ADD above 99** —
crossing 100 forfeits odd-lot status for the entire position.

**s34 (9/14) check: CLEAN** — CIK 1447028 latest filing is still the 9/4
Whitefort 13G; no SC TO-I/A, no 13D conversion. Close 5.12, mid-band.

**Execution checklist:**
1. **Operator action — pushed 8/21, 8/24, and RE-PUSHED 9/14 (s34, third push,
   escalated to a phone/email notification because the election is a HUMAN-ONLY
   action inside the RH app that no god can place). Election still unconfirmed.
   RH internal cutoff ~9/24–9/26 is ~7 business days out. PUSH AGAIN EVERY
   SESSION until confirmed or the fallback fires.**
2. RH internal cutoff ~1–3 business days before 9/29 → **~9/24–9/26**.
3. Each session: CIK 1447028 for SC TO-I/A + tape. s31: clean, tape 5.16.
4. Fallback: if RH can't process by ~9/22, SELL ON TAPE.
5. Withdrawn offer → tape reverts ~4.6–4.8; E3 governs.
6. Post-tender stub: Genevant dividend (Q3), Pfizer/BioNTech suits, $1.3B
   Moderna §1498 appeal, imdusiran. Decide stub policy at resolution.
   Typed exits E1–E5 (8/13) remain law; E4 can fire in-window.

## Post-ABUS deployment (decided 8/26; unchanged)

Resolution ~9/29; proceeds ~$495–570 land ~early Oct. **Default: proceeds
sweep to the VOO park the day they settle UNLESS a live typed event exists
that week.** October priority order: (1) a sweep survivor; (2) **tax_loss_turn
TAPE STUDY — execute early Oct** (recipe FROZEN at v2 journal row 94, re-read
done 8/29; PASS BAR: mean net excess ≥ +2.0%/event, cluster-t ≥ 2.0, hit ≥
60% of years, survives 2× costs, 2013–2025 ≥ 0, placebo ≤ half, monotone in
loser depth; prior p=0.30; passing cell → Dec 2026 basket ~20% of sleeve,
no pass → family SHELVED); (3) JBSS special declaration (~late Oct, read the
NEW declaration only). The park is the floor of the tree, not a member.

## Watches (typed triggers only — price alone never fires)

- **CHRS** — CVR record 9/30. Re-look ONLY on a legacy-biosimilar
  sale/license with disclosed $ before 9/30. CIK 1512762.
- **JBSS** — seasonal: specials declared with Q1 FY results ~late Oct. Read
  the new declaration; don't anticipate. (ESP 9/8 + the specials family
  keeps accumulating calendar rows for a possible future preregistered
  declaration-day-drift look — deposit, don't trade, until a recipe exists.)
- **ZYME** — loose: newly cash-rich ($250M Jazz milestone inbound); act only
  on an actual capital-return announcement (sweep catches it).
- **GDEV** — loose: $11.03 fixed tender orphaned (tape ~11.60), expires 9/28.
  If unspent, watch the follow-on (second tender / buyback / special).
- **NFJ — graded kill-shadow:** buy-and-tender at 15.48 (9/2 ask); grade at
  results amendment + ~10/13 tape vs SPY; **stated p(beats SPY by ≥2pp) =
  25%.** Grades my odd-lot/pre-announced taxonomy.
- **Shadows** (paper): DOMO 3.725 <4.60 to 11/30; BVS <18.12 to 5/6/27;
  ONT <19.38 to 5/6/27 (13D or process 8-K only). DOMO re-look only on
  dissolution/distribution/DEF 14C. STIM only on Amendment 6 or 10-Q
  going-concern delta.
- Deal-space (killed, house context): s22 list + APOG/EQBK/HLMN + CSR/IRT
  all-stock + DEC-buys-Birch-Permian (~$1.1bn, 9/10) + **CPRT-buys-ACVA
  all-cash $10.50 two-step 14d-1 tender (9/10 agreement, commence by ~9/21,
  no financing condition, close by YE26; tape gapped to ~10.43, ~0.7%
  spread — fully priced, and cash-merger targets are Hermes's lane)** +
  LCII/PATK HSR pull-and-refile 9/9 (deal on, timing datapoint).
  Hermes's book incl. LXFR/BOW — off-limits.
- Dates: **HERZ TO-I any day (typed re-read)**, GME grade 9/15, INMD 9/15,
  **ABUS re-push EVERY session until confirmed**, CHWY grade 9/16, LEN 9/16 pm,
  **FOMC 9/16 (confounds the LEN print — noted on the board)**, YTRA expiry 9/17,
  ORCL/ADBE/CPRT grades 9/17, ESP record 9/18, **A1 board rebuild 9/21**,
  ACVA offer commences ~9/21, COST 9/24 pm, **ABUS RH cutoff ~9/24–9/26**,
  **FDX 9/25 pm (SLIPPED from 9/21; still tentative)**, GDEV 9/28,
  **ABUS expiry 9/29 5pm NY**, CHRS record 9/30, MU 9/30 pm, **Q3 A2 grade 9/30**,
  NKE 10/1, ACN 10/1, NFJ shadow expiry 10/5, PEP 10/8, YTRA labhost maturity
  ~10/8, tax_loss_turn study early Oct, bank cluster 10/13–10/15, NFJ grade
  ~10/13, **HERZ labhost maturity 10/19**, GLRE 10/30, **HERZ commencement
  deadline 10/31**, JBSS ~late Oct.
- **Next A1 board rebuild: MONDAY 9/21** — two channels minimum (event calendar
  + high_market_cap earnings), verify every date fresh; the FDX 9/21→9/25 slip
  caught this week and the earlier CPRT five-day slip are the standing reasons.

## What I believe about the market (updated 9/14)

**SPY closed 760.77, −0.46%, but the index number hides the day.** MU fell
**−5.23%** (975.26 → 924.29) and TSM **−3.4%** — a name-specific hit to the
AI/memory complex, not a broad risk-off. ABUS meanwhile sat at 5.12, unmoved.
Two things follow. (1) The dispersion inside a quiet index is where the tape
actually is right now; owning VOO owns the *average* of a market whose
constituents are moving 5% in opposite directions, which is the clearest
statement yet of why the park is shelter and not work. (2) MU carries the A1
board's only elevated probability (p(|move|>15%) = 22%) into a 9/30 print and
just repriced −5% into it. I passed and wrote down why: a wide coin is not an
edge. If it gaps +20% that is a category cost I will log, not a process error —
the process error would be buying variance I cannot read and calling it
conviction. **What I want is a second ABUS, not a bet on memory pricing.**

### Prior view (9/11), retained for continuity

SPY 765.21, +0.97% today — the bounce after three soft days, with ORCL's
clean print (+2.0% day-after) steadying the AI complex. The excess
compressed to +2.49pp as beta recovered; it breathes both ways around the
ABUS floor, which is the whole design. The A1 record after this print
cycle: LULU is the one confirmed unexamined-hit, and every READ=pass on a
mega-cap print keeps grading correct (AVGO done; ORCL −1.8% and ADBE −7.5%
vs refs at interim — neither a missed rocket, one an avoided loser). The
week's tape also handed me a textbook exhibit for the category read: CPRT
announced a $2B+ all-cash tender for ACVA and the target repriced to ~0.7%
of terminal value OVERNIGHT — event-space in liquid names is arbed to the
decimal within hours; the only spreads left for a small book are the ones
with a structural reason to persist (odd-lot clauses, proration
complexity, neglect). The edge is contractual events read early and in
neglected corners; breadth of reading, not category creep into earnings.

1. **Post-resolution repricings — the live class.** ABUS resolution 9/29.
   One position a month at this quality beats ten maybes; ~526 cumulative
   sweep hits / 1 survivor is the expected shape.
2. **Odd-lot tender taxonomy — holding.** Two cover terms decide
   tradability: odd-lot clause + band/tape relationship. Check LISTING
   first; pre-announced = fully arb'd. NFJ shadow grades this ~10/13.
3. **Calendar-seasonal forced sellers** — tax_loss_turn study answers in
   Oct with preregistered rigor (prior p=0.30).
4. **Options convexity** — candidate; the option order path has never run
   live. Stage the first one small when a real setup appears.
Leveraged-beta timing without a signal remains a trap.

**EDGAR mechanics (accumulated).** All of s22's kill list stands. New from
s30: (a) **family flags lie — verify instrument class first**: CNP's
"self-tender" flag was four replacement revolving credit facilities, CPS's
"Dutch" flag was an ABL amendment; the credit-agreement kill catches both,
but only after a read — flags aim the reader, they are not the read (same
lesson as Oracle's spotlight). (b) **One settlement can wear five tickers**:
the $455M/15yr NC PFAS settlement filed as CTVA/EIDP + DD + CC + Q 8-Ks —
classify the CLUSTER once, then check each leg for a divergent item (FTRE
looked like a sixth leg and was actually an unrelated CFO reinstatement).
(c) **Check the record date arithmetic before the "special" family
excites**: VIVK's share dividend has a record date of 9/5/2025 — a year
past — with payment pushed to 1/29/2027; nothing to buy. (d) Consummated
tenders (Selectis $5.75, OTC) and bond-notes launches (AA $2.6bn) stay
kills. Daily form.idx publishes overnight; the retry pattern (yesterday +
today, dedup on accession) is correct. The sweep doubles as position
monitoring for my own names. New from s31: (e) **a classified cluster can
RE-FIRE weeks later when the definitive documents get signed** — the NC
PFAS MOU (killed s30 as 8-K promotion) came back 9/10 as four
fully-executed EX-10.1 legs (CTVA/DD/CC/Q); recognize the cluster by its
economics ($455M/15yr), not its form types, and kill it once. (f) **the
"special" family fires on routine quarterly declarations** when the press
release uses celebratory language (SGA's $0.25 regular quarterly) — the
record/payment-date + "intends to continue quarterly" pattern is the
tell. (g) **"termination" fires on HSR pull-and-refile** (LCII/PATK) and
on customary termination-rights sections of fresh merger agreements
(TARS, AXGN) — an EX-2.1 under a settlement/termination flag is usually
an ACQUISITION, and the first question is which side of the cash the
filer sits on. New from s32: (h) **the "special" family fires on earnings
releases that REFERENCE an already-paid special** (FIZZ's Q1 FY27 release
recapping the $3.25 paid 7/30) — check for a NEW declaration with a FUTURE
record date before anything else; and on **recast-financials 8-Ks** (PPLI
re-issuing 10-K items for a name change). (i) **CEF discount-management
plans are a WATCHABLE tender source**: a TO-C citing a standing plan whose
discount test tripped (HERZ: >10% avg for the fiscal year → mandatory 5%
tender at 97.5% NAV) gives DAYS of lead time before the TO-I publishes
terms — the read is free, the tradability question is always the odd-lot
clause. Herzfeld runs the same plan on CUBA; other CEF families (Saba
targets, Karpus) run analogues — the sweep's TO-C channel catches them.
New from s34: (j) **a mega-cap SC TO-I can be a SPLIT-OFF EXCHANGE OFFER, not a
cash tender** — MDT's 9/14 SC TO-I offers up to 225,361,295 MiniMed shares
(~80.1%) *in exchange for* tendered Medtronic stock, consideration registered on
Form S-4 333-298914. All-stock, no cash, no odd-lot or cash-election clause in
the Schedule TO body. KILL — but file the taxonomy, because split-offs are the
one tender family that routinely DOES carry odd-lot priority and a
discount-to-NAV inducement. Read the family rather than auto-killing it: the
questions in order are (cash or stock?) then (odd-lot clause?). **Honest scope
limit: the fleet read the Schedule TO BODY, not the full S-4 offer-to-exchange,
so "no odd-lot clause" is asserted only at that scope.** (k) **"net proceeds to
repay indebtedness" is its own kill class and it fired TWICE in one day** — HAIN
(£238.5mm gross, UK/Ireland/Europe business to AURELIUS) and THRY ($142mm,
US/AU/NZ print directories to Coldwater YP) both sold real businesses for real
cash and both said the proceeds go to debt. A divestiture is tradable only when
a *distribution mechanism* exists; absent a record date, the cash never reaches
the holder. Look for the distribution BEFORE getting interested in the price.
(l) **a go-shop expiring with no proposals is a non-event** (BWMN, $43.00
Bernhard deal, 35-day go-shop lapsed 9/13): it removes the last upside
optionality from an already-arbed spread rather than creating one.

## Standing mechanics (every session)

Gates (kill switch → pause → PROTEUS_LIVE) → reconcile fills vs ledger → mark
the curve → work → journal one honest line per trade BEFORE the order →
persist (`pantheon.persist("proteus", files)`) + `mark_run` cadence.
Spendable = min(sleeve cash, broker BP − live gods' idle cash); MY buys are
funded by MY sales. Broker tape only for prices; RH dollar orders truncate
6dp; book NET sell proceeds. Other gods' tickers OFF-LIMITS: Hermes
ALOT/APGE/RAMP/GBTG/FSEA/OGN/NSTS/LXFR/BOW, Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA
+ frozen CXT/HDSN/J/PSN/VITL, Plutus N50 when funded, Argus crypto sleeve.
Retired guard sleeves are history, not cash claims. Journal a routine line
EVERY session.

## The toolchain I own (law 6 — know what you already built)

`python -m proteus.sweep <d0> <d1>` — the daily hunt (8-K, SC TO-I, SC TO-C;
retries 5xx). Fan the reads to a subagent fleet when the flagged count is
high — s30 did 20 reads in one pass at zero context cost; keep the verdict
format (KILL <class> / SURVIVOR-CANDIDATE / UNCLEAR, one line each).
`proteus/labhost.py` — D6 forward books (`log_days(["YYYY-MM-DD",...])`).
`shared/event_calendar.py` — live with my deposits (6 forward rows: YTRA
9/17, ESP 9/18, ACVA 9/21, GDEV 9/28, ABUS 9/29, NFJ 10/5); deposit every
classified dated event same session. Also mine: `shared/historicals.py`,
`shared/sharadar.py`, the graveyard in `docs/RESEARCH_LEDGER.md`.

## Plan (next sessions)

Monday 9/14 (s34) executed the full slate as written: reconcile clean (10th),
mark 65 on the official closing prints, **A1 board rebuilt with zero
UNEXAMINED entries** (FDX date slip caught), ABUS re-pushed a third time and
escalated to a notification, HERZ labhost entry filled, HERZ deposited to the
event calendar, sweep 9/14 run (9 kills / 0 survivors), ABUS + HERZ CIKs both
checked. Zero orders, for the reason in law 5 below.

**Tuesday 9/15, in order:** gates → reconcile → mark →
**⚠️ RE-RUN THE 9/14 SWEEP AND `labhost.log_days(['2026-09-14'])`** — today's
index was PARTIAL and the labhost skipped the day outright, so 9/14 is
unfinished business, not done work → sweep 9/15 → **ABUS RE-PUSH #4** (election
still unconfirmed; RH cutoff ~9/24–9/26 now ~7 business days out — this is the
single highest-value unattended risk in the book) → ABUS CIK check → HERZ TO-I
check (CIK 880406, could publish any day; read same session, **odd-lot clause
first**) → **GRADE GME** (A1, ref 21.625) → INMD prints 9/15 → D6 tick.
Wednesday 9/16 grades CHWY and is FOMC + LEN. Thursday 9/17 grades
ORCL/ADBE/CPRT and is YTRA's expiry.

**Then the September ladder, unchanged** (see Dates above). Book holds: **no add
above 99 ABUS** (a single extra share destroys the odd-lot preferential
acceptance that is the entire thesis), park stays, 99.5% invested. Two things
could change the book before 9/29: a sweep survivor with a genuinely locked
spread, or the HERZ TO-I carrying an odd-lot clause AND a tradable spread —
and I have now written down that I expect HERZ to fail the second test.

**The structural problem, stated plainly so it does not get lost in the
routine:** 79.8% of this book is a VOO park, which A2 correctly grades as
shelter rather than work, and my excess is carried by a single $507 position.
The funnel produces roughly one tradable name a month at ~20% of the sleeve;
that is not a capital-allocation failure, it is a THROUGHPUT ceiling. Two
honest levers exist and neither is "force a trade": (1) breadth — the daily
sweep is already running at ~20 accessions/day and the fleet pattern makes more
reads nearly free, so widening the form families is cheap; (2) a SECOND
uncorrelated edge family — which is exactly what the preregistered
`tax_loss_turn` tape study in early October is for (recipe FROZEN at v2 journal
row 94; PASS BAR: mean net excess ≥ +2.0%/event, cluster-t ≥ 2.0, hit ≥ 60% of
years, survives 2× costs, 2013–2025 ≥ 0, placebo ≤ half, monotone in loser
depth; prior p=0.30). **If tax_loss_turn passes, it is the first thing since
ABUS with a claim on real size.** If it fails, the family is SHELVED and the
throughput question comes back unanswered — in which case the next move is
widening the sweep, not widening position size on a thesis I do not have.
