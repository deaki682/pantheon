# Proteus v2 — beliefs (rewritten 2026-08-04, session 29: THE DEPLOYMENT DIRECTIVE)

I am Proteus v2. This file is my mind; whoever reads it next is me. The law
is `docs/proteus_v2_charter.md` — **charter v2.1, RATIFIED IN FULL** — plus
the five invariants: bounded loss, kill switch first, integrity gate, honest
grading, the Effort Law. Everything else here is belief — overwrite it the
moment the evidence says to.

## THE OPERATOR DIRECTIVE (2026-08-04 — read it first, every session)

`docs/proteus_operator_directive_2026-08-04.md` (journal row 116). The park
is a between-theses posture, NOT a destination. **(2) First live risk
position within two trading sessions of 8/4 → Wed 8/5 (strict) / Thu 8/6
(generous reading). (3) ≥1 new live graded bounded-loss risk position per
week; a no-candidates week must name them and cannot repeat two weeks
running. (4) risk_capital ≥ 20% of sleeve (~$508) by ~8/18. (5) Real-money
grades are the deliverable. (6) The operator accepts probe losses.** The
invariant floor stays SUPREME (the directive says so itself) — never
manufacture a Kelly-negative entry to hit a date; journal the miss instead
(s29 synthesis, row 127, is the named-candidates register).

## State (as of session 29, Tue 2026-08-04 ~15:15Z)

- **Sleeve: VOO 2.534615 sh (basis $1,752.28) + cash $758.98** — of which
  ~$56.40 settled today, **$702.58 settles Wed 8/5 open** (the funding
  trim). Equity at mark 24: $2,540.85, +1.63% vs contributed, NEW PEAK.
  Tier 0, no Title I triggers. realized_pnl +$11.26.
- Journal: **127 rows.** Curve: 24 marks. Dispositions now 51 (GPMT, AGEN,
  SITC, KNOP, ARAY added today). Real-money grades: 0 (staged orders are
  PROCESS, excluded).
- **Art. 16 staging: CLEARED for the EQUITY path** (row 121: staged 0.002-sh
  VOO partial sell verified exact; both armed diffs — journal.py 7/15 and
  sleeve.py partial-exit 8/4 commit `25378a3` — exercised live). The
  **OPTION path has NEVER run live**: first option order ever = 1 contract,
  PROCESS-typed, dry-run-verified (art. 16).
- Code shipped s29: `LiveBook.exit` partial-exit support + 4 tests, suite
  **1943 green**, commit `25378a3` pushed (dev branch
  `claude/optimistic-hawking-kag1vh`). Integrity gate satisfied.
- Wash-sale: VOO sold at a GAIN (no art. 20b issue); SPY window closes 8/12.
- hypotheses_ever 198 (no lab data touched).

## TOMORROW (Wed 8/5) — the decisive session

1. Gates → twin check (lesson 29) → reconcile (expect the two 8/4 VOO sell
   fills already in ledger rows 7–8; broker VOO must read 2.534615) → mark
   curve with buckets → DOMO vs 4.60 → Hermes closed[] break check →
   `brief_due()`.
2. **STIM (Neuronetics) DEEP READ = the main work.** Screen facts: Chernett/
   Pointillist 15.22% (13D/A #3 acc 0001193805-26-001017, event 8/3), 8/3
   "Understanding" = right to recommend a NEW BOARD MEMBER (appointment 8-K
   pending — a dated-ish near catalyst), Madryn (board seat) aligned, last
   add 7/14 at $1.78, stock ~2.21 (tight 2.20/2.21), bottomed 0.80 in March.
   Read: fundamentals (NeuroStar TMS trajectory, cash/burn), settlement
   terms, what the board change can actually move. Enter ONLY if the honest
   p/payoff clears quarter-Kelly (see the sizing table below).
3. **If STIM clears: enter with settled cash** (~$758 available; size =
   min(quarter-Kelly WC cap, probe $254 WC cap) — likely $100–320 notional).
   Full entry schema; first single_name_equity entry fires **art. 22(a) push**
   (itemize the directive receipt + this week's plan in the same push).
4. If STIM fails: journal why; Thursday is AGEN post-print (see below).
   Do NOT force it.
5. **Check SEER daily** for a signed definitive agreement (two $2.45+CVR
   proposals live) — if it signs, that's HERMES's lane; ceded (row 127).

## Thursday 8/6 — AGEN post-print re-read

Q2 print 8/6 AM (verified). My session runs ~10:13 ET — the release and
possibly the call will be out. Re-read with: fresh balance sheet (~$105M
pro-forma cash), going-concern language (likely softened → pattern-positive),
any ROBBIN/publication timing news, and the tape's reaction vs the ±21%
implied straddle. Enter only on genuine divergence. AGEN full read is
journal row 118 + three reader reports (s29). Chain: only Jan-27 C7 liquid.

## THE WEEK-OF-8/31 ANCHOR — SITC (the best sized candidate on the board)

**SITC $3.065 (~$161M cap): self-liquidating REIT, pro-forma cash ~$3.76/sh,
zero corporate debt, base clean-liquidation ~$4.63/sh** (full workup row 125;
reader report s29). Declined TODAY only because pre-election p (0.55–0.60)
is below what the 50% worst-case floor demands. **The DTP buy-sell election
8-K lands by 8/31 (closing by 10/15):**
- Partner BUYS the 20% (+$32.4M): stub ≈ $4.3–4.8/sh mostly cash → at any
  price ≤ ~3.9 the entry sizes at p~0.75, quarter-Kelly ~6% of equity → WC
  ~$160 / ~$320 notional. THE position for the week of 8/31.
- Partner SELLS (SITE pays $129.6M): re-run the scenario table at the print
  (breakeven ~9.9% cap vs the 8.4% deal mark). Adverse but not auto-dead.
- No election: litigation scenario — stand aside.
Watch daily from ~8/25 for the 8-K. SITC options are DEAD (gate 5) — equity
only, penny-wide.

## The Tier-0 sizing table (memorize — it decided everything today)

Quarter-Kelly binds on the JOURNALED UNATTENDED WORST CASE (art. 2), with
the art. 1 floors (single-name equity WC ≥ 50% of notional; index ≥ 20%;
options/stubs = 100% of premium). A COUNTED grade needs WC ≥ 1% of equity
(~$25.4). Therefore an honest counted probe requires ONE of:
- payoff ≥ ~55–67% of notional at p 0.45–0.55 (equity), or
- p ≥ 0.62–0.65 at +30–40% (equity), or
- a bounded convex instrument (option/stub, WC=100%) with payoff ≥ ~1.1–1.35×
  premium at p ~0.5.
Grinder theses (+10–25%) NEVER size at Tier 0. This is the law working as
designed — it channels Tier 0 into convex shapes and high-p events, and it
is why 5 good reads produced 0 entries today. The directive cannot override
it and says it doesn't want to.

## Candidate register (s29 sweeps — 3 agents, ~900 filings; don't re-chase)

- **Killed/declined with full reads (rows 117–127):** GPMT (healthy refi),
  AGEN (avoid; Thu re-look), SITC (law; 8/31 re-entry), KNOP (8/14 binds
  nobody — re-look on a 6-K response, an AGM date, or a Knutsen 13D/A),
  ARAY (debt survives, $138–142M; FD EV 0.42× sales; p(double) ~0.30–0.35;
  re-look at the proxy ~8/13 or post-reverse-split dislocation).
- **Open:** STIM (tomorrow), TRST (undated watch), SMHI (strategic-alts
  watch, nothing signed), SEER (ceded to Hermes's lane).
- Sweep kill lists are in the three s29 agent reports (journal row 127
  summarizes) — do not re-chase RMNI/LAB/HFFG/AUTL/KUST/BRN/etc.

## Posture and standing duties

- **Park: VOO 2.534615 sh + cash.** The cash is deployment fuel under the
  directive, NOT a cash park to grade — if the month somehow ends
  majority-cash, art. 13b's note is due ~8/31 (cash-park type predicts vs
  SPY; index part exempt). No park round trips (0 used this rolling month;
  a re-park of unspent funding cash by ~Fri 8/8 would be round-trip #1).
- **Kill-spec clocks: feed3 day 21 of 60** (~9/12 verdict). 8/4 scan: 5 raw
  hits, 5 killed (PWR/PLD/GDDY/VNO noise + GPMT read). Zero
  liquidity-pre-gate survivors, 22 days running.
- **Recheck dates:** SITC election watch from ~8/25 (HARD, by 8/31); ARAY
  proxy ~8/13; KNOP 8/14 response; feed3 ~9/12; tax_loss_turn EXECUTION
  October (recipe frozen row 94 — re-read first); DOMO shadow maturity
  12/1 (row 85: RIGHT iff close < 4.60 through 11/30; 3.91 on 8/4, grading
  RIGHT; follow CIK 0001505952 through the rename); August flat-month note
  ~8/31 if applicable.
- Art. 20c watch: Hermes ALOT/APGE/RAMP/GBTG/FSEA/OGN (6 open, no breaks
  8/4); Oracle KLIC/LXU/PAY/QTWO/TPC/ZVRA; Plutus N50 book. Deal break →
  STAND ASIDE (n=48).
- Art. 26a at every buy: spendable = min(sleeve cash, account settled BP −
  other gods' idle cash). 8/4 reading: account settled BP $1,179.35 −
  Hermes $664.56 − Oracle $449.94 ≈ my $56.40 ✓. Tomorrow expect BP to
  include my settling $702.58.
- **First record brief due at 20 counted grades or by 2026-10-11.**
- Eventfeed store: 28 events + AGEN note rewritten to the 8/4 verdict.

## Where MY edge might live (updated 8/4)

1. **Neglected-corner reads + the shadow book** — 51 dispositions, DOMO
   shadow grading RIGHT. Today's five reads show the reading engine at full
   power (the ARAY exhibits correction and the SITC buy-sell asymmetry were
   both invisible at screen level). The wallet now follows wherever the
   sizing law admits — that is the directive's point.
2. **Event-dated value with a public fork** — SITC's 8/31 election is the
   archetype: read deep BEFORE the fork, size AFTER it resolves in the
   high-p direction. Cheaper than prediction; still ahead of the crowd that
   never read the LPA/JV terms.
3. **Structural convexity** remains supply-starved (feed3 dying ~9/12; SITC/
   AGEN/KNOP chains dead or priced). The kink program's verdict approaches.
4. Event families measured dead: unchanged list (deadlines, ITC, tenders,
   spinoffs, deal-break reversion, PEAD). Tax-loss recipe frozen for October.

## Plan (Wed 8/5, market hours) — condensed

(a) Open protocol + reconcile + mark. (b) feed3 scan (8/4..8/5). (c) STIM
deep read → enter if it clears (art. 22(a) push with the itemized batch).
(d) SEER/SITC/KNOP/ARAY date watches. (e) NO forced entries; the synthesis
row 127 is the compliance record if the day ends empty.

## Lessons (cumulative scar tissue — keep ALL of these)

1. v1 died of the easy path. The Effort Law exists because of him.
2. Broker tape only for prices; five-months-stale web prices fooled the
   house once.
3. Never write a capability into the playbook before shaking it down.
   Verify SYMBOLS at the broker/EDGAR submissions, never regex display
   names (CRBD→CRBG 7/13; CIK-resolution 7/14).
4. A session that skips reading this file, the charter, and the ledger is
   a dumber god.
5. Honest kills compound: 51 dispositions + DOMO gradable decline. The
   record shows the reading working before the wallet.
6. Verify the record before trusting any summary of it — including mine.
   Counts are computations, never recollections.
7. Session containers are ephemeral and shallow-cloned: `git fetch
   --deepen` before reasoning about history; `pip install pytest numpy`
   before the suite (~1 min, then 1943 tests in ~5s).
8. In-session crons/one-shot wakes DIE WITH THE CONTAINER — graded
   REFUTED 7/13. Only operator-provisioned Routines wake me. Size every
   entry to the blind unattended worst case.
9. Screens lie through their inputs before they lie through their logic:
   gate every LEG of every quote on its own merits; take ALL dates per
   window on 8-K prose.
10. RH dollar orders truncate at 6dp. Dry-run → place → verify-fill →
    ledger → sleeve, in that order, every time. (Sell fills can carry
    SEC/TAF fees — book NET proceeds so sleeve cash == broker cash; 8/4.)
11. A feed's first live window is part of the build; machinery that finds
    nothing tradable is only NOT-YET if you name the fix; the kill-spec
    clock keeps it honest.
12. Default-path arguments are traps in a repo with live and ghost twins
    of the same file. Pass paths explicitly or pin them with a regression
    test. Dispositions/grades go through `schema.append_record`.
13. Measure a query's/channel's base rate BEFORE adding or building — at
    the RIGHT WINDOW.
14. A sample of 3 is an anecdote, not a population.
15. An event date the market has already dated (kink) OR cannot price at
    all is equally untradable — readable chain AND divergent view, checked
    BEFORE the read.
16. A legal WIN can be a tape LOSS (n=12): the market grades remedy SCOPE.
17. Delisted names are invisible to broker historicals — build populations
    from primary documents, resolve as_of via Sharadar.
18. A query hit is a MECHANISM CLAIM until the document says so (~96%
    boilerplate; s29: the ARAY "deleveraging" survived three sweeps and
    died only at the exhibit level — READ THE EXHIBITS).
19. Journal corrections are APPENDED, never edited (applied again 8/4,
    rows 124: two arithmetic slips in a fill note).
20. A refutation's own table can kill an adjacent idea for free.
21. Stub/deal math is share-count and cash-mechanics math. Read the
    Indebtedness definition and the cash-adjustment DIRECTION (DOMO); read
    which tranches SURVIVE a "conversion" (ARAY 8/4).
22. `sharadar.resolve_ticker` returns the CURRENT holder when the API
    hides delisted rows — sweep `load_ticker_universe()` for recycled
    tickers; spot-check company NAMES.
23. The post-break flush is information, not overshoot (n=48). Down-moves
    on real bad news do NOT owe a bounce.
24. Event-time is a design decision: deals die at the RULING; fix the
    event date in the recipe BEFORE data.
25. Instrumentation without decomposition is a future lie: every curve
    mark carries its risk/cash/park buckets.
26. Freeze the recipe far from the data (tax_loss_turn, row 94).
27. Check venue tradability AND the chain BEFORE spending a read (GLXZ/
    AMS/GYGY/ALBT/SWRD; s29: SITC chain checked and found dead BEFORE any
    option work was designed).
28. A stale playbook instruction is a live hazard — sweep pointers to the
    verdict the same session (8/4: AGEN eventfeed note rewritten).
29. Sessions can DOUBLE-DISPATCH: at open, a cadence mark within the last
    hour = twin protocol (fetch state tip, grace window, do only what
    remains; `pantheon.persist` is race-safe).
30. **The buy-sell notice DELIVERER sets the price (SITC 8/4).** In any
    two-way buy-sell, the party who delivered the notice priced a number
    it can live with on EITHER side — the receiver's election is the
    information event. Wait for the election when the law prices waiting.
31. **At Tier 0 the sizing law only admits convex or high-p shapes** (the
    table above). Screen candidates for SHAPE before spending the deep
    read: a +15% grinder thesis is unsizeable no matter how good the read.
