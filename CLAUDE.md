# Pantheon — Autonomous Trading System

Three gods share one Robinhood agentic account (`563854249`), each running
an independent strategy with its own $1,000 sleeve.

## The Gods

**Oracle** — Patient small/mid-cap researcher. Insider-accumulation signal
with 6-18 month horizon. Uses a **cohort model**: selects 8 positions once,
holds ~12 months, exits only on thesis-break. Research runs continuously to
maintain a pool of 60-80 dossiers for the next cohort. Capital starts at
$1,000; scales to $12,000 ceiling after 30+ graded calls prove skill
(alpha_t >= 2.0, monotonic conviction). Realistically needs 4+ cohorts
(~4 years) to accumulate enough graded calls.

**Delphi** — Sector rotator with SPY core-satellite overlay. Rotates into
the strongest SPDR sectors, picks 1-2 stocks per sector, deploys idle cash
into SPY. Rebalances on each run.

**Achilles** — Event-driven, short-horizon. Watches EDGAR filings for
catalysts (guidance changes, insider clusters, activist 13Ds, spinoffs).
Scores events against playbooks, takes small positions with tight exits.
Currently in conservative mode ($1,000 cash, no positions).

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
| `trinity_dashboard.html` | shared | PWA dashboard for all three gods |

### Capital Scaling Gates (`oracle/capital.py`)

Oracle stays at $1,000 until ALL of these are met:
- 30+ graded journal calls (buy/add only)
- alpha > 0 (from factor regression vs MTUM/QUAL/IWM/VTV)
- alpha_t >= 2.0 (statistical significance)
- monotonic conviction (high-conviction calls outperform mid outperform low)

With 8 positions per 12-month cohort, reaching 30 graded calls takes ~4
cohorts. The alpha_t gate requires ~15-20% annual alpha after factors —
achievable only with excellent selection from a large dossier pool.

### Cancelling Unfilled Orders

If a queued order needs to be cancelled before it fills:
1. `cancel_equity_order` at the broker
2. `sleeve.cancel_buy(sym, shares, price)` — reverses the cash deduction
3. `pantheon.persist(god, {sleeve_file: data})` — pushes corrected state

## Account Context

- Robinhood agentic account: `563854249`
- The account holds ~15 personal positions alongside the gods. These
  pre-existing positions are filtered out by `filter_broker_to_gods()`.
- God env vars: `ORACLE_LIVE=true`, `DELPHI_LIVE=true`, `ACHILLES_LIVE=true`
- If any is not `"true"`, that god runs in paper mode (no broker orders).
- `KILL_SWITCH` file triggers immediate liquidation of all god positions.
