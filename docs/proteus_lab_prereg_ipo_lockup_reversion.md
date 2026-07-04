# Proteus Lab — Prereg: IPO Lockup-Expiration Reversion

**Slug:** `ipo_lockup_reversion`
**Date:** 2026-07-04
**Status at registration:** hypothesis → preregistered (this doc)

Committed BEFORE any price bar, IPO list, or NAV/discount datum is pulled.
Git history on this file is the timestamp that proves "before."

## Hypothesis (recorded verbatim in `cache/proteus_lab.json`)

Standard ~180-day IPO lockups create a calendar-certain, information-free
supply shock at expiry (float mechanically increases; no news). Momentum
shorts and lockup-cliff narrative traders pile onto the anticipated
overhang and depress price into/just after expiry; once the shock is
absorbed (1-2 weeks), price should partially revert toward its pre-shock
trend. This is differentiated from the well-known mega-cap version of
this trade (which session `/proteus` 2026-07-04 already rejected on
EQPT and SPCX as fully priced-in and over-published) by restricting to
**small-cap, low-coverage IPOs**, where the calendar-certain lockup date
is public and EDGAR-documented but essentially uncovered by systematic
research or media.

## Population definition (complete catalog, defined BEFORE results)

All US primary equity IPOs (common stock, standard underwritten IPO;
**excludes** SPACs, closed-end funds, ADRs, uplistings from OTC, and
direct listings) that priced in **calendar year 2023** (2023-01-01
through 2023-12-31), with **total offer size < $300M** (small-cap —
the "low coverage" side of the population), sourced from a **complete**
public IPO calendar for that year (e.g. stockanalysis.com/ipos or
iposcoop.com's full-year listing), not a hand-picked subset. 2023 is
chosen so that entry (T+185 trading days) and the full 60-trading-day
hold complete well before today (2026-07-04), with no partial/pending
events, and so the sample sits in a specific, nameable regime (2024
disinflation/soft-landing rally) that will be disclosed, not hidden.

Every IPO meeting the filters that priced in the window is IN the
population, including any that were later delisted, acquired, or went
to near-zero — a delisted/failed name is a real historical outcome and
must not be silently dropped for lack of continued price data.

## Metric and horizon

For each qualifying IPO: enter long at the close **185 trading days**
after the IPO's first trading day (5 sessions past the standard 180
calendar-day lockup, converted to trading days as the nearest whole
number ~127 trading days is NOT used — 185 trading days is used as a
fixed, non-tuned buffer past the ~180 calendar-day mark regardless of
weekends/holidays, chosen before seeing any data). Hold exactly **60
trading days**, then exit at the close. Metric: `holding-period simple
return − SPY's simple return over the identical calendar dates`
("excess return"). No stop-loss, no discretion, no re-entry — a pure
mechanical test of the calendar rule itself.

## Success criteria (thresholds fixed now, not after seeing results)

- **n >= 30** independent IPO events (population size, not cherry-picked).
- **Supported**: mean excess return > 0 with t >= 1.5, AND the effect is
  not concentrated in a single name or single month of 2023 (no more
  than 40% of total excess from any one event).
- **Refuted**: mean excess <= 0, or positive but t < 1.0.
- **Inconclusive**: everything between (0 <= t < 1.5 with mean > 0, or
  n < 30 reachable from the complete 2023 small-cap IPO population).

## Planned bias handling (addressed again, with real numbers, at
record_backtest time — this is the plan, not the final answer)

- **Survivorship**: population is the complete 2023 filing list, not
  survivors; delisted names are included with their actual last-traded
  outcome (or -100% if delisting reason is bankruptcy/liquidation and
  no rescue price exists) rather than dropped for missing data.
- **Look-ahead**: only facts knowable at T+185 are used (the lockup
  term is stated in the S-1/424B4 at IPO, i.e. before T+0); the 60-day
  forward window is realized return, used only as the outcome, never
  as a filter on which names to include.
- **Selection**: population fixed by (year, offer-size, IPO-type)
  filters applied to a complete external calendar BEFORE any price
  data is pulled — no name is added or dropped because it "looks like
  a good example."
- **Multiple testing**: this is hypothesis #1 in `hypotheses_ever` (see
  `cache/proteus_lab.json`) — first cut, no prior variants tried on
  this data.
- **Overfitting**: two knobs total (185-trading-day entry offset,
  60-trading-day hold), both fixed by the mechanism (lockup length +
  a round-number hold) before any data was seen, not tuned against the
  2023 sample.
- **Costs/liquidity**: small-cap post-IPO names can be thin six months
  out; average daily dollar volume in the 20 sessions before entry
  will be recorded per name, and any name below a executable-size floor
  will be flagged (not silently included as if costless) when the
  backtest is written up.
- **Regime**: single calendar year (2023 IPO class, 2024 hold window) —
  one regime only. The write-up will state plainly that this does not
  yet test across a rate-cutting cycle, a risk-off regime, or a hot-IPO
  year, and that generalization beyond 2024's soft-landing regime is
  unproven until repeated on a fresh year with its own prereg.
- **Small-n**: raw n and the Bayesian-shrunk mean (prior_n=20,
  prior_mean=0, per `oracle.learning.bayesian_shrunk_skill`) will both
  be reported; forward-test promotion (if backtest is `supported`)
  requires >= 20 graded paper trades before the shrunk mean is trusted
  for `validated`.

## What would kill this idea outright

Mean excess <= 0 across the complete population, or a result that only
survives because 1-2 explosive names carry the whole spread (the same
failure mode that hit Nemesis's spinoff ocean and Midas's convergence
test — a real effect must show up broadly, not in a lottery ticket or
two).
