# Lab prereg — `spinoff_orphans` (COMMITTED BEFORE DATA)

**Sponsor:** operator (cram-for-one-more-god, 2026-07-05, candidate #2).
**Backlog:** the growth-hunt's #2 forced-seller survivor. Committed before data.

## Hypothesis

The **small, neglected** spun-off subsidiary ("orphan") is underpriced at/after
separation and drifts UP over ~3–12 months, because the parent's holders are
**structurally forced to sell the child.**

## Mechanism (G2 — forced seller + document)

When a large-cap parent distributes a small subsidiary, the parent's **index
funds** must sell the child if it isn't index-eligible (below the size/float
threshold — S&P/Russell methodology), and the parent's **large-cap/sector
mandates** dump a child that no longer fits. The child lists with **no analyst
coverage** and a mismatched holder base. That is price-insensitive forced supply
into a thin market → underpricing that unwinds as the orphan finds its natural
holders. (Greenblatt's classic result — but see the crowding caveat below.)

## The five gates

- **G1:** event-driven (the distribution), not a price signal. PASS.
- **G2:** counterparty = index funds + large-cap/sector mandates; document =
  index inclusion methodology + fund mandates. PASS.
- **G3:** the edge is capacity-inverted — a $100M fund can harvest a *large*
  spin but not the small neglected tail. So we restrict to the SMALL child
  (see population). Diversifier, not a scalable engine (accepted).
- **G4:** no contractual terminal — a re-rating drift. FAIL, disclosed → high bar.
- **G5:** ~15–30 US spins/yr, of which a minority are small orphans → adequate
  backtest n over 10 yr, thin-ish forward (~10/yr). Noted.

## The crowding caveat (why "small" is load-bearing)

The general spinoff effect is *well-known* (Greenblatt) and the **large-cap
version is arbitraged away.** The growth-hunt's read: the uncrowded edge lives
**strictly in the small/neglected tail.** So the prereg's PRIMARY test is the
small-child subset (child market-cap in the SMALL/MICRO bucket at listing); the
full-spin set is reported only as the crowded control. If the edge exists only
in the full set and not the small tail, that is a *refutation* of the tradable
thesis (the full-set edge is the one already competed away).

## Population (built AFTER commit)

**Definition:** US corporate spinoffs 2015-01-01 … 2024-12-31 where a subsidiary
was distributed to parent shareholders and the child listed on a major US
exchange. Recorded per event: parent, child ticker, distribution/first-trade
date, child market-cap-at-listing bucket (to isolate the SMALL tail), and
re-failure flag. **Survivorship:** children that later delisted/re-failed KEPT,
exit at last print. Built exhaustively from spinoff trackers (stockspinoffs.com,
Edgar Form 10 / Form 10-12B) + cross-check to Sharadar SEP; coverage_note states
known-missing (OTC-only spins, size-ambiguous cases).

## Test design (frozen)

- **Entry:** first Sharadar SEP close after the child's first-trade date, T+1 lag.
- **Benchmark:** size-matched SMALL/MICRO bucket equal-weight over the identical
  window (same engine as gauntlet_v1 / PEAD).
- **Horizons:** {63, 126, 252} trading days; **primary 252d**; total-return.
- **Costs:** 30bps one-way + 2× stress.
- **Regime split:** in-sample spins 2015–2019; holdout 2020–2024 (touched once).
- **Primary subset:** SMALL/MICRO child at listing. Crowded control: full set.

## Success thresholds (pass ALL or refuted)

1. Small-tail in-sample 252d mean excess > 0, **t ≥ 2**, n ≥ 30.
2. Small-tail holdout mean excess > 0 (same sign), n ≥ 20.
3. Still positive at 2× cost in holdout.
4. Non-isolated across adjacent horizons.
5. The small tail beats the crowded full-set control (else the edge is the
   already-arbitraged general effect, not a harvestable orphan premium).

Miss any → **refuted** (terminal). Supported → forward test + god-scaffold
candidacy (convex diversifier, small/per-name-capped). The population-quality
lesson from `post_bk_emergence` applies: a sector/time-skewed or survivorship-
floored population is NOT a fair test and will not be dignified with a verdict.
