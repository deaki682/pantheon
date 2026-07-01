# /catalyst — Weekly Catalyst Engine (research only)

A standalone research/screening tool, **fully disconnected from the gods**. It
maps the coming week's forecastable events, subtracts what the options market
has already priced in, and surfaces the residual for a human to judge.

**Hard rules (non-negotiable):**
- NEVER places a trade. No sleeve, no ledger, no broker orders.
- Imports NOTHING from oracle/midas/delphi/achilles and shares no state.
- Does NOT `pantheon.persist` to `claude/live`. Its output lives in its own
  namespace (`cache/catalyst_calendar.json`) and is for review only.
- The final layer is human judgment. The engine ranks; the human decides.

The one idea: **edge = expected_outcome − what_the_market_already_expects.** A
row is only interesting when your view *disagrees* with the priced move.

## Steps

### Phase 1 — the calendar

1. **Window.** `catalyst.calendar.next_week_window()` → `[today, today+7]`.

2. **Earnings (dense, tractable).** `get_earnings_calendar(start_date=today, days=7)`
   for market-wide coverage. `catalyst.calendar.normalize_earnings(rows)` — dedups,
   drops already-reported names, downweights unverified dates.

3. **Other catalyst connectors (extensible, add as available).** Normalize each
   into the same schema via `catalyst.calendar.make_event(...)`:
   - **Econ** — CPI / FOMC / jobs / PCE for the week (WebFetch an economic
     calendar). Market-wide, `is_binary=False`, `event_type="econ"`.
   - **FDA / PDUFA** — biotech decisions/readouts (WebFetch a PDUFA tracker).
     `is_binary=True`, `event_type="fda"`.
   - **Index rebal / lockups / ex-div** — SEC filings / IPO lockup schedules.
   Skip a connector cleanly if its source is unavailable — never fabricate events.

4. **Build.** `catalyst.calendar.build_calendar(earnings, econ, fda, …, start=start, end=end)`
   → one sorted table (soonest first, then confidence). This alone is useful.

### Phase 2 — the expectations overlay

5. **For each name with liquid options, attach the priced move:**
   - Spot: `get_equity_quotes([ticker])`.
   - `get_option_chains(underlying_symbol=ticker)` → expirations. Pick the
     nearest expiry on/after the event date.
   - `get_option_instruments(chain_symbol=ticker, expiration_dates=<expiry>, type=call/put)`
     for strikes near spot (both call and put).
   - `get_option_quotes(instrument_ids=[...])` → marks (or bid/ask mid).
   - Pass `[{strike, type, expiration, mark|bid/ask}]` to
     `catalyst.expectations.implied_move_from_chain(spot, contracts, event_date)`.
     Set `event["expected_priced_move_pct"]` from the result (and record expiry/strike).
   - **Illiquid names have no usable options → leave the field None and mark N/A.**
     Do not invent a number. Microcap "implied moves" are fantasy.

6. **The residual is the point.** For any name where you form your own view of
   the move, `catalyst.expectations.edge_vs_priced(my_expected_move_pct,
   priced_move_pct, direction)` gives the signed surprise vs what's priced.
   This is a field for human reasoning, not an automated signal.

### Output

7. **Write** `cache/catalyst_calendar.json` (own namespace — NOT persisted to
   claude/live) and print the review table: ticker, event, date/timing,
   days_until, binary?, priced move %, consensus. Sorted soonest-first.

8. **Human review.** Flag the handful where a real catalyst + a gap-versus-priced
   expectation line up. That shortlist is the deliverable — nothing auto-executes.

## Deliberately NOT built yet (discipline)
- No predictive model, no backtest, no ranking "score." Those are later phases
  and the blueprint is emphatic: the modeling is the fun part and the least
  important. Prove the calendar + expectations are useful first.
- No sentiment/buzz layer yet (Phase 3) — and when added, it's a volatility flag
  gated by market cap and a manipulation filter, never a directional signal.

## Why disconnected from the gods
The gods trade mechanically off their own signals. This is an edge-adjacent
research tool that concentrates human attention on forecastable events. Keeping
it isolated means it can never touch a god sleeve, and a bug here can never place
an order.
