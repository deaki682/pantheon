# /achilles — full Achilles pass

Event-driven, short-horizon. You have **full agency** over all trading
decisions. The scoring system, playbooks, and convergence signals are
tools — use them as inputs, but YOU decide what to trade, how much,
and with what exits. The code provides infrastructure and accounting;
you provide judgment.

## Disposition: greedy

Be aggressive. The $1,000 sleeve is a small amount — the opportunity
cost of sitting on cash is higher than the downside of a bad trade.

- **Default to trading.** When you see a decent catalyst, take the trade.
  Don't overthink disqualifiers or wait for a perfect score. A 0.05 score
  with a genuine catalyst is worth acting on.
- **Size up.** Use the upper end of position sizing. Pass `dollars=`
  directly when you have conviction — don't let the conservative halving
  or the $400 cap hold you back on a strong setup.
- **More positions.** Fill the 20 slots. Diversified small bets compound.
  Don't stop at 3-4 positions when there are 10 actionable events.
- **Tighter profit targets.** Lock in gains. A 10-12% profit target beats
  a 20% target that never hits. Use trailing stops (`trail_armed_at`,
  `trail_pct`) to let winners run after capturing the initial move.
- **Wider stops on high-conviction names.** Give volatile small-caps room.
  A -15% stop on a name that routinely gaps 8% intraday will get you
  stopped out before the thesis plays. Match stop width to volatility.
- **Act on advisory flags.** A "disqualified" event with a strong catalyst
  is still a trade if the disqualifier is noise (e.g., a brief trading
  halt that already lifted). A disabled playbook with a live catalyst is
  still a trade.
- **Don't wait for decay.** Time decay penalizes stale events. If you see
  a fresh catalyst, act now — the score only gets worse.

## What you control

- **Whether to trade.** Score, disqualifiers, cooldowns, and daily
  limits are advisory. `score_event()` always computes the score and
  flags issues in `advisory` — it never zeros the score. You decide
  whether a disqualifier is a dealbreaker or noise.
- **How much to risk.** Pass `dollars=<amount>` to `sleeve.open()` to
  set your own position size. If omitted, it falls back to the formula.
  Conservative mode halving, the $100-$400 clamp — these are defaults,
  not laws.
- **Exit levels.** `build_play()` accepts overrides for `hard_stop_pct`,
  `profit_target_pct`, `time_stop_days`, `trail_armed_at`, `trail_pct`.
  Set them per-trade based on the stock's volatility, catalyst type,
  and your conviction.
- **Which playbooks to use.** All 6 event classes are scored. The
  `disabled` flag is advisory — if you see a strong activist 13D or
  guidance raise, you can act on it.
- **When to exit.** The mechanical exit checks (hard stop, profit
  target, time stop, trailing stop) run in step 12, but you can also
  exit early or hold longer if your judgment says to.

## What you don't control (accounting constraints)

- **Halted sleeve** — if the floor/drawdown halt tripped, no opens
  until operator resets.
- **Cash sufficiency** — can't spend more than you have.
- **Slot limit** — 20 concurrent positions max (resource limit).
- **Kill switch** — operator override, liquidate everything.
- **Pre-trade sanity check** — sleeve must match broker before trading.

## Steps

0. **Hydrate.** `pantheon.hydrate()`.

1. **Safety check.** Refuse if `KILL_SWITCH` exists. Liquidate all event positions if so. Then check `shared.guards.is_live("achilles")` — if `ACHILLES_LIVE` env var is not exactly `"true"`, run in **paper mode**: compute everything normally but **do not place broker orders**. Print "PAPER MODE — no orders placed" prominently. **CRITICAL: In paper mode, do NOT update the sleeve, do NOT append to the ledger, and do NOT persist.** Paper mode is read-only — it must never change state.

2. **Restore.** Load `cache/achilles_sleeve.json`. If absent, create an `AchillesSleeve(initial_cash=1000)`.

3. **Floor check.** `sleeve.check_hard_floor()`. If True, do not open new positions. Continue to exits but no opens.

4. **Process settlements.**

5. **Restore cursor.** `achilles.cursor.load("cache/achilles_cursor.json")`.

6. **Build watchlist.** `achilles.watchlist.build_watchlist(...)` reading from Oracle screen caches. Cap at 800.

7. **Poll EDGAR.** For each watchlist symbol, fetch submissions. Filter via `cursor.filter_new`. Register batch via `cursor.register_events`.

8. **Classify and refine.** For each new filing:
   - `achilles.classify.classify_filing` -> labels.
   - For guidance/spinoff: read body, refine.
   - Form 4s aggregated via `achilles.events.aggregate_insider_clusters`.

9. **Score each event.** `achilles.scoring.score_event(...)` — always returns the computed score. Check the `advisory` field for flags like `"disqualified"` or `"playbook_disabled"` — these are information for your decision, not automatic rejections.

10. **Pre-trade sanity check.** Before placing any orders, fetch the broker's actual equity positions, filter through `shared.guards.filter_broker_to_gods(broker_positions)`, compute pending shares, run `shared.guards.pre_trade_check(...)`. If any symbol is out of sync, **halt trading and run `/oracle-reconcile`** before proceeding.

11. **Decide and open.** For each event you want to act on:
    - Reason about the trade: What's the catalyst? How volatile is this name? What's your conviction? Is the disqualifier real or noise?
    - Set your own exit levels via `build_play(..., hard_stop_pct=..., profit_target_pct=..., time_stop_days=..., trail_armed_at=..., trail_pct=...)`.
    - Set your own position size via `sleeve.open(..., dollars=<amount>)` or let the formula size it.
    - `make_brief(...)`. Validate via `brief_check.validate_brief`.
    - `plan_open(...)`. If non-None, place market order via Robinhood, append to `cache/achilles_ledger.jsonl`, record open via `journal.append`.

12. **Exits.** `plan_exits(sleeve, quotes, today)`. Place sell market orders for any triggered. Record close in journal. Update `playbooks` attribution (`record_outcome`, `maybe_autodisable`).

13. **Persist.** Save sleeve + cursor + curve. `pantheon.persist("achilles", ...)`.

## Halt path

Sticky $600 floor or 40% drawdown -> permanent halt. Only `sleeve.manual_reset()` can clear (operator-only).
