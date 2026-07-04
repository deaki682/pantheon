# Prereg — `cef_toc_anchor_2014_19` (out-of-sample replication of the TO-C anchor)

- **Sponsor:** operator ("go", 2026-07-04)
- **Committed:** 2026-07-04, BEFORE any 2014–2019 index sweep or price
  outcome for this window. The 2020–2026 window is SPENT for this
  question (`cef_tender_toc_anchor`, inconclusive-positive: shrunk
  +0.81%, t 1.92, n 82). 2014–2019 has never been touched by any house
  tender study — this is a genuine out-of-sample replication of the
  SAME frozen rule in a different rate/activist regime.

## Rule (identical to `cef_tender_toc_anchor`, no re-tuning)

- Events: SC TO-I filings by listed CEFs 2014-01-01→2019-12-31 (EDGAR
  quarterly full-index, exact form type, /A excluded), 180-day per-fund
  dedup, matched via SFP TICKERS category=CEF (delisted included,
  price-window-checked name fallback), kept iff an SC TO-C by the same
  CIK exists 1–90 calendar days BEFORE the TO-I.
- Anchor: earliest such TO-C; entry first close strictly after it.
- Listing screen: ≥15 SFP bars in the 30 calendar days pre-anchor
  (pre-event data only). Both raw and screened reported; verdict on
  screened.
- Metric: market-adjusted CAR vs SPY total return at +25 trading days
  (`shared.gauntlet.event_car`); full curve to +40 published (the
  window-1 HUMP — peak ~25, full reversal by 40 — is itself a
  replication target, stated in advance: we expect rise-then-reverse,
  not monotonic drift).

## Verdict (frozen — same bars as window 1)

- SUPPORTED iff shrunk mean CAR(25) > +1.0% AND t ≥ 2 AND n ≥ 30.
- REFUTED iff shrunk mean CAR(25) ≤ 0 with n ≥ 30.
- INCONCLUSIVE otherwise.
- SUPPORTED here earns `start_forward_test` per the standard ratchet
  (≥20 graded paper events on fresh 2026+ TO-Cs — the forward leg both
  windows would then share). Combined-window statistics are reported
  as context, never substituted for this window's own bars.

## Bias checklist deltas (full eight at record time)

Survivorship: 2014-era CEFs that later delisted must appear via SFP's
delisted coverage; funds with no SFP bars land in `unpriceable` with
counts — if that bucket is large, it is THE caveat and gets said
first. Regime: 2014–2019 spans taper tantrum aftermath, 2015–16
credit stress, 2017 calm, 2018 Q4 crash — per-year table mandatory.
Multiple testing: counter +1 at registration; no secondaries. Costs:
gross, disclosed, same +1.0% buffer rationale. Look-ahead/selection/
overfitting: identical structure to window 1; zero parameters differ.
