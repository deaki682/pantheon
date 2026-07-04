# Prereg — `buyback_quality_overlay` (Lens B: reading on the net-issuance shortlist)

- **Sponsor:** operator (Lens B — LLM integration on a mechanical filter)
- **Committed:** 2026-07-04, BEFORE any forward observation is graded.
  Prospective A/B only — NO historical backtest (the 2000-2025 panel is
  spent for the fundamentals family, and the LLM-judgment arm cannot be
  backtested without training-data contamination). Fresh quarters are
  the sole arbiter.

## Hypothesis

net-issuance-low LARGE only ties SPY because it buys every buyback name
blind, including debt-funded EPS-engineering, dilution-offsetting
non-reductions, and distressed-company buybacks. A QUALITY filter that
keeps only genuine, value-creating buybacks should beat both the raw
basket AND SPY, forward. Two filters are tested against the raw basket:

- **Arm R (raw):** the validated net-issuance-low top-50 (control).
- **Arm M (mechanical quality):** raw names scoring ≥4/5 on: not
  debt-funded (Δdebt < +2%), FCF-positive, ROA > 3%, gross-profit/assets
  > 15%, PE in (0,18]. Fully reproducible from SF1+DAILY.
- **Arm L (LLM quality):** an LLM reads each raw name's buyback context
  (funding source, business health, valuation discipline, sector-
  appropriate treatment — e.g. it must NOT penalize banks for deposit
  "debt") and keeps the genuine value-buybacks. Judged on business /
  capital-allocation quality ONLY, never price memory; the forward
  window (2026Q3+) is after the model's knowledge cutoff, so no
  look-ahead.

## Metric & verdict (frozen)

Each arm is an equal-weight paper basket, same quarterly rebalance and
next-day-close entry as the validated strategy, graded each quarter as
basket total-return excess vs SPY. Tracked in
`cache/lab_buyback_quality_ab.json`.

- **The Lens-B question (primary):** does Arm L beat Arm R over ≥8
  graded quarters (shrunk mean excess, Arm L − Arm R > 0)? That is the
  test of whether READING adds over the raw factor.
- **The quality question (secondary):** does either M or L beat SPY
  (shrunk mean excess > 0) where raw only tied? ≥8 quarters.
- Interim quarters reported, never concluded early. This is a
  DIAGNOSTIC A/B, not a capital gate — no arm goes live on it; a
  winning arm would earn its own standalone forward test at n≥20.

## Reproducibility

The mechanical arm is deterministic. The LLM arm records, each quarter,
the per-name judgment + one-line rationale in the tracker, so the
reading is auditable and the process repeats on every roll (the roll
runner carries the frozen prompt). The three arms share one entry-price
set, so differences are pure selection, not timing or cost.

## What this is NOT

Not a live strategy, not a Delphi replacement decision, not a backtest.
A prospective, honest test of the single most important open question in
the house: whether the LLM's reading is worth anything on top of a
measured mechanical edge.
