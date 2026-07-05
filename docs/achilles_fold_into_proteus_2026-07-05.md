# Achilles folded into Proteus as a seasonal mode (2026-07-05, operator directive)

## The decision

Achilles is **retired as a standalone god.** His PEAD (Post-Earnings Announcement
Drift) strategy becomes a **seasonal *mode* inside Proteus** — during the four
earnings windows Proteus may run the diversified beat-basket as one of his plays,
on his own live sleeve. No dedicated Achilles sleeve, no idle capital.

## Why (two strikes)

1. **Capital-inefficient by construction.** Achilles trades only ~16 weeks/year
   (four ~6-week earnings windows) and sits in cash the other ~36. A dedicated
   sleeve is idle ~70% of the year — pure opportunity cost for a return-seeking
   book. A specialist that only acts when its edge is present is fine *if* the
   in-season edge is strong; here it isn't.
2. **The long edge he actually trades measured absent.** The reaction-gate replay
   (2026-07-03, RESEARCH_LEDGER) found rewarded beats show **no 5-day drift**
   (small/mid −0.9%); the only real signal was the SHORT side (sold beats keep
   falling, t −2.3) — which a long-only book can't trade. So Achilles was a
   capital-inefficient sleeve wrapped around an unproven long thesis.

An idle-70%-of-the-year sleeve around a measured-weak edge does not deserve a
standalone god. Folding PEAD into a full-time discretionary god removes the idle
capital *and* keeps the option of harvesting the drift if it proves real.

## What changes

- **Achilles the god is retired.** `/achilles` becomes wind-down/library-only;
  `ACHILLES_LIVE=false`. His ~$2,000 sleeve is wound to cash and **returned to
  the treasury**, available for the pending portfolio allocation (not force-swept
  to any one god — the allocation decides).
- **The `achilles/` package is KEPT as a library** (the Buzz/Catalyst precedent —
  "package kept as the mechanical layer"). Proteus imports `achilles.scanner`,
  `achilles.scoring`, `achilles.season`, `achilles.earnings` for his seasonal
  PEAD mode. The reaction-magnitude guard (`MAX_REACTION_PCT`) and the sold-beat
  ban travel with it.
- **Proteus gains a seasonal PEAD mode.** During the earnings windows
  (`achilles.season`) he may run the beat-basket as one discretionary play, with
  the honest caveat that the long drift is unproven, journaled and graded like
  every Proteus decision. Not an autopilot — a tool in his kit.

## The gauntlet still runs — now in service of Proteus

`achilles_pead_gauntlet` (preregistered 2026-07-05, before data) still runs. Its
job is no longer "should Achilles stay live" but **"should Proteus bother running
the PEAD basket in-season, and in what universe/parameters."** The **MICRO band
(exchange-listed marketcap rank ~2001–3500) is a first-class thing to test, not a
caveat** — those names are tradable and fully visible in Sharadar SEP (the data
hole is the OTC/pink tier *below* the exchange line, which Robinhood mostly can't
trade anyway). The real micro-cap caveat is cost/spread at size, which the
2×-cost gate stresses. A SUPPORTED cell tells Proteus the mode is worth using; a
REFUTED verdict means PEAD stays dormant and the sold-beat ban is all that
survives.

## What does NOT change

- No PEAD backtest may be cited as evidence FOR the strategy except a SUPPORTED,
  forward-confirmed `achilles_pead_gauntlet` cell (the Delphi rule).
- `/achilles-ghost` may keep shadowing for the record if useful; it places no
  live orders.
