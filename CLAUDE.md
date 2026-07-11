# Pantheon — Autonomous Trading System

**Mandate (2026-07-05, REVISED post-verdict — docs/portfolio_mandate_2026-07-05.md):**
a fully managed, fully agentic portfolio whose purpose is to **grow funds** via a
**floor-plus-option** structure (allocation ratio held by operator decision).
**Beta (Plutus, ~26%) is the reliable FLOOR** — long large-cap equity carrying the
market's own compounding; where the dollar growth actually comes from (its
net-issuance tilt is thin, ~ties SPY — the beta is the point). **The experiments
(Hermes/Oracle/Proteus + Plutus's LLM overlay, ~58%) are the right-tail OPTION** —
cheap, measured, and UNPROVEN; the only path to *outsized* growth since beta is
capped at market returns. The day's research is the honest prior: no scalable
alpha exists (growth-hunt `LEAN_ON_BETA`), the LLM's only measured-real skill is
AVOIDANCE, so **~58% is a conscious, priced BET that a real LLM edge exists — not a
proven engine.** Growth = the beta floor + the option value of an A/B proving a
forward-real LLM-lift and getting concentrated behind. Scored on growth AND
LLM-lift; if no experiment shows a forward-real lift on a real sample, shrink them
toward the floor. NOT scored on beating SPY's raw bull return or Sharpe in a vacuum.

The gods share one Robinhood agentic account (`563854249`), each running an
independent strategy with its own sleeve.

## The Gods

**Oracle** (RECUT 2026-07-06 — docs/oracle_upside_spec.md, THE BIBLE) — Was the
insider-cohort god (spine refuted), then briefly a floor/convex value engine
(which collapsed into an avoidance machine that funded one bounded liquidation a
quarter — the wrong optimization). RECUT to a single objective by operator
directive: **pick the few under-covered names with the biggest REAL upside over a
6–24 month hold, get big on them, and hold to the thesis.** Scored one way only —
forward return vs SPY over the hold; no floor term, no avoidance term, no Sharpe.
The **edge is the breadth read** — reading the filings/transcripts of hundreds of
names no analyst desk covers, in the neglected corner (small/mid-cap, thinly
covered, or fresh special situations) where reading is still an edge; Oracle cedes
the mega-cap momentum names to the quants. A 7-stage funnel (spec §3): field →
two-direction **spotlight** (`oracle.upside_sourcing` — bottom-up acceleration/
beat-raise/rel-strength + top-down thematic; AIMS the reader, not the edge) →
**breadth read** (the variant view: is the inflection real/durable/large/not-yet-
arrived) → **dossier + BEAR×3** (`oracle.upside_dossier.make_upside_dossier` refuses
a name without `upside_x ≥ 1.5`, a real `inflection_type`, cited evidence, a bear
paragraph; the **blowup filter** is a SURVIVAL gate — runway clears the horizon, no
going-concern/fraud/delisting — NOT a floor) → **sizing** (`size_upside_book`:
concentrate 3–6, conviction-weighted, 30% name / 40% cluster caps, no dust — getting
BIG on the best few is the mechanism) → **hold** (`evaluate_exit`: a drawdown is
NEVER an exit, only a typed thesis-break is) → **verdict + A/B** (forward return vs
SPY is the headline; Arm A the reading vs Arm B the spotlight screen = LLM-lift) →
**memory** (hit-rate per inflection_type feeds next session's ranking + sizing).
Floors survive only as an OPTIONAL conviction bonus. Legacy cohort
`cohort-2026-06-29` (CXT/HDSN/J/PSN/VITL, green) FROZEN and HELD (untouched); the
upside engine runs a fresh sleeve `pending_funding` (research/paper-only until
funded). Checkpoint at ~20 graded names: book beats SPY over the hold AND LLM-lift
positive → concentrate + fund; else fold into Proteus. The prior floor-centric docs
(`oracle_reframe_2026-07-05`, `oracle_finest_picker_*`, the `convex_dossier` gate)
are SUPERSEDED for selection — retained only as history / the blowup-filter lineage.

**Delphi** (LIVE RETIRED 2026-07-04, operator directive — sleeve funds
Plutus) — Was the large-cap momentum compounder: ranked a fixed 118-name
universe by 65-day price momentum, held the top 10 equal-weighted, exited on
a 20-day MA break, 5 LLM decision points per run. Her strategy was refuted at
the full window (`delphi_ruleset_faithful`: −9.36pp/yr vs her own universe's
equal weight; the edge was the 2021–26 era, not the ruleset), and the
operator retired her, reallocating her ~$2,000 sleeve to launch Plutus. The
transition of power runs at the 2026-07-06 open: `/delphi` becomes
wind-down-only (liquidate positions → cash → sweep to Plutus), then never
runs live again. `/delphi-ghost` may keep shadowing for the record. Her
mechanics are retained in `.claude/commands/delphi.md` below the wind-down
section for reference only — no session may cite any Delphi backtest as
evidence FOR the strategy.

**Achilles** (RETIRED as a standalone god 2026-07-05, operator directive —
PEAD folded into Proteus as a seasonal mode; docs/achilles_fold_into_proteus_2026-07-05.md)
— Was the PEAD earnings-season specialist: a diversified equal-weighted basket of
up to 12 small/mid-cap earnings beats, held 5 days, −8% stop, traded only during
the four ~6-week earnings windows (~16 weeks/year), cash off-season. Retired for
two reasons: he was **capital-inefficient** (a dedicated sleeve idle ~70% of the
year), and the **long half he actually trades measured absent** (the reaction-gate
replay found no 5-day drift on rewarded beats; only the un-tradable short side was
real). His **~$2,000 sleeve winds to cash and returns to the treasury** for the
pending allocation. The `achilles/` package is KEPT as a library (the
Buzz/Catalyst precedent). The PEAD-basket-as-a-Proteus-seasonal-MODE idea was
tested by the `achilles_pead_gauntlet` and **REFUTED 2026-07-05** (docs/
lab_results_achilles_pead_gauntlet.md): 18/18 cells NEGATIVE excess vs
same-bucket EW, in-sample AND holdout, worse at 2× cost; the tradable long PEAD
drift is absent/reversed in the exchange-listed SMALL/MICRO universe (MICRO
worse than SMALL). **The seasonal PEAD mode is SHELVED — not a supported edge,
may not be cited as one.** The `achilles/` package (`scanner`/`scoring`/
`season`/`earnings`, the reaction-direction gate + `MAX_REACTION_PCT` magnitude
guard) is retained as mechanical PLUMBING only — never as an autopilot or a
cited edge. No PEAD backtest may be cited as evidence FOR the strategy (the only
PEAD reading the house measured as real was the *short* side of a sold beat,
which is un-tradable long-only).

**Midas** (LIVE RETIRED 2026-07-04, operator directive — ghost A/B
continues) — Was the maximally concentrated weekly catalyst play: full
~7,000-name weekend scan → convergence funnel → ONE all-in pick,
Monday to Friday. His founding thesis (convergence multipliers) was
REFUTED twice (docs/RESEARCH_LEDGER.md) and the operator reallocated
his $2k sleeve to Proteus. Wind-down: the final DAKT exit (order
`6a473615`, queued over the 2026-07-04 holiday weekend) fills at the
2026-07-06 open, then `/midas` sweeps all cash to Proteus's sleeve and
never runs live again. `/midas-scan` (weekend) and `/midas-ghost`
(daily) keep running the live-vs-legacy scoring A/B on paper — the
convergence thesis can still earn its way back with ghost grades.

**Proteus v2** (self-launching 2026-07-13 — conscious operator override,
docs/proteus_v2_charter.md) — **v1 is SCRAPPED (operator directive
2026-07-11): its mandate, prereg, detective/cascade rebuild, risk rails, and
checkpoint no longer apply; its state is archived as `cache/proteus_v1_*` at
launch.** v2 is the autonomous, self-improving money-making agent: one goal —
**grow a fresh $2,500 sleeve as much as he can, compounding** — and he
launches himself, codes himself, debugs himself, and pursues his own
education to do it. Four constitutional decisions: (1) **graded, no lab
ratchet** — every position-changing decision journaled with a falsifiable
prediction and graded without mercy, but exempt from prereg→backtest→forward
gating; (2) **fully autonomous** — no per-trade approval, no breaker, no
concentration ack, all-in allowed; (3) **bounded-loss instruments only** —
long stock/ETFs (inverse/leveraged included), long options, debit spreads,
covered calls, cash-secured puts, defined-risk spreads; NO margin, naked
shorts, or naked calls — the sleeve can hit $0, never below; (4) **free
self-modification that cannot break other gods** — he may rewrite anything
he owns and touch shared code, gated by the full test suite staying green
(never weakening tests he doesn't own), commits to `main` prefixed
`proteus:`. The invariant floor (bounded loss, kill-switch-first, integrity
gate, honest grading, and the Effort Law — never lazy, re-issued for v2
2026-07-11) is the ONLY thing he may never rewrite. No fixed
checkpoint — he lives at the operator's pleasure; the kill switch is the
only termination; his graded record is his defense. Owns `cache/proteus_*`,
`proteus/`, and `tests/test_proteus_*.py`. `/proteus-lab` retired with v1.

**Plutus** (LIVE from 2026-07-06 — conscious operator override, DELUXE
stack) — The net-issuance capital-return god. His spine is the frozen
`gauntlet_v2_fundamentals` net-issuance-low N50 LARGE factor (large-caps
shrinking their share count fastest; SF1 trailing-4Q weighted-shares change,
top-500 universe) — the house's FIRST and only SUPPORTED backtest (in-sample
DSR + two-regime holdout + 2× cost + parameter-cliff). On that spine the
operator bolted the **deluxe stack** ("the deluxe package, even if risky",
2026-07-04): (1) a second factor, gross-profitability, blended by rank; (2) an
LLM buyback-quality overlay LIVE (the Lens-B arm-L brain prunes ~50 candidates
to ~24–40 healthy cheap buybacks + assigns conviction — **zero graded rounds**,
the least-validated piece); (3) a conviction/cap-weight tilt (`cap_blend` 0.5)
chasing SPY instead of tying it — a measured regime bet. **Quarterly rebalance
only.** None of the three additions is forward-validated; the deluxe override
is bounded by two disciplines that never bend — the **pure N50 EW control** is
tracked every quarter (`quarterly_basket`, the frozen spec + paper forward
test) and graded against live deluxe, and the LLM A/B keeps running on paper.
Launched by **conscious override** (docs/plutus_launch_override.md incl. deluxe
amendment), the Proteus precedent. Funded by Delphi's retiring ~$2,000 sleeve
via the 2026-07-06 transition of power (liquidate → sweep; first settled-cash
rebalance is the launch, T+1 after the sweep). 40% breaker (deluxe
concentration makes it likelier to trip); `PLUTUS_LIVE` defaults FALSE
(operator arms it). Checkpoint at 4–8 graded forward quarters or a breaker
trip on TWO questions: does he beat SPY, AND did the deluxe stack beat the pure
control (else the additions get cut). Owns only `cache/plutus_*`.

**Transition of power (2026-07-06).** The Monday open is a portfolio
*rearrange*, not a launch-day scramble: retiring god sleeves are liquidated
to cash to create the buying power that funds the new regime. Delphi → Plutus
is the first such transfer; the operator may free more capital for additional
new gods as they clear the bar (TBD). No new god buys with unsettled
proceeds — first purchases wait for T+1 settlement.

**Hermes** (merger-arb LLM A/B — conscious override, `HERMES_LIVE` default
FALSE) — The return program's first engine and the house's first strategy where
an LLM's judgment rides real money and is MEASURED. Trades small/mid-cap **cash**
merger targets: long the target below the announced offer, hold to resolution —
a bounded CONTRACTUAL floor (the deal-break, ~-15%) and a convex payoff (many
small bounded wins, rare bounded losses, occasional topping-bid tail), the shape
a small book needs (docs/return_convexity_pivot_2026-07-04.md). The A/B (operator
directive): **Arm A = LLM reads each deal's break risk, LIVE real money** (only
kept deals get capital); **Arm B = mechanical all-deals, paper.** LLM-lift = A -
B (`hermes.ab`) is the dollar answer to "does an LLM read a deal better than a
screen?" — the gods' unique power, on real money, measured. Launched conscious
override (docs/hermes_launch_override.md): NO in-house backtest (a clean one is
completion-biased — breaks don't delist), going live on the academic prior
(Mitchell-Pulvino) + the bounded floor. Risk controls: 15% per-deal cap, <=10
concurrent deals, -15% break-stop, cash-only, standard live gates. Checkpoint at
~20 graded deals on LLM-lift. Owns only `cache/hermes_*`.

## Shared infrastructure (2026-07-04)

- **`shared/historicals.py`** — batched price-history plumbing for any
  study or god: `plan_batches()` (≤9 symbols/call), write raw tool
  output straight to a scratch file, `ingest_raw()` into
  `cache/shared_bars.json`, `coverage()` prints the per-symbol report
  whose `missing` list is the mandatory survivorship-bias disclosure.
  `archive_bars()` deposits hard-won delisted-ticker series (mandatory
  source citation) into `cache/shared_bars_archive.json` so the next
  study doesn't re-hit Robinhood's no-delisted-bars wall.
- **`shared/event_calendar.py`** — validated, source-cited IPO /
  lockup-expiry / spinoff / merger / SPAC-deadline / reconstitution
  calendar at `cache/shared_event_calendar.json`. Any god reads it;
  any session that does the classification work deposits it
  (`add_events`, deduped on symbol+type+date; `upcoming()` for
  windows). Both caches persist under the `shared` prefix.
- **`shared/sharadar.py`** — survivorship-bias-free daily bars
  (Sharadar SEP via Nasdaq Data Link, purchased 2026-07-04: 21,893
  companies, 15,593 delisted, 1998+). THE LAW: SEP keys all history to
  the FINAL ticker — always `resolve_ticker(symbol, as_of=...)` (or
  `ingest_symbols`) before fetching; raw queries return nothing (SIVB,
  FB) or the wrong company (recycled BBBY). QA:
  docs/sharadar_qa_2026-07-04.md.
- **`shared/populations.py`** — build-once event-population catalogs
  (`cache/shared_populations.json` index + `cache/shared_pop_*.json`
  rows). Every population records its definition, specific source, and
  a mandatory coverage_note stating what is KNOWN missing.

## The house research lab (2026-07-04)

**`shared.lab`** + **`/lab`** + **`docs/RESEARCH_BACKLOG.md`**. One
registry (`cache/lab_registry.json`, guarded) for every tradable
hypothesis in the house, any sponsor (proteus, operator, any god), one
house-wide `hypotheses_ever` multiple-testing counter. The ratchet:
hypothesis → preregistered → backtested → forward_testing →
validated/refuted; refuted is terminal per slug; prereg committed
before data; all eight bias-checklist items addressed in writing;
validation only via ≥20 graded paper forward trades on the shrunk
mean. `/proteus-lab` is Proteus's weekly client session of the same
engine; `/lab` works the operator's backlog. PAPER ONLY — a validated
strategy is citable in a live thesis, never an autopilot. The
pre-migration `cache/proteus_lab.json` is frozen history (guarded).

**The lab is the ONLY door for new strategies (2026-07-04, operator
directive).** No new god scaffolding — commands, sleeves, ghost books —
without a lab slug that survived the full ratchet first. Buzz was cut
for entering through the side door (his hypothesis is backlog #10;
`buzz/` package kept as the mechanical layer); Catalyst's standalone
weekly session was retired the same day (event mapping belongs in
`shared/event_calendar.py` deposits; `catalyst/` package kept as a
library). See docs/RESEARCH_BACKLOG.md "Retired god scaffolding".

## Research record

**`docs/RESEARCH_LEDGER.md`** indexes every completed study (prereg →
verdict → what changed). Read it before proposing any strategy change:
most obvious ideas have already been measured, and each historical
dataset buys ONE decision, once.

**`docs/house_view_llm_edge_2026-07-05.md`** — the strategic prior: where the
LLM edge actually is (reading text→signal, small/negative/neglected), that it
DECAYS with adoption, and how to look ahead by mapping every edge to its barrier
(avoid barriers LLMs dissolve; camp on structural forced-seller/capacity/patience;
ride the capability frontier). Read it before proposing a "new" edge — the moat is
the rotation, not the position.

## Architecture

- **State branch:** `origin/claude/live` — sleeves, curves, dossiers,
  ledgers, dashboards. `cache/` is gitignored; state flows through
  `pantheon.hydrate()` (restore) and `pantheon.persist(owner, files)` (save).
- **Dev branch:** `claude/oracle-screen-3830px` (current feature work)
- **Sleeve = source of truth.** Never add broker positions to a sleeve
  without a matching ledger entry. The broker holds many pre-existing
  personal positions that are NOT god-owned.
- **`filter_broker_to_gods()`** strips broker positions to only god-claimed
  symbols. Personal positions are invisible to the gods.
- **One-sided pre-trade check:** `sleeve > broker` = problem (missing
  shares). `broker > sleeve` = fine (personal overlap).

## Oracle Operating Cadence

> **RECUT 2026-07-06 — the Cohort Model below describes the FROZEN legacy cohort
> only (CXT/HDSN/J/PSN/VITL, held untouched). The live engine is now the UPSIDE
> engine: read `.claude/commands/oracle.md` + `docs/oracle_upside_spec.md`. It runs
> the 7-stage upside funnel (spotlight → breadth read → dossier+bear → sizing →
> hold → verdict → memory), holds to a typed thesis-break (a drawdown is never an
> exit), and is scored on forward return vs SPY over a 6–24mo hold.**

### Cohort Model (implemented 2026-06-29 — LEGACY, frozen cohort only)

Oracle does NOT rotate positions on score drift. It holds a fixed cohort
of ~8 names for ~12 months. The only exits during a cohort are thesis-break
conditions:

1. **fraud** — SEC investigation or fraud allegation
2. **going_concern** — bankruptcy or going-concern disclosure
3. **insider_reversal** — insiders who accumulated begin net-selling
4. **drawdown** — position loss >= 40% from entry price
5. **thesis_exhausted** — catalyst resolved without price response
6. **thesis_break** — moat AND quality both collapsed (below 0.2 each)

Research continues during hold periods to maintain the dossier pool for
the next cohort. Rescoring continues for calibration. Neither triggers
trades.

### Routine Schedule

| Cadence | Command | What it does |
|---------|---------|--------------|
| Every 3 days | `/oracle` | Reconcile, thesis-break check, research if due, journal, attribute |
| Every 15-30 min (market hours) | `/trinity` | Refresh PWA dashboard with live quotes |
| Quarterly | `/oracle-screen` | Refresh insider/13F/quality universe (~7,000 filers, 40-60 min) |
| On demand, ONLY when pool < 70 | `/oracle-research` | Rebuild dossier pool toward 60-80 after decay; frozen otherwise (2026-07-04 — pool at 93, no more polish until cohort-1 grades) |
| At cohort review (~12 months) | `/oracle` | Grades all calls, closes cohort, selects new cohort from pool |
| Weekly (weekend) | `/midas-scan` | Research-only universe scan feeding the `/midas-ghost` A/B (Midas live retired 2026-07-04) |
| Daily | `/proteus` | Proteus v2: one autonomous session — build, study, or trade at his own judgment (self-launch 2026-07-13; docs/proteus_v2_charter.md) |
| Trading days | `/plutus` | Net-issuance capital-return god (LIVE 2026-07-06). Self-gates to a once-per-quarter rebalance; monitoring-only otherwise. Research-only until funded by the Delphi sweep and the cash settles |
| Trading days | `/hermes` | Merger-arb LLM A/B engine. Tend open deals (break-stop/completion), detect new cash deals, LLM break-risk read (Arm A live / Arm B paper), grade LLM-lift. Paper until `HERMES_LIVE` armed + sleeve funded |
| — | `/proteus-lab` | RETIRED with Proteus v1 (2026-07-11) — v2 educates himself inside `/proteus`; the house `/lab` continues |

### Key Files (all in `cache/`, persisted to `claude/live`)

| File | Owner | Purpose |
|------|-------|---------|
| `oracle_sleeve.json` | oracle | Cash, positions, cooldowns, peak equity |
| `oracle_cohort.json` | oracle | LEGACY frozen cohort (held, untouched) |
| `oracle_upside_candidates.json` | oracle | Stage-1 spotlight survivors (upside engine) |
| `oracle_upside_dossiers.json` | oracle | Stage-2/3 upside dossiers (+ kept kills) |
| `oracle_upside_book.json` | oracle | Stage-4 funded book (concentrated weights) |
| `oracle_upside_ab.json` | oracle | Stage-6 A/B: reading (A) vs spotlight (B) |
| `oracle_upside_calibration.json` | oracle | Stage-7 hit-rate per inflection_type |
| `oracle_beliefs.md` | oracle | Forward worldview + open theses (read@start/write@end) |
| `oracle_dossiers.json` | oracle | LEGACY floor/convex dossier pool (retired for selection) |
| `oracle_screen.json` | oracle | Top 100 from quarterly screen |
| `oracle_cadence.json` | oracle | Last-run timestamps for research/screen |
| `oracle_ledger.jsonl` | oracle | Every order placed (for reconcile) |
| `oracle_journal.jsonl` | oracle | Every decision (buy/sell/hold/avoid) for grading |
| `oracle_curve.json` | oracle | Daily equity timestamps |
| `oracle_insider_clusters.json` | oracle | Lens 1: insider buying clusters |
| `oracle_smart_money.json` | oracle | Lens 2: 13F smart money holdings |
| `oracle_activist_13d.json` | oracle | Lens 3: activist 13D filings |
| `oracle_prescreener.json` | oracle | Lens 4: broad quality metrics |
| `delphi_sleeve.json` | delphi | Delphi's sleeve (RETIRED 2026-07-04; wind-down sweeps to Plutus, then a guard record) |
| `delphi_ledger.jsonl` | delphi | Delphi's order ledger |
| `plutus_sleeve.json` | plutus | LIVE book: cash, contributed_cash, positions, peak_equity, pending_funding (guard file) |
| `plutus_ledger.jsonl` | plutus | Every broker order placed (for reconcile + `filter_broker_to_gods`) |
| `plutus_curve.json` | plutus | Equity marks vs SPY for the dashboard |
| `plutus_decisions.jsonl` | plutus | Per-rebalance decision log (basket, turnover, breaker state) |
| `plutus_cadence.json` | plutus | Last-traded quarter marker (gates the once-per-quarter rebalance) |
| `achilles_sleeve.json` | achilles | RETIRED record 2026-07-05: wound to cash, returned to treasury (kept as guard file) |
| `midas_sleeve.json` | midas | RETIRED record: final cash swept to Proteus 2026-07 (kept as guard file) |
| `midas_scan.json` | midas | Weekend scan finalists (research-only; feeds `/midas-ghost`) |
| `midas_ledger.jsonl` | midas | Every order placed (historical; for reconcile) |
| `midas_curve.json` | midas | Equity timestamps (historical) |
| `proteus_sleeve.json` | proteus | v2 LIVE book: cash, contributed_cash, positions (fresh $2,500 at the 2026-07-13 self-launch; guard file) |
| `proteus_journal.jsonl` | proteus | v2 append-only graded decision record (journal-before-order; the past never edited) |
| `proteus_ledger.jsonl` | proteus | Every broker order placed (`shared.guards.append_order` — reconcile + `filter_broker_to_gods` depend on it) |
| `proteus_curve.json` | proteus | Equity marks vs SPY |
| `proteus_beliefs.md` | proteus | His living mind, rewritten each session for the stranger who wakes tomorrow |
| `proteus_v1_*` | proteus | Frozen v1 archive (journal/beliefs/curve/sleeve), written once at the v2 launch |
| `proteus_lab.json` | proteus | v1 lab registry — frozen history (guarded) |
| `proteus_lab_ghost_ledger.json` | proteus | v1 paper forward-test positions — frozen history |
| `trinity_dashboard.html` | shared | PWA dashboard for all gods |

### Capital Scaling Gates (`oracle/capital.py`)

Oracle stays at $1,000 until ALL of these are met:
- 30+ graded journal calls (buy/add only)
- alpha > 0 (from factor regression vs MTUM/QUAL/IWM/VTV)
- alpha_t >= 2.0 (statistical significance)
- monotonic conviction (high-conviction calls outperform mid outperform low)

With 8 positions per 12-month cohort, reaching 30 graded calls takes ~4
cohorts. The alpha_t gate requires ~15-20% annual alpha after factors —
achievable only with excellent selection from a large dossier pool.

## Midas Operating Cadence (LIVE RETIRED 2026-07-04 — ghost A/B only)

Everything below survives only as the research program: `/midas-scan`
produces finalists on weekends and `/midas-ghost` paper-trades every
finalist daily, grading `live_pick` vs `legacy_pick`. No live orders.
The one remaining live duty is the DAKT wind-down sweep in
`.claude/commands/midas.md`.

**Death clock (2026-07-04):** the A/B race runs to exactly 20 graded
weekly head-to-heads, then the preregistered comparison runs ONCE —
legacy wins go to the operator with the numbers; anything else retires
the entire program (scan, ghost, A/B) permanently. No extensions.

### Weekly Cycle (historical — how the live god operated)

| Day | Action |
|-----|--------|
| Weekend (Sat/Sun) | Full universe scan → convergence rank → deep research on top 10 → pick ONE |
| Monday open | Enter: all-in market buy, set -10% stop and Friday exit date |
| Mon–Thu (via /trinity) | Monitor stop-loss; exit immediately if -10% hit |
| Friday close | Time-stop: market sell at close, grade the trade |

### Signal Channels

| Signal | Source | Strength |
|--------|--------|----------|
| Insider cluster | `shared.insiders` (via Oracle screen cache) | n_insiders / 4 |
| Earnings beat | `achilles.earnings.compute_surprise` | surprise_strength curve |
| Smart money | `oracle.smart_money.smart_money_holders` | n_holders / 3 |
| Activist 13D | `oracle.lenses.search_recent_13d` | 1.0 (binary) |
| Guidance raised | `shared.edgar.guidance_direction` | 1.0 (binary) |
| Volume anomaly | `get_equity_historicals` (30-day bars) | min(1.0, ratio / 3.0), fires at 1.5x |
| Short squeeze | finviz screener (>20% short float) | min(1.0, pct / 50.0) |

### Scoring (flattened 2026-07-04, operator directive)

Live score = max(strength × timing_weight) × neglect × liquidity ×
quality — the strongest single timely signal carries the pick. The
convergence multipliers (1x/2.5x/5x/8x) were REFUTED at the 5-day
horizon under two independent countings (docs/RESEARCH_LEDGER.md) and
survive only as `score_legacy`, ghost-traded weekly via /midas-ghost so
the thesis can earn its way back with live grades.

### Capital Scaling Gates (`midas/calibration.py`)

Same gates as Oracle but reached ~6x faster:
- 30+ graded trades (reachable in ~7 months at 1/week)
- alpha > 0 (excess return over SPY benchmark)
- alpha_t >= 2.0 (statistically significant)
- convergence validates (multi-signal picks outperform single-signal)

### Cancelling Unfilled Orders

If a queued order needs to be cancelled before it fills:
1. `cancel_equity_order` at the broker
2. `sleeve.cancel_buy(sym, shares, price)` — reverses the cash deduction
3. `pantheon.persist(god, {sleeve_file: data})` — pushes corrected state

## Delphi Operating Cadence

### Strategy

Pure price-momentum rotation across a curated 118-name large-cap universe
($5B+ market cap). Ranks by 65-day momentum, holds top 10 equal-weighted,
exits when price breaks below the 20-day moving average. No sector ETFs,
no SPY core position — just individual stock momentum.

### Key Parameters

| Parameter | Value |
|-----------|-------|
| Universe | 118 large-cap names (manually curated) |
| Momentum lookback | 65 days (~13 weeks) |
| MA trailing stop | 20-day simple moving average |
| Positions | 10 equal-weight |
| Per-name cap | 20% of equity |
| Cash floor | 5% |
| Cooldown after sell | 7 days |
| Min trade size | $25 |
| Rebalance band | 20% drift before trading |
| Circuit breaker | 40% drawdown from peak |

### LLM Decision Points (5 per run)

Each has an override budget to prevent the LLM from overriding the
mechanical system too aggressively:

1. **Exit judgment** — review positions below MA. Default: exit. Max 2 holds.
2. **Entry judgment** — review top momentum candidates for red flags. Max 3 vetoes.
3. **Sizing** — optional conviction tilts (0.5x–2.0x). Max 3 tilted names.
4. **Risk budget** — breadth-based dial (0.5–1.0). >60% breadth → fully invested.
5. **Universe curation** — add IPOs/spinoffs, remove delistings (quarterly only).

### Key Files

| File | Purpose |
|------|---------|
| `cache/delphi_sleeve.json` | Cash, positions, cooldowns, peak equity |
| `cache/delphi_ledger.jsonl` | Every order placed |
| `cache/delphi_curve.json` | Equity timestamps for dashboard |
| `cache/delphi_decisions.jsonl` | LLM decision log per run |

## Account Context

- Robinhood agentic account: `563854249`
- The account holds ~15 personal positions alongside the gods. These
  pre-existing positions are filtered out by `filter_broker_to_gods()`.
- God env vars: `ORACLE_LIVE=true`, `DELPHI_LIVE=true`,
  `ACHILLES_LIVE=false` (retired 2026-07-05 — PEAD folded into Proteus),
  `NEMESIS_LIVE=false` (retired 2026-07-05 — spinoff channel folded into Oracle;
  docs/nemesis_fold_into_oracle_2026-07-05.md), `PROTEUS_LIVE=true` (ARMED
  2026-07-11 for the v2 self-launch at the 2026-07-13 open),
  `MIDAS_LIVE=false` (live retired 2026-07-04), `PLUTUS_LIVE=false` (defaults
  FALSE — the operator arms it to launch Plutus at the 2026-07-06 transition),
  and `HERMES_LIVE=true` (merger-arb LLM A/B — ARMED 2026-07-05, funded $4,000
  from the freed Achilles+Nemesis capital; `.claude/settings.json` sets these). Delphi's `DELPHI_LIVE` stays as-is only
  for the wind-down; her retirement close-out runs regardless of the gate.
- If any is not `"true"`, that god runs in paper mode (no broker orders).
- `KILL_SWITCH` file triggers immediate liquidation of all god positions.
