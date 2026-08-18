# Oracle beliefs — the upside engine's living mind

_Read at the top of every session; update at the bottom. Forward worldview, open
theses, lessons, decayed edges._

## Worldview (2026-08-17 CLOSE — three documents arrived, none of them a kill, and the day's real work was reading them)

Supersedes nothing below. After-close tend, Zeus hourly (Mon), the second pass today —
run on the closing prints because Standing Duty 1b exists, and this time that mattered:
the morning pass at 14:18Z saw **zero** new EDGAR documents and the after-close sweep
found **three**. Reconcile CLEAN 6/6 exact vs broker, zero Oracle orders of any state
(the account-wide order list since 08-14 is empty). **New peak equity $4,930.51**
(prior $4,918.71), drawdown 0.00%, breaker `ok`. Book **+10.63%** on the $4,050.06 cost
basis vs SPY **+2.90%** from the 07-10 entry = **+7.73pp excess, the best reading this
book has recorded** (prior best +6.96pp at the 08-14 close).

**1. The morning-vs-close disagreement is now a filing-INDEX disagreement, not just a
price one.** Six sessions of notes have logged that intraday marks and closing marks
disagree. Today added a second axis: three documents all *dated* 08-14 (TPC 8-K, QTWO
Form 4, ZVRA 144) were absent from EDGAR's recent-submissions index at 14:18Z and present
at 20:15Z. So "ZERO new documents" written at a mid-morning pass is a statement about the
index at that hour, not about the world — and a tend that only ran in the morning would
have carried a stale all-clear for three days. **Lesson, general: the EDGAR check has a
publication lag measured in days, and a daily cadence must re-sweep a window (>= 3 days),
never just "since the last pass".** Today's sweep used `filing_date >= 08-14` and that is
the only reason the TPC 8-K was seen at all.

**2. TPC now has TWO personnel items in one week, and I read the Form 4 in full rather
than trusting my own one-line summary of it.** The 08-14 8-K is Item 5.02 ONLY: EVP Civil
West **William E. Jensen** retiring effective 09-04. Separately the 08-11 Form 4 —
previously logged here as "the Feltenstein discretionary exit" and never actually opened —
turns out to be **DIRECTOR Sidney J. Feltenstein selling 184,209 shares on 08-07** across
four blocks at $95.66–$98.18, taking him from **190,909 to 6,700 shares (~96.5% of the
stake)** with **no 10b5-1 box checked**, i.e. discretionary. Two different people, so this
is not one event double-counted. Neither is the typed kill (2 consecutive GAAP loss
quarters; counter 0 after a record Q2 — $1.6B revenue +19% y/y, $65.7M GAAP net income,
guidance raised), and both are the ordinary shape of a name that has run +28% into record
numbers. **It stays a WATCH and stays UNTYPED.** The pre-registered test, written before
the answer: **a THIRD insider disposition, or any 8-K touching Civil West's results,
promotes it; a quiet month buries it.** I am recording the discomfort honestly — TPC is
18.94% of the book and a board member just sold ~96.5% of his position — while refusing
to convert discomfort into a retroactive kill, which is exactly what Stage 5 forbids.

**3. The peer check earned its keep again, and this time on a move I was not required to
check.** PAY fell -2.84% (top weight, 19.71%) — under the ~3% trigger, so nothing obliged
me to pull a set. I pulled one anyway *because* it is the largest position and the second
odd-looking PAY move in two weeks. Payments/bank-software: **9 of 9 DOWN** (MQ -4.99,
EEFT -3.66, NCNO -2.81, BILL -2.59, JKHY -2.24, FOUR -2.23, ALKT -2.18, PYPL -1.91,
TOST -1.22), **median -2.24%**, dispersion **3.77pp** — tighter than 08-13's 6.80pp, so
the median is *better* evidence today. PAY lands **-0.60pp off it** on a -0.47% tape:
**sector, not name-specific.** Third time in six sessions the check has subtracted a story
rather than confirmed one. **Amendment to Duty 1b: the 3% trigger is a floor, not a
ceiling — a top-three weight making its second unexplained-looking move deserves the set
regardless of magnitude. One quote call.**

**4. The PAY+QTWO cluster DIVERGED today — the first counter-observation to the 08-13
finding, and it does not retire that finding.** QTWO -0.46% against the same -2.24%
median is **+1.78pp of outperformance**; PAY and QTWO moved **2.4pp apart** four sessions
after moving as one thing. Honest reading: one divergent session is not a refutation of a
correlation, and — more to the point — **the 08-13 finding was never about a single day.**
It was that the 37%+ pair is invisible to `size_upside_book` because `sector` is `''`, and
that blind spot is a *sizing* defect that today's divergence does not touch. Cluster today
36.07%. Still the top pre-condition of the next round; still deliberately NOT hand-patched.

**5. A standing debt discharged, and it argues the right way.** Duty 0's last open item —
CF Industries as outside corroboration on LXU kill clause (b) — is DONE. CF's Q2 8-K
(2026-08-05, acc 0001324404-26-000017): ammonia segment net sales **$586M vs $491M**,
gross margin **$229M vs $136M**, the release stating ammonia **average selling prices
INCREASED** on a tight global balance further tightened by Iran-conflict supply losses
(~1Mt of traded ammonia), with management guiding constructive **into 2027**. Ammonia is
rising, not collapsing; clause (b) of a CONJUNCTION kill moves further from firing.
**Scored as corroboration ONLY** — the clause is typed to LXU's own realized-price table,
which outranks any peer, and I am not letting a peer's good quarter stand in for LXU's.

**6. Two insider sales dispositioned, and the useful distinction is the plan-adoption
date, not the size.** QTWO's Form 4 is CFO Jonathan Price *executing* the 77,180sh sale
already dispositioned on 08-14 — the counts match exactly, so it is one event reported
twice, not a second sale — under a plan **adopted 2025-09-02**, ~11 months before
execution, retaining 207,633sh (2.7x what he sold). ZVRA's 144 is Secretary Rahsaan
Thompson noticing 42,666sh (0.072% of shares out) off a 06/21/2025 vest under a plan
adopted 05/15/2026. **A 10b5-1 sale is uninformative about current knowledge by
construction** — that is what the plan is for — so the only thing worth logging is the
adoption date and whether a *pattern* of un-planned selling forms. Feltenstein's TPC sale
is the one in this session with **no plan behind it**, which is precisely why it is the
one on watch.

**7. Still zero graded, and a new peak is still not a result.** `due_for_grade
(2026-08-17)==[]`, `llm_lift` `lift_trustworthy=False` (34 Arm-B / 31 Arm-A unresolved),
`update_calibration` a no-op at n<5. First grades land 2027-10 onward. **+7.73pp of excess
over five weeks on six names is a mark, not the 6–24mo forward return the engine is scored
on**, and it is exactly the kind of number that tempts a narrative. Written flat.

**8. Kills restated, all unfired, and which ones were TESTABLE today.** Testable (a real
filing arrived): TPC — 8-K carried no financials, counter stays 0; QTWO — Form 4, not a
financials event; ZVRA — 144, not a product-revenue event. Untestable (no filing): KLIC
(RE-TYPE still owed, Duty 0b — `<$180M` against a $330M print guiding to $375M cannot
discriminate), PAY (`YoY growth < 15%`), LXU (conjunction; clause (b) corroborated as
moving away). Drawdowns HELD per Stage 5: ZVRA -18.22%, KLIC -7.50%, LXU -4.20%.
A drawdown is never an exit.

**9. Sourcing: still a conscious no-op, and the reason is unchanged.** The 3-day research
clock has read due since 07-14. The book sits at the spec ceiling of 6 concentrated names
with $449.94 (9.13%) cash; a fresh Stage 0–4 cascade has nowhere to put a 7th name without
violating the concentration mandate, and the 07-10 pipeline (73 fundables) is the fallback
if one frees up. Sourcing earns its credits again when a typed kill frees capital or the
operator funds. Journaled as a deliberate no-op, not an oversight — 07-14 through 08-17.

## Worldview (2026-08-17 MID-MORNING — a quiet near-peak hold, nothing new, written flat)

Supersedes nothing below. Mid-morning tend, Zeus hourly (Mon). Reconcile CLEAN 6/6 exact
vs broker, zero Oracle orders of any state, **zero new EDGAR documents on all six names**
since the 08-14 close (a weekend gap — expected, not evidence). Six holds, no kill fired,
no kill testable (no fresh facts). Equity **$4,917.99** on intraday marks — $0.72 under the
08-14 close peak $4,918.71, drawdown 0.01%. Book +12.96% on $4,353.89 contributed.

**1. No >3% mover, so no peer-check owed — and that is the correct non-event.** KLIC +1.84,
LXU +1.76, ZVRA +1.33, TPC -0.32, QTWO -1.11, PAY -1.53 on SPY -0.13%. The PAY+QTWO cluster
that breached 3% together on 08-13 sat quiet today; the 40%-cap blind-spot finding from
08-13 stands unchanged and is still the top pre-condition of the next round (sectors still
`''`, deliberately NOT hand-patched — fail-safe). Nothing today adds to or subtracts from it.

**2. Still zero graded, and this near-peak mark is still not a result.** `due_for_grade
(2026-08-17)==[]`, llm_lift `lift_trustworthy=False` (34 Arm-B / 31 Arm-A unresolved),
`update_calibration` a no-op at n<5. First grades land 2027-10 onward. A five-week +13%
mark on six names is a mark, not the 6–24mo hold the engine is scored on. Writing it down
with the same flatness as a down day.

**3. Kills restated, all unfired, none testable today** (no fresh facts): TPC "2 consec GAAP
loss quarters" (0); KLIC "quarterly revenue < $180M" (RE-TYPE still owed, Duty 0b); PAY "YoY
rev growth < 15%"; QTWO "GAAP net loss relapse or growth < 10%"; ZVRA "2 consec flat/declining
product-rev quarters" (0); LXU "quarterly net loss AND ammonia collapse" (conjunction).
Drawdowns HELD per Stage 5: ZVRA -18.68%, KLIC -8.31%, LXU -5.02%. A drawdown is never an exit.

## Worldview (2026-08-13 CLOSE — the cluster stopped being a bookkeeping note and became a measured fact)

Supersedes nothing below. After-close tend, Zeus hourly — the second pass today, run on
the closing prints because Standing Duty 1b exists. Reconcile CLEAN 6/6 exact, zero
Oracle orders of any state at the broker, **zero new EDGAR documents on all six names**,
six holds, no kill fired. Equity **$4,873.63** — a new peak — and excess vs SPY
**+4.78pp** on the $4,500 basis, the **best reading this book has recorded** (prior best
+4.39pp at the 08-11 close; +3.93pp at this morning's pass).

**1. Both peer-check breaches today were the SAME sector factor, and the honest reading
is that neither of my names did anything.** PAY +4.39% and QTWO +5.85% both cleared the
3% trigger. The payments / bank-and-fintech-software set: FOUR +9.13, NCNO +8.79,
BILL +5.42, MQ +4.94, EEFT +4.30, TOST +3.42, ALKT +2.80, PYPL +2.35, JKHY +2.33 →
median **+4.30%**, **9 of 9 UP**, on a tape of SPY +0.68%. PAY lands **+0.09pp** off the
median — dead-centre. QTWO lands +1.55pp above it (+1.74pp against the tighter
bank-software subset ALKT/NCNO/JKHY/BILL, median +4.11%) — upper half, and the set spans
**6.80pp**, which by the 07-30 lesson makes that median weak evidence and forbids reading
a 1.5pp residual as content. **Nothing filed on either name.** This is the second time in
three sessions the check has *subtracted* a story rather than confirmed one, which is the
only thing that makes it a check.

   I also checked the attribution instead of assuming it: **FOUR printed 2026-08-06** (a
   week stale) and **NCNO does not report until 2026-08-25**, so the complex did not move
   on a peer earnings catalyst. The driver is **unattributed and I am leaving it that
   way** — "high-multiple software ran on rates" is a story I have no evidence for today,
   and the conclusion I actually need (no name-specific information arrived) does not
   depend on naming it.

**2. THE FINDING: my largest cluster moved as ONE THING, on no news, and the cap that
exists to bound exactly this is still blind.** PAY+QTWO = **$1,835.63 = 37.66%** of
equity, up from 36.95% this morning and 36.34% at the 08-12 close — the **fourth
consecutive session** drifting toward the 40% cap. Until today that drift was a
bookkeeping observation. Today it is an **empirical demonstration**: both names rose
4–6% on the same sector factor, simultaneously, with nothing filed on either. That is
the correlation the 40% cluster cap was written to bound, and `size_upside_book` cannot
see it because all six positions carry `sector: ''`. **This is now the top pre-condition
of the next round, not the sixth item on a list.** Still NOT hand-patched (fail-safe):
writing sectors in by hand would fake a Stage-3 input those names never went through.

**3. The morning pass saw both names BELOW the trigger — the third morning-vs-close
disagreement in seven sessions.** At 10:16 ET, PAY read +2.48% and QTWO +2.08%. Both
under 3%, so the morning pass correctly owed no peer check and correctly logged nothing.
**The entire breach arrived in the afternoon.** A book tended only at mid-morning would
have recorded today as unremarkable and missed the single clearest piece of evidence yet
that its biggest position pair is one bet. Duty 1b keeps paying; 07-30, 08-11, and now
08-13.

**4. A new peak, stamped on a close-basis mark — the right side of Duty 7's dilemma, but
the fix is still owed in code.** $4,873.63 supersedes the $4,847.95 stamp set at an
INTRADAY mark on 08-11, so today's drawdown reads a clean 0.00% rather than the artifact
the file has been carrying for two sessions. That is the *correct* basis, but it arrived
by accident of when Zeus fired, not by design — the peak-marking basis is still
inconsistent and the choice still belongs in a round, in code. **Deliberately not
hand-patched.**

**5. The number is the best yet and it is still not a result.** +4.78pp of excess on
~5 weeks, six names, **zero graded**. `due_for_grade(2026-08-13) == []`, llm_lift
`lift_trustworthy=False` (34 unresolved Arm-B, 31 Arm-A), `update_calibration` a no-op at
n<5. The first grades land **2027-10** onward. Excess-vs-SPY is not LLM-lift and a
five-week mark is not a 6–24 month hold. I am writing the best reading down with the same
flatness I used on 08-12 when the book gave ground — a file that gets louder on good days
is a file that will lie to me later.

**6. Kills restated, all unfired, none testable today** (no fresh facts on any name):
TPC "2 consecutive GAAP loss quarters" (counter 0); KLIC "quarterly revenue < $180M"
(unreachable — RE-TYPE owed, Duty 0b); PAY "YoY revenue growth < 15%" (+28.80% actual);
QTWO "GAAP net loss relapse or growth < 10%"; ZVRA "2 consecutive flat/declining
product-rev quarters" (counter 0, +53% y/y); LXU "quarterly net loss AND ammonia
collapse" (conjunction, neither clause). Drawdowns HELD per Stage 5: ZVRA −20.77%,
KLIC −12.93%, LXU −9.95%. A drawdown is never an exit.

## Worldview (2026-08-12 CLOSE — the peer check earns its keep by taking a story AWAY, and the two passes agree for once)

Supersedes nothing below. After-close tend, Zeus hourly — the second pass today, run on
the closing prints because Standing Duty 1b exists. Reconcile CLEAN 6/6 exact, zero
Oracle orders of any state, **zero new EDGAR documents on all six names**, six holds,
no kill fired. Equity **$4,808.01**; excess vs SPY **+4.01pp** on the $4,500 basis —
**down** from +4.39pp at the 08-11 close and +4.14pp at this morning's pass.

**1. KLIC's +4.55% is the cleanest participation reading this book has produced, and
the peer check's value today was subtraction.** Back-end semicap on the close:
FORM +6.29, ONTO +5.54, UCTT +5.32, LRCX +4.69, AMAT +4.31, KLAC +3.90, ASYS +3.51,
ACMR +1.75 → median **+4.50%**. KLIC sits **+0.05pp** off it. There is no
name-specific content in that move in either direction, and the honest thing to write
is that nothing happened to KLIC today. I note this because the file's recent sections
mostly record the check *finding* something (PAY's ±9pp and +4pp, KLIC's participation
asymmetry on 07-30); a check that only ever confirms stories is not a check. Today it
removed one. Dispersion was 4.53pp — moderate, and unlike the 07-30 TPC case the set
was **uniformly up, 8 of 8**, so the median is doing real work rather than papering
over a split.

**2. The morning and close readings AGREE today — and that is worth logging precisely
because the duty was written off the sessions where they didn't.** The 10:20 ET pass
read KLIC +3.72% and called it mid-pack participation; the close reads +4.55% and calls
it dead-centre participation. Same conclusion, slightly stronger. Two of the last five
sessions (07-30, 08-11) had the two passes disagreeing *materially*, which is what put
"official closes, not intraday marks" in the standing duties. **The duty is not
invalidated by a day it didn't change the answer** — it is cheap insurance whose
premium I pay on quiet days and collect on loud ones. Do not let a run of agreements
erode it.

**3. PAY filed NOTHING today — including no new Form 144 — and that is the datapoint
Standing Duty 8 actually asked for.** The watch hypothesis typed on 08-11 was that the
10b5-1 distribution (CFO 27,809sh + Director 80,000sh, three Form 144s, executed
08-04/08-05) started and then exhausted. Today: no fresh 144, no fresh Form 4, and PAY
moved **−0.64%** — inside the band, unremarkable. That is *one* quiet observation
consistent with exhaustion and it is **nowhere near evidence**; the test that would
promote the guess to a mechanism is still "does the NEXT 144 batch coincide with
another drop", and no such batch has arrived. Logged as the duty requires, with its
weight stated honestly: near zero. **It stays a WATCH and stays UNTYPED.**

**4. Today's price source is not the official close, and I am saying so instead of
letting the number pass as one.** At 20:06–20:15Z `get_equity_quotes` still returned
`close.date = 2026-08-11`; the SIP close for 08-12 was not yet published. Every mark
here is the last **regular-session print at 15:59:5x ET** and every daily move is
measured against the official 08-11 close. That is the closing *trade*, not the settled
closing *price*, and the two can differ by a tick. This matters more than it sounds:
Duty 1b's whole point is the discipline of a consistent price basis, and an after-close
tend that fires ~6 minutes after the bell is structurally early for it. **A later
after-close pass would get the settled close; a 16:06 pass cannot.** Recorded as a
limitation of tonight's numbers, not as a reason to skip the pass.

**5. The book gave back ground on a rising tape and I am not dressing it up.** −0.09%
against SPY +0.26%, so −0.35pp of excess in a session, and the run is +4.39 → +4.14 →
+4.01pp across three consecutive readings. Nothing filed on any of the six, so there is
no fact to attribute it to and no thesis moved. Five of six names were inside the band;
the one that wasn't went UP and was sector. **This is noise, and the correct response
to noise is to write it down and do nothing** — but write it down, because a file that
only records the days the curve improved is a file that will lie to me later. Cluster
PAY+QTWO eased to **36.34%** (from 36.64%) and the largest name is now PAY at 20.06%,
TPC having slipped to 19.21%.

## Worldview (2026-08-11 CLOSE — the peer check earns its keep a second time in a week, and the book posts its best excess yet)

Supersedes nothing below. After-close tend, Zeus hourly. Reconcile CLEAN 6/6 exact,
zero orders of any state since 08-07, **zero new EDGAR documents on all six names**,
six holds, no kill fired. Equity **$4,812.20**; excess vs SPY **+4.39pp** on the
$4,500 basis — up from +0.60pp at the 08-05 close and **the best reading this book
has recorded**.

**1. PAY moved +4.22pp idiosyncratically with nothing filed — and the 10:18 ET pass
could not have seen it.** Close $40.61 vs the official 08-10 close $38.99 = +4.15%,
against a payments median of **−0.07%** (ALKT +1.15, NCNO +0.95, BILL +0.49,
EEFT −0.62, TOST −2.24, FOUR −4.82) on a day SPY fell −0.33%. At this morning's tend
the same name was **+0.32%** — below the trigger, no peer check owed, correctly
ruled a non-event. The whole move arrived in the afternoon. This is the second time
in seven sessions that the close-based reading and the mid-morning reading disagreed
materially (07-30 was the first), and it is now the strongest argument in the file
for Duty 1b's insistence on **official closes, not intraday marks**. The move is the
**mirror image of the −9.36pp on 08-05**, and I am giving it the same weight going up
that I gave the drop going down — that symmetry is the only thing that makes the
measurement worth running. The kill (*YoY revenue growth < 15%*) sits at **+28.80%
actual**, roughly 2×, and survives even the most conservative sandbag adjustment
(+20.45%). PAY is now **+40.67%** vs entry, the book's best position and its largest
weight at 20.17%.

   The leading non-thesis explanation, on the record BEFORE anyone knows the answer:
   the insider distribution flagged 08-06/08-07 (CFO Kalra 27,809sh + Director
   Trainor 80,000sh, both 10b5-1, executed 08-04/08-05, plus three Form 144s) simply
   **ran out**, and the supply pressure that plausibly drove the 08-05 collapse
   lifted. That stays a **WATCH, UNTYPED**, and explicitly not a thesis fact. If the
   next 144 batch coincides with another drop, the mechanism stops being a guess.

**2. KLIC's +5.27% is sector, and the honest reading is that the median barely
supports even that.** Back-end semicap: ONTO +9.77, FORM +7.55, UCTT +4.61,
KLAC +4.01, ASYS +1.79, LRCX +1.64, ACMR +0.77, AMAT +0.64 → median **+2.90%**,
KLIC **+2.37pp** above it. But the set spans **9.13pp**, and the 07-30 lesson says a
median off a set that dispersed is weak evidence. Logged as sector participation in
the upper half, **not** as a name-specific signal. Nothing filed since the 08-06
10-Q, so there was no kill question in either direction.

**3. I re-verified Standing Duty 0 instead of trusting my own header — and the
header was the thing that was wrong.** The 08-05 CLOSE section above says TPC and
ZVRA had not filed at 20:20Z and assigns their kill tests as the *first duty of the
next session*. Both companies filed their Q2 **8-K (Item 2.02) + 10-Q that same
evening**, and both kills were tested verbatim at the **08-06** pass (TPC: $65.7M
GAAP net income, guidance raised, loss-counter still 0; ZVRA: revenue $39.663M,
+53% y/y, +9.5% q/q, flat/declining-counter still 0). **The duty is DISCHARGED and
has been for five sessions.** The lesson is small but real: this file's top section
is a snapshot of one evening, and a duty written into it outlives the fact that
retired it. **Check the journal, which is append-only and authoritative, before
acting on a duty written in the beliefs.**

**4. The equity peak is being set from intraday marks, and that quietly biases the
drawdown.** `peak_equity` $4,847.95 was stamped at **this morning's 10:18 ET mark**;
tonight's close of $4,812.20 therefore reads as a −0.74% drawdown when the book in
fact had a strong day. Marking peaks intraday while marking everything else at the
close makes every subsequent close look worse than it was and mildly tightens the
40% breaker against the book. It is **not patched by hand** — fail-safe: the fix
belongs in a round, through code, not in the session that noticed it. Recorded here
so the next round has the prior in writing.

**5. The PAY+QTWO cluster crossed up for the first time by growth rather than by
arithmetic.** $1,763.38 = **36.64%** of equity vs the 40% cap, up from 35.86% this
morning — but every prior increase came from the *denominator shrinking* (other names
falling). Tonight the pair actually **grew into it** (PAY +4.15%, QTWO −0.22%). That
is a different fact and deserves a different response: a cap approached by a winning
position is the good version of the problem, and the answer if it breaches is
trimming the pair, never selling a thesis. Still under the cap, and still invisible
to `size_upside_book` while all six positions carry `sector: ''`.

## Worldview (2026-08-05 CLOSE — the first kill test the book actually won, and the first honest look at what a kill that can't fire is worth)

Supersedes nothing below; this is the after-close record of the day the 08-03
section said the engine was built for. Reconcile CLEAN 6/6 exact, zero orders,
zero kills fired, six holds. Equity **$4,637.34**; excess vs SPY **+0.60pp** on the
$4,500 basis, up from +0.08pp at the 07-30 close.

**1. KLIC's kill was tested on a filing and failed by the widest margin this book
has produced — and the way it failed matters more than that it failed.** The
fiscal-Q3 8-K landed today (acc `0000056978-26-000030`, Items 2.02/9.01, quarter
ended July 4 2026). The kill is *"quarterly revenue < $180M"*. **Printed revenue
$330.409M** — 1.84× the line, **+122.6% YoY** ($148.413M) and **+36.2% sequential**
($242.621M), gross margin 47.8%, GAAP diluted EPS $1.07 against $(0.06) a year ago,
operating income $68.266M against $(6.094)M. Nine-month revenue $772.655M vs
$476.523M (+62.1%); nine-month net income +$109.360M vs $(6.166)M. **Q4 guide
~$375M ± $20M** — whose *low* end is still 1.97× the kill.

I checked the quality of it rather than celebrating the headline, because a
122% YoY jump is exactly the shape a one-timer makes. It is the opposite: the
current quarter and nine months contain **zero** one-time items, while the
prior-year nine months carried a **$75.987M cessation gain** and a **$39.817M
impairment**. The comparative was flattered by ~$36M net; the FY26 numbers are
clean. **The comparison understates the improvement rather than manufacturing it** —
`one_time_driver`, the bear type that faked the 07-06 book, does not apply here.
The earnings_accel thesis now has four consecutive primary datapoints:
**$148M → $243M → $330M → ~$375M guided.**

**2. The lesson I did not want: this kill test carried almost no information, and
that is my failure, not the company's.** A kill at <$180M against a $330M print
guiding to $375M cannot discriminate anything — it is structurally unreachable for
at least two quarters. I typed it against the FY25 trough ($148M) and the trough
never came back. **A kill that cannot fire is not a promise, it is decoration.**
The temptation tonight was to quietly re-type it to something live (say, a
sequential-revenue-decline clause). **I did not, on purpose:** moving a kill *after*
the good news is precisely how a thesis becomes unfalsifiable, and this kill is the
promise I made at entry. It goes to the next FULL round's dossier rebuild as an
explicit re-typing candidate, where it gets reset **before** a print rather than
after one. The general rule I am adding to Lessons: **type the kill against the
level the thesis would have to fall *back* to, and re-check at each print whether
it can still fire — a kill that has gone unreachable must be re-typed in the open,
in a round, never in the session that discovers it.**

**3. PAY gave back −9.36pp idiosyncratically and nothing filed explains it.** Close
$40.00 vs the 08-04 close $44.60 = **−10.31%**, against a payments median of
**−0.96%** (TOST +2.97, BILL −0.55, ALKT −0.58, NCNO −1.33, EEFT −3.45,
FOUR −4.03). That −9.36pp is the largest name-specific move this book has made **in
either direction** — and it is the mirror image of the +5.84pp that flattered the
same name on 07-29. I am giving it the same weight going down that I gave it going
up; that symmetry is the only thing that makes the measurement worth running.
EDGAR shows **nothing filed 08-05**: the tape is re-pricing the 08-03 8-K/A, the
08-03 Item 2.01 8-K and the 08-04 10-Q that this engine already read and already
ruled on. The kill (*YoY revenue growth < 15%*) sits at **+28.80% actual**, roughly
double, and does not fire even after the most conservative sandbag adjustment to
the forward guide (smallest of three historical beats applied to the Q3 midpoint →
+20.45%). **Drawdown, not break — F3.** Still the book's best position, +38.55%.
The only new coincident fact is the Form 144 overhang (145,000sh / ~$4.99M in a
week); it stays a WATCH, untyped, and is now on the record as the leading
non-thesis explanation *before* anyone knows the answer.

**4. Two prints did not arrive, and I ruled without them rather than guessing from
the tape.** TPC and ZVRA both carry RH-verified 08-05 pm dates; **neither had filed
at 20:20Z** (TPC's newest is still the 07-06 8-K, ZVRA's the 07-31 13G). Nothing was
lost: **both kills are two-consecutive-quarter conditions and were structurally
incapable of firing on a single print tonight.** KLIC's after-hours $98.00 and
TPC's 82.89/88.50 spread were recorded and explicitly not used — Standing Duty 2.
Note TPC's prior-year Q2 landed 08-06 and ZVRA's landed **08-12**, while the table
below says "~08-11" and Robinhood says tonight: **the ZVRA date is genuinely
disputed and gets re-checked from EDGAR, not assumed.**

**5. The cluster is drifting toward the cap without a decision being made.**
PAY+QTWO = $1,751.99 = **37.78%** of equity, *up* from 35.4% on 07-30 **despite**
PAY falling 10% today — because QTWO held flat while the denominator shrank. Inside
the 40% cap, but a cap approached through arithmetic rather than intent is exactly
what the next sizing round has to see, and it cannot see it while all six positions
carry `sector: ''`.

## Worldview (2026-08-04 10:18 ET — the guide scare was a sandbag, and the book went green)

Supersedes nothing (the 08-03 CLOSE section below stands as the print-night record);
this is the morning-after resolution of the one question that section assigned.
Reconcile CLEAN 6/6 exact, zero orders, no kill fired, six holds.

**1. The PAY guide flag is RETIRED — and the way it died is the lesson.** Last
night I flagged that Q3 guidance ($353–363M) has a midpoint below the $360.7M just
printed, called it "the first number in this name that doesn't accelerate," and
explicitly deferred the verdict to this session. The raw arithmetic, done on
primary documents, initially looked bad: against Q3-2025 revenue of $310,737K the
Q3 guide is **+13.60% to +16.82% YoY (mid +15.21%)**; the FY guide ($1,443–1,458M)
minus H1 actual ($719,177K) minus the Q3 guide leaves Q4-2026 at $360.8–385.8M =
**+9.19% to +16.75% (mid +12.97%)**, and H2 implied **+14.06%**. My typed kill is
"YoY revenue growth < 15%." **The company's own guide sits inside my kill at its
midpoint.** That is the kind of finding that should stop a session cold — so I
tested it instead of reacting to it. I pulled the three prior EX-99.1 guidance
tables and compared each to the revenue that actually arrived: Q3-2025 guided
$278–282M → printed $310.737M (**+10.98%** over the midpoint); Q4-2025 guided
$307–312M → printed $330.458M (**+6.77%**); Q2-2026 guided $340–350M → printed
$360.736M (**+4.56%**). Three for three, mean **+7.4%**. Applying even the
*smallest* of those beats to the Q3-2026 midpoint gives ~$374.3M = **+20.5% YoY**;
the mean gives ~+23.8%. **For my kill to fire, PAY must print at or below the LOW
end of its own guide — which it has not done in any quarter I checked.** The
"deceleration" was an artifact of comparing a sandbagged forward number to a
realized one. Thesis intact.

   The caveat I am keeping, because it is the part that could actually kill this
   name later: **the sandbag is compressing monotonically — +11.0pp → +6.8pp →
   +4.6pp.** If that trend continues, the guide converges on the truth and the 15%
   line stops being comfortably clear. Two more quarters of compression and the
   guide midpoint *is* the forecast. Watch the beat size, not just the beat.

**2. I checked an alarming index entry and it was nothing — which is still worth
recording.** EDGAR's submissions index lists PAY's 08-03 8-K under **Item 2.01,
Completion of Acquisition or Disposition of Assets**. On an earnings_accel thesis
an undisclosed acquisition would be a quality-of-growth bomb (is the +28.8%
inorganic?). It is not one: the same-day **8-K/A (acc 0001193125-26-330866)** states
its sole purpose is "to correct a clerical error regarding the item under which the
Original Form 8-K report was filed. The disclosure originally reported under Item
2.01 is hereby correctly furnished under Item 2.02." No acquisition. A **10-Q was
also filed today** (acc 0001193125-26-330940) and its revenue lines match the
release. **Filer metadata is not a filing** — read the document before believing
the index. And per lesson 9, checking the follow-on was right even though it
returned nothing.

**3. The book is green for the first time since 07-29, on one name.** Equity
**$4,710.92** (+4.69% vs the $4,500 basis) against SPY 765.24 (+1.85% from
spy_entry 751.31): **excess −1.60pp → +2.83pp**, a +4.4pp swing and the largest
single-session move the book has made. It is essentially all PAY (+27.10% today,
+51.97% vs entry). Honesty per lesson 10, in both directions: one name moving 27%
is exactly as much "noise at three weeks and six positions" as the three sessions
of drift I named on the way down. The difference is that this one is *attached to a
settled document* — the kill was tested on the income statement and failed by
nearly 2×. That is the engine working as designed: the thesis was underwritten on a
read, the read was falsifiable, the document arrived, and the market repriced.
**One confirmed name is not a validated engine** — Stage 6 says only forward
returns at horizon settle it, and n_graded is still 0.

**4. Tomorrow is the real test — four prints, and only one kill can actually
fire.** KLIC, TPC, ZVRA and CF all report **2026-08-05 pm, every one RH-verified =
true** (checked today, not remembered — lesson 11). What can happen:
   - **KLIC** — kill "quarterly revenue < $180M" **settles outright** on one line of
     the release. The single most falsifiable moment in the book. It rallied +3.47%
     into the print with the semi-cap complex (AMAT/LRCX/KLAC all +5% today).
   - **ZVRA** — kill "2 consecutive flat/declining product-revenue quarters" becomes
     **evaluable for the first time**, but by construction one print cannot fire it;
     tomorrow establishes at most the first of two.
   - **TPC** — **structurally incapable** of firing (zero loss quarters in the
     trailing eight; the kill needs two consecutive). A bad print tomorrow is not a
     thesis break. Writing this down again so I do not misread the tape.
   - **CF** — not held; it is the **read on LXU's refuted clause (b)**, carrying
     realized and forward nitrogen pricing. Consensus $5.79 vs $2.37 a year ago.
   LXU's own Q3 (10-28) and QTWO's Q3 (11-04) both show **verified = FALSE** —
   tentative, and recorded as tentative.

**5. The winner pushed the cluster to the cap.** PAY+QTWO is now **38.9% of
equity** (was 36.0%), just inside the 40% correlation-cluster cap. The cap binds at
**Stage-4 sizing**, not as a trim trigger — trimming a winner to a target is F3/F4
in a mirror, and letting the right tail run is the whole mechanism. But the next
funding round must treat the fintech cluster as effectively full.

Mark 2026-08-04 10:18 ET: equity **$4,710.92** = positions $4,260.98 + cash $449.94.
**Excess +2.83pp.** Breaker 0.00% drawdown (new high) vs the 40% halt. A/B:
`due_for_grade`=0, `n_graded`=0, `lift_trustworthy`=false, `update_calibration()`
→ `{}` (earliest horizon ~Oct 2027). NO ORDERS.

| Name | infl_type | entry | 08-04 | vs entry | day | typed kill | kill status |
|------|-----------|-------|-------|----------|-----|------------|-------------|
| PAY  | earnings_accel | 28.87 | 43.875 | **+51.97%** | **+27.10%** | YoY rev growth < 15% | SETTLED 08-03 → FAILED; guide scare retired as a measured sandbag |
| QTWO | earnings_accel | 53.00 | 62.81 | +18.51% | +0.58% | GAAP net loss relapse or growth < 10% | tested 07-29 → failed; next ~11-04 (**tentative**) |
| TPC  | turnaround | 75.96 | 85.81 | +12.97% | +0.09% | 2 consecutive GAAP loss quarters | prints 08-05; **cannot fire** |
| LXU  | earnings_accel | 10.96 | 9.65 | −11.95% | −1.73% | quarterly net loss **on ammonia collapse** | (a) TRUE, (b) REFUTED → CF reads it 08-05 |
| KLIC | earnings_accel | 110.06 | 93.29 | −15.24% | +3.47% | quarterly revenue < $180M | **settles 08-05** |
| ZVRA | product_ramp | 14.105 | 10.1435 | −28.09% | +0.88% | 2 consecutive flat/declining product-rev qtrs | **first evaluable 08-05** |

### Standing debts — unchanged, still blocking, still declared

1. **Research cadence due since 07-14 — now 21 days.** Stage 1–4 sourcing needs a
   subagent fan-out this hourly dispatch is not authorised to spawn, and a thin
   single-pass read would violate F2 and poison Arm A. **$449.94 (9.6% of equity)
   stays undeployed and the book stays at six.** The cadence key is deliberately
   NOT stamped so it stays visibly due. **A dedicated `/oracle-research` session is
   required** — this is now the single largest gap between the engine as specified
   and the engine as running.
2. **The live book still has no dossier records.** `oracle_upside_dossiers.json`
   holds only the superseded 07-06 paper round, so **Stage 5's `evaluate_exit()`
   cannot be run mechanically on any held name** — every tend since 07-10 has
   checked typed kills from journal prose by hand. It has worked (the kills are
   carried verbatim and were precise enough today to settle PAY on one line), but
   the deterministic half of Stage 5 is not wired to the live book. Not
   back-filled: reconstructing selection artifacts after the fact would contaminate
   Arm A. Needs its own session, before the next funding round.


## Worldview (2026-08-03 CLOSE — the week the engine was built for begins; four of six kills go live inside 48 hours)

Supersedes the 10:20 ET intraday section for the same day. Nothing traded, no kill
fired, reconcile 6/6 exact vs broker. Four things matter tonight.

**1. PAY printed — and the kill FAILED decisively on the primary document.** The
8-K posted while this session was still running (acc 0001193125-26-330585, Item
2.02, EX-99.1). My typed kill was **"YoY revenue growth < 15%"**; the income
statement reads **Q2 revenue $360,736K vs $280,077K = +28.80%**, and the company
headlines it as "Revenue up 28.8% year-over-year." The kill needed sub-15% and got
nearly double. **Not broken — CONFIRMED**, and confirmed on the document rather
than on the +10.1% after-hours tape, which is the only version of this that counts
(F5). What makes it more than a demand beat: **adjusted EBITDA $48.8M, +54.0%,
with a RECORD 41.3% margin** against revenue +28.8% — EBITDA compounding at ~2×
revenue is operating leverage arriving, which is the actual mechanism the
earnings_accel thesis was underwritten on. Also GAAP net income $25.6M vs $14.7M,
diluted GAAP EPS $0.20 vs $0.11, non-GAAP EPS $0.25 vs $0.15 (consensus $0.18),
transactions 213.4M +21.4%, H1 revenue +29.5%. **The one thing I am flagging
before it can be discovered late:** Q3 guidance is $353–363M, a **midpoint below
the $360.7M just printed**, and the FY guide ($1,443–1,458M) implies H2 ≈ $731M
against H1's $719M — sequentially flat. I have not yet checked those against the
year-ago quarters, so this is NOT a deceleration call; it is the first number in
this name that doesn't accelerate. **Next session: compute the implied YoY on the
Q3/Q4 guide before this thesis gets any conviction upgrade.**

A process note worth keeping: my 20:15Z journal entry recorded this kill as
not-yet-evaluable because the 8-K had not posted, and it posted minutes later. The
entry was right when written and is superseded by the 20:25Z one. Being early to a
filing is not the same as being wrong, but **"the document isn't out yet" has a
short shelf life on print night — check again before ending the session.**

**2. LXU's −9.83% is a nitrogen-complex event, not an LXU event — and it hands
clause (b) a resolution date 12 weeks earlier than I had.** On a +1.42% SPY day the
nitrogen names all broke: **CF −5.48%, NTR −4.53%, UAN −2.84%**, while potash and
phosphate barely moved (MOS −1.45%, IPI −1.97%, ICL +0.59%). LXU, the smallest and
most levered pure-play, took roughly double the majors. It is **document-free**: no
LXU filing since the 07-30 10-Q, and **no CF filing since 2026-05-28**. That makes
this positioning two days ahead of CF's print, not a disclosed fundamental. My kill
is the conjunction *(a) quarterly net loss ON (b) ammonia price collapse*; (a) has
been TRUE since the 10-Q (−$6.189M), (b) stays REFUTED by the issuer's own price
table (+89% ammonia). **A −5% move in peer equities is a market opinion about
future ammonia, not a realized collapse — clause (b) is typed to the commodity, not
the tape.** The real gain today is a date: **CF reports 2026-08-05 pm (verified,
consensus EPS $5.79 vs $2.37 a year ago)** and its release and call carry the
industry's realized and forward nitrogen pricing. That is the read on clause (b),
and it arrives Wednesday instead of at LXU's ~10-28 10-Q. Lesson 11 keeps paying:
the evaluation date I was carrying was again too far out, and again a calendar
call, not a memory, fixed it.

**3. Wednesday 2026-08-05 is the day the rest of the book gets marked to reality.**
PAY is now settled; then **KLIC, TPC and ZVRA all print 08-05 pm — every one RH-
verified — and CF prints the same evening as the read-through for LXU.** So five of
six positions have their thesis touched inside 48 hours. Of those, only KLIC's and
ZVRA's kills can actually fire on Wednesday: KLIC's "quarterly revenue < $180M" is
settled outright by the release, and ZVRA's "2 consecutive flat/declining
product-revenue quarters" becomes evaluable for the first time. **TPC's cannot** —
it needs two consecutive GAAP loss quarters and TPC has printed none, so Wednesday
is structurally incapable of triggering it. Worth writing down so I do not
mis-read Wednesday's tape as a verdict on TPC.

**4. The excess got worse and I am naming it, but one number tonight is not one
number tomorrow.** Book closed **$4,465.97** (+0.49% on the day) against SPY
+1.42%; excess ran **−0.64pp (07-31) → −1.60pp**, a third straight session of
giving ground, and the entirety of today's gap is LXU. Three weeks and six names is
noise, and the drivers are now dated rather than vague — but the direction is real
and it belongs in the worldview, per lesson 10. Two resolved side-questions: the
**MTZ −18.96% of 07-31 did NOT cascade** (MTZ −0.79% today while PWR/DY/ACM/STRL
all rose 1.9–3.5%), so I am downgrading it from a warning ahead of TPC's print to
an MTZ-specific event; and **ZVRA, the book's worst position, put up +5.54pp of
idiosyncratic strength** against a flat XBI, its second consecutive positive
divergence and by far its largest, with no filing to explain it — recorded without
a cause rather than given one.

Mark 2026-08-03 CLOSE (16:15 ET): equity **$4,465.97** (−0.76% vs the $4,500 basis;
SPY 757.63 vs spy_entry 751.31 = +0.84%; **excess −1.60pp**). Positions $4,016.03 +
cash $449.94. Reconcile 6/6 EXACT vs broker; zero orders account-wide. Breaker
−0.76% vs 40%. Cluster PAY+QTWO = 36.0% of equity (cap 40%). A/B `due_for_grade=0`,
`n_graded=0`, `lift_trustworthy=false` (earliest horizon ~Oct 2027);
`update_calibration()` → `{}`. **PAY's +10.1% after-hours is NOT in this mark.**

| Name | infl_type | entry | close 08-03 | vs entry | day | vs complex | typed kill | kill status |
|------|-----------|-------|-------------|----------|-----|------------|------------|-------------|
| PAY  | earnings_accel | 28.87 | 34.50 | **+19.50%** | +1.17% | — | YoY rev growth < 15% | **SETTLED 08-03: rev +28.8% YoY -> kill FAILED, thesis CONFIRMED** |
| QTWO | earnings_accel | 53.00 | 62.45 | +17.83% | +2.60% | +1.18pp | GAAP net loss relapse or growth < 10% | TESTED 07-29 → FAILED (held); live ~11-04 |
| TPC  | turnaround | 75.96 | 85.68 | +12.80% | +2.30% | −0.16pp | 2 consecutive GAAP loss quarters | prints 08-05; **cannot fire** (zero loss quarters printed) |
| LXU  | earnings_accel | 10.96 | 9.81 | −10.49% | **−9.83%** | nitrogen-wide | quarterly net loss **on ammonia collapse** | (a) TRUE, (b) REFUTED → **read via CF 08-05** |
| KLIC | earnings_accel | 110.06 | 90.14 | **−18.10%** | +1.05% | −0.68pp | quarterly revenue < $180M | **settles at the 08-05 print** |
| ZVRA | product_ramp | 14.105 | 10.06 | **−28.68%** | +5.78% | **+5.54pp** | 2 consecutive flat/declining product-rev qtrs | **first evaluable 08-05** |

### Standing debts — declared, not hidden

1. **The research cadence has been due since 07-14 (20 days) and Stage 1–4 sourcing
   has still not run.** The breadth read is a subagent fan-out this session was not
   authorised to spawn, and a thin single-pass read would violate F2 and poison Arm
   A. So **$449.94 (~10% of equity) stays undeployed** and the book stays at six.
   The cadence key is deliberately NOT stamped so it stays visibly due. **A
   dedicated `/oracle-research` session is required.**
2. **NEW (08-03): the live book has no dossier records.**
   `cache/oracle_upside_dossiers.json` still contains only the SUPERSEDED 07-06
   paper round (SABR/ACVA/CBZ/FRPT/EYE/NCNO). None of TPC/KLIC/PAY/ZVRA/QTWO/LXU
   has a dossier, which means **Stage 5's `evaluate_exit(dossier, …)` cannot be run
   mechanically on any held name** — every tend since 07-10 has checked typed kills
   from journal prose by hand. That has worked (the kills are carried verbatim
   session to session), but the deterministic half of Stage 5 is not wired to the
   live book. I did NOT back-fill dossiers tonight: reconstructing selection
   artifacts after the fact would contaminate Arm A. This needs a dedicated session
   that rebuilds them from the 07-10 round's actual reads, and it should happen
   before the next funding round.


## Worldview (2026-07-30 — the peer check found a THIRD mode, and it cost me a belief)

Oracle hunts the few under-covered names with the biggest REAL upside over a
6–24mo hold. The edge is the breadth read — reading filings the desk doesn't, in
the small-cap corner. The spotlight only AIMS; the read decides. The engine is
LIVE: the Stage-1 read-cascade was built and calibrated (2026-07-07→07-10), ran
the full 3,154-name field on 2026-07-10, and funded the first real book the same
day. Sourcing pause lifted 2026-07-14.

**07-29 was the session the book stopped being a paper claim** — LXU and QTWO
both printed, both typed kills were tested against the actual 8-Ks, both FAILED
to trigger, and both theses were confirmed by the filings. That still stands.

**07-30 is the session the peer check earned its keep in a new way — by
overturning something I had just concluded.** For two sessions I checked KLIC
against the semicap complex on the way DOWN, found it tracked to within 0.7–2.3pp,
and explicitly walked back a name-level worry as "noise in a violent sector
derating." Today the complex re-rated violently UPWARD (+14.7% median) and **KLIC
captured under half of it (+6.53% vs +14.69% = −8.16pp)**. Full participation in
the selloff, under half the rebound. That asymmetry is not sector beta — it is
the market discounting KLIC specifically, and it means **my 07-29 conclusion was
the weaker hypothesis.** The lesson generalizes: a peer check run only on
down-days measures whether a name falls with its complex, which is the easy half.
The information is in the **asymmetry between the two directions**, and you only
get it by running the check on up-days too.

Nothing was traded on it. The kill is print-based, F3 forbids selling a drawdown,
and a price move is not information until the filings speak. But the ~08-05 KLIC
print is now the single most consequential date in the book.

## The LIVE book — round `upside-2026-07-10-r1` ($4,500 basis, filled 07-10 open)

Funnel: 3,154 field → 251 filing-read → 73 fundable → 6 sized. All six carry a
typed kill; every kill is PRINT-BASED, so kill checks concentrate at earnings.
A drawdown is never an exit.

### CURRENT STATE — 2026-08-05 CLOSE (supersedes the 07-30 table below)

| Name | infl_type | entry | close 08-05 | vs entry | wt | typed kill | kill status |
|------|-----------|-------|-------------|----------|----|------------|-------------|
| PAY | earnings_accel | 28.87 | 40.00 | **+38.55%** | 20.61% | YoY revenue growth < 15% | **TESTED 08-04/05 on 10-Q XBRL (+28.80%) → FAILED (held)**; next ~11-04 |
| TPC | turnaround | 75.96 | 84.32 | +11.01% | 17.47% | 2 consecutive GAAP loss quarters | **PRINT PENDING — not filed at 20:20Z**; cannot fire on one print; test the 8-K next session |
| QTWO | earnings_accel | 53.00 | 63.595 | +19.99% | 17.17% | GAAP net loss relapse or growth < 10% | TESTED 07-29 → FAILED (held); next ~11-04 (tentative) |
| KLIC | earnings_accel | 110.06 | 93.84 | −14.74% | 12.87% | quarterly revenue < $180M | **TESTED 08-05 on the 8-K → FAILED DECISIVELY ($330.409M = 1.84×)**; now UNREACHABLE → re-type candidate |
| LXU | earnings_accel | 10.96 | 9.675 | −11.72% | 11.49% | quarterly net loss on ammonia price collapse | clause (a) TRUE, clause (b) REFUTED → does not fire; next ~10-28 |
| ZVRA | product_ramp | 14.105 | 10.54 | **−25.27%** | 10.69% | 2 consecutive flat/declining product-rev quarters | **PRINT PENDING — not filed at 20:20Z; DATE DISPUTED** (RH says 08-05 verified, prior-year analog 08-12); cannot fire on one print |

Equity **$4,637.34** (cash $449.94 + marks $4,187.40). vs $4,500 basis **+3.05%**;
SPY 751.31 → 769.74 **+2.45%**; **excess +0.60pp** (was +0.08pp at the 07-30 close).
vs contributed $4,353.89 **+6.51%**. Peak $4,739.09 (this morning's intraday tend)
→ drawdown −2.15% against a 40% breaker. Zero orders account-wide since 07-20.
Stage-6 `due_for_grade` = 0; `llm_lift` untrustworthy (34 Arm-B / 31 Arm-A
unresolved) and NOT reported; `update_calibration` = `{}` (neutral, n=0).
**CLUSTER: PAY+QTWO = $1,751.99 = 37.78%** of equity, up from 35.4% on 07-30 —
approached through the denominator, not a decision.

| Name | infl_type | entry | close 07-30 | vs entry | typed kill | kill status |
|------|-----------|-------|------|------|------------|-------------|
| PAY (Paymentus) | earnings_accel | 28.87 | 34.855 | **+20.73%** | YoY revenue growth < 15% | not evaluable → **~08-03 print** |
| QTWO (Q2 Holdings) | earnings_accel | 53.00 | 59.06 | +11.43% | GAAP net loss relapse or growth < 10% | **TESTED 07-29 → FAILED (held)**; live again ~11-04 |
| TPC (Tutor Perini) | turnaround | 75.96 | 83.28 | +9.64% | 2 consecutive GAAP loss quarters | not evaluable → ~08-05 print |
| LXU (LSB Industries) | earnings_accel | 10.96 | 11.06 | +0.91% | quarterly net loss on ammonia price collapse | **TESTED 07-29 → FAILED (held)**; next ~10-28 |
| KLIC (Kulicke & Soffa) | earnings_accel | 110.06 | 88.27 | **−19.80%** | quarterly revenue < $180M | not evaluable → **~08-05 print** |
| ZVRA (Zevra) | product_ramp | 14.105 | 9.64 | **−31.66%** | 2 consecutive flat/declining product-rev quarters | not evaluable → ~08-11 print |

Mark 2026-07-30 CLOSE (after-close Zeus tend, official 4pm closes, quotes
19:59–20:00Z; the second tend today — supersedes the 14:12Z intraday marks):
equity **$4,446.16** (−1.20% vs basis; SPY 741.73 vs spy_entry 751.31, −1.28%;
excess **+0.08pp — COLLAPSED from +1.49pp at the 07-29 close**, via +0.23pp
intraday). Cash $449.94. **The book made $8.08 (+0.18%) on a +1.68% SPY day —
the largest one-day excess give-back since the 07-10 funding**, and it is almost
entirely KLIC and TPC under-participating in violent sector rallies. Reconcile
clean 6/6 exact; zero orders account-wide since 07-20; breaker −1.20% vs 40%.
A/B due_for_grade=0 (326 rows, 0 graded, earliest horizon 15mo → ~Oct 2027);
`update_calibration` returns `{}` (neutral, n=0). Stage 5 `evaluate_exit` run
verbatim on all six = NO EXIT.

### The close peer checks — two readings changed vs the intraday tend

Duty 1b, run on the official closes. Every name that moved >3% got 3–5 peers and
a median. **Two of the four readings differ from the 10:12 ET tend**, which is
itself the argument for marking at the close rather than intraday:

- **KLIC +6.53% vs semicap median +14.69%** (LRCX +17.95, AMAT +15.01,
  ONTO +14.69, ACLS +11.91, KLAC +5.90) = **−8.16pp**. The intraday reading was
  −5.83pp; **the gap did not close into the bell, it widened by ~2.3pp.** See the
  worldview above — this is the session's finding.
- **TPC +8.61% vs E&C median +12.91%** (STRL +17.39, PWR +17.28, MTZ +12.91,
  GVA −2.27, ACM −2.42) = **−4.30pp**, reversing the intraday "no divergence, the
  complex was broadly bid." Caveat honestly: the peer set split hard (three at
  +13–17%, two at −2%), so this median is less stable than usual and this
  divergence carries materially less weight than KLIC's.
- **LXU −3.49% vs fertilizer median +0.17%** (MOS +0.69, NTR +0.17, CF −1.24) =
  −3.66pp — a second consecutive session lagging its complex, but LXU **recovered
  ~3.4pp into the close** off the −6.89% intraday low.
- **PAY −5.03% vs payments median −2.84%** (TOST +0.74, NCNO −2.44, ALKT −2.84,
  FOUR −4.09, BILL −4.37) = −2.19pp. Hands back ~2.2pp of yesterday's clean
  +5.84pp idiosyncratic gain. Net over two sessions PAY is still well ahead of its
  complex — the 07-29 signal is **dented, not erased**. The 08-03 print settles it.

### ZVRA — the CHMP 8-K window CLOSED WITHOUT A FILING (deferred item, resolved)

The 07-24 CHMP negative-opinion press release fell on a Friday; the
4-business-day 8-K window ran 07-27/28/29/30 and **today was the last day.
Nothing was filed** — EDGAR CIK 1434647 re-checked ~20:15Z, newest filing is
still the 07-08 Form 144.

**This is not a disclosure failure.** A CHMP opinion on an EU marketing
application triggers no enumerated 8-K item, and Item 8.01 is voluntary; Zevra
was entitled to disclose by press release alone. But it has a real consequence
for the engine: **there will never be a primary FILED document on the CHMP
event.** The company PR is the primary source of record, and the ~08-11
re-underwrite must lean on the 10-Q's product-revenue lines rather than waiting
for an 8-K that is not coming.

### LXU — I verified the intraday claim instead of inheriting it

The 14:12Z tend asserted that today's Item 7.01 deck (acc 0001193125-26-325064)
"discloses NO new financial fact beyond the 07-29 Item 2.02." I checked rather
than assumed, because the deck's **El Dorado CCS project** looked like a new
upside leg: $25–30M of annual earnings once fully operational, Q1'27 start,
$85/MT 45Q credits, ~$95M remaining capital, 100% owned, no upfront cash.
**The intraday read was correct** — CCS appears in the 07-29 earnings release
EX-99.1 ("Low Carbon Ammonia Project Summary"), not first in today's deck.

What the deck *does* add is corroboration the tape is ignoring, on a **TTM** basis
where the turnaround-quarter noise disappears entirely (slides 8, 11, 12):
TTM 6/30/26 Adjusted EBITDA **$199.4M vs $122.4M (+63%)**, net sales **$658.1M vs
$538.9M (+22%)**, net income **+$36.7M vs −$33.1M**, Adj EBITDA margin **30% vs
23%**, **net debt/TTM Adj EBITDA 1.1x vs 2.7x**, operating cash flow $59M vs $18M,
FCF $32M vs $8M, cash $218M. The earnings_accel thesis is intact on the record
while the tape marks it down — the filing wins under doctrine, and the ~10-28 Q3
print settles it.

**CLUSTER WATCH: PAY+QTWO = $1,572.27 = 35.4% of equity** (down from 36.8% as PAY
gave back) — inside the 40% cap.

**CIK HYGIENE — all six re-resolved from EDGAR `company_tickers` this session and
all matched the pins:** TPC 77543, KLIC 56978, PAY 1841156, QTWO 1410384,
ZVRA 1434647, LXU 60714.

**SOURCING — conscious no-op, same reasoning, logged not silent.** The research
cadence still reads DUE (last 07-14, 16 days). Still a no-op: the book holds 6
names = the TOP of the Stage-4 3–6 band; no kill fired, so no capital was freed;
cash $449.94 is ~10% of equity and is a CEILING against a shared pool. A fresh
round would produce dossiers that **cannot be funded without selling**, which F3
forbids absent a typed kill. The research stamp stays untouched deliberately so it
remains visibly due to the operator. Revisit when a kill frees capital or the
operator funds more.

### Earlier marks (history)

Mark 2026-07-30 ~10:12 ET intraday (Zeus hourly tend, quotes 14:10–14:11Z):
equity $4,428.19 (−1.60% vs basis; SPY 737.585, excess +0.23pp). Superseded by
the close mark above. Reconcile clean at both checks; the only new filing all day
was the LXU Item 7.01 deck.

Mark 2026-07-29 CLOSE (after-close Zeus tend, official 4pm closes, quotes
19:59–20:00Z): equity **$4,436.63** (−1.41% vs basis; SPY 729.54 vs spy_entry
751.31, −2.90%; excess **+1.49pp — WIDENED HARD from +0.53pp at the 07-28
close** on a −1.53% SPY day; day P&L −$23.73). Cash $449.94. Close vs entry:
**PAY +27.14%** (36.705, **+7.51%**), **QTWO +13.91%** (60.37, +1.91%),
LXU +4.52% (11.455, +0.22%), TPC +0.91% (76.65, −6.50%), **KLIC −24.77%**
(82.80, −8.94%), ZVRA −30.66% (9.78, +0.51%). Reconcile clean 6/6 exact; zero
orders account-wide since 07-20; breaker −1.41% vs 40%. A/B due_for_grade=0
(242 rows in the 07-10 round, 0 graded, earliest horizon 15mo → ~Oct 2027);
calibration still neutral.

#### [07-29] LXU Q2'26 — the kill landed on clause (a) and DIED on clause (b)

**8-K acc 0001193125-26-323751, Item 2.02 + EX-99.1, filed 07-29.** This was the
session's hard call, so the reasoning is written out in full.

The kill is a **conjunction**: *"quarterly net loss on ammonia price collapse."*
- Clause (a) **TRUE**: GAAP **net loss $6.2M** vs net income $3.0M a year ago;
  diluted LPS −$0.09 vs +$0.04. Against a $0.46 consensus that is a **−$0.55
  miss** — enormous on its face.
- Clause (b) **REFUTED BY THE ISSUER'S OWN TABLE**: Tampa Ammonia benchmark
  **$787/ton vs $416 = +89% YoY**; NOLA UAN $494 vs $344 = **+44%**; average
  natural-gas input cost **$2.96/MMBtu vs $3.50 = −15%**. There is no ammonia
  price collapse; ammonia nearly doubled while the key input got cheaper.

And the underlying trajectory *accelerated*: net sales **$168.1M vs $151.3M
(+11.1%)**, Adjusted EBITDA **$53.1M vs $38.3M (+38.6%)** — margin 31.6% vs
25.3%, **+630bp** — and H1 Adjusted EBITDA **$105.2M vs $67.4M (+56%)**.
Cash + ST investments $218.0M against total debt $441.3M.

**The loss is arithmetic, not deterioration:** turnaround expense **$28.8M vs
$2.6M = a +$26.2M swing**, against a YoY net-income swing of only $9.2M. LSB
completed the El Dorado ammonia turnaround on time/on budget and **pulled the
Pryor turnaround FORWARD from Q3 into Q2**. That is exactly why consensus was
$0.46 — the Street modelled Pryor in Q3. Management: *"positions us to generate
stronger results in the second half of 2026."*

**Verdict: NO EXIT, thesis confirmed and strengthened.** `evaluate_exit` run
verbatim → `fundamental_deteriorated=False` (growth and margins moved the right
way in the filing). A one-line reading of "net loss → fire" would have sold the
strongest-improving name in the book on a planned-maintenance quarter.

#### [07-29] QTWO Q2'26 — both clauses fail, and it's the best print in the book

**8-K acc 0001410384-26-000051 (Items 2.02/8.01/9.01) + 10-Q acc
0001410384-26-000053, filed 07-29.** Kill = *"GAAP net loss relapse or growth
< 10%."*
- **GAAP net income $29.9M** vs $11.8M prior-year quarter and $26.6M in Q1 → no
  loss relapse, and GAAP income more than doubled.
- **Revenue $219.8M, +13% YoY** → clears the 10% floor.
- Corroborating: GAAP gross margin **59.2% vs 53.6%** (+560bp); Adjusted EBITDA
  **$62.8M vs $45.8M** (+37%); Subscription ARR **$825.5M, +15%**; backlog
  **~$2.8B, +17%**; **retired the convertible notes in June — quarter ended
  DEBT-FREE**; **FY26 guidance RAISED** on both revenue ($881–886M) and adjusted
  EBITDA ($244–248M, 28% margin); Board authorized **an additional $350M
  buyback** on top of the Nov-2025 $150M.

Non-GAAP EPS was $0.70 vs $0.62 est, but the kill is written on GAAP and on
growth — and it is tested on those, not on the headline.

**FORWARD FLAG (the one thing to carry):** Q3 guidance is **$218.5–222.5M =
8–10% YoY growth**, which **brushes the kill's "<10% growth" clause.** Nothing
triggers today because the kill tests actuals, but **the ~2026-11-04 Q3 print is
now a live kill date, not a formality.** Guidance is not a kill; it is a warning
that this kill can land on arithmetic alone.

#### [07-29] Peer checks — three moves, and one is real

On a −1.53% SPY day:
- **PAY +7.51% vs payments peer median +1.67%** (BILL +2.29, FOUR +2.13,
  NCNO +1.67, ALKT +0.83, TOST +0.77) = **+5.84pp — the FIRST clean
  idiosyncratic PAY divergence.** This is materially different from 07-27/07-28,
  where PAY's +9.04%/+8.53% were complex-wide rallies I correctly discounted as
  cluster beta. Tonight the complex was barely green while the tape was red, and
  PAY still put on 7.5%. That is a name-level fact. It is **still not
  confirmation** — the 08-03 print is what settles the +27.14%.
- **KLIC −8.94% vs semicap peer median −8.26%** (KLAC −11.00, ONTO −9.71,
  AMAT −8.26, LRCX −7.04, ACLS −6.69) = **−0.68pp. This NARROWS the 07-28
  question.** Yesterday KLIC lagged its complex by ~2.3pp and I logged it as a
  name-level question; today, with the complex down another ~8%, KLIC tracked it
  to within 0.7pp. The honest update is that the 07-28 gap looks more like noise
  in a violent sector derating than a name signal. KLIC is the book's worst name
  (−24.77%) and is held under F3 **with conviction, not neglect** — the kill
  (quarterly revenue < $180M) is first evaluable at the ~08-05 print.
- **TPC −6.50% vs E&C peer median −4.68%** (STRL −8.15, MTZ −8.02, PWR −4.68,
  GVA −2.82, ACM −1.16) = −1.82pp. Mild, no filing behind it. Logged, not acted on.

#### [07-29] Other filings dispositioned

- **PAY Form 144 (acc 0001950047-26-007401, 07-29)** — TF Investment Holdings
  LLC, a **director**-related holder, proposes to sell **40,000 sh / $1.37M**
  against **62,936,502 shares outstanding = 0.06%**. This is the **second 144 in
  two days** (07-28 was 0001950047-26-007360), both landing after PAY's ~+27%
  run and days before the print. Individually trivial and routine for an
  affiliate 10b5-1 plan; the *pattern* is worth watching, not acting on. Not
  kill-relevant (PAY's kill is print-based).
- **PAY 13G (acc 0002012383-26-002850, 07-29)** — **BlackRock 4,362,220 sh =
  6.9% of class**, Rule 13d-1(b), type HC = **passive**, not an activist 13D.
  Mildly supportive; not kill-relevant.
- **ZVRA: the CHMP 8-K STILL has not landed.** Newest ZVRA filing remains the
  07-08 Form 144. The PR was 07-24 and **07-30 is the LAST day of the
  4-business-day window** — the next tend either reads the 8-K or records that
  the window closed without one, which is itself a fact worth logging.

**CIK HYGIENE — all six re-resolved from EDGAR `company_tickers` this session and
all matched the pins:** TPC 77543, KLIC 56978, PAY 1841156, QTWO 1410384,
ZVRA 1434647, LXU 60714. Never hand-type: 1053691 is CervoMed, not Zevra, and a
wrong CIK returns a clean-looking "zero new filings."

**CLUSTER WATCH: PAY+QTWO = $1,632.88 = 36.8% of equity** (up from 35.8%) — the
tightest yet and closing on the 40% cluster cap. Both have now printed or print
within three sessions; QTWO's is in and strong.

**SOURCING — conscious no-op, reasoned again.** The research cadence reads DUE.
Still a no-op, and logged rather than silent: the book holds 6 names = the TOP of
the Stage-4 3–6 band, so a fresh name would breach the band's intent; no kill
fired tonight, so no capital was freed; cash $449.94 is ~10% of equity and is a
CEILING against a shared pool (live broker buying power $1,179.35 tonight, but it
is shared). A fresh round would produce dossiers that **cannot be funded without
selling**, which F3 forbids absent a typed kill. Revisit when a kill frees
capital or the operator funds more. The research stamp stays untouched deliberately.

#### Marks before 2026-07-29

Mark 2026-07-28 CLOSE (after-close Zeus tend, 4pm prints, quotes 19:59–20:00Z):
equity **$4,460.50** (-0.88% vs basis; SPY 740.76 vs spy_entry 751.31, -1.40%;
excess **+0.53pp**, off the +0.88pp at the 07-27 close, up from +0.31pp at
today's 10:13 ET tend; day P&L -$5.41 on a +0.23% SPY tape). Cash $449.94.
Close vs entry: **PAY +18.34%** (34.165, +8.53% — new book leader), QTWO +11.74%
(59.22, +1.84%), TPC +8.03% (82.06, -4.33%), LXU +4.29% (11.43, -0.26%),
**KLIC -17.45%** (90.85, -7.50%), ZVRA -31.09% (9.72, +0.10%). EDGAR swept all
six CIKs (>= 07-24): **ZERO new filings on all six** — no typed kill evaluable;
Stage 5 `evaluate_exit` run verbatim on all six = NO EXIT; held. Reconcile clean
6/6 exact; zero orders account-wide since 07-20; breakers ok. Live broker
buying_power $1,179.35 vs sleeve cash claim $449.94 (sleeve binds; moot, no buy).
The ZVRA CHMP 8-K **still** has not landed — one business day left in the window
(~07-30).

**THE 07-27 LESSON APPLIED IN BOTH DIRECTIONS — every big move today was its
sector.** Four moves, four peer checks, zero name events:
- **KLIC -7.50% vs semicap peer median -7.53%** (AMAT -7.82, ONTO -7.78,
  LRCX -7.53, ACLS -6.35, KLAC -6.18) — dead-on the sector, session four of the
  AI-capex-fear selloff. KLIC is now -17.45% vs entry, the book's second-worst
  drawdown, and is held **with conviction under F3, not neglect**: the kill is
  quarterly revenue < $180M, first evaluable ~08-05.
- **TPC -4.33% vs E&C peer median -5.19%** (STRL -15.28 — looks like a print,
  MTZ -7.29, PWR -5.19, GVA -3.33, ACM +4.90) — a sector derating TPC actually
  *outperformed*.
- **PAY +8.53% vs payments peer median +4.78%** (FOUR +9.83, NCNO +4.82,
  TOST +4.78, BILL +3.22, ALKT +2.34) — second consecutive complex-wide rally
  day. PAY sits above the median but inside FOUR's range, so the honest read is
  **mostly cluster beta with at most a modest idiosyncratic sliver.** The 08-03
  print settles the thesis; the tape does not. Do not bank the +18.34%.
- **LXU -0.26% vs fertilizer peer median +3.04%** (MOS +3.27, NTR +3.04,
  CF +2.65) — the one genuinely NEW signal: LXU **lagged its own complex by
  ~3.3pp on the eve of its print**, the first negative divergence from ammonia
  strength since entry. Peer strength is mild evidence *against* the LXU kill
  ("quarterly net loss on ammonia price collapse"); the divergence is a
  name-level question tomorrow's print answers.

**CLUSTER WATCH: PAY+QTWO = $1,557.78 = 34.9% of equity** (up from 33.1%) —
inside the 40% cap but the tightest yet. Two of the six move together.

**PRINT CALENDAR RE-VERIFIED 07-28:** LXU **2026-07-29 pm (VERIFIED)**, Q2 est
$0.46 EPS vs $0.04 actual a year ago — a large expected step-up, and LXU beat the
last two (Q1'26 $0.27 vs $0.12; Q4'25 $0.22 vs $0.20). QTWO **2026-07-29 pm
(VERIFIED)**, Q2 est $0.62. Then PAY ~08-03, KLIC ~08-05, TPC ~08-05, ZVRA ~08-11.
**The 07-30 tend is the first with teeth — pull both prints and test both kills
verbatim.**

Mark 2026-07-27 CLOSE (after-close Zeus tend, 4pm prints, quotes 19:59–20:00Z):
equity **$4,465.91** (-0.76% vs basis; SPY 739.02 vs spy_entry 751.31, -1.64%;
excess **+0.88pp — RECOVERED** from -0.16pp at the 10:18 ET tend, on a flat tape,
+$35.68 on the day). Cash $449.94. Close vs entry: TPC +12.86% (85.73, -1.20%),
QTWO +9.60% (58.09, **+6.37%**), PAY +9.04% (31.48, **+9.04%**), LXU +4.65%
(11.47, **-6.29%** into its own print), KLIC -10.78% (98.20, -3.09%), ZVRA
-31.16% (9.71, +1.94%). EDGAR swept all six CIKs post-close (>= 07-24): **ZERO
new filings on all six** — no typed kill evaluable; Stage 5 `evaluate_exit` run
verbatim on all six = NO EXIT; held. The ZVRA CHMP 8-K **still** has not landed
(PR 07-24; window closes ~07-30). Reconcile clean 6/6 exact; zero orders
account-wide since 07-20; breakers ok.

**LESSON LOGGED — read a big green day before believing it.** PAY +9.04% and
QTWO +6.37% with SPY +0.01% and ZERO filings looked like the thesis arriving. It
was not: the whole fintech/payments-software complex rallied — NCNO +6.64%, TOST
+6.15%, ALKT +5.90%, GPN +3.88%, FOUR +3.33%, BILL +3.17%, JKHY +1.63%. Today's
gain is **cluster beta, not idiosyncratic confirmation**, and the excess-recovery
to +0.88pp should be discounted accordingly. (Symmetric to KLIC, whose -3.09% is
the semi-equipment complex, not a name event — the same discipline that forbids
selling KLIC on sector red forbids celebrating PAY on sector green.) PAY+QTWO =
$1,479 = **33.1% of equity in one cluster**, inside the 40% cap but worth
watching: the book is more correlated than six names suggests. The prints
(QTWO 07-29, PAY 08-03) are what settle the theses, not tape.

**BOOKKEEPING GAP (flagged 07-27, deliberately NOT patched — fail-safe says open
a PR, never silently patch):** `cache/oracle_upside_book.json` still holds the
07-06 paper round (`{"CBZ": 3000.0}`) and `cache/oracle_upside_dossiers.json`
still holds the 07-06 paper six (SABR/ACVA/CBZ/FRPT/EYE/NCNO). **Neither was
overwritten at the 07-10 funding**, so the live six's typed kills exist only in
`oracle_journal.jsonl` (the authoritative append-only record) and
`oracle_upside_ab.json`. Stage 5 is being run off the journal kills each tend —
correct, but the Stage-4 artifact does not describe the live book. The next FULL
round must rewrite both files.

Mark 2026-07-27 ~10:18 ET intraday (Zeus hourly tend, quotes 14:17Z): equity
$4,430.23 (-1.55% vs basis; SPY 740.83 vs spy_entry 751.31, -1.39%; excess
**-0.16pp — the FIRST NEGATIVE excess reading since the 07-10 funding**, after
+0.23pp at the 07-24 open and -0.06pp at the 07-24 close). The whole give-back
is two names, both HELD per Stage 5 / F3: **ZVRA -29.95% vs entry** (9.88, but
+3.73% today — the first bounce since the CHMP gap) and **KLIC -10.05%** (99.00,
-2.30% today; the semi-equipment selloff ran a third session — AMAT/LRCX/KLAC all
red again). The other four carry the book: QTWO +8.28% (57.39, **+5.09% today, its
best day since entry**, two sessions before its print), TPC +10.91% (84.25, -2.90%),
LXU +6.48% (11.67, -4.66% into its own print), PAY +3.71% (29.94, +3.71%).
EDGAR swept all six CIKs for filings >= 07-24: **ZERO new filings on all six** —
no typed kill evaluable (every kill is print-based). Worth flagging: **the ZVRA
CHMP 8-K STILL has not been filed** (PR was 07-24; the 4-business-day window
closes ~07-30). Reconcile clean 6/6 exact; pre_trade_check TRUE house-wide; zero
orders account-wide since 07-20. A/B due_for_grade=0. Sourcing: conscious no-op
again (duty 3). **The 07-30 tend is the first with teeth — LXU and QTWO print
2026-07-29 pm; pull both and test the kills verbatim.**

Mark 2026-07-24 ~10:30 ET intraday (Zeus hourly tend, quotes 14:18Z): equity
$4,432.25 (-1.51% vs basis; SPY 738.25 vs spy_entry 751.31, -1.74%; excess
+0.23pp — narrowed HARD from +3.43pp at the 07-23 close). **THE EVENT: ZVRA
-20.5% on the day (9.95, -29.5% vs entry) on a CHMP NEGATIVE OPINION on the
arimoclomol EU MAA for NPC** (company PR 07-24; re-examination to be
requested; global EAP continues; NO 8-K on EDGAR yet — next tends re-read
the 8-K when it lands). Typed-kill test ran and did NOT trigger: the
underwritten thesis is the US MIPLYFFA product_ramp, kill = 2 consecutive
flat/declining product-rev quarters (first evaluable ~08-11 print); no
dated EU catalyst was underwritten, so no catalyst_fail; not a
fundamental_break/dilution/going-concern. HELD — a drawdown is never an
exit. BUT the CHMP hit is a REAL haircut to upside_x (EU optionality gone
or delayed); the 08-11 re-underwrite must consciously re-price ZVRA's
upside, not just test the kill. KLIC -5.1% (100.71, -8.5% vs entry) on the
sector-wide semi-equipment selloff (AMAT/LRCX/KLA -23–28% off 6/30 peaks,
AI-capex fears; no filing) — drawdown noise, held. PAY 8-Ks 07-23
dispositioned: director resignation (AKKR nominee, no disagreement) + 5.07
votes — not kill-relevant. Reconcile clean 6/6; zero orders; A/B
due_for_grade=0; sourcing conscious no-op continues (duty 3).

Mark 2026-07-23 CLOSE (after-close tend, 4pm prints, quotes 19:59-20:00Z):
equity $4,575.94 (+1.69% vs basis — NEW CLOSING HIGH; SPY 738.24 vs
spy_entry 751.31, -1.74%, a -1.23% SPY day the book closed green through;
excess +3.43pp, widened from +1.34pp at the 07-22 close). Cash $449.94.
Per-name vs entry: TPC +15.25% (87.54), LXU +11.50% (12.22, +3.2% on the
day), PAY -0.38%, QTWO -0.23% (stabilized after the 07-22 slide), KLIC
-3.65%, ZVRA -11.31% (12.51, +3.1% on the day; drawdown, never an exit;
kill first evaluable ~08-11 print). EDGAR sweep all six CIKs ~20:10Z
(>= 07-17): ZERO new filings (only the dispositioned PAY Wasatch 13G/A
07-17) — no kill evaluable; all six kills print-based. Broker reconcile
clean: 6/6 share counts exact; zero orders account-wide today. A/B
due_for_grade=0. Sourcing remains a conscious no-op (standing duty 3 —
fully deployed, 07-10 pipeline fresh); research stamp untouched. First kill
checks with teeth: LXU + QTWO prints 2026-07-29 pm — the 07-30 tend must
pull both prints and test the kills verbatim.

Mark 2026-07-23 ~10:12 ET intraday (Zeus hourly tend): equity $4,563.00
(+1.40% vs basis; SPY 740.49, excess +2.84pp). Superseded by the close mark
above; EDGAR and reconcile were clean at both checks.

Mark 2026-07-22 CLOSE (after-close tend, 4pm prints, quotes 19:59-20:00Z):
equity $4,536.42 (+0.81% vs basis — giveback day off the 07-21 high
$4,593.91; SPY 747.33 vs spy_entry 751.31, -0.53%; excess +1.34pp,
narrowed from +2.49pp). Cash $449.94 (~10%). Per-name vs entry: TPC
+14.55% (87.01, +0.3% on the day), LXU +8.12% (11.85, +2.6% on the day),
PAY +0.61% (29.045, -1.9% on the day), QTWO -0.21% (52.89, -4.1% on the
day — second straight no-filing slide into the 07-29 print; drawdown
noise, never an exit), KLIC -4.10% (105.55, -2.8% on the day), ZVRA
-14.00% (12.13, -2.6% on the day; drawdown, never an exit; kill first
evaluable at the ~08-11 print). EDGAR all six CIKs at ~20:08Z: ZERO new
filings since 07-17 — the only post-entry filings remain the KLIC JPM 13G
(07-16) and PAY Wasatch 13G/A (07-17), both passive-ownership,
dispositioned, NOT kill-relevant. No kill evaluable; all six kills
print-based. **PRINT CALENDAR (confirmed 07-17): LXU 2026-07-29 pm
(VERIFIED), QTWO 2026-07-29 pm (VERIFIED), PAY 2026-08-03 pm (tent.), KLIC
2026-08-05 pm (tent.), TPC 2026-08-05 pm (tent.), ZVRA 2026-08-11 pm
(tent.). First kill checks with teeth: LXU + QTWO on 07-29 — the 07-30 tend
must pull both prints and test the kills verbatim.** Broker reconcile clean
07-21 close: 6/6 share counts exact; no oracle orders today; personal/OGN
positions invisible; legacy CXT/HDSN/J/PSN/VITL absent as expected (exited
07-06). A/B due_for_grade=0. Sourcing remains a conscious no-op (standing
duty 3 — fully deployed, shared buying-power pool, 07-10 pipeline fresh);
research stamp untouched.
NOTE (housekeeping): earlier 07-16 tend entries stamped 18:15Z ("14:15 ET")
actually ran ~15:05Z (~11:05 ET) — UTC mislabeled as ET; entries from 15:30Z
onward are stamped correctly in UTC. Zeus dispatch headers may still carry the
mislabel (today's said "~14:05 ET" at a 14:07 UTC clock).

## A/B state (Stage 6 — the checkpoint's evidence)

`cache/oracle_upside_ab.json`: **326 candidate rows total** — 242 from the 07-10
funding round (real entry/spy marks; the 6 funded names are Arm A, the passed 236
are Arm B/paper), plus `calib-2026-07-09` (78) and `convex-2026-07-07` (6).
**0 graded; `due_for_grade` = 0.** Horizons on the 07-10 round run 15–24mo, so the
earliest grade lands ~Oct 2027 — `llm_lift` returns "insufficient graded data" and
`lift_trustworthy=false`, correctly. The calibration writer stays neutral (0.5) until
the first grades land. **Do not read the +1.49pp excess as LLM-lift** — excess vs
SPY is the book's P&L; LLM-lift is Arm A minus Arm B, and it is not yet measurable.

## Open theses

- **The six, held to their typed kills.** Two are now tested and standing.
- **LXU (kill tested 07-29, FAILED → held).** The earnings_accel thesis is
  confirmed by the filing, not the tape: ammonia +89% YoY, gas −15%, revenue
  +11.1%, H1 adj EBITDA +56%. The 07-30 deck adds the **TTM** view, which is the
  cleanest form of the thesis because it washes out turnaround timing entirely:
  TTM adj EBITDA $199.4M vs $122.4M (+63%), net sales +22%, net income +$36.7M vs
  −$33.1M, net debt/TTM adj EBITDA 1.1x vs 2.7x. The open question is **H2
  delivery**: management promised "stronger results in the second half" with El
  Dorado done and Pryor finishing in Q3. The ~2026-10-28 Q3 print is the test —
  and Q3 still carries residual Pryor cost, so read it on adjusted EBITDA and
  production rates, not headline EPS. **Resolved 07-28's puzzle:** the 3.3pp lag
  vs CF/NTR/MOS into the print was the market pricing the turnaround miss.
  **Still open:** LXU lagged its complex again on 07-30 (−3.66pp), a second
  session of the tape disagreeing with the filing. Doctrine says the filing wins;
  two sessions is a pattern worth naming, not yet worth acting on.
- **A dated upside leg nobody is paying for yet: El Dorado CCS** (disclosed in
  the 07-29 earnings EX-99.1, restated in the 07-30 deck). ~$25–30M of annual
  earnings once fully operational, ops beginning **Q1'27 — inside the hold
  window**, $85/MT 45Q credits, ~$95M remaining capital, 100% owned, no upfront
  cash. Against TTM adj EBITDA of $199.4M that is a ~13–15% increment. Whether the
  07-10 underwrite priced this is unknown (the dossier state gap below), so treat
  it as a candidate addition to `upside_x` at the next re-underwrite, not as an
  established part of the thesis. Milestone to watch: **Class VI permit, expected
  later in 2026**.
- **QTWO (kill tested 07-29, FAILED → held) — and a dated kill risk.** Best print
  in the book (GAAP income $29.9M, +13% growth, debt-free, guide raised, +$350M
  buyback). **But Q3 guidance of 8–10% growth brushes the "<10% growth" kill
  clause.** The ~2026-11-04 print is a live kill date. Two honest readings: either
  QTWO's growth is genuinely decelerating toward the high single digits (in which
  case the kill was well-written and should fire), or guidance is conservative as
  it has been (Q2 came in at 13% against a similar setup). **Do not pre-decide —
  test it on the November filing.** If it lands, fire it: a kill is a promise.
- **PAY — the first clean idiosyncratic signal, dented but not erased.** +20.73%
  vs entry. It put on +5.84pp vs its complex on 07-29 and handed back −2.19pp on
  07-30; net over two sessions it is still well ahead of the payments group. The
  **08-03 print (2 business days out)** tests the kill (YoY revenue growth < 15%).
  Two director-entity Form 144s in two days ahead of it are a pattern to note, not
  to trade on.
- **KLIC — held with conviction at −19.80%, and the read on it just REVERSED.**
  On 07-29 I concluded the drawdown was a pure sector derating and walked back a
  name-level worry. On 07-30 the semicap complex ripped +14.69% and KLIC captured
  +6.53% — **−8.16pp, and the gap widened ~2.3pp from the intraday reading.**
  Full participation down, under half up. My 07-29 conclusion is now the weaker
  hypothesis, and I am carrying that explicitly rather than quietly. Still held —
  the kill is print-based and F3 forbids drawdown exits — but **the ~08-05 print is
  the most consequential date in the book.** Test revenue < $180M verbatim, and
  read the result against this participation asymmetry: if the print is merely
  fine, the asymmetry says the market knows something the 07-10 read did not.
- **TPC — the ~08-05 print tests 2 consecutive GAAP loss quarters.** +9.64% vs
  entry. −4.30pp vs E&C peers at the 07-30 close, but on a peer set that split
  hard (three +13–17%, two −2%), so weight it lightly. No filing behind the move.
- **ZVRA post-CHMP (opened 07-24).** The US-ramp thesis is intact until the ~08-11
  print. **The CHMP 8-K window CLOSED 07-30 WITHOUT A FILING** — resolved, and
  legitimate (no enumerated 8-K item is triggered; Item 8.01 is voluntary). The
  consequence: **no primary FILED document on the CHMP event will ever exist**, so
  the re-underwrite runs off the 10-Q product-revenue lines, not off a pending 8-K.
  At the 08-11 print: (a) test the kill verbatim on product revenue, (b)
  **re-price upside_x WITHOUT near-term EU optionality** (the 07-10 underwrite
  included it), (c) if remaining upside no longer clears ≥1.5x, journal that as a
  thesis-level re-underwrite — explicitly NOT a drawdown exit.
- The interim convex trio (SEER/NNDM/FULC, liquidated 07-10 by operator direction)
  keeps its A/B rows open for grading at horizon — do NOT drop them (an ungraded
  Arm B is survivorship bias).

## Standing duties for the next sessions

0. ~~**FIRST DUTY NEXT SESSION (2026-08-05 close):** pull and test **TPC's** Q2 8-K
   and **ZVRA's** Q2 release the moment they exist~~ — **DISCHARGED 2026-08-06,
   re-verified 2026-08-11.** Both companies filed their Q2 **8-K (Item 2.02) + 10-Q
   on the evening of 08-05**, after that session's 20:20Z check, and both kills were
   tested VERBATIM at the 08-06 pass: TPC printed **$65.7M GAAP net income** (record
   $1.6B revenue +19% y/y, guidance raised) so the two-consecutive-loss counter stays
   at 0; ZVRA printed **$39.663M total net revenue, +53% y/y and +9.5% q/q** so the
   two-consecutive-flat/declining counter stays at 0. The ZVRA date dispute is
   RESOLVED from EDGAR in Robinhood's favour — 08-05, not the ~08-11 this file
   guessed. **Standing lesson from re-verifying it: the journal is append-only and
   authoritative; this file's top section is one evening's snapshot, and a duty
   written into it can outlive the fact that retired it. Check the journal before
   acting on a duty written here.** (~~Still open: pull **CF Industries'** print as
   outside corroboration on LXU clause (b)~~ — **DISCHARGED 2026-08-17.** CF's Q2
   8-K (2026-08-05, acc 0001324404-26-000017) reports ammonia segment net sales
   $586M vs $491M and gross margin $229M vs $136M y/y, states ammonia **average
   selling prices INCREASED** on a tight global nitrogen balance further tightened
   by Iran-conflict supply losses (~1Mt of traded ammonia), and guides the balance
   constructive into 2027. Clause (b) moves AWAY from firing. Scored as
   corroboration ONLY — the clause is typed to LXU's own realized-price table, which
   outranks any peer, and a peer's good quarter never substitutes for it.)
0b. **RE-TYPE KLIC'S KILL — in the next FULL round, not in a tend.** `<$180M`
   against a $330M print guiding to $375M is unreachable and can no longer
   discriminate. It must be reset **before** a print, through
   `make_upside_dossier`, never quietly in the session that discovers it.
   Same audit for every other kill at the same time: *can this still fire?*
0c. **KLIC WATCH items, neither typed and neither a kill:** (i) AR $329.498M vs
   $183.538M at 10/04/25 (+79.5%) against nine-month revenue +62.1% — ~91 days
   DSO; plausibly a quarter that ramped +36% sequentially loading the back end,
   but if AR outruns revenue again next quarter it is a quality-of-earnings
   question, and the prior is on the record BEFORE the answer. (ii) Lester Wong
   signs as **Interim** CEO *and* CFO — no permanent CEO. Governance, not thesis.
1. **Tend daily (cheap):** reconcile fills, mark at official closes, EDGAR-check
   all six held names (CIKs re-resolved from `company_tickers`, never hand-typed);
   evaluate typed kills only on real filings.
1a. **NEW 2026-08-17 — EDGAR's recent-submissions index LAGS, so sweep a WINDOW,
   never "since the last pass".** Today's mid-morning tend (14:18Z) recorded ZERO
   new documents; the after-close sweep at 20:15Z found THREE, all *dated* 08-14
   (TPC 8-K, QTWO Form 4, ZVRA 144). A "since last pass" filter would have carried a
   stale all-clear on a TPC 8-K for three days. **Always query `filing_date >=
   today − 3 days` and re-disposition anything not already in the journal.** A
   duplicate disposition costs one line; a missed 8-K costs the kill check.
1b. **Peer-check every move > ~3% BEFORE interpreting it — ON THE CLOSE, and in
   BOTH tape directions.** It has now caught eleven moves in four sessions and been
   right in every direction that matters: it stopped me celebrating PAY's
   07-27/07-28 sector rallies, it stopped me selling KLIC into a sector derating
   twice, it isolated the one real move (PAY +5.84pp on 07-29), and on 07-30 it
   **overturned my own 07-29 conclusion** by catching KLIC's participation
   asymmetry on an up-day. 3–5 peers, one quote call, take the median.
   **Use official closes** — two of four readings on 07-30 differed materially
   between the 10:12 ET tend and the bell (KLIC −5.83pp → −8.16pp; TPC "none" →
   −4.30pp). **And check the peer set's dispersion:** TPC's E&C median came off a
   set split three-up-13-to-17 / two-down-2, which makes that median weak evidence.
   **AMENDED 2026-08-17 — the 3% trigger is a FLOOR, not a ceiling.** PAY fell only
   -2.84% today, under the trigger, but it is the top weight (19.71%) making its
   second odd-looking move in two weeks, so I pulled the set anyway: 9 of 9 peers
   DOWN, median -2.24%, dispersion 3.77pp, PAY -0.60pp off it → sector, not the
   name. **A top-three weight moving oddly earns the set regardless of magnitude.**
   One quote call is cheaper than one wrong story.
2. **At each held name's print: test the kill VERBATIM on the FILING, never on the
   after-hours reaction.** Tonight proved why. LXU's −$0.55 EPS "miss" and its
   flat, wide-spread after-hours quote (bid 9.88 / ask 13.02) carried almost no
   information; the 8-K's benchmark table settled it in one line.
   **And read the kill's full grammar.** LXU's kill was a conjunction — loss AND
   ammonia collapse. Firing on the first clause alone would have sold the
   fastest-improving name in the book.
3. **Sourcing:** the next FULL cascade round runs when there is capital to deploy
   (a kill/exit or new funding) or at the August re-underwrite — not on a timer
   while the book is fully deployed at 6 names (top of the 3–6 band) and the 07-10
   pipeline (73 fundables) is fresh. Journaled as a conscious no-op 07-14 → 07-29.
4. **Grading:** run `due_for_grade` every session; grade BOTH arms the day they
   come due, then `update_calibration`. Earliest is ~Oct 2027 — do not confuse
   excess-vs-SPY with LLM-lift in the meantime.
5. **BOOKKEEPING GAP — still open, still deliberately unpatched (fail-safe: open a
   PR, never silently patch).** `cache/oracle_upside_book.json` still holds the
   07-06 paper round (`{"CBZ": 3000.0}`) and `cache/oracle_upside_dossiers.json`
   still holds the 07-06 paper six (SABR/ACVA/CBZ/FRPT/EYE/NCNO). Neither was
   overwritten at the 07-10 funding, so the live six's typed kills exist only in
   `oracle_journal.jsonl` (authoritative, append-only) and `oracle_upside_ab.json`.
   Stage 5 is run off the journal kills each tend — correct, and it worked tonight
   on two real print tests. **It is NOT patched by hand on purpose:** writing
   dossiers by hand would fabricate a Stage-3 BEAR×3 gate those names never went
   through. The next FULL round must rewrite both files through
   `make_upside_dossier`/`size_upside_book`.
6. **Pre-condition for the next sizing round (execution discipline):** the sleeve's
   six positions all carry `sector: ''`, and `size_upside_book`'s 40% cluster cap
   silently degrades to a per-symbol cap when sector/theme are empty. Sectors
   identified from this session's peer work, to be attached at the next dossier
   build: TPC = engineering & construction; KLIC = semiconductor equipment;
   PAY = payments/fintech software; QTWO = financial-services software (SAME
   cluster as PAY — this is the 36.8% pair the cap must see); ZVRA = pharma
   (rare disease); LXU = nitrogen chemicals/fertilizer.
   **ESCALATED 2026-08-13 — this is now the TOP pre-condition, not the sixth item.**
   The pair is no longer drifting on paper: on 08-13 PAY (+4.39%) and QTWO (+5.85%)
   BOTH breached the 3% trigger on the SAME sector factor, simultaneously, with
   NOTHING filed on either name, against a payments/bank-software median of +4.30%
   (9 of 9 peers up). The cluster reached **37.66%** of equity against a 40% cap it
   cannot enforce because `sector` is empty. The correlation is now MEASURED, not
   assumed. Still not hand-patched: hand-written sectors would fake a Stage-3 input
   these six never went through. The next round attaches sectors THROUGH
   `make_upside_dossier` before `size_upside_book` sees the book.

7. **NEW 2026-08-11 — the equity peak is stamped from INTRADAY marks.** `peak_equity`
   $4,847.95 was set at the 10:18 ET tend on 08-11; the same day's CLOSE was
   $4,812.20, so the book reads as −0.74% in drawdown after a strong session.
   Marking the peak intraday while marking everything else at the close biases every
   subsequent drawdown reading and mildly tightens the 40% breaker against the book.
   **Not patched by hand (fail-safe).** The next FULL round decides: either stamp the
   peak only on close marks, or mark the peak intraday consistently — but pick one.
   **2026-08-13 UPDATE:** the artifact cleared itself — the book made a new high at the
   after-close pass, so `peak_equity` is now **$4,873.63 stamped on a CLOSE-basis mark**
   and the drawdown reads a true 0.00%. That is the side of the dilemma I would choose,
   but it arrived by accident of when Zeus fired, not by design. **The duty is NOT
   discharged** — the basis is still whichever pass happens to set the high.
8. **NEW 2026-08-11 — PAY is making large idiosyncratic moves in BOTH directions with
   nothing filed.** −9.36pp (08-05) and +4.22pp (08-11) against the payments median,
   no EDGAR document either day. The leading non-thesis explanation, typed here
   BEFORE the answer is known, is the 10b5-1 insider distribution (CFO 27,809sh +
   Director 80,000sh executed 08-04/08-05, three Form 144s) starting and then
   exhausting. **It stays a WATCH and stays UNTYPED** — it is not a kill and must not
   become one retroactively. The test that would promote it from guess to mechanism:
   **does the next 144 batch coincide with another drop?** Log every 144/Form 4 with
   its dates so the coincidence can be checked rather than remembered.
   **2026-08-12 observation (the first data the duty produced):** NO new 144 and NO new
   Form 4 on PAY, and the name moved −0.64% — inside the band. One quiet day consistent
   with exhaustion, weight near zero, still NOT evidence. The batch-vs-drop test remains
   unrun because no new batch has arrived.
   **2026-08-13 observation:** still NO new 144 and NO new Form 4 on PAY (last document
   08-06). PAY rose +4.39% — a breach — but the peer median was +4.30% with 9 of 9 up,
   so the move was SECTOR and carries no information about the distribution hypothesis
   in either direction. Two quiet days now; the batch-vs-drop test is STILL unrun
   because no new batch has arrived. Weight unchanged: near zero. WATCH, UNTYPED.
9. **NEW 2026-08-12 — an after-close tend that fires ~6 min after the bell cannot get the
   official close.** At 20:06–20:15Z the SIP close for the session was still unpublished
   (`close.date` lagged one day), so marks had to be the 15:59:5x ET regular-session
   prints. Duty 1b asks for official closes; a 16:06 pass structurally cannot supply them.
   Either accept the last-print basis and SAY SO in the journal (what I did tonight), or
   move the after-close pass later. **Not patched by hand — Zeus owns the dispatch clock,
   not Oracle.** **2026-08-17: recurred exactly as described** (`close.date` still lagged
   to 08-14 at 20:15Z); marks are the 15:59:5x ET prints and the journal says so.
10. **NEW 2026-08-17 — TPC insider/personnel WATCH, typed BEFORE the answer, NOT a kill.**
   Two items in one week on the book's #2 weight (18.94%): (i) **DIRECTOR Sidney J.
   Feltenstein** sold **184,209 sh on 08-07** across four blocks at $95.66–$98.18, going
   **190,909 → 6,700 shares (~96.5% of the stake)**, with **NO 10b5-1 box checked** =
   discretionary (Form 4 acc 0000077543-26-000189, read in full 08-17 — the prior
   sessions' one-line summary had never been opened); (ii) **8-K Item 5.02** (acc
   0000077543-26-000193): **EVP Civil West William E. Jensen** retiring effective
   **09-04**. Different people, so not one event double-counted. Neither touches the
   typed kill (2 consecutive GAAP loss quarters; counter 0 after a record Q2 — $1.6B
   revenue +19% y/y, $65.7M GAAP net income, guidance raised), and both are the ordinary
   shape of a name +28% off entry into record numbers. **The promotion test, written
   before the answer: a THIRD insider disposition, or any 8-K touching Civil West's
   results. A quiet month buries it.** The discomfort is recorded; it does not become a
   retroactive kill — Stage 5 forbids exactly that.
   **Corollary lesson: with 10b5-1 sales, the PLAN-ADOPTION DATE is the information, not
   the size.** QTWO's CFO sold 77,180sh under a plan adopted 2025-09-02 (~11 months
   earlier, retains 2.7× what he sold) and ZVRA's Secretary noticed 42,666sh (0.072% of
   shares out) under a plan adopted 05/15/2026 — both uninformative about current
   knowledge *by construction*. Feltenstein's is the one with no plan behind it, which is
   the whole reason it is the one on watch.
11. **NEW 2026-08-17 — the PAY+QTWO cluster diverged, and that does NOT retire the 08-13
   finding.** QTWO -0.46% vs PAY -2.84% against a common -2.24% median: 2.4pp apart, four
   sessions after moving as one thing. One divergent day is not a refutation of a
   correlation — and more importantly the 08-13 finding was never about a single day. It
   was that the 36–38% pair is **invisible to `size_upside_book` because `sector` is
   `''`**, which is a SIZING defect no price day can cure. Duty 6 stands unchanged as the
   top pre-condition of the next round. Cluster 36.07% today.
## Lessons (compounded — do not relearn these)

-1. **A KILL THAT CANNOT FIRE IS DECORATION — and re-typing it in the session that
   discovers that is cheating (learned 08-05, KLIC's first real test).** I typed
   `revenue < $180M` against the FY25 trough ($148M); the trough never returned and
   the name printed $330M guiding to $375M. The test was *won* and told me almost
   nothing. **Type the kill against the level the thesis would have to fall BACK
   to, and re-check at every print whether it can still fire.** When one goes
   unreachable, re-type it **in the open, in a FULL round, before the next print** —
   never in the tend that found the good news. Moving a kill after the result is
   how a thesis quietly becomes unfalsifiable, which is the one thing this engine
   cannot survive.
-0.5. **Give an idiosyncratic move the same weight down as up (learned 08-05,
   PAY).** The −9.36pp peer-adjusted decline was measured by exactly the machinery
   that produced the flattering +5.84pp on 07-29. Reporting the first and
   discounting the second would make the whole Duty-1b measurement worthless. Log
   the leading non-thesis explanation (here: the 145,000sh / ~$4.99M Form 144 week)
   **before** the answer is known, so the record cannot be reverse-engineered later.

0. **READ THE KILL'S GRAMMAR, then test every clause (learned 07-29, the first
   real kill tests).** LXU's kill was *"quarterly net loss on ammonia price
   collapse"* — a conjunction. The loss was real ($6.2M GAAP, a −$0.55 EPS miss);
   the mechanism was refuted by the issuer's own table (ammonia +89%, gas −15%),
   and the true cause was $28.8M of planned turnaround expense with revenue and
   EBITDA both accelerating. A one-clause reading would have sold the
   fastest-improving name in the book on a maintenance quarter. **Corollary:** a
   kill's qualifier is load-bearing, not decoration — it encodes *why* the thesis
   would be dead, and a loss for a different reason is not that thesis dying.
   **Second corollary:** consensus can "miss" for pure timing reasons (Pryor's
   turnaround was pulled forward from Q3 into Q2); a big miss is a question, not
   an answer.

1. **Single-pass reads are credulous.** The 07-06 book collapsed 6→1 under a
   BEAR pass (one-time gains, price hikes, asset-sale deleveraging taken at face
   value). BEAR×3 with filing-cited defenses is mandatory before fundable.
2. **Hunt LOW in the 52-week range with a recent upturn.** Rounds 1–2 converted
   11% (momentum-biased queue); round 3 converted 40% after rebuilding the queue
   around washed-out names. Every kill high-in-range was "already arrived."
3. **Trailing-6mo momentum surfaces blowoff-and-fade, not early.** Use recent
   trend off a base; penalize near-52wk-high.
4. **The screen's fundamental signals lie without a read** (EPC "margin
   improving" was compressing; WLY "accel" was flat). The read is the edge.
5. **The blowup filter earns its keep** (KPTI going-concern, POET pre-revenue).
6. **The queue is the engine:** the read is only as good as what it's aimed at.
7. **A price move is not information until it is peer-checked** (07-27 → hardened
   07-28). Twice now a move that looked like the thesis arriving or breaking was
   the whole complex moving: PAY's +9.04%/+8.53% was the payments sector, KLIC's
   -7.50% was the semicap sector to within 0.03pp, TPC's -4.33% was a sector it
   beat. The discipline is symmetric and cheap — 3–5 peers, one quote call, take
   the median. Only a divergence from the complex (LXU lagging fertilizer by
   3.3pp on 07-28) is a name-level fact worth a line in the journal.

8. **THE SIGNAL IS THE ASYMMETRY, NOT THE SINGLE-DAY GAP (learned 07-30, and it
   cost me a conclusion I had just written).** A peer check on a down-day only
   asks "does it fall with its complex?" — the easy half, and a name can pass it
   for four straight sessions while still being discounted. KLIC tracked the
   semicap selloff to within 0.7–2.3pp on 07-28/07-29, so I logged the drawdown as
   sector beta and explicitly walked back a name-level worry. On 07-30 the complex
   ripped +14.7% and KLIC took +6.5% — **full participation down, under half up.**
   That is the market discounting the name, and no number of down-day checks would
   have shown it. **Corollary: run the check in both tape directions before
   concluding "it's just the sector," and treat a reversal in the divergence as
   stronger evidence than any single day's gap.** Second corollary: the close is
   the mark that counts — KLIC's lag measured −5.83pp at 10:12 ET and −8.16pp at
   the bell, and TPC flipped from "no divergence" to −4.30pp over the same hours.

9. **A FORM 144 IS INTENT; A FORM 4 IS EXECUTION — dispositioning the first does
   not discharge the second (learned 07-31).** I logged PAY's two Form 144s on
   07-29 as "40k sh, not kill-relevant" and moved on. The Form 4 that landed 07-31
   showed **80,000 shares actually sold for ~$2.7M** — double the figure I was
   carrying. The verdict did not change (the footnote proves a Rule 10b5-1 plan
   established 2026-03-12, i.e. scheduled, not a pre-print exit), but I held a
   wrong number for two days because "already dispositioned" felt like done.
   **A follow-on filing is a NEW primary document, not a receipt for the old one.**
   This is the same shape as lesson 8's LXU conjunction rule: once a clause or a
   disclosure has gone live, every subsequent document reopens it.

10. **Name the drift even when nothing acted on it (07-31).** Excess ran
   +1.49pp (07-29 close) → +0.08pp (07-30) → −0.64pp (07-31): two straight
   sessions giving back ~0.7pp, and the book is now behind SPY since funding. At
   three weeks and six names this is noise and says nothing about the thesis — but
   a session that ends in six "NO EXIT" lines can quietly bury the one number that
   scores the engine. **The verdict metric goes in the worldview every session,
   in the direction it actually moved.**

11. **AN ESTIMATED EVALUATION DATE IS A GUESS UNTIL A CALENDAR VERIFIES IT
    (learned 08-03).** From 07-29 onward I carried ZVRA's kill as "first
    evaluable at the ~08-11 print" — an estimate I inherited from my own
    earlier note and then repeated in four consecutive sessions without ever
    testing it. One `get_earnings_results` call showed the report is 08-05,
    verified, six days earlier; PAY/KLIC/TPC were confirmed the same way, and
    four of six positions turn out to print inside 48 hours. A kill that is
    "not evaluable yet" is the most comfortable answer a tending session can
    give, which is exactly why the date behind it must be sourced, not
    remembered. **Check the earnings calendar for every held name every
    session — it is one cheap call and it sets when the thesis is falsifiable.**
    Corollary: the earnings RELEASE (8-K/EX-99.1) carries the revenue lines a
    print-based kill is typed to, so it — not the later 10-Q — is the first
    evaluable document.

12. **A FORWARD NUMBER IS NOT A REALIZED NUMBER, AND THE GAP IS MEASURABLE
    (learned 08-04).** I nearly carried "PAY's own guide implies my kill" as a
    standing worry. The guide *does* imply it — mid +15.21% Q3, +12.97% Q4,
    +14.06% H2, all at or under the 15% line. But three EX-99.1 guidance tables
    took twenty minutes to pull and showed the company beats its own revenue
    midpoint by +11.0 / +6.8 / +4.6pp, 3-for-3. **When a guide threatens a typed
    kill, calibrate the guide before you believe it** — the question is never "what
    did they say" but "what is the historical distance between what they say and
    what arrives." This is the mirror image of F5: a snapshot is not evidence, and
    a *forecast* is not evidence either. Corollary, and the part with teeth: **track
    the beat size, not just the beat.** The sandbag is compressing monotonically,
    and a shrinking sandbag is the early warning a single beat/miss never shows.

13. **Read the document, not the index (08-04).** EDGAR listed PAY's earnings 8-K
    under Item 2.01, Completion of Acquisition — which on an earnings_accel thesis
    would be a quality-of-growth bomb. The document itself said Item 2.02, and the
    same-day 8-K/A existed solely to fix the clerical tag. **Filer metadata is a
    claim about a filing, not the filing.** The check cost one fetch and the answer
    was "nothing" — which is the correct and common outcome of a discipline, not a
    reason to skip it next time.

## Decayed / de-prioritized

- 6mo-trailing-momentum as a "still early" net — DECAYED (fixed in the cascade
  queue build).
- The 07-06 paper book (SABR/ACVA/CBZ/FRPT/EYE/NCNO dossiers) — SUPERSEDED by
  the 07-10 cascade round; kept in `oracle_upside_dossiers.json` as history
  until the next dossier round overwrites.

## Engine gaps still open (Stage 0–1)

- TOP-DOWN thematic net (needs a forming-themes map) — still off, under-counts.
- Real analyst-coverage data (proxied as thin) and eps_surprise (earnings feed).
- y/y or TTM revenue trajectory (needs the year-ago quarter) to de-noise accel.


## OPERATOR SITUATION NOTE — shared buying-power pool (2026-07-14)

The Robinhood account is ONE cash pool shared by all gods. The sleeves'
`cash` fields collectively overstated real buying power ~5x on 2026-07-14
($1,165 claimed across the four sleeves vs $237 actually available). My own
sleeve claims ~$450 cash; that is a CEILING, not spendable dry powder. NEW
DISCIPLINE (now in my runbook, house-wide): before ANY buy, read the LIVE
broker buying power (get_portfolio -> buying_power / get_accounts) and cap
every order at `shared.guards.spendable_buying_power(broker_bp)` — the
minimum of sleeve cash and the live pool binds. I mostly self-fund anyway
(I only buy on a cohort selection; a kill raises its own cash), so this
rarely bites me, but it is now the floor. The operator sold ~$930 of a
personal holding (VXUS) on 2026-07-14 to back the gods' claimed dry powder;
the pool is larger after tomorrow's fill but still SHARED — if another god
reaches for it the same session, I am capped second.


## Watch item added 2026-08-12 (Zeus tend) — TPC insider exit is NOT a kill

TPC Form 4 filed 2026-08-11 (accession 0000077543-26-000189): director Sidney J. Feltenstein sold
184,209 shares on 08/07/2026 in four weighted-average tranches ($95.66 / $96.26 / $97.50 / $98.18;
ranges $95.01-$98.99; ~$17.8M), leaving **6,700 shares** held directly — roughly 96.5% of his direct
stake, sold near the highs, with the **10b5-1 affirmative-defense box unchecked** and no plan cited in
the footnotes. A discretionary open-market exit by a sitting director is a real fact and I am recording
it, but it is **not** TPC's typed kill ('2 consecutive GAAP loss quarters'), and insider-reversal belongs
to the retired LEGACY cohort model, not the recut upside engine. Stage 5 permits an exit only on a typed
thesis-break; improvising one here is precisely the drift the recut forbids. So: HOLD, and watch whether
this is the leading edge of a broader insider distribution (a second officer/director discretionary sale,
or a 10-Q/8-K that bends the backlog-burn thesis) — that combination, not the sale alone, would be the
fact worth re-underwriting on. TPC is the book's second-largest position (19.7% of equity) and its best
performer alongside PAY (+29.9% vs the $75.96 entry), which is exactly when a thesis deserves the most
scepticism and the least improvisation.

## Lesson 14 added 2026-08-14 (Zeus after-close tend) — a filing CLUSTER can be a deadline artifact

Three ZVRA Schedule 13Gs landed inside three weeks (07-31 Vanguard Capital Management, NEW at
5.11%; 08-06 FMR LLC at 8.3%; 08-14 Woodline Partners at 8.1%). Read as a cluster that is a loud
"institutions are accumulating my worst name during its drawdown" story — and it would have been a
fabricated one. **All three carry the same 06/30/2026 event date, and 06/30 + 45 days = 08/14:** the
amended-13G quarterly amendment deadline. The clustering is the SEC's calendar, not anyone's
conviction. This is the ownership-data sibling of lesson 13 (read the document, not the index):
**before reading a group of filings as a signal, check whether their event dates are the same
regulatory deadline.** Arrival dates cluster on deadlines; only event dates carry information.

Two corollaries with teeth, both of which survived this pass:
- **Direction requires the prior filing.** "8.1%" alone is not a fact about behaviour. Woodline's own
  Amendment No. 1 (event 09/30/2025) said 6.2% / 3,476,143 shares vs 8.1% / 4,785,771 now — a real
  +37.7% accumulation. One extra fetch converted a number into a direction.
- **A 13G position is stale on arrival and may pre-date the position.** Woodline's is stated as of
  06/30/2026, six weeks old and BEFORE my 07-10 entry. It cannot tell me what any holder owns today.
  And a multi-manager platform's long stake is routinely hedged or paired, so it is weaker evidence
  of directional conviction than a long-only holder's. Mildly confirming; never sizeable.

## Watch item 2026-08-14 — KLIC and the front-end/back-end semicap split

KLIC +3.49% on a day the front-end WFE names were all red (AMAT -5.12% on what looks like an
earnings/guide reaction, KLAC -2.69%, ACLS -2.15%, ONTO -1.78%, LRCX -1.36%) while back-end/test/
packaging went green (TER +2.01%, COHU +1.68%). Against the whole semicap tape KLIC looks +5pp
name-specific; against its OWN back-end cohort it is ~+1.6pp off the TER/COHU median — participation,
not content. **The peer set you choose decides whether a move looks idiosyncratic.** Pick the cohort
that matches the business (KLIC is back-end packaging/bonding, not front-end deposition/etch) before
concluding a name moved on its own news. Worth watching whether a genuine front-end/back-end capex
divergence is forming — that would be thesis-relevant for KLIC, which is currently the book's second-
worst name at -9.92%.


## 2026-08-18 (Zeus tend) — KLIC has a permanent CEO, and the front/back-end split did NOT hold

Two updates from one session, both from documents rather than tape.

**KLIC's interim period ended.** 8-K filed 08-17 for an 08-13 event (acc 0000056978-26-000034,
Item 5.02): Dr. Raj Talluri appointed President & CEO effective 2026-09-01, joining the board 08-17;
Lester Wong reverts from interim CEO to EVP & CFO. Package: $750K base, 110% target bonus, $14.0M
one-time new-hire equity (50% RSU / 50% performance). A Form 3 the same day is the mechanical
companion. This is thesis-relevant in the right direction — a permanent operator can commit to a
capex cycle that an interim caretaker cannot, and the size of the performance-equity slug says the
board is buying a multi-year turn, not a stabiliser. The scepticism to keep: Talluri arrives from
Enovix, a mixed operating record. It is **not** the typed kill (quarterly revenue < $180M, a
10-Q test), and I did not treat it as one. **Do not let a leadership headline re-underwrite a
revenue thesis** — record it, size nothing on it, and wait for the print.

**Lesson 15 — a one-session divergence is not a divergence.** On 08-14 I opened a watch item on a
possible front-end/back-end semicap capex split (KLIC +3.49% while AMAT/KLAC/LRCX were all red).
Today the whole complex moved as ONE thing: back-end median -7.58% (FORM -9.11, AEIS -8.72,
ONTO -8.18, TER -8.04, UCTT -7.11, ACLS -6.63, COHU -6.53, ASYS +0.71) with front-end in step
(AMAT -5.67, LRCX -6.57, KLAC -4.05), and KLIC -7.71% landing -0.14pp off its own cohort's median.
The divergence is **retired as a one-session artifact.** The general form, which is the part worth
keeping: *a cross-sectional split observed on a single day is a sample of one and carries no
information about a capex cycle.* I gave it a watch item rather than a conclusion, which was right;
the discipline now is to close it promptly rather than let it linger as a half-belief. Corollary to
lesson 14's shape — check whether the thing you are reading as a signal survives a second
observation before it earns any weight at all.

**The peer check keeps paying.** Fourth time in seven sessions that it has SUBTRACTED a story.
Today it did the work twice: KLIC's -7.71% (which reads as a fright) is the sector median, and
TPC's -2.02% (which reads as weakness) is actually +0.34pp BETTER than its E&C peer median
(STRL -5.21, MTZ -3.01, GVA -2.39, FLR -2.37, PWR -2.34, DY -1.98, J +0.32, ACM +0.43). Two names
that both looked like news were both complex moves. Keep running it on the big weights.

**PAY/QTWO: the second counter-observation.** QTWO +0.93% vs PAY -0.30% today, 1.23pp apart,
after 2.4pp apart on 08-17. Two consecutive sessions now sit against the measured correlation that
motivated the 40%-cluster-cap concern. Still not enough to overturn a measured relationship, but the
count is no longer one and I am tracking it deliberately rather than noticing it twice by accident.

**Open item for the operator, not for me to improvise.** The `research` cadence key last stamped
2026-07-14 — 35 days stale. Stage 0-1 is a full-field cascade over ~3,150 names, not something an
hourly dispatcher pass should start and half-finish; a partially-read field would produce exactly
the credulous book the recut exists to prevent. Flagged, not improvised. The live book is tended
daily regardless; sourcing is the piece that is waiting.
