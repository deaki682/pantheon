# The Alpha Map — every anomaly family vs the gates and the graveyard

Built 2026-07-04 (operator: "deep research on every perceivable alpha
strategy"). This is the enumeration that bounds the search: the
published "factor zoo" is ~400 anomalies (Harvey-Liu-Zhu counted 316
by 2016; it has grown), but they collapse to ~15 mechanism families.
This map lists every family, its gate profile (lab.md §3b), its house
status, and whether the house's data can test it — so the overnight
sweep is a deliberate coverage plan, not a fishing trip.

## The empirical backdrop (why the graveyard is normal, and contested)

- **Hou-Xue-Zhang (2020), "Replicating Anomalies":** of 452 published
  anomalies, 65% fail even t>1.96 once microcaps are mitigated (NYSE
  breakpoints + value weighting); 82% fail the multiple-testing
  hurdle (t>2.78). ~18% survive rigorous standards.
- **McLean-Pontiff (2016):** 97 anomalies decay ~58% out-of-sample /
  post-publication.
- **Jensen-Kelly-Pedersen (2023), "Is There a Replication Crisis in
  Finance?":** the OTHER side — >50% of factors replicate in 11/13
  themes under a Bayesian multiple-testing model. The contradiction
  with HXZ is almost entirely METHOD: value-weighting + NYSE
  breakpoints (HXZ, tests "is it real for the market") vs hierarchical
  shrinkage on a broader construction (JKP, tests "is the theme
  real"). **The house's own frame is a third one:** is the effect
  harvestable by a tiny EQUAL-WEIGHTED book in names we can actually
  trade — measured benchmark-relative against that book's own
  equal-weighted universe. gauntlet_v1 already answered that for the
  price families (no), which is consistent with HXZ's harsher reading.

The load-bearing caveat for every cell below: **equal-weighted
small-cap results are exactly the setup the replication literature
finds most fragile.** The house handles this by benchmarking against
the same-universe equal weight (an anomaly must beat the naive book,
not just be positive) and by out-of-sample replication of any
survivor. Both are already standing policy.

## The families

Legend — house status: DEAD (measured refuted here), TESTING (a
grid running tonight), LIVE (a god owns it), UNTESTED, OUT (no honest
data). Gate profile per lab.md §3b (G1 tape / G2 constraint / G3
capacity / G4 arithmetic / G5 power).

### Price-derived (G1 FAIL — the tape families)

1. **Cross-sectional momentum** — DEAD. gauntlet_v1 (48 cells) +
   Delphi (5 cells). Refuted vs same-universe EW across 27 years.
2. **Short-term reversal** — DEAD. gauntlet_v1 (18 cells).
3. **Low volatility / low beta** — DEAD-as-alpha. gauntlet_v1: sole
   in-sample survivor (10/12), all failed the holdout benchmark. Real
   defensiveness, not benchmark-beating alpha.
4. **52-week-high proximity** — UNTESTED but G1-fail; a momentum
   cousin, prior ~dead. Not worth a cell absent an override.
5. **Seasonality (turn-of-month, January, day-of-week)** — G1-fail;
   OUT of scope — pure calendar effects, crowded, no constraint.
6. **Trend / time-series momentum (managed futures)** — DEAD in the
   house's asset-class form (cross_asset_trend, refuted).

### Fundamentals (G1 PASS, G2 PARTIAL — the statement families)

7. **Net share issuance** — TESTING (gauntlet_v2). NOTE the
   literature flag: not robust to value-weighting (microcap-
   concentrated). The house's equal-weight-small frame is where it
   looks best AND least robust — the benchmark-relative bar is the
   arbiter.
8. **Asset growth / investment** — TESTING (v2). Displaced from the
   tangency portfolio in multi-factor tests (JKP) — weak prior.
9. **Accruals (earnings quality)** — TESTING (v2). One of the more
   durable in HXZ.
10. **Gross profitability / ROA (quality)** — TESTING (v2). Quality
    is among the better-replicating themes.
11. **Value (B/M, E/P, S/P, EV/EBITDA, FCF yield)** — UNTESTED,
    gate-passing, data-supported (SF1 + DAILY marketcap). The single
    most-documented anomaly not yet in the house. → gauntlet_v3.
12. **Composite quality+value (Piotroski F, Greenblatt magic
    formula, quality-at-a-price)** — UNTESTED, data-supported. The
    "combine weak signals" family; where JKP finds the most
    robustness. → gauntlet_v3.
13. **Earnings/fundamental momentum (revisions, SUE, ROE trend)** —
    PARTIAL house coverage: PEAD is LIVE (Achilles) on the price-
    reaction side; the fundamental-revision side (change in ROE,
    standardized earnings surprise from SF1) is UNTESTED and
    data-supported. → gauntlet_v3 (one cell, disclosed overlap).

### Event / structure (G1 PASS, G2 PASS — the constraint families)

14. **Forced flows (index reconstitution, lockups)** — UNTESTED;
    the highest-gate-quality untested family. Needs an index-
    membership-change event feed (buildable from Sharadar TICKERS
    add/drop dates or Russell reconstitution lists — a cataloging
    project, not a tonight-runnable grid). FLAGGED for an
    operator-commissioned build.
15. **Tender offers / M&A (issuer, target, CEF)** — DEAD/NULL. Four
    cells tonight (cef_tender, operating, 14d9, toc_anchor): the
    residual is priced; announcement value regime-bound and killed
    in replication.
16. **Insider clusters (quiet subset)** — LIVE-forward
    (quiet_cluster_ghost, accruing). Raw signal DEAD.
17. **Spinoffs / Form 10 reading** — LIVE (Nemesis, ghost race).
18. **Guidance / 8-K text** — near-inert (Midas guidance channel,
    inconclusive-by-construction).

### Cross-asset / macro (mostly OUT at house scale)

19. **Carry, term structure, currency** — G1-adjacent; the ETF
    expression died (cross_asset_trend). OUT absent new structure.
20. **Volatility risk premium (options)** — OUT: the house is
    long-only, no options; inverse-vol ETFs carry their own decay.

## The overnight test plan (derived from the map)

Runnable tonight with SEP+DAILY+SF1, gate-passing, genuinely untested:

- **gauntlet_v2** (running): families 7-10, 20 cells. In flight.
- **gauntlet_v3** (to preregister): family 11 (value — 4-5 multiples
  × 2 sizes × 2 buckets), family 12 (composite quality+value), family
  13 (fundamental momentum, 1 cell). ~18-24 cells.

NOT runnable tonight, flagged for operator decision (honest coverage
gap): family 14 (forced flows) needs an event-feed build; families
19-20 are out of the long-only-no-options mandate. These are the
genuinely-uncovered corners — named, not hidden.

## The standing prediction

Given the map + the graveyard + the replication literature: the
price families are dead (confirmed), the fundamentals families most
likely die against their own equal-weight benchmark at house costs
(v2/v3 will settle it), and the only families with a real prior of
surviving are the CONSTRAINT ones (14, 17) — which are forward/
reading-based, not historical-panel-testable, and therefore live
with the gods, not the gauntlet. If v2+v3 come up empty, that is not
a failure of the search; it is the search completing, and it routes
all remaining hope to the live instruments and an operator-
commissioned forced-flow catalog.

## Two operator lenses (added 2026-07-04, overnight directive)

### Lens A — Delphi replacement candidates (the large-cap mechanical seat)

Delphi's seat = a mechanical, rotational, large-cap ($5B+) long-only
strategy. Her momentum ruleset is refuted (family score 5/5). What
could honestly occupy that seat:

- **value_*__LARGE cells (gauntlet_v3, running)** — the direct
  replacement test: if any value multiple beats the LARGE EW
  benchmark in-sample AND holdout, it IS a drop-in Delphi replacement
  (same universe scale, mechanical, quarterly rotation). This is the
  live search; verdict tonight.
- **Low-volatility LARGE** — gauntlet_v1's only in-sample survivor
  family. NOT benchmark-beating alpha, but real defensiveness
  (shallower drawdowns). A candidate for the seat REFRAMED as "a
  lower-drawdown large-cap core," not as an alpha engine — an
  operator judgment call, not a lab validation. Flagged, not endorsed.
- **Composite quality+value LARGE** — untested tonight (deferred with
  the composites); the family JKP finds most robust. The strongest
  UNTESTED Delphi-replacement candidate if v3-value shows life.
- Honest default if all fail: the LARGE EW benchmark itself (or SPY)
  is the thing to beat and nothing did — the seat's honest occupant
  is then a low-cost index, and Delphi's capital is best not
  deployed on a mechanical stock-picker at all.

### Lens B — LLM-integration candidates (reading on a mechanical filter)

The house's one measured real edge is careful reading of complete
primary documents. A family benefits from LLM integration when: a
mechanical filter narrows the universe cheaply, AND a
document-reading step adds discriminating information the filter
can't see, AND the reading is a comparative advantage (not a
crowded, already-priced signal). Ranked by fit:

1. **Forced flows / index reconstitution (family 14, UNTESTED)** —
   HIGH fit. Mechanical filter: names with a scheduled index
   add/drop. LLM read: the reconstitution announcement + the name's
   float/liquidity to size the forced flow. The reading is niche and
   time-boxed. This is the best combined candidate the map contains.
2. **Spinoffs (Nemesis, LIVE)** — already the canonical LLM-read
   family (Form 10 deep read). Working template.
3. **Quiet insider clusters (LIVE-forward)** — mechanical cluster
   filter + LLM read of the 8-K/context to confirm "quiet." Already
   partly structured this way.
4. **Tender offers (DEAD as mechanical)** — the residual is priced,
   BUT the deal-BREAK subset is a reading task (does the 14D-9 /
   financing / regulatory language predict breaks?). A possible LLM
   revival of a mechanically-dead family — low prior, flagged only.
5. **Value traps (if v3-value shows any life)** — value's classic
   failure mode is the trap (cheap for a reason). An LLM read of
   WHY-cheap on the mechanical value shortlist is the textbook
   quality-overlay on a value filter — the exact "mechanical narrows,
   LLM discriminates" shape. Contingent on v3-value not being flat-dead.

The pattern: LLM integration earns its keep on the CONSTRAINT/event
families (1-4), not the statistical-factor families — consistent with
the whole map. The single most promising build is the forced-flow
event feed (family 14 / Lens B #1), which is also the highest-gate
untested family. If the overnight compute allows, that catalog is the
"leg-stretch" worth attempting.
