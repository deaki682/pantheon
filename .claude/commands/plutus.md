# /plutus — the net-issuance capital-return god (LIVE 2026-07-06)

Plutus is the god of wealth, and his edge is the oldest honest one on the
tape: **companies that are shrinking their own share count.** He holds the
50 large-caps buying back stock (or otherwise reducing weighted shares)
fastest, equal-weighted, and rebalances once a quarter — no more. Net
issuance is the house's first and only SUPPORTED backtest
(`gauntlet_v2_fundamentals`): survived in-sample DSR, a two-regime holdout
touched once, a 2× transaction-cost rerun, and a parameter-cliff check.

He is also the house's first **conscious-override launch**: real money on a
strategy that is supported but NOT yet forward-validated. Read
`docs/plutus_launch_override.md` before touching this book — it is the
operator's signed record of exactly which laws were overridden and why, and
the honest caveats (net-issuance only TIES SPY equal-weight; it is a famous,
decay-prone anomaly; house multiple-testing counter is 141). Plutus exists
to find out, with live grades, whether a gauntlet-supported factor survives
contact with real fills. Nothing in this runbook second-guesses the factor —
his job is to trade the frozen spec faithfully and be graded without mercy.

## What Plutus trades — FROZEN at the validated spec (do NOT tune)

`plutus.strategy.quarterly_basket(signal_date)` — the exact validated
version, and the SAME code the paper forward test
(`run_forward_net_issuance.py`) tracks, so the live book and the forward
test can never drift:

- **Signal date** = the most recent calendar quarter-end.
- **Universe** = top 500 US names by Sharadar DAILY marketcap on/near it.
- **Metric** = trailing-4Q vs prior-4Q change in weighted-average shares
  (SF1 ARQ `shareswa`, strictly `datekey <= signal_date` — point-in-time).
- **Hold** = the 50 lowest (most negative) share-count changers, equal weight.
- **Rebalance** = quarterly ONLY. Between quarter-ends Plutus does nothing
  but monitor and mark. The slow cadence is the design — the intra-day churn
  that sank Delphi is structurally absent here, and re-computing the basket
  intra-quarter would be an untested rule change.

The signal (which names) comes from survivorship-free Sharadar. **Execution
prices come from the live broker tape** — never from Sharadar closeadj.

**The LLM buyback-quality overlay is NOT live.** It runs as a paper A/B in
the lab (`cache/lab_buyback_quality_ab.json`, tended by `/lab`). Plutus's
live book is pure mechanics; the overlay touches nothing here until its own
arm proves out forward.

## Cadence

Zeus dispatches `/plutus` on trading days. The runbook self-gates: it only
REBALANCES when a new quarter-end has arrived and hasn't been traded yet.
Every other pass is monitoring-only (mark equity, check the breaker, check
kill switch). See the quarter guard in step 1b.

## Session liturgy

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live`, restores `cache/`.

0b. **Safety gates (live money — non-negotiable, before anything else).**
   - `shared.guards.kill_switch_active()` → if true, liquidate every
     position at market (`sleeve.liquidate_all(marks, today)` + real sells,
     append each to the ledger), persist, stop.
   - `shared.guards.is_live("plutus")` → if `PLUTUS_LIVE` is not exactly
     `"true"`, this is **PAPER MODE**: compute the target basket and print
     what *would* trade, then stop. **In paper mode do NOT place orders, do
     NOT mutate the sleeve, do NOT append the ledger, do NOT persist.** Paper
     mode is read-only. The operator arms `PLUTUS_LIVE`; the first live
     rebalance IS the launch.
   - **Funding gate.** `PlutusSleeve.load(...)` (see step 2). If
     `sleeve.pending_funding` is set — the Delphi retirement sweep hasn't
     landed yet — the session is research-only: mark nothing to buy, journal
     a decision note that funding is pending, persist only the (unchanged)
     sleeve if you must, stop before any order.
   - **Settled-cash gate (T+1).** Even once funded, do not buy with cash that
     hasn't settled. Delphi's Monday liquidation settles T+1, so the first
     rebalance's buying power is real only from Tuesday. Check
     `get_accounts` for actual settled cash / buying power and size to
     `sleeve.settled_cash(today)`; if the swept proceeds are still unsettled,
     hold and rebalance on the next pass. A skipped day beats a good-faith
     violation.
   - **Pre-trade reconcile.** Before ANY order: fetch broker positions,
     `filter_broker_to_gods(...)`, `pending_shares_from_orders(...)`, and
     `pre_trade_check(...)`. Sleeve > broker (missing shares) is a HALT —
     reconcile before trading. Broker > sleeve is personal overlap, fine.
     And `already_placed_today(ledger, sym, side, today)` to never
     double-place.

1. **Restore.** `from plutus.sleeve import PlutusSleeve`;
   `sleeve = PlutusSleeve.load("cache/plutus_sleeve.json")`. If absent (should
   not happen — it is a guard file created at launch), stop and tell the
   operator; do not silently birth a fresh unfunded sleeve.

1b. **Quarter guard — is a rebalance due?**
   ```python
   from plutus.strategy import (latest_data_date, quarter_end_on_or_before,
                                quarter_label)
   from oracle.calendar import is_trading_day, ran_today
   today = latest_data_date()          # honest 'today' from the SEP tape
   qe = quarter_end_on_or_before(today)
   q  = quarter_label(qe)              # e.g. "2026Q2"
   already = (sleeve_meta_last_quarter == q)   # persisted marker, see step 5
   rebalance_due = is_trading_day(today) and not already
   ```
   - If `not rebalance_due`: **monitoring-only pass.** Fetch quotes for open
     positions + SPY, mark equity, append to `cache/plutus_curve.json`,
     `update_peak`, run `check_halt` (if it trips, process the halt — no new
     buys, log it), persist the sleeve+curve, stop. No basket compute, no
     rotation.
   - If `rebalance_due`: proceed. This is the once-a-quarter trade.

2. **Compute the target basket.** `target = plutus.strategy.quarterly_basket(qe)`
   — the 50 frozen names. Disclose coverage: if fewer than 50 come back
   (stale filings / thin coverage), trade what there is and log the count —
   never backfill from a different rule to force 50.

3. **Mark and set equity.** Fetch live quotes (`get_equity_quotes`) for every
   held name, every target name, and SPY. `equity = sleeve.equity(marks)`.
   `sleeve.update_peak(marks)`.

### Circuit breaker

Before any buy, `sleeve.check_halt(marks)`. If equity is **40% below peak**
(`HALT_DRAWDOWN`), the breaker trips: `sleeve.halted = True`, place NO new
buys, still process SELLS to de-risk toward the new basket, log the trip, and
leave it for the operator (`docs/plutus_launch_override.md` names the 40%
breaker as a checkpoint trigger). Only an operator reset clears `halted`.

### Execute — sells first, then buys (equal weight)

4. **Rotate to the target basket.**
   - **Sells:** every held name NOT in `target` is sold in full at market
     (this is the quarterly turnover — names that stopped shrinking their
     float leave the book). Also trim any name whose weight has drifted
     above the target by more than `REBAL_BAND` (20%). `sleeve.sell(sym,
     shares, px, today)`.
   - **Buys:** target weight is equal, `1/len(target)` of investable equity
     (respecting `CASH_FLOOR` 2%). For each target name not yet at weight,
     buy the shortfall — but only with `settled_cash` and only tickets above
     `MIN_TICKET`. Respect the `REBAL_BAND`: a name already within 20% of its
     target weight is left alone (no churn on noise). Fractional shares are
     fine (sub-$2k book, 50 names → ~$38/name).
   - Verify tradability (`get_equity_tradability`) before committing to any
     name; skip and log anything untradable rather than forcing it.
   - Place market orders via `place_equity_order`. Append EVERY order to
     `cache/plutus_ledger.jsonl` via `shared.guards.append_order` (order_id,
     symbol, side, dollars, date) — a ledger row is what
     `filter_broker_to_gods` and reconcile depend on. Every fill updates the
     sleeve with the ACTUAL fill price/quantity (the sleeve records reality;
     if a fill is pending at session end, record the order in the ledger and
     reconcile it next pass).

5. **Decision log + quarter marker.** Append one record per rebalance to
   `cache/plutus_decisions.jsonl` (validated JSONL append — do not hand-write):
   ```json
   {"date": "2026-07-07", "quarter": "2026Q2", "signal_date": "2026-06-30",
    "n_target": 50, "n_bought": 50, "n_sold": 10, "equity": 1900.12,
    "peak_equity": 1948.03, "drawdown": 0.024, "halted": false,
    "coverage_note": "50/50 names priced"}
   ```
   Set the persisted `last_quarter` marker to `q` so the quarter guard in 1b
   won't re-trade this quarter (store it on the sleeve dict or a small
   `cache/plutus_cadence.json` — whichever the code uses; be consistent).

6. **Persist.** `pantheon.persist("plutus", {"cache/plutus_sleeve.json": …,
   "cache/plutus_ledger.jsonl": …, "cache/plutus_curve.json": …,
   "cache/plutus_decisions.jsonl": …, "cache/plutus_cadence.json": …})`.
   Plutus owns only `cache/plutus_*`.

## Strategy parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Universe | top 500 by marketcap (LARGE) | the validated bucket |
| Signal | trailing-4Q net share-count change (SF1 `shareswa`) | the validated metric, point-in-time |
| Positions | 50 equal-weight (~2%/name) | the validated N50 basket; diversification IS the edge for a thin factor |
| Rebalance | quarterly only | slow signal; no intra-quarter churn |
| Per-name cap | 5% | safety ceiling; equal-weight sits far below it |
| Cash floor | 2% | minimal drag |
| Rebalance band | 20% drift | avoids churning on noise |
| Circuit breaker | 40% drawdown from peak | halts new buys, operator checkpoint |

## The checkpoint (this launch is not permanent license)

Graded like every god (`docs/plutus_launch_override.md`). At the forward
test's first meaningful readings (4–8 graded quarters) OR a 40% breaker
trip, the operator revisits: the LIVE grades — basket excess vs SPY, not the
backtest — decide whether Plutus keeps the capital. Negative forward excess
retires him to the ledger with the answer, capital back to the treasury, the
same deal Proteus and Delphi got. The ledger row will say plainly: launched
live, unvalidated, on a conscious operator override.

## What /plutus does NOT do

- Place any order when `PLUTUS_LIVE != "true"`, the kill switch is up, the
  funding gate is open (sweep not landed), cash is unsettled, or
  `pre_trade_check` failed.
- Rebalance more than once per quarter, or re-compute the basket intra-quarter.
- Tune, improve, or override the frozen spec — improvements are separate lab
  slugs with their own forward tests, never a live edit here.
- Trade the LLM buyback-quality overlay with real money (paper A/B only).
- Touch any other god's sleeve, ledger, or cache; personal broker positions
  are invisible (`filter_broker_to_gods`).
- Buy with unsettled cash (good-faith-violation guard) or add a position
  because the broker shows it (the sleeve is authoritative).
