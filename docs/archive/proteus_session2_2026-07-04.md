# Archive: Proteus session 2 (2026-07-04) — second operator memory reset

Archived 2026-07-04 on operator directive (second reset; the first is
docs/archive/proteus_session1_2026-07-04.md). Session 2 made NO trades
and the book was flat $10,000, so grading, the checkpoint clock, and
all frozen prereg criteria are unaffected. State files below verbatim.

## Book at reset

```json
{
 "cash": 10000.0,
 "positions": {},
 "closed": []
}
```

## Curve at reset

```json
[
 {
  "date": "2026-07-04",
  "equity": 10000.0,
  "spy": 744.8
 }
]
```

## Journal (verbatim)

```
{"action": "note", "date": "2026-07-04", "text": "Session 2 (first session after operator memory reset; session 1 archived docs/archive/proteus_session1_2026-07-04.md for single-stock fixation, no trades existed, book was flat $10,000, checkpoint clock unaffected). Read prereg, RESEARCH_LEDGER standing findings, and the journal engine fresh before touching anything. Breadth-before-depth sweep (new runbook guard): checked Nemesis's 22-name spinoff pipeline (3 in_window: VGNT, OCTV, RNA - all already status=entered by Nemesis, redundant with a better-tested process, skipped), Oracle's 26-symbol activist-13D scan and 3 insider-cluster lists (table-stakes triggers per standing findings, not theses alone), Midas's top-10 convergence dossiers (DAKT/HELP/APOG - same table-stakes problem), then went to the open web for what's actually moving: (1) a real 'Parabolic 7' basket unwind (SanDisk/Marvell/Micron/Intel/Dell/AMD/Broadcom) driven by S.Korea chip rout + AI-capex valuation fear + an OpenAI IPO-delay report, MU down ~5.5% Jul 2 to $975.77 after a prior -6% day - but this is front-page CNBC/Yahoo news already, no name-specific mispricing identified beyond 'sector is down', which is not a thesis per standing finding #1 (I have no forced-flow or leverage-unwind mechanics confirmed, only a valuation narrative everyone already has); (2) the 2026 Russell semiannual reconstitution - implementation was Jun 26, over a week stale, no fresh forced-flow edge left; (3) IPO lockup calendar - EQPT (EquipmentShare) lockup expires Jul 22, ~18 days out, which is the same name Oracle's 13D scan also surfaced independently (founder co-CEOs Jabbok Schlacks/William Schlacks IV, 81% voting control via a Jan 2026 voting agreement, 13D filed Jun 23 after OPEN-MARKET PURCHASES Jun 15, stock down ~41% from IPO high to $19.185 last trade Jul 2, bid still shows a stale $15 outlier vs ask $19.80). Two vectors converging on the same name is interesting, not sufficient: I still don't know from a primary source which holders are actually subject to the Jul 22 release (founders' super-voting shares vs VC/employee common - Insight Partners holds 13.5M shares/6.3% via a 13G, passive-flavored but lockup-eligible) or the prospectus's exact lockup terms, so I cannot write a falsifiable prediction on lockup-driven supply, and I cannot separate that from the founder buyout-optionality bull case without reading the actual 13D exhibit and the S-1 lockup section - the same gap session 1 left open. (4) CEF discounts: Liberty All-Star Equity (USA) near 8.3%, a 5-year wide, and Calamos Strategic Total Return in double digits - noted for the watchlist, no dislocation urgent enough today to research deeper given time already spent. Also: today is a market holiday (NYSE/Nasdaq closed Jul 3 observed + weekend, reopens Mon Jul 6), so all quotes here are Thursday Jul 2's last prints, not live action - a real reason for extra patience, not urgency, on top of an unfinished diligence gap. Decision: NO TRADE. Forcing a trade into a stale holiday tape to satisfy the daily mandate would be exactly the conviction-theater the mandate explicitly warns against - a green day of $0.00 beats a red day of manufactured activity. EQPT is the one lead worth a deepening pass next session: read the actual Schedule 13D exhibit and S-1/424B4 lockup provision for share-count specifics before Jul 22. Full reasoning and next steps written to ghost_proteus_beliefs.md for whichever instance runs next."}
```

## Beliefs file (verbatim)

# Proteus — beliefs (session 2, 2026-07-04)

## Who I am, and what happened before me

I am the discretionary ghost: full strategy freedom, $10,000 paper,
graded without mercy at 30 closed trades or 2027-01-15
(docs/proteus_prereg.md). Session 1 (earlier today) was reset by the
operator for single-stock fixation — repeated same-day deepening on
one ticker (EQPT) instead of a broad sweep. No trades existed, the
book was flat $10,000, so the reset cost nothing but the lesson. That
session is archived at `docs/archive/proteus_session1_2026-07-04.md`
if I ever want the raw detail, but I do NOT get to treat it as my own
memory — this file and the journal are my only real inheritance now.
A breadth-before-depth guard was added to my runbook because of it:
every session starts with a fresh whole-market sweep before any name
gets a second look, and yesterday's watchlist earns at most ONE
deepening pass, after the sweep, not instead of it.

## What the house has already proven, so I don't re-litigate it

From `docs/RESEARCH_LEDGER.md`:

- Every mechanical BUY trigger tested measures ~zero-to-negative alone:
  insider clusters (-6.4%/yr vs IWM, n=291, win 32%), earnings-guidance
  raises (inconclusive, channel too thin), signal convergence
  (REFUTED, -0.87% spread even after fixing a double-count bug). These
  are table stakes, not theses. "Insiders bought" / "beat + reaction" /
  "signals converged" alone is not a thesis I'm allowed to write.
- Spinoffs are regime-dependent (+41% warm vintage 2025-26 vs -1.0%/
  event 2021-24 cohort) and lottery-shaped (32-50% win rates
  everywhere measured). Nemesis already runs the disciplined
  spinoff-veto strategy; I need a reason Nemesis's own frozen rules
  don't capture, or I'm a worse copy of a better-tested process.
- Continuous scores near a threshold are dice (40-80% flip rate);
  enumerated binary gates are rock-stable (0/50 flips). Frame
  decisions as binary disaster-checks against named criteria, not
  "conviction 0.63 vs 0.65."
- All five gods are high-beta long equity (β 1.0-1.4). My
  differentiated value is more likely on the short side, in
  structurally forced trades, or in idiosyncratic event-driven names
  the long-only gods can't touch.

## Session 2: the sweep, and why I did NOT trade

Checked every shared cache before going outside: Nemesis's pipeline
(3 in_window names — VGNT, OCTV, RNA — all already `status: entered`
by Nemesis, so trading them adds nothing), Oracle's activist-13D list
(26 symbols) and insider clusters (table-stakes, not theses alone),
Midas's top-10 convergence dossiers (DAKT/HELP/APOG — same problem).
None of these clear my bar standalone.

Went to the open web for what's actually happening today:

1. **Chip-sector "Parabolic 7" unwind** (SanDisk/Marvell/Micron/Intel/
   Dell/AMD/Broadcom) — S.Korea rout (SK Hynix -14%, Samsung -9%) +
   AI-capex valuation fear + an OpenAI IPO-delay report. MU down ~5.5%
   Jul 2 to $975.77 after a prior -6% day. Real move, but it's
   front-page CNBC/Yahoo news already — I have no name-specific
   mispricing or confirmed forced-flow/leverage-unwind mechanic, only
   a valuation narrative everyone already has. "Sector is down" is not
   a thesis (standing finding #1). Watching for evidence this is
   specifically a margin/leverage liquidation (real forced flow) vs.
   discretionary repricing — that distinction is the whole thesis if
   I ever trade this basket.
2. **Russell reconstitution** — implementation was Jun 26, over a week
   stale by the time I looked. No fresh edge left; SPCX's ~$22-27B
   mechanical inflow already happened.
3. **EQPT (EquipmentShare) lockup, Jul 22** — surfaced independently
   through TWO channels this session (Oracle's 13D scan AND the IPO
   lockup calendar), which is more interesting than either alone, but
   still not enough to trade. Facts in hand: co-CEOs Jabbok Schlacks /
   William Schlacks IV hold 81% voting control via a Jan 2026 voting
   agreement; 13D filed Jun 23 following OPEN-MARKET PURCHASES Jun 15
   (they were buying, not just consolidating); stock down ~41% from
   IPO high to $19.185 (last trade Jul 2); bid still shows a stale $15
   outlier vs ask $19.80 — don't get faked out by that print again.
   Insight Partners holds 13.5M shares (6.3%) via a 13G — passive-
   flavored but still lockup-eligible.
   **What's missing, and it's the whole ballgame:** I have not read
   the actual Schedule 13D exhibit or the S-1/424B4 lockup section, so
   I don't know (a) which holders are actually released Jul 22 —
   founders' super-voting shares vs. VC/employee common — or (b)
   whether any early-release waiver already happened (common in 2026
   IPOs). Without that I cannot tell a lockup-driven SHORT thesis
   (forced non-founder supply into/after Jul 22, adding to the
   existing downtrend) apart from a founder-buyout LONG thesis (control
   holders who just bought more, with stated take-private optionality,
   at a 41%-off price) — they could both be true at once (near-term
   supply pressure, longer-term buyout premium) and the right trade
   depends entirely on the mechanics I haven't read yet. This is the
   exact gap session 1 also left open; I don't get to just re-guess it.
4. **CEF discounts** — Liberty All-Star Equity (USA) near 8.3%, a
   5-year wide; Calamos Strategic Total Return in double digits. Noted,
   not researched — no urgency signal today, just a shelf item.

**Today is also a market holiday** (NYSE/Nasdaq closed Jul 3 observed
+ weekend, reopens Mon Jul 6) — every quote above is Thursday Jul 2's
last print, not live action. That's a second, independent reason for
patience: forcing a trade into a stale holiday tape to hit a daily
quota would be the conviction-theater the green-book mandate exists to
prevent. A green day of $0.00 (flat, no position, nothing forced) beats
a red day of manufactured activity.

**Decision: no trade, session 2.** Journaled as a `note`.

## Watchlist (trigger conditions for next session)

| Name | Trigger | What I need before acting |
|---|---|---|
| EQPT | Lockup expires Jul 22, 2026 (~18 days out at time of writing) | Read the actual Schedule 13D exhibit (sec.gov/Archives/edgar/data/0001693736/...) and the S-1/424B4 lockup section for: which holders release Jul 22, whether any early-release waiver already happened, exact share count vs. 214.8M Class A shares out. THEN decide long (founder-buyout/control thesis) vs. short (lockup-supply thesis) vs. both being true on different horizons vs. pass. Do this as session 3's ONE deepening pass, not an obsession — if the filings don't resolve it cleanly in one sitting, note what's still unclear and move on, don't repeat session 1's mistake. |
| Chip "Parabolic 7" unwind (MU/MRVL/SNDK/INTC/DELL/AMD/AVGO) | Any specific report of margin calls / forced fund liquidation / a name diverging hard from the basket on idiosyncratic news | Need a forced-flow or leverage mechanic, not just "valuation fear" — that's already fully public and priced by everyone reading the same news. |
| CEF discounts (USA, Calamos Strategic Total Return) | Discount widens further or a catalyst (rights offering, activist push, distribution policy change) appears | Not researched yet — shelf item only. |

## Lessons log (empty — no graded trades yet)

Nothing to grieve or credit yet. First entry here should be after the
first CLOSED trade, whatever the outcome.

## Standing self-reminders

- A profitable trade with a failed prediction is LUCK, not skill.
- If my thesis is "insiders bought" / "beat + reaction" / "signals
  converged" and nothing else, I have not written a thesis.
- Breadth before depth, every session, no exceptions — the sweep
  happens even when a name from a prior session is screaming for
  attention. One deepening pass, after the sweep, not instead of it.
- I am a fresh instance every session. This file, the journal, and the
  research ledger are the entire inheritance. Read them before doing
  anything else.

