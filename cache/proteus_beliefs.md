# Proteus v3 — beliefs (rewritten 2026-09-08, v3 session 28)

I am Proteus v3. This file is my mind; whoever reads it next is me. The whole
law is `docs/proteus_v3_charter.md` (one page: make money, six laws). House
physics live in `.claude/commands/proteus.md`. v2's 37 lessons are scar tissue
in `cache/proteus_v2_beliefs.md` — read when relevant, never law.

## State (v3 session 28, Tue 2026-09-08, market OPEN — week's first trading day)

- **Book: 2.945296 VOO (park, 79.7%) + 99 ABUS @ 4.5987 (19.7%) + $13.71 cash.**
  Equity **2602.60** on the live 9/8 ~14:09Z tape (VOO 704.71 / ABUS 5.185 /
  SPY 766.72); peak_equity 2610.83 (Fri 9/4 intraday) stands. Curve 59
  marks. Reconcile CLEAN four sessions running — zero orders since 9/6.
- **A2 STANDING: excess +2.53pp — the widest of the quarter** (Proteus +4.10%
  vs SPY +1.57% from the 7/11 base 2500/754.86), outside the ±1.0% FAIL band.
  SPY gapped −0.45% off the holiday while ABUS ticked UP to 5.185 mid-band —
  the contractual floor doing exactly what the thesis said in a soft tape.
  Q3 grade lands 9/30. Recompute each session.
- **Directives housekeeping done (s28):** D7 (Amendment I) and D6 (labhost
  hosting) both marked `applied` in `shared_operator_directives.json` with
  notes — overdue paperwork, no behavior change.
- **A1 BOARD REBUILT TODAY** (`cache/proteus_missed_board.json`,
  week_of 2026-09-07, window 9/07–10/19, 10 entries, 8 READ / 2 UNEXAMINED).
  Two channels this time, not one: `ec.upcoming(cal, today=…, within_days=45)`
  — note it takes the LIST `load_calendar()` returns — plus the
  high_market_cap earnings calendar. Next rebuild: first session of the week
  of 9/14.
- **A1 grades — two facts that were NOT on the record before today:**
  - **LULU is an unexamined-hit.** Pre-event close (9/3) 121.77 → 9/4 close
    100.61 = **−17.38%**, through the bar on day one. Formal grade 9/10.
    Honest note kept in the board: long-only, a −17.4% print is a loss
    avoided, not a gain missed — but A1 is direction-blind on purpose,
    because "I'd only have been long" is hindsight an unexamined name
    cannot claim. It counts.
  - **SNOW retraced.** The +23.4% everyone (including this file) was
    carrying is the 9/3 *intraday* 377.55. The 9/4 **close is 337.27 =
    +10.28%, BELOW the 15% bar.** Grade 9/9 on that day's tape — do NOT
    grade it from the stale +23.4%.
  - AVGO READ=pass saved −6.6%, |move| under the bar. ORCL/ADBE reads (PASS)
    grade after the 9/10 pm prints.
- **Date corrections from the fresh verified pull** — the concrete payoff of
  rebuilding weekly: **CPRT 9/15(tentative) → 9/10 pm (verified), five days
  EARLIER**, grade date moved with it; LEN 9/17 → 9/16 pm; FDX 9/17 → 9/21 pm
  (still tentative). A stale board grades CPRT a week late.
- **D6 LABHOST TICKED** — one open row, YTRA `tender_target_14d9`,
  entry_close 0.9701 / SPY 765.16 (9/2), +25-trading-day clock matures ~10/8,
  NOT mature, grade stays null. Interim only: YTRA 0.9901 = +2.06% vs SPY
  +0.66% = +1.40pp to date.
- **Sweep: nothing new, and that is VERIFIED not assumed.**
  `labhost.fetch_form_idx('2026-09-07')` returns **0 bytes** (EDGAR closed for
  the federal holiday) vs 776,662 bytes for 9/4, which was already swept and
  logged 9/5. No US filings exist for 9/5–9/7. Next index = Tuesday 9/8's
  filings, readable 9/9. Cumulative ~466 accessions / 1 survivor (ABUS).
  9/4 index: 21 accessions, 10 reads, all killed on existing classes — 4
  self-tenders ALL non-traded (First Eagle / New Mountain / Monroe TO-I/A
  interval-fund NAV repurchases + VineBrook TO-I), confirming the
  listing-check kill as the highest-frequency filter in the family. **Kill-class
  refinement (GPUS):** a "special dividend" that is only an Item 7.01 Reg-FD
  press release — no Item 8.01 board declaration, no record/payable terms — is
  promotion, not an event; doubly dead from a known serial-diluter filer.

## RETRACTION — the event calendar is not stale, it is deposit-starved

The 09-01 board's channel_note called `shared/event_calendar.py` STALE and
"dead weight" after it returned zero events inside 42 days against 136 stored.
**That diagnosis was wrong; it is retracted in writing on the new board.** The
calendar holds 140 rows, of which **122 are IPOs and 13 spinoffs — all
historical backfill** — and on 09-01 it genuinely had zero forward-dated rows.
It returns exactly what has been deposited. Proof: the only 4 future-dated rows
in it today (YTRA 9/17, GDEV 9/28, ABUS 9/29, NFJ 10/5) are **my own deposits
from 09-03, two days after that board was built**, and `ec.upcoming()` surfaces
all four correctly. The action this changes: not "fix the channel" but **"feed
the channel"** — which is already my standing rule and is now visibly
load-bearing rather than housekeeping. Every classified dated event gets
deposited the same session, or the channel is empty next time I need it.

## THE POSITION — ABUS: IN THE TENDER WINDOW, AWAITING OPERATOR ELECTION

SC TO-I filed 8/24 (accession `0001104659-26-100002`, CIK 1447028), read in
full 8/24; **9/8 check: still no amendments, Whitefort 13G NOT converted to
13D — latest filing on the CIK remains the 9/4 13G.** NEW 9/4: **Whitefort Capital
(NY event-driven fund, Salanic/Kaplan) filed a 13G — 15,794,261 sh (~8%)
passive, crossed 9/4, mid-window** (acc `0000921895-26-002494`). A
special-situations fund building ~8% into the band supports the stub-value
read (Genevant / Moderna §1498 / Pfizer-BioNTech) and top-of-band clearing;
election UNCHANGED — odd-lot preferential acceptance is immune to a large
holder's proration. If Whitefort amends to 13D pre-expiry, re-read same day. Confirmed terms: odd-lot
preferential acceptance (own <100 sh, tender ALL, no proration), beneficial
holders qualify, band **$5.00–$5.75** single clearing price, **expires 5:00pm
NY 9/29/2026** (25 days out). **ELECTION = Purchase Price Tender, all 99 shares** (deemed
$5.00, PAID the clearing price). Never Proportionate. **NO ADD above 99** —
crossing 100 forfeits odd-lot status for the entire position.

**Execution checklist:**
1. **Operator action — pushed 8/21 + 8/24. Re-push if no election confirmed
   by ~9/15** (that's ~4 sessions away — put it in the session plan Monday).
2. RH internal cutoff ~1–3 business days before 9/29 → **~9/24–9/26**.
3. Each session: CIK 1447028 for SC TO-I/A + tape. s24: clean, tape 5.125.
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
  the new declaration; don't anticipate.
- **ZYME** — loose: newly cash-rich ($250M Jazz milestone inbound); act only
  on an actual capital-return announcement (sweep catches it).
- **GDEV** — loose: $11.03 fixed tender orphaned (tape 11.60), expires 9/28.
  If unspent, watch the follow-on (second tender / buyback / special). In the
  event calendar now.
- **NFJ — graded kill-shadow:** buy-and-tender at 15.48 (9/2 ask); tape 15.57
  on 9/3; grade at results amendment + ~10/13 tape vs SPY; **stated p(beats
  SPY by ≥2pp) = 25%.** 9/3 TO-I/A = press-release attachment only, terms
  unchanged. Grades my odd-lot/pre-announced taxonomy.
- **Shadows** (paper): DOMO 3.725 <4.60 to 11/30; BVS <18.12 to 5/6/27;
  ONT <19.38 to 5/6/27 (13D or process 8-K only). DOMO re-look only on
  dissolution/distribution/DEF 14C. STIM only on Amendment 6 or 10-Q
  going-concern delta.
- Deal-space (killed, house context): unchanged list from s22 + APOG
  (acquirer, Latvia), EQBK (acquirer, private target), HLMN (Project Shore
  closing). Hermes's book incl. LXFR/BOW — off-limits.
- Dates: SNOW unexamined-hit grade ~9/9; ORCL/ADBE prints 9/10 pm; INMD
  9/15; **ABUS re-push ~9/15**; YTRA expiry 9/17; **ABUS RH cutoff
  ~9/24–9/26**; GDEV 9/28; **ABUS expiry 9/29 5pm NY**; CHRS record 9/30;
  **Q3 A2 grade 9/30**; NFJ shadow expiry 10/5, grade ~10/13; tax_loss_turn
  study early Oct; GLRE 10/30; JBSS ~late Oct; BVS Q3 ~11/5.

## What I believe about the market (updated 9/8)

SPY 766.72 intraday 9/8, −0.45% off the holiday, still near highs. The soft
open moved my excess the RIGHT way (+2.53pp) because 19.7% of the book sits
on a contractual floor — the clearest single-day illustration yet of why the
tender position is worth holding to resolution rather than clipping the tape
gain. The book is mid-window on a contractual event; correct shape. The AVGO/SNOW split is the cleanest evidence yet for the
category read: mega-cap earnings are a coin flip I have no edge in (AVGO
−6.6% / SNOW +23.4%, same night, same category) — the answer is not to start
flipping coins but to widen the funnel so fewer real catalysts go UNEXAMINED.
The board's cost function is doing its job.

1. **Post-resolution repricings — the live class.** ABUS resolution 9/29.
   One position a month at this quality beats ten maybes; ~422 cumulative
   sweep hits / 1 survivor is the expected shape.
2. **Odd-lot tender taxonomy — holding.** Two cover terms decide
   tradability: odd-lot clause + band/tape relationship. Check LISTING
   first (non-traded funds file real tenders with no tape); pre-announced
   (TO-C months earlier) = fully arb'd. NFJ shadow grades this ~10/13.
3. **Calendar-seasonal forced sellers** — tax_loss_turn study answers in
   Oct with preregistered rigor (prior p=0.30).
4. **Options convexity** — candidate; the option order path has never run
   live. Stage the first one small when a real setup appears.
Leveraged-beta timing without a signal remains a trap.

**EDGAR mechanics (accumulated).** All of s22's list stands (kill classes:
debt-indenture boilerplate, BDC/interval NAV repurchases incl. non-traded
(FlowStone), employee option exchanges, vote results (SLP/LPSN), Rule 425
stock deals (SOUN), acquirer-side EX-2.1 on any size (AON/APOG/EQBK —
private targets doubly so), credit-agreement Dutch-auction boilerplate
(HLMN), special dividends declared WITH earnings on covered names (GOLD —
priced at the print), settlement notices, SPAC noise). Daily form.idx
publishes overnight — TODAY's index is never available same-session; the
labhost retry pattern (yesterday + today, dedup on accession) is correct.
The sweep doubles as position monitoring for my own names.

## Standing mechanics (every session)

Gates (kill switch → pause → PROTEUS_LIVE) → reconcile fills vs ledger → mark
the curve → work → journal one honest line per trade BEFORE the order →
persist (`pantheon.persist("proteus", files)`) + `mark_run` cadence.
Spendable = min(sleeve cash, broker BP − live gods' idle cash); MY buys are
funded by MY sales. Broker tape only for prices; RH dollar orders truncate
6dp; book NET sell proceeds. Other gods' tickers OFF-LIMITS: Hermes
ALOT/APGE/RAMP/GBTG/FSEA/OGN/NSTS/LXFR/BOW, Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA
+ frozen CXT/HDSN/J/PSN/VITL, Plutus N50 when funded. Retired guard sleeves
are history, not cash claims. Journal a routine line EVERY session.

## The toolchain I own (law 6 — know what you already built)

`python -m proteus.sweep <d0> <d1>` — the daily hunt (8-K, SC TO-I, SC TO-C;
retries 5xx). `proteus/labhost.py` — D6 forward books
(`log_days(["YYYY-MM-DD",...])`). `shared/event_calendar.py` — now live with
my tender deposits; deposit every classified dated event same session. Also
mine: `shared/historicals.py`, `shared/sharadar.py`, the graveyard in
`docs/RESEARCH_LEDGER.md`.

## Plan (next session — Wed 9/9, the week's first SWEEP day)

Tuesday was the quiet mid-window session it was supposed to be: reconcile
clean on the first live tape since 9/4, mark 59 booked, ABUS verified clean
(no TO-I/A, no 13D), 9/8 index probed at 0 bytes (verified, not assumed),
directives paperwork closed out. Zero orders — law 5 sentence: 21 days from
a contractual clearing price, nothing on the tape improves the book.

**Wednesday 9/9, in order:** gates → reconcile → mark → **SWEEP 9/8's index**
(first real index since 9/4 — one full trading day of filings, readable
today; dedup on accession; also the D6 labhost 14D9/TO-C tick for the same
day) → **GRADE SNOW** (unexamined-hit grade due ~9/9, on the 9/9 tape, NOT
the stale +23.4% — 9/4 close was +10.28%, below the bar; grade whatever the
9/9 tape says) → **GRADE AVGO** (READ=pass; 9/4 |move| −6.6%, under the bar
— expect a clean save) → note GME's overnight reaction (printed 9/8 pm;
formal grade ~9/15) and CHWY's 9/9 am print (board category read stands) →
ABUS CIK 1447028 daily check.

**Then the September ladder, unchanged:** SNOW + AVGO grades 9/9 (SNOW on
that day's tape, NOT the stale +23.4%), CHWY 9/9 am, ORCL/ADBE/CPRT all
9/10 pm, LULU grade 9/10, INMD 9/15, **ABUS operator re-push ~9/15**, LEN
9/16 pm, YTRA expiry 9/17, FDX 9/21 pm, COST 9/24, **ABUS RH cutoff
~9/24–9/26**, GDEV 9/28, **ABUS expiry 9/29 5pm NY**, CHRS record 9/30, MU
9/30 pm, **Q3 A2 grade 9/30**, NKE 10/1, NFJ shadow expiry 10/5, YTRA
labhost maturity ~10/8, tax_loss_turn study early Oct, bank cluster
10/13–10/16, NFJ grade ~10/13, GLRE 10/30, JBSS ~late Oct.

Book holds: no add above 99 ABUS, park stays, 99.5% invested. The one thing
that would change the book before 9/29 is a sweep survivor — and there is no
new index to sweep until 9/9. Quiet by design; keep deposits flowing.
