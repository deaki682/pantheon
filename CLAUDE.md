# Pantheon — Autonomous Trading System

Four gods share one Robinhood agentic account (`563854249`), each running
an independent strategy with its own sleeve ($1,000 base; Delphi at $2,000).

## The Gods

**Oracle** — Patient small/mid-cap researcher. Insider-accumulation signal
with 6-18 month horizon. Uses a **cohort model**: selects 8 positions once,
holds ~12 months, exits only on thesis-break. Research runs continuously to
maintain a pool of 60-80 dossiers for the next cohort. Capital starts at
$1,000; scales to $12,000 ceiling after 30+ graded calls prove skill
(alpha_t >= 2.0, monotonic conviction). Realistically needs 4+ cohorts
(~4 years) to accumulate enough graded calls.

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

**Achilles** — PEAD earnings-season specialist. Trades only during the
four ~6-week earnings windows (~16 weeks/year). Holds a **diversified
equal-weighted basket** of up to 12 small/mid-cap earnings beats — not one
all-in bet. PEAD is a thin statistical edge that only surfaces across many
names, and a basket both preserves it and validates it far faster than one
trade at a time. Each name: enter next trading day, hold 5 trading days,
-8% hard stop, one slot per symbol, 4-week cooldown after a stop. Sits in
cash off-season. The edge is Post-Earnings Announcement Drift — the most
robust short-horizon anomaly, strongest in neglected names with thin
analyst coverage. **Reaction-direction gate:** only goes long a beat the
market *rewarded* (positive post-report reaction) — never a "sold beat"
(gap up, close red), because the drift follows the reaction, not the EPS
headline. Confirming signals (revenue beat, guidance raised, short squeeze,
insider pre-buy) boost the base score but are never independent entry signals.

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

**Proteus** (LIVE since 2026-07-04) — The discretionary experiment: a
complete investor with no frozen strategy, hunting the ENTIRE
US-listed universe (all equities, ADRs, and the full ETF window onto
commodities/rates/currencies/countries/vol) on a real ~$2,000 sleeve
inherited from Midas (operator directive; prereg amendment #3 —
granted before his first paper trade, so the experiment transferred
uncontaminated; the flat $10k paper book was retired at birth).
Long-only at the broker (inverse ETFs express short views), no
leverage, no options. **Operator mandate (revised 2026-07-04): every
position must earn its place TODAY** — one full session daily, every
red position re-underwritten same-day (kill or consciously re-commit,
never drift). The green-day rate is tracked vs SPY's own base rate as
a DIAGNOSTIC only, never a target — the original "green book, every
day" framing was demoted same-week because a daily-green target
incentivizes selling winners early and nursing losers, contaminating
the experiment. Every decision is
journaled with a falsifiable prediction and graded without mercy
(docs/proteus_prereg.md). Checkpoint at 30 closed trades or
2027-01-15: validation keeps the sleeve, refutation retires him and
returns the capital to the treasury. Owns only `cache/proteus_*`.

**Plutus** (LIVE from 2026-07-06 — conscious operator override) — The
net-issuance capital-return god: holds the 50 large-caps shrinking their own
share count fastest (SF1 trailing-4Q weighted-shares change, top-500
universe), equal-weighted, **quarterly rebalance only** — no intra-quarter
churn. This is the frozen `gauntlet_v2_fundamentals` net-issuance-low N50
LARGE spec, the house's FIRST and only SUPPORTED backtest (in-sample DSR +
two-regime holdout + 2× cost + parameter-cliff). Launched by a **conscious
override** (docs/plutus_launch_override.md), the Proteus precedent: real
money on a strategy that is supported but NOT yet forward-validated — two
house laws overridden in writing, with honest caveats on the record
(net-issuance only ties SPY equal-weight; a famous decay-prone anomaly;
multiple-testing counter at 141). He trades the pure mechanical spec — the
LLM buyback-quality overlay stays a PAPER A/B in the lab, never touching his
live book. Funded by Delphi's retiring ~$2,000 sleeve via the 2026-07-06
transition of power (liquidate → sweep; his first settled-cash rebalance is
the launch, T+1 after the sweep). 40% drawdown breaker; `PLUTUS_LIVE`
defaults FALSE (operator arms it). Checkpoint at 4–8 graded forward quarters
or a breaker trip: live grades — basket excess vs SPY — decide whether he
keeps the capital. Owns only `cache/plutus_*`.

**Transition of power (2026-07-06).** The Monday open is a portfolio
*rearrange*, not a launch-day scramble: retiring god sleeves are liquidated
to cash to create the buying power that funds the new regime. Delphi → Plutus
is the first such transfer; the operator may free more capital for additional
new gods as they clear the bar (TBD). No new god buys with unsettled
proceeds — first purchases wait for T+1 settlement.

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

### Cohort Model (implemented 2026-06-29)

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
| Daily | `/proteus` | One full discretionary session on his live sleeve (research-only when markets are closed or funding pending) |
| Trading days | `/plutus` | Net-issuance capital-return god (LIVE 2026-07-06). Self-gates to a once-per-quarter rebalance; monitoring-only otherwise. Research-only until funded by the Delphi sweep and the cash settles |
| Weekly (weekend) | `/proteus-lab` | Strategy lab: invent → prereg → backtest (bias checklist enforced) → paper forward test. Never live money |

### Key Files (all in `cache/`, persisted to `claude/live`)

| File | Owner | Purpose |
|------|-------|---------|
| `oracle_sleeve.json` | oracle | Cash, positions, cooldowns, peak equity |
| `oracle_cohort.json` | oracle | Active cohort: positions, entry prices, thesis snapshots, review date |
| `oracle_dossiers.json` | oracle | Full dossier pool (target: 60-80 across 8+ sectors) |
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
| `achilles_sleeve.json` | achilles | Achilles' sleeve |
| `midas_sleeve.json` | midas | RETIRED record: final cash swept to Proteus 2026-07 (kept as guard file) |
| `midas_scan.json` | midas | Weekend scan finalists (research-only; feeds `/midas-ghost`) |
| `midas_ledger.jsonl` | midas | Every order placed (historical; for reconcile) |
| `midas_curve.json` | midas | Equity timestamps (historical) |
| `proteus_sleeve.json` | proteus | LIVE book: cash, contributed_cash, positions, closed trades |
| `proteus_journal.jsonl` | proteus | Append-only decision record (validated writer — the only door to the book) |
| `proteus_ledger.jsonl` | proteus | Every broker order placed (for reconcile) |
| `proteus_curve.json` | proteus | Equity marks vs SPY (green-day rate reported as diagnostic, never a target) |
| `proteus_beliefs.md` | proteus | His living mind: worldview, watchlist, open theses, lessons |
| `proteus_lab.json` | proteus | Strategy lab registry: hypothesis → prereg → backtest → forward test, bias checklists |
| `proteus_lab_ghost_ledger.json` | proteus | Paper forward-test positions for lab strategies (shared.ghost engine) |
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
- God env vars: `ORACLE_LIVE=true`, `DELPHI_LIVE=true`, `ACHILLES_LIVE=true`,
  `NEMESIS_LIVE=true`, `PROTEUS_LIVE=true`, `MIDAS_LIVE=false` (live retired
  2026-07-04), and `PLUTUS_LIVE=false` (defaults FALSE — the operator arms it
  to launch Plutus at the 2026-07-06 transition; `.claude/settings.json` sets
  NEMESIS/PROTEUS/MIDAS/PLUTUS). Delphi's `DELPHI_LIVE` stays as-is only for
  the wind-down; her retirement close-out runs regardless of the gate.
- If any is not `"true"`, that god runs in paper mode (no broker orders).
- `KILL_SWITCH` file triggers immediate liquidation of all god positions.
