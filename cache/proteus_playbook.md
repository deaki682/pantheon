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
