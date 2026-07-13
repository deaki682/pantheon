# Proteus v2 — playbook (started 2026-07-11, session 3)

Working standards I hold myself to before capital moves. Beliefs may change;
these change too — but only by rewrite-with-reasoning, never by quiet neglect.

## Options-convexity entry checklist (hunting ground #2)

**STATUS: LEVEL 2 APPROVED (2026-07-11, operator confirmed; verified at
broker — `option_level_2` on 563854249).** Level 2 on RH = **long calls,
long puts, covered calls, cash-secured puts**. NOT permitted at Level 2:
debit spreads, credit spreads (any multi-leg) — those need Level 3. So the
charter's spread instruments stay dormant; the executable convex menu is
long options only (max loss = premium, inherently bounded — sits inside
the charter's instrument rule with no extra cash-reserve mechanics).
Checklist below is ACTIVE for long calls/puts.

**BUILD PRECONDITION — CLEARED 2026-07-11 session 4 (commit `a8c2938`,
suite 1808 green).** (a) `proteus/options.py` + sleeve `option_positions`:
long calls/puts live honestly with `max_loss = net debit` computed at
entry; journal validates `instrument="option"` entries against gates 2/3/4
mechanically (catalyst-expiry buffer, debit/max_loss consistency,
edge-arithmetic floor); worthless expiry records at 0.0. (b) Chain glue
executed on real SPY chain data (Sep-18 755 straddle): `priced_read`
breakeven cross-checked EXACTLY against the broker's own break_even_price
(776.42). (c) `review_option_order` dry-run returned clean structure on
563854249 — order_checks (it flags wide spreads itself:
OPTION_WIDE_BID_ASK_SPREAD), fees, collateral, live greeks. NO order
placed. (d) sourcing beyond tenders: still unbuilt — the only remaining
gap, and it's a research gap, not plumbing.
**Fee reality (from the dry-run): ~$0.04/contract/side (OCC+ORF).**
Immaterial vs a $150+ debit; remember it exists on multi-contract size.
Remaining hard rule: the 7 gates below, every time.

No options order without ALL of:

1. **Primary document read.** The catalyst thesis rests on a filing,
   transcript, or contract I read myself — never a headline or a screen.
   Cite the document in the journal entry.
2. **Dated catalyst.** A calendar-anchored event (ruling, expiration,
   PDUFA, deal vote, earnings) inside the option's life, with time buffer:
   expiry ≥ 2 weeks past the latest plausible catalyst date.
3. **My probability vs the market's price.** Write p(thesis) and the
   implied move / implied probability from the option chain BEFORE entry
   (use `catalyst/` implied-move math as the priced-in baseline). Entry
   requires my estimate to diverge enough that being half-wrong still
   breaks even. Show the arithmetic in the journal.
4. **Defined max loss = premium (or net debit), sized as a full loss.**
   Position sized so a 100% loss is an acceptable, journaled outcome —
   never "it won't go to zero."
5. **Liquidity read.** Bid-ask spread checked at the actual strikes; a
   spread > ~10% of premium must be justified in writing or the trade is
   skipped (the fill is the cost).
6. **Typed kill condition.** A falsifiable exit trigger written at entry:
   catalyst passes without the predicted outcome → exit; thesis-input
   invalidated (deal breaks, ruling adverse) → exit. Time decay is not a
   kill; the kill is thesis-typed.
7. **Falsifiable prediction with a date** in the journal BEFORE the order,
   graded as written at maturity. Profitable-but-wrong = LUCK.

## Options sourcing doctrine (gap d) — v1, 2026-07-12 (session 5)

**Measured kill: the retail-calendar channel is dead as a convexity source.**
Tested Sunday 2026-07-12 on the two genuinely small names with Q3 PDUFA
dates from the free calendars (Friday 7/10 tape, indicative):

- REPL (~$800M, RP1 melanoma resubmission, PDUFA 2026-08-02): Aug-21
  near-money calls bid/ask 3.50/4.80 ($10c, 31% of mark), 3.10/4.70
  ($11c, 41%), 3.00/4.30 ($12c, 36%); IV 269–300%. Gate 5 fails 3×
  over, and the 270% IV means the binary is fully specialist-priced —
  no gate-3 divergence claim is honest here.
- SVRA (~$1B, molgramostim aPAP, PDUFA 2026-08-22): monthlies only, and
  Aug-21 expires ONE DAY before the catalyst (gate 2 forces Nov-20);
  Nov-20 calls show ZERO BID at every strike, OI 32–220. Untradable.

**The generalization: the calendar IS the crowd.** Any event listed on a
free/retail catalyst calendar (PDUFA trackers, FDA calendars, whisper
sites) is presumptively priced — the IV pump is visible proof. "Neglected"
must be measured in the CHAIN (no event premium), not in market cap.
A calendar name is only revisitable with tape evidence the chain has NOT
priced the date.

**The inverted doctrine (the only honest gate-3 template found so far):**

1. Source dated events from PRIMARY feeds retail calendars don't carry —
   Federal Register agency notices, dockets, merger outside dates buried
   in DEFM14As — and verify the date in the source document itself.
2. Mechanical divergence test: does the chain's IV term structure show a
   kink/hump at the expiry straddling the event? NO kink + verified date
   = the market hasn't dated the event; that mispricing is structural,
   not a claim to out-handicap specialists.
3. Only then the document read, the 7 gates, and the journal.

**Feed #1 PROVEN 2026-07-12 (shaken down before being written here):**
Federal Register API — machine-readable, dated, filterable by agency;
267 ITC §337 target-date docs returned on the test query. Caveat from the
same test: ITC parties skew mega-cap/foreign (GM, Caterpillar-class) —
this is a slow-drip monitor, not a name factory. **End-to-end validation
2026-07-13:** the feed surfaced its first live candidate (Cricut GEO win,
337-TA-1426) and the document read correctly KILLED it — the remedy was
narrow (design patent on EasyPress housing; the real competitor HTVRONT
adjudicated non-infringing on redesigns) and the tape's non-reaction was
efficiency, not neglect. The pipeline works; the answer was no.

**Feed #2 PROVEN 2026-07-13: EDGAR DEFM14A vote/outside dates —
`proteus/eventfeed.py`** (13 proxies w/ outside-date language in 30d;
LPSN extraction verified against the document: meeting 8/20, initial
outside date 10/21 auto-extending to 12/5). Store at
`cache/proteus_eventfeed.json`; plausibility rule drops events dated ≤
filing date (6/21 raw extractions failed it — the regexes DO
mis-extract; the store is an aim, never an authority). Honest caveat:
announced-deal votes are specialist-covered; the neglected residue
(extensions, financing deadlines, small deals) is the target. Feeds
still NOT shaken down (do not cite): FERC/state-PUC rate cases,
bankruptcy confirmation dockets.

**Next build — now unblocked (13 upcoming stored events to run it on):**
ATM-IV-per-expiry kink detector reusing `proteus/options.py` chain glue;
run as the cheap screen between feed hit and document read. Build it in
a MARKET-HOURS session — overnight IV marks are stale/unreliable for a
term-structure read.

**Kink screen — first live run, 2026-07-13 (5 names, all killed):** the
DEFM14A merger-vote channel is a CATEGORY ERROR for the kink screen.
Announced cash-merger targets price their event risk in the EQUITY SPREAD
(OGN 13.53 vs $14.00 offer), not the vol surface; their ATM chains are
functionally dead (volume 0 on all 26 ATM contracts checked across
OGN/EQH/CRBG/AXTA, OI single digits, MM spreads up to 0.05/3.90). A
letter-of-the-law UNPRICED on a dead chain fails gate 5 before the
document read is even earned. RULE: the kink screen only runs on names
whose chain shows LIVE two-sided ATM markets (a bid-side liquidity
pre-gate before the read); merger votes feed spread/tender structures,
never long options. Same run exposed and fixed a screen bug: per-leg IV
admission (own bid + IV ≥ 1%), commit `19b71f1` — the raw EQH "kink"
(1.19) was a zero-bid put's degenerate IV blended into a real call IV;
fixed-gate ratio 1.01. Supply for the screen must come from UNDATED
non-merger events (Federal Register/ITC, extensions, financing
deadlines) — still the open sourcing gap.

## Order path — STAGED AND CLEAN (art. 16, 2026-07-13)

The live equity order path (schema journal → guards → place_equity_order
→ ledger → LiveBook enter/exit) completed its one clean staged use: $5.00
SPY round trip, both fills <0.2s, dry-run clean, ledger and sleeve exact.
The path carries full Title I sizes. Two permanent mechanics facts bought
for $0.0012 (the realized spread loss):
- **RH dollar-based orders TRUNCATE share quantity at 6dp, never round.**
- Market fills on penny-wide ETFs land at/inside the quoted ask in
  sub-second time; fill-vs-ask drift on the two legs was ≤0.05%.
The OPTION order path has never placed a live order — its first live use
remains staged (art. 16) when the first option entry comes.

## Posture — PARKED IN INDEX since 2026-07-13 (art. 13b-exempt)

VOO 3.536615 sh @ 691.339 (order `6a54f8a9`), ~$55 cash. The park is the
no-edge default, NOT a thesis: it exits only to fund an entry clearing
the full bar, or on the kill switch. More than one index-park round trip
in a rolling month = a thesis in disguise (art. 1). GFV note: park sized
to settled funds only; staged-sell proceeds ($4.998) settle 2026-07-14.

## Odd-lot tender — broker mechanics (kill-condition #2) — ANSWERED 2026-07-11

All five unknowns answered 2026-07-11 by the operator via RH support chat
(plus RH's published fee schedule for Q3). Evidence grade: SUPPORT-CHAT
CLAIMS — good enough to keep the hunting ground alive and shape the live
test; the first real deal's 99-share test remains the proof (support
scripts can be wrong about back-office DTC behavior).

1. **Submission + cutoff (Q1):** Election is EMAIL-triggered — RH emails
   offer materials with a BROKER deadline, typically 1–3 business days
   before the official expiration (exact date in the event email).
   Election via the linked voluntary-election site, or through support
   with symbol + share count. Operational note — Gmail watch PROVEN
   2026-07-11 (after one false start the same day: the connector was
   initially authenticated to the operator's WORK Google account, which
   had zero RH mail; the operator re-pointed it at deaki682@gmail.com,
   which IS the RH notification address — 201 RH threads/90d visible,
   incl. the Level 2 approval email). On a live deal: watch
   `from:robinhood.com` + the deal symbol for the event email and
   extract the exact broker deadline. No historical tender email exists
   in the inbox (none ever held), so the template is unknown — FALLBACK
   RULE STANDS until the first real event email is seen: assume broker
   cutoff = official expiration MINUS 3 business days and hand the
   operator the ready-to-paste election EARLY.
2. **Odd-lot pass-through (Q2, the make-or-break):** FAVORABLE claim —
   RH collects individual customer elections and submits them to the
   tender agent per-customer; no bulk aggregation destroying odd-lot
   status. "Tender ALL shares, hold <100" attestation expected to pass
   through. PENDING LIVE VERIFICATION — the 99-share test's journaled
   prediction: un-prorated acceptance per support's 2026-07-11 statement.
3. **Fees (Q3):** $0 — confirmed BOTH in RH's published fee schedule
   (cdn.robinhood.com RHF Fee Schedule: voluntary corporate action /
   election $0) and by support. Residual: SEC/TAF regulatory sell fees
   (pennies at 99-share size) + any tender-AGENT fee disclosed in offer
   docs (the dossier read covers that per-deal).
4. **Timing (Q4):** Shares are RESTRICTED from trading once the election
   is processed until the offer closes. Cash lands a few business days
   after the payment date and arrives SETTLED — immediately deployable,
   no GFV risk on redeploy. Deal math: annualize per-event return over
   purchase → cash-in-hand (payment date + ~3bd buffer), not to expiry.
5. **Withdrawal (Q5):** Elections can be withdrawn/changed until the
   BROKER deadline (not the offer's official expiry — narrower than the
   SEC 14d-7 legal right). TACTIC: elect LATE, near the broker deadline,
   keeping the sell-on-market exit alive as long as possible; withdrawal
   is the only exit once elected. KNOWN TAIL RISK (journaled): an offer
   materially amended AFTER the broker cutoff could trap the position —
   mitigated by the ≥10-business-day extension material amendments
   require, which should generate a new broker deadline.

Plan unchanged: first LIVE deal that passes the filing read gets the
minimum-size test (99 shares, worst case = cost basis, journaled as an
operational experiment — the prediction is about MECHANICS, not price).
Kill-spec stands: actionable supply <12/yr, OR RH can't deliver
un-prorated acceptance (now testable against a documented claim), OR
median $/event <$150 → kill the hunting ground.

**OPERATOR DEPENDENCY (flagged to operator 2026-07-11, acknowledged):
the tender ELECTION has no API path** — the agentic toolset has no
corporate-action endpoint. I buy the shares; the OPERATOR submits the
tender instruction in-app/via RH support. On a live deal: notify the
operator EARLY with symbol, share count, the odd-lot election language
quoted from the offer document, and the broker cutoff (assume 1–3 days
before offer expiry). Build the timeline around the operator's
availability, not the offer's last day.

## Settled-cash discipline (cash account physics)

- Before ANY order: settled buying power ≥ order size (2026-07-11 reading:
  $813.15 BP vs $2,681.63 cash — sweeps not yet settled; Monday's first
  check is BP, not cash).
- T+1: proceeds from a sale settle next trading day; buying with unsettled
  proceeds then selling = good-faith violation. Never buy-then-sell inside
  the settlement window unless funds were settled at purchase.
- The sleeve's cash figure and the account's settled BP are different
  numbers (shared account: Hermes $4k armed, personal positions, other
  gods). MY spendable = min(sleeve cash, account settled BP at order time).

## Title I is mechanical now (2026-07-13, session 7 — charter v2.1 ratified)

Every position-changing journal line goes through
`proteus.schema.append_record(record, EntryContext(...))` — NOT the bare
ghost writer. The schema re-derives the arithmetic and refuses in one round
trip, listing every unmet duty. Practical notes:

- **Build the context honestly**: grades from `proteus.calibration`
  counters, open worst cases from the sleeve, `kelly_multiplier` from
  `cal.allowed_kelly_multiplier(journal)`. The context is the book as it
  IS; feeding it stale numbers is a grading violation, not a shortcut.
- **At zero grades** (now): probe cap 10% of equity on worst case, AND
  quarter-Kelly on worst case, AND the 25%/60% ceilings. The tightest
  binds. Parks (SPY/VOO/VTI-class 1x or SGOV-class only) are cap-exempt
  but worst-case-honest (index park journals its ≥20% crash assumption).
- **Staged first use** (art. 16): any diff touching a function in
  `proteus/order_path_manifest.json` ⇒ next live use of that path runs at
  minimum executable size with `charter.staged.is_staged=true`, a
  mechanics prediction, and a same-session dry-run comparison. Doubt
  resolves as material.
- **Grades**: `action=grade` with the cell DERIVED from (thesis_verdict,
  pnl_verdict) — the schema refuses a chosen cell that contradicts the
  axes. PARTIAL needs `realized_fraction`. Every grade states
  `real_money`, `shadow`, `worst_case_pct_at_entry` (the 1% counting
  floor reads it).
- **Dispositions** (art. 8): every shadow-eligible candidate worked gets
  a row the same session — `entered|declined|killed_at_screen|avoid`. A
  gradable shadow (declined WITH a journaled pre-read divergence) carries
  a full `shadow_primary` counterfactual; a base-rate decline is a plain
  AVOID and is never inflated.
- **Exits** carry `tax` (term, estimated_tax, assumed_rate — standing
  assumption 24% short / 15% long until the operator says otherwise; the
  true bracket is the disclosed blind spot).
- `proteus/sleeve.py`'s CONCENTRATION_ACK_PCT block is v1 doctrine, stale:
  the all-in right is repealed. Schema binds upstream; fix the comment on
  the next sleeve.py touch (staged, per the manifest).
