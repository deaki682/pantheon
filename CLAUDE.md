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

**Delphi** — Large-cap momentum compounder. Ranks a fixed 118-name universe
by 65-day price momentum, holds the top 10 equal-weighted, exits when
price breaks below the 20-day moving average. Rebalances on each run.
5 LLM decision points per run (exit, entry, sizing, risk budget, universe
curation) with override budgets to prevent second-guessing the mechanical
system. Capital at $2,000; 7-day cooldown after selling a name.

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
leverage, no options. **Operator mandate: a green book, every day** —
one full session daily, every red position re-underwritten same-day,
green-day rate tracked vs SPY's own base rate. Every decision is
journaled with a falsifiable prediction and graded without mercy
(docs/proteus_prereg.md). Checkpoint at 30 closed trades or
2027-01-15: validation keeps the sleeve, refutation retires him and
returns the capital to the treasury. Owns only `cache/proteus_*`.

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
| As needed | `/oracle-research` | Build dossiers to maintain pool of 60-80 |
| At cohort review (~12 months) | `/oracle` | Grades all calls, closes cohort, selects new cohort from pool |
| Weekly (weekend) | `/midas-scan` | Research-only universe scan feeding the `/midas-ghost` A/B (Midas live retired 2026-07-04) |
| Daily | `/proteus` | One full discretionary session on his live sleeve (research-only when markets are closed or funding pending) |
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
| `delphi_sleeve.json` | delphi | Delphi's sleeve |
| `delphi_ledger.jsonl` | delphi | Delphi's order ledger |
| `achilles_sleeve.json` | achilles | Achilles' sleeve |
| `midas_sleeve.json` | midas | RETIRED record: final cash swept to Proteus 2026-07 (kept as guard file) |
| `midas_scan.json` | midas | Weekend scan finalists (research-only; feeds `/midas-ghost`) |
| `midas_ledger.jsonl` | midas | Every order placed (historical; for reconcile) |
| `midas_curve.json` | midas | Equity timestamps (historical) |
| `proteus_sleeve.json` | proteus | LIVE book: cash, contributed_cash, positions, closed trades |
| `proteus_journal.jsonl` | proteus | Append-only decision record (validated writer — the only door to the book) |
| `proteus_ledger.jsonl` | proteus | Every broker order placed (for reconcile) |
| `proteus_curve.json` | proteus | Equity marks vs SPY (green-day scoreboard) |
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
  `NEMESIS_LIVE=true`, `PROTEUS_LIVE=true`, and `MIDAS_LIVE=false` (live
  retired 2026-07-04; `.claude/settings.json` sets the last three).
- If any is not `"true"`, that god runs in paper mode (no broker orders).
- `KILL_SWITCH` file triggers immediate liquidation of all god positions.
