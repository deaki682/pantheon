# Pre-registration: Pantheon correlated-drawdown study

Committed 2026-07-03 (late night), before any stress numbers exist.

## Question

Five sleeves — Oracle (8 small/mid names), Delphi (10 large-cap
momentum), Achilles (≤12 small/mid, seasonal), Midas (1 name, all-in),
Nemesis (≤5 spincos) — are ALL long US equities with heavy small/mid
tilt. Each has a per-god 40% halt; NOTHING watches the combined book.
When the correlated month arrives (all five ponds sell off together),
what does the combined $10K book plausibly lose, and what
portfolio-level breaker should exist BEFORE it happens?

## What this is

Risk research producing a stress estimate and a PROPOSED breaker rule.
Adding a portfolio breaker is a risk-REDUCING rule addition — it still
requires explicit operator approval before implementation; this study
only earns the right to propose it. It is NOT a backtest of god skill
and produces no alpha claims.

## Method (FROZEN)

1. **Benchmark history**: IWM and SPY weekly closes 2000→present, MTUM
   from inception — broker bars. Identify every episode where IWM fell
   ≥ 20% peak-to-trough; record depth and length. (2008, 2011, 2015-16,
   2018, 2020, 2022, spring-2025 expected.)
2. **Per-god market sensitivity**, from reference classes already
   measured on disk (disclosed proxies, event-level regression of event
   return on matched-window benchmark return):
   - Nemesis β vs SPY: 48 bear-vintage + study-1 ocean events.
   - Oracle β vs IWM: 6-month cluster-replay events.
   - Achilles β vs IWM: 293 graded 5-day reaction events.
   - Midas: proxied by the cluster replay's 5-day slice (1-week
     small/mid single-name exposure) — weakest proxy, disclosed.
   - Delphi: β vs MTUM assumed 1.0 (she IS a momentum book), MTUM
     episode moves mapped from its overlap with IWM episodes.
3. **Stress construction**: for each historical episode, combined loss
   = mean over gods of (β_g × episode benchmark move + idio_g), with
   idiosyncratic draws Monte Carlo'd (10,000 paths) from each reference
   class's residual dispersion and each god's true position count
   (Midas n=1 — idio does NOT diversify). Cash states (Achilles
   off-season ~60% of the year) modeled as a scenario toggle.
4. **Breaker candidates** (pre-stated, evaluated on the same paths):
   - A: HALT new entries across all gods at combined −25% from
     combined peak; exits/stops keep running.
   - B: A plus liquidate-to-50%-cash at combined −35%.
   - C: status quo (per-god 40% halts only).
5. **Decision criterion (FROZEN)**: recommend the least-intrusive
   candidate for which P(combined drawdown exceeds 50%) < 10% across
   the Monte Carlo paths of the WORST historical episode, subject to a
   false-trigger budget: the breaker would have fired in < 5% of
   rolling 12-month non-crisis windows since 2000. If C already
   satisfies both, recommend no new rule.

## Output

One doc: episode table, β table with dispersion, stress distribution
per episode, breaker evaluation, and a single recommendation for
operator sign-off. No rule is implemented by this study itself.
