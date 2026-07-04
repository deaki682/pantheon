# Prereg — `quiet_cluster_ghost` (backlog #1)

- **Slug:** `quiet_cluster_ghost`
- **Sponsor:** operator (backlog #1, filed 2026-07-04)
- **Date:** 2026-07-04 — committed BEFORE any Form 4 in the fresh window
  below is fetched. The only prior touch of insider-cluster data is the
  now-SPENT 2025-01-01..2026-05-31 replay
  (`docs/oracle_prereg_cluster_replay.md`,
  `docs/oracle_replay_results_2026-07.md`, REFUTED at 12mo: n=291,
  −6.38%, t −1.06) — that population and its outcomes may not be reused
  for this test; the "quiet" filter is only honest against data the
  original refutation never touched.

## Question

The spent replay graded the FULL cluster population and refuted it as an
auto-buy. It did not test whether a subset — clusters nobody else was
reacting to at the moment of filing — behaves differently. Mechanically:
**do insider clusters with no contemporaneous 8-K and no abnormal
price/volume reaction at the knowability date ("quiet" clusters)
outperform the −6.4%/yr the full population measured at 12 months?**
This is Oracle's own intuition (informed buying is most informative
when nobody else has reacted yet) stated as a falsifiable, mechanical
filter rather than a vibe.

## Population (FROZEN, fresh window only)

Identical cluster mechanics to the spent replay (reusing validated,
already-QA'd infrastructure — `shared/insiders.py` — is not a data peek;
only the OUTCOMES were off-limits, and none exist yet for this window):

- **Source**: EDGAR daily form indexes, every Form 4 filed
  **2026-06-01 onward** (the day after the spent replay's window closes;
  zero overlap by construction — verified by date, not by re-checking
  results).
- **Cluster event**: ≥2 distinct insiders each making open-market
  purchases (code P, positive shares/price) ≥ $10,000 each, all within a
  60-calendar-day window, aggregate ≥ $50,000. Grant-mill exclusion:
  issuers with >60 Form 4 filings in the trailing 12 months excluded.
  Candidacy pre-filter: an issuer is fetched only if ≥2 distinct
  reporting owners filed within 14 days of each other at least once —
  same tight-cluster trade-off disclosed in the original prereg.
- **Event dating**: knowability date = max(transaction date, filing
  date) of the buy that completes the cluster — identical look-ahead
  guard as the original (delinquent Form 4s can be filed up to two years
  late; grading from transaction date would credit information nobody
  had).
- **Rolling, forward-built population**: because the window starts
  today, this population does not exist yet — it accrues as real filings
  land. This is a genuine forward construction, not a lookback with a
  fresh cutoff date bolted on. Each qualifying event is added to the
  catalog on the day it is first observed; no event is added or removed
  retroactively based on how it later performed.

## The "quiet" filter (FROZEN, mechanical proxies only)

An event is "quiet" iff **all three** hold at its knowability date (kd):

1. **No news filed**: zero 8-K filings (any item number) by the issuer's
   CIK in the window [kd − 3 trading days, kd + 3 trading days]. This is
   a filing-based proxy for "nothing newsworthy happened," the same
   class of mechanical proxy the house already uses for guidance/earnings
   channels (CLAUDE.md's Midas signal table) — not a claim that zero news
   ever existed anywhere, only that no SEC-disclosable event coincided.
2. **No abnormal price reaction**: |raw daily return| < 2% on kd AND on
   the next trading day. Both must hold — a delayed one-day-lagged pop
   would still count as "the market reacted," just slowly.
3. **No volume anomaly**: day-of-kd volume < 1.5× the trailing 21-day
   median volume. 1.5× is not a new number invented for this study — it
   is the exact threshold CLAUDE.md's existing volume-anomaly channel
   already treats as "fires," reused here rather than picked freely.

Events failing any one of the three are "loud" and are tracked as the
comparison arm (not discarded — both arms report).

## Grading (FROZEN, identical to the spent replay for comparability)

- **Entry price**: first daily close on or after knowability date + 5
  calendar days.
- **Horizons**: +126 trading days (~6mo) and +252 trading days (~12mo),
  graded only once each horizon has elapsed for a given event.
- **Benchmark**: IWM total return over the identical calendar window;
  excess = stock return − IWM return.
- **Unpriceable at horizon** (delisted/acquired/renamed): bucketed and
  reported by name, not auto-scored — same rule as the original.

## What would count as validation / refutation

Primary metric is the **12-month excess of the quiet-cluster arm**,
directly comparable to the spent replay's −6.4%/yr headline:

- **Validated**: quiet-cluster mean 12-month excess > 0 with t ≥ 2 on
  event-level returns, n ≥ 30 quiet events graded.
- **Refuted**: mean excess ≤ 0, or t < 2 with n ≥ 30.
- **Inconclusive**: n < 30 at any check-in — reported as still
  accruing, no early verdict, no peeking used to extend or shrink the
  window.

n≥30 (not the original's n≥150) because this population accrues in real
time from a single forward-moving month rather than a 17-month
retrospective sweep — a floor consistent with this house's other
small-n forward tests (e.g. `ipo_lockup_reversion`'s n≥30 floor). Getting
to n≥30 quiet events, each needing a 12-month hold to grade, will take
well over a year of real time; interim 6-month readings are reported
alongside as directional context, never substituted for the frozen
12-month bar.

## A known process gap this prereg surfaces

`shared.lab`'s registry (`new_strategy` → `preregister` →
`record_backtest` → `start_forward_test`) hard-requires a `backtested`
(`verdict="supported"`) status before any forward paper entry is allowed
into the registry's own forward-tracking (`start_forward_test`,
`record_forward_grade`). This hypothesis has **no possible backtest** —
that is the entire point of using fresh, unspent data — so it cannot
pass through `record_backtest` honestly (there is no dataset to backtest
against without either reusing the spent replay, which this prereg
explicitly refuses, or waiting for the forward window to accrue, at
which point it is a forward test, not a backtest). Filing this as a
`new_strategy` + `preregister` pair is safe (those two steps require no
outcome data and correctly bump `hypotheses_ever`), but the registry
cannot currently carry it any further without either (a) a
`shared.lab` change adding a legitimate no-backtest-possible path
straight from `preregistered` to a forward-tracking state, or (b) running
this as a measurement study outside the registry (per the `/lab`
liturgy's alternate path) with paper entries tracked directly via
`shared.ghost` under this slug, and a ledger row on conclusion. Flagged
here rather than forced through a fabricated backtest step — this
prereg recommends option (b) until the operator decides whether (a) is
worth building.

## What this is NOT

- Not a change to Oracle's live cohort rules or research process.
- Not a re-analysis of the spent 934-event / 291-graded-at-12mo dataset
  — that population is retired for this question, full stop.
- Not a backtest wearing a forward-test's clothes — zero outcome data
  existed for this population at the time this document was committed.
