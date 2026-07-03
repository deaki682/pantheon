# Pre-registration: full-population insider-cluster replay (Oracle signal)

Committed 2026-07-03, BEFORE any results exist. Frozen before data, per
house protocol (see docs/nemesis_prereg_news_bounce.md for the precedent
— that one FAILED and was reported anyway; this one gets the same
treatment whatever it says).

## Question

Oracle's core signal is the insider-buying cluster: 2+ insiders spending
their own cash on the same stock within a short window, with payoff
expected 6–18 months later. This replay reconstructs EVERY such cluster
across the whole US filer population from 2025-01-01 through 2026-05-31
— from the filings themselves, not conditioned on outcomes — and grades
them forward. It answers:

1. **Base rate**: what fraction of clusters beat the small-cap benchmark
   at +6 and +12 months? (This is P(win | signal) — the number the
   2026-07-03 mover-conditioned scan structurally could not produce.)
2. **Dose-response**: do bigger clusters (more buyers, more dollars)
   grade better? If not, the signal's sizing logic is decoration.
3. **Convergence** — Oracle is a FOUR-lens system (insider clusters,
   13F smart money, activist 13D, quality screen) and her conviction
   comes from names where lenses agree. Every cluster event is annotated
   with the other three lenses AS OF THE EVENT DATE (a tracked
   smart-money fund holding per the most recent prior 13F-HR; an
   activist 13D on the name within the prior 6 months; the XBRL quality
   snapshot from filings available at event time). Pre-registered test:
   events with 2+ lenses agreeing must outperform cluster-only events at
   12 months for the convergence thesis to validate. Clusters are the
   replay's spine because they are the trigger lens and the only one
   requiring full-population reconstruction; the other three are
   annotations on the event set.
4. **The live tail** (byproduct, not a grade): clusters aged 6–15 months
   whose stock has NOT re-rated — the "Oracle would have found it, the
   payoff window is still open" candidate list, ranked by convergence.

## Population and cluster definition (FROZEN)

- **Source**: EDGAR daily form indexes (complete — no full-text-search
  truncation), every Form 4 filed 2025-01-01..2026-05-31.
- **Issuer identification**: index rows whose CIK maps to a listed ticker
  in the official company_tickers registry; other rows on the same
  accession are the reporting owners.
- **Grant-mill exclusion**: issuers with >150 Form 4 filings in the span
  are excluded (mega-cap compensation machinery, not conviction; also
  outside Oracle's small/mid pond).
- **Cluster event**: ≥2 DISTINCT insiders each making open-market
  purchases (transaction code P, positive shares and price, parsed from
  the filing XML — filer counts alone are NOT a cluster, most Form 4s
  are sales/grants), each buyer ≥ $10,000, all within a 60-calendar-day
  window, aggregate ≥ $50,000.
- **Event dating**: the event date is the FIRST qualifying buy in the
  window. One event per issuer per 90 days (later windows that overlap
  an existing event within 90 days extend it, not duplicate it).

## Grading (FROZEN)

- **Entry price**: first daily close ON or AFTER event date + 5 calendar
  days (signal is public on filing; the lag is an honesty buffer for
  filing delay — Form 4s are due within 2 business days).
- **Horizons**: +126 trading days (~6mo) and +252 trading days (~12mo),
  graded only where the horizon has elapsed.
- **Benchmark**: IWM total return over the identical window; the graded
  quantity is the excess return.
- **Unpriceable at horizon** (delisted/acquired/renamed): bucketed as
  "unresolved-unpriceable" and REPORTED as a count with named tickers —
  NOT auto-scored (unlike spinoffs, disappearance here is often an
  acquisition at a premium, not death; auto-scoring either way would
  bias). Manual disposition, documented per name.
- **All events grade.** No exclusions beyond the frozen ones above.
  Small/mid slice (market cap < $10B at grading time) reported alongside
  all-cap, since Oracle's pond is the former.

## What would count as validation / refutation

- **Validated**: 12-month excess return of the cluster population > 0
  with a t-statistic ≥ 2 on event-level returns, AND monotonic
  dose-response across buyer-count terciles.
- **Refuted**: excess ≤ 0, or significance < 2 with n ≥ 150 events.
- **Inconclusive**: anything else — reported as such, no re-cuts, no
  "but if we exclude..." surgery. One shot.

## What this is NOT

- Not a change to Oracle's live rules — she trades her cohort regardless.
- Not backdated journal entries or ghost entries. The replay grades the
  SIGNAL, not her; nothing here enters any ledger.
- The "live tail" list feeds her next research pass as candidates only —
  every name still needs a full balanced dossier before it can be
  selected, same as any screen output.
