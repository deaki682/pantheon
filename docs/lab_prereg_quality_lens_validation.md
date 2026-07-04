# Prereg — quality-lens validation (backlog #2)

- **Type:** measurement study (no tradable claim) — per the `/lab`
  liturgy's own example ("does quality predict anything?"), this skips
  `shared.lab`'s registry (no `new_strategy`/`preregister` call, no
  `hypotheses_ever` increment from this study) but carries the SAME
  discipline: prereg before data, results doc, ledger row, win or lose.
- **Sponsor:** operator (backlog #2, filed 2026-07-04)
- **Date:** 2026-07-04 — committed BEFORE any forward return for this
  population exists. The population's INPUTS (quality scores) already
  exist (see below, disclosed) — what's fresh is the return data, which
  cannot exist yet for a forward-only window starting today.
- **House context at commit time:** `hypotheses_ever` = 98 (registry
  count; this study doesn't add to it, per the measurement-study
  exception above, but the number is recorded here for anyone reading
  this prereg later as a snapshot of house-wide multiple-testing scale).

## Question

Oracle's mechanical "quality" lens (`oracle.screener.quality_score`,
built from `shared.quality`'s gross/operating/FCF margin, revenue
growth, and dilution component scores on trailing XBRL fundamentals)
carries a 15% weight in her insider-gated composite score
(`oracle.screener.multi_lens_score`) and is one of the four lenses her
convergence thesis rests on (CLAUDE.md). It has never been validated
against FORWARD returns on its own — only ever used as an input.
**Does the quality score, on its own, predict cross-sectional forward
returns within Oracle's actual candidate pool (insider-backed,
market-cap-filtered small/mid names)?** The decision this buys: whether
quality stays in the cohort-2 selection stack (~11-12 months away) or
gets dropped/re-weighted before that selection happens — hence the
urgency of pre-registering NOW, well before cohort-2, rather than
letting the question go unanswered until the selection is imminent and
schedule pressure forces an un-preregistered call.

## Population (FROZEN, one-shot cross-section — NOT a rolling accrual)

- **Source:** `cache/oracle_screen.json`, the quarterly heavy screen's
  output, screened 2026-06-28 (six days before this prereg; the
  screen's own fundamentals are the frozen input, disclosed as a
  judgment call below, not re-run or touched by this study).
- **Exact list:** all 100 rows currently in that file (`metadata`:
  `total_universe` 10,434 filers → `insider_backed` 210 (passed the
  insider/smart-money/activist gate) → `after_mcap_filter` 100, Oracle's
  actual small/mid pond ceiling of $20B). This is a COMPLETE,
  already-committed population — no cherry-picking, no re-run. 100
  unique symbols, verified no duplicates.
- **Signal:** the `lenses.quality` field verbatim from that file for
  each symbol — `oracle.screener.quality_score()`'s output at screen
  time, 0..1, mean of up to 5 present components
  (`shared.quality.MIN_QUALITY_COMPONENTS = 3` floor). NOT
  recomputed, NOT re-derived from fresh fundamentals — the exact value
  Oracle's own pipeline produced, so this tests the SAME number she'd
  actually use, not a idealized re-implementation.
- **Known population characteristic, disclosed not corrected:** 18/100
  rows carry `quality == 0.0` exactly. `mean_of_present` returns 0.0 for
  BOTH "genuinely zero score" and "zero components present" — the
  frozen field cannot distinguish these, and this study does not
  attempt to (doing so would mean touching/recomputing the signal,
  which is off the table for a frozen population). These rows are
  disclosed, not excluded; they will fall predominantly in the "low"
  tercile as-is, a known dilution the results doc will name explicitly.
  One row (HLNE) has no `market_cap` field — disclosed, not excluded
  (market cap is not part of the graded signal here).
- **This is intentionally a ONE-SHOT snapshot, not a rolling
  population** (unlike `quiet_cluster_ghost`): Oracle's screen refreshes
  quarterly and cohort-2 selection happens once, so one frozen
  cross-section graded once at its horizon is the design that actually
  answers the decision. A later quarter's screen is a fresh slug if
  re-tested, not an extension of this one.

## Entry and grading (FROZEN)

- **Entry price:** first close on or after 2026-07-04 (this prereg's
  commit date) for each of the 100 symbols. 2026-07-04 is itself a
  market holiday (July 4th weekend), so in practice this resolves to
  the next trading session's close — a natural signal_lag rather than
  a chosen one.
- **Horizons:** +126 trading days (~6mo, interim read only) and +252
  trading days (~12mo, the PRIMARY grading horizon — chosen because it
  lands within weeks of Oracle's actual cohort-2 selection window,
  directly answering the backlog's timing need). Graded once each
  horizon has elapsed; the 6-month read is reported as directional
  context and is NOT a verdict.
- **Benchmark:** IWM total return over each name's identical
  entry→exit window; excess = stock return − IWM return. (Same
  benchmark convention as every other Oracle-pond study in this house.)
- **Unpriceable at horizon** (delisted/acquired/renamed): bucketed and
  reported by name, not auto-scored — same rule as the insider-cluster
  replay.
- **Analysis:** `shared.ghost.numeric_tercile_stats` on the graded
  12-month excess returns, keyed to the frozen `quality` value per
  entry (terciles built from the graded sample's own distribution, not
  an arbitrary cutoff). Primary metric: high-tercile mean excess minus
  low-tercile mean excess, plus the `monotonic` flag
  (high ≥ mid ≥ low), mirroring the "monotonic conviction" language
  already load-bearing in Oracle's own capital-scaling gate
  (`oracle/capital.py`) — this study asks the same shape of question
  one lens at a time.

## What would count as validation / refutation

- **Validated:** high-tercile mean 12-month excess > low-tercile mean
  12-month excess, monotonic (high ≥ mid ≥ low), AND the high/low
  spread significant at t ≥ 2 (two-sample t-test on event-level excess
  returns, high vs. low tercile).
- **Refuted:** spread ≤ 0, OR t < 2, OR non-monotonic (high < low or mid
  outside the high/low range).
- **n:** ~33 per tercile (100 total, one-shot, non-accruing) — below
  the house's usual n≥150 floor for a definitive call, but consistent
  with this house's other necessarily-small forward tests
  (`quiet_cluster_ghost`, `ipo_lockup_reversion` both use n≥30). No
  "inconclusive, still accruing" branch applies here since the
  population is frozen at n=100 by design — the verdict at 12 months is
  final for THIS slug regardless of n, though a small-n caveat will be
  stated plainly in the results doc.

## Bias checklist preview (full checklist committed with `record_backtest`-equivalent results doc)

- **Survivorship:** grading will bucket delisted/acquired names as
  unpriceable-not-scored (not silently dropped), same rule as the
  cluster replay.
- **Look-ahead:** signal (2026-06-28 screen) predates entry (~2026-07-06
  first close) by about a week — a small, disclosed gap. Since the
  quality lens is fundamentals-derived (quarterly XBRL, not price), a
  week of staleness is immaterial to signal validity, unlike a
  momentum/price signal would be.
- **Selection:** the population is Oracle's own already-committed
  screen output, not hand-picked or re-run for this study.
- **Multiple testing:** one pre-committed metric (tercile spread +
  monotonicity) on one frozen population — n_trials=1 for this specific
  measurement; this study does not touch the house `hypotheses_ever`
  registry counter (measurement-study exception), but is itself a
  single, one-shot test with no re-cut option.

## What this is NOT

- Not a change to Oracle's live scoring weights or cohort-1 holdings —
  cohort-1 already exists and holds regardless of this study's outcome.
- Not a backtest — no historical return has been examined for any of
  these 100 names before this document was committed.
- Not a rolling population — a future quarter's screen tested the same
  way is a new slug, not an extension.
