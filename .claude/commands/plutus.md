# /plutus — the net-issuance capital-return god (LIVE 2026-07-06)

Plutus is the god of wealth, and his spine is the oldest honest edge on the
tape: **companies that are shrinking their own share count.** Net issuance is
the house's first and only SUPPORTED backtest (`gauntlet_v2_fundamentals`):
survived in-sample DSR, a two-regime holdout touched once, a 2× cost rerun,
and a parameter-cliff check. On that spine the operator bolted the **deluxe
stack** (2026-07-04, "the deluxe package, even if risky"): a second factor, an
LLM quality brain, and a conviction/cap-weight tilt.

He is the house's first **conscious-override launch** — real money on a
strategy that is supported but NOT forward-validated — and the deluxe
additions push that override further: none of the three is validated at all
(the LLM overlay has zero grades). Read `docs/plutus_launch_override.md`
(including the deluxe amendment) before touching this book — the operator's
signed record of which laws were overridden and the honest caveats
(net-issuance only TIES SPY equal-weight; a famous decay-prone anomaly; the
deluxe stack widens both tails and only *maybe* shifts the mean; counter 141).
Plutus exists to find out, with live grades, whether a gauntlet-supported
factor — steered by an LLM brain and stacked tilts — beats both SPY and its
own pure control, or just adds variance.

## What Plutus trades — the DELUXE STACK (operator directive, "even if risky")

The operator directed the full deluxe package on 2026-07-04. Plutus does NOT
trade the bare factor; he trades a three-layer pipeline. **Read the deluxe
amendment in docs/plutus_launch_override.md first** — none of these three
additions is forward-validated, they are a deliberate, documented over-reach,
and they widen both tails (the honest read: they buy variance and only *maybe*
buy mean). The pure spec stays tracked as the CONTROL so we can grade whether
the deluxe stack earned its risk.

The quarterly pipeline (all in `plutus.strategy` / `plutus.overlay`):

1. **Two-factor composite** — `composite_basket(signal_date)`. Net-issuance-low
   is the spine (Plutus's validated identity); gross-profitability (the OTHER
   gauntlet survivor) enters as an equal-ranked quality blend. Returns ~50
   candidates by average factor rank. Universe = top-500 by marketcap; both
   factors strictly `datekey <= signal_date` (point-in-time, survivorship-free
   Sharadar). The blend itself is unvalidated — a reasonable combination of two
   supported survivors, not a gauntleted construct.
2. **LLM quality overlay (LIVE)** — the session reads each candidate's buyback
   quality (funding source, valuation discipline, business health,
   sector-appropriate — do NOT penalize banks for deposit "debt") and returns a
   `plutus.overlay.QualityRead` per name: `keep` (prune financed/expensive
   buybacks), `conviction` (0.5–2.0), and a one-line `rationale`. This is the
   Lens-B arm-L judgment, now on real money. Prunes ~50 → ~24–40 keepers. The
   read IS the experiment; journal every keep/drop.
3. **Conviction / cap-weight tilt** — `overlay.apply_overlay(candidates, reads,
   marketcaps)` turns keeps + convictions into bounded target weights:
   conviction-tilted with a `cap_blend` cap-weight lean (default 0.5, chasing
   SPY which is cap-weighted), per-name cap ~6% (floats up to ~2× equal on
   small baskets so the book stays fully invested), 2% cash floor. This is the
   lever most likely to just add drawdown — it is a measured regime bet.

**Rebalance = quarterly ONLY.** Between quarter-ends Plutus monitors and marks;
re-running the pipeline intra-quarter is forbidden (the churn that sank Delphi).
Execution prices come from the live broker tape — never Sharadar closeadj.

**The CONTROL (mandatory, never skip).** Every rebalance also computes the pure
`quarterly_basket(signal_date)` — the frozen validated N50 equal-weight spec,
the SAME code the paper forward test (`run_forward_net_issuance.py`) tracks —
and records it in the decision log alongside what deluxe actually bought. At
grading we compare live deluxe excess-vs-SPY against the pure control's
excess-vs-SPY: that difference is the only honest measure of whether the LLM +
blend + tilt added anything or just added risk. If deluxe trails pure over a
real sample, the additions are noise and get cut.

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

2. **Compute the deluxe pipeline (once per quarter).**
   ```python
   from plutus.strategy import (composite_basket, quarterly_basket,
                                universe_marketcaps)
   from plutus.overlay import QualityRead, apply_overlay
   caps       = universe_marketcaps(qe)          # {ticker: marketcap}
   candidates = composite_basket(qe, set(caps))  # ~50 two-factor names
   control    = quarterly_basket(qe)             # the pure N50 CONTROL — record, do NOT trade
   ```
   Disclose coverage: if fewer than ~50 candidates come back (stale filings /
   thin coverage), work with what there is and log the count — never backfill
   from a different rule to force a number.

3. **LLM quality read (LIVE — this is the experiment).** For EACH candidate,
   read its buyback quality with the effort the /lab arm-L spec demands (funding
   source, valuation, business health, sector-appropriate — banks' deposit
   "debt" is not leverage). Produce one `QualityRead(symbol, keep, conviction,
   rationale)` per name: `keep=False` prunes financed/expensive buybacks;
   `conviction` 0.5–2.0 sizes the survivors; `rationale` is one line, journaled.
   Use the SAME reasoning you'd record for Arm L in `cache/lab_buyback_quality_ab.json`
   so the live book and the paper A/B stay consistent. If the read keeps
   nothing, sitting in more cash this quarter is a legitimate outcome — log it.

4. **Mark, set equity, weight the book.**
   - Fetch live quotes (`get_equity_quotes`) for every held name, every kept
     candidate, and SPY. `equity = sleeve.equity(marks)`; `sleeve.update_peak(marks)`.
   - `targets = apply_overlay(candidates, reads, caps)` → `{symbol: weight}`
     (conviction-tilted, cap-weight lean, per-name cap, cash floor). Convert to
     dollar targets: `weight * equity`.

### Circuit breaker

Before any buy, `sleeve.check_halt(marks)`. If equity is **40% below peak**
(`HALT_DRAWDOWN`), the breaker trips: `sleeve.halted = True`, place NO new
buys, still process SELLS to de-risk toward the new basket, log the trip, and
leave it for the operator (`docs/plutus_launch_override.md` names the 40%
breaker as a checkpoint trigger). Only an operator reset clears `halted`.

### Execute — sells first, then buys (to the tilted weights)

5. **Rotate to the target weights.**
   - **Sells:** every held name NOT in `targets` is sold in full at market
     (quarterly turnover — names that left the composite or the LLM dropped).
     Also trim any name whose live weight has drifted above its target by more
     than `REBAL_BAND` (20%). `sleeve.sell(sym, shares, px, today)`.
   - **Buys:** for each target name below its dollar target, buy the shortfall —
     but only with `settled_cash` and only tickets above `MIN_TICKET`. Respect
     the `REBAL_BAND`: a name already within 20% of its target weight is left
     alone (no churn on noise). Fractional shares are fine (sub-$2k book,
     ~24–40 names → ~$40–80/name after the tilt).
   - Verify tradability (`get_equity_tradability`) before committing to any
     name; skip and log anything untradable rather than forcing it.
   - Place market orders via `place_equity_order`. Append EVERY order to
     `cache/plutus_ledger.jsonl` via `shared.guards.append_order` (order_id,
     symbol, side, dollars, date) — a ledger row is what
     `filter_broker_to_gods` and reconcile depend on. Every fill updates the
     sleeve with the ACTUAL fill price/quantity (the sleeve records reality;
     if a fill is pending at session end, record the order in the ledger and
     reconcile it next pass).

6. **Decision log + quarter marker.** Append one record per rebalance to
   `cache/plutus_decisions.jsonl` (validated JSONL append — do not hand-write).
   Record the deluxe book, the pure CONTROL, AND the LLM reads, so the deluxe
   stack can be graded against the control every quarter:
   ```json
   {"date": "2026-07-07", "quarter": "2026Q3", "signal_date": "2026-06-30",
    "deluxe_weights": {"AAPL": 0.061, "WFC": 0.045, "...": 0.0},
    "control_basket": ["AAPL", "...50 pure N50 EW names..."],
    "llm_reads": [{"symbol": "EA", "keep": false, "conviction": 1.0,
                   "rationale": "PE 58, buyback financed — drop"},
                  {"symbol": "WFC", "keep": true, "conviction": 1.4,
                   "rationale": "cheap; +debt is deposits not leverage"}],
    "n_candidates": 50, "n_kept": 28, "n_bought": 28, "n_sold": 0,
    "cap_blend": 0.5, "equity": 1912.34, "peak_equity": 1912.34,
    "drawdown": 0.0, "halted": false, "coverage_note": "50/50 candidates priced"}
   ```
   The `control_basket` is what pure net-issuance would have held; at the next
   grading we compare live deluxe excess-vs-SPY to the control's — the honest
   test of whether the LLM + blend + tilt earned their risk.
   Set the persisted `last_quarter` marker to `q` (in `cache/plutus_cadence.json`)
   so the quarter guard in 1b won't re-trade this quarter.

7. **Persist.** `pantheon.persist("plutus", {"cache/plutus_sleeve.json": …,
   "cache/plutus_ledger.jsonl": …, "cache/plutus_curve.json": …,
   "cache/plutus_decisions.jsonl": …, "cache/plutus_cadence.json": …})`.
   Plutus owns only `cache/plutus_*`.

## Strategy parameters (deluxe stack)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Universe | top 500 by marketcap (LARGE) | the validated bucket |
| Factor 1 (spine) | net-issuance-low (SF1 `shareswa`, trailing-4Q change) | the validated metric, point-in-time |
| Factor 2 (blend) | gross-profitability (gp/assets) | the other gauntlet survivor; the quality axis |
| Candidates | ~50 by average factor rank | two-factor composite (unvalidated blend) |
| LLM overlay | keep/drop + conviction 0.5–2.0 | Lens-B arm-L judgment, LIVE (0 grades — the experiment) |
| Positions | ~24–40 kept names | LLM prunes the composite; concentration is deliberate |
| Weighting | conviction × cap-lean (`cap_blend` 0.5) | chases SPY (cap-weighted); a measured regime bet |
| Per-name cap | 6% (floats to ~2× equal on small baskets) | concentration ceiling, never strands cash |
| Cash floor | 2% | minimal drag |
| Rebalance | quarterly only | slow signal; no intra-quarter churn |
| Circuit breaker | 40% drawdown from peak | halts new buys, operator checkpoint |
| CONTROL (paper) | pure N50 equal-weight (`quarterly_basket`) | the frozen validated spec, graded against deluxe |

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
- Rebalance more than once per quarter, or re-compute the pipeline intra-quarter.
- Skip the pure CONTROL — every rebalance records `quarterly_basket` so deluxe
  can be graded against it. Grading the additions is the whole point.
- Let the deluxe additions leak into `quarterly_basket()` (the frozen control)
  or into the paper forward test — those stay pure, always.
- Tune the composite/overlay/tilt on live results mid-stream — a change is a new
  documented decision, not a quiet edit; the checkpoint decides what survives.
- Touch any other god's sleeve, ledger, or cache; personal broker positions
  are invisible (`filter_broker_to_gods`).
- Buy with unsettled cash (good-faith-violation guard) or add a position
  because the broker shows it (the sleeve is authoritative).
