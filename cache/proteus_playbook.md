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

No options order (when unblocked) without ALL of:

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

## Odd-lot tender — broker mechanics questions (kill-condition #2)

Unknowns that decide whether hunting ground #1 is executable at Robinhood.
Answerable ONLY by one small live test on a real deal (or operator asking
RH support; documentation is thin by design):

1. Does RH surface the corporate action and accept a tender instruction
   for a 99-share position at all (app/support flow)? By what deadline
   relative to the offer's expiration (broker cutoffs run 1–3 days early)?
2. Does RH pass through the ODD-LOT PRIORITY election correctly (the
   "tender ALL shares, hold fewer than 100" attestation), or does it
   lump odd-lot holders into the general pool (proration risk)?
3. Fees: does RH charge a corporate-action / tender fee that eats the
   spread (some brokers charge $0–$50 per voluntary corporate action)?
4. Timing: when do tendered shares leave the account, and when does cash
   land (payment date vs expiration — affects settlement math for the
   next trade)?
5. Partial/withdrawal mechanics: can an instruction be withdrawn before
   expiry if the deal terms deteriorate (amendment risk)?

Plan: first LIVE deal that passes the filing read gets a minimum-size test
(99 shares only, worst case = cost basis, journaled as an operational
experiment — the prediction is about MECHANICS, not price). Kill-spec
stands: actionable supply <12/yr, OR RH can't deliver un-prorated
acceptance, OR median $/event <$150 → kill the hunting ground.

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
