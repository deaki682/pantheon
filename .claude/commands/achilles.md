# /achilles — PEAD earnings-season basket

Event-driven, short-horizon. Achilles harvests **Post-Earnings Announcement
Drift**: after a company beats and the market *rewards* it, the stock tends to
keep drifting up for days. The edge is thin and statistical, so Achilles holds
a **diversified equal-weighted basket** (up to `MAX_POSITIONS`, currently 12),
never one all-in bet — that's what lets the drift average out over single-name
noise and what makes the strategy validate in months instead of years.

Only trades during the four ~6-week earnings windows (`achilles.season`).
Sits in cash off-season.

## The two rules that matter most

1. **Trade the reaction, not the headline.** A beat the market *sold* (gap up,
   close red) is a *negative* reaction — the drift runs down, not up. Achilles
   only goes long a beat with a confirmed **positive** post-report reaction
   (`earnings.is_rewarded_beat`). Never buy a sold beat because "EPS beat."
2. **Basket, not one bet.** Fill slots with the best rewarded beats, equal-
   weighted. One slot per symbol. Diversification is the risk control.

## Steps

0. **Hydrate.** `pantheon.hydrate()`.

1. **Safety check.** Refuse if `KILL_SWITCH` exists — liquidate the whole basket
   (`sleeve.liquidate(marks, today)`) and stop. Then `shared.guards.is_live("achilles")`:
   if `ACHILLES_LIVE` is not exactly `"true"`, run **paper mode**. **CRITICAL:
   in paper mode compute everything and print what WOULD happen, but do NOT
   place orders, do NOT update the sleeve, do NOT append to the ledger, and do
   NOT persist.** Paper mode is read-only.

2. **Season gate.** `achilles.season.is_earnings_season(today)`. If not in a
   window, do exits/management only (step 8) — no new entries — then persist.

3. **Restore.** Load `cache/achilles_sleeve.json` (or `AchillesSleeve(initial_cash=1000)`).
   Legacy single-position sleeves migrate automatically on load.

4. **Halt + settlements.** `sleeve.check_halt(marks)` (40% drawdown → halt, no
   new opens). `sleeve.process_settlements(today)`.

### Find rewarded beats (only if season + slots open)

5. **Recent reporters.** `get_earnings_calendar(start_date=today, days=-5)` — the
   names that reported in the last ~5 trading days (the drift window is still
   open). For each, `get_earnings_results` → actual vs estimate.
   `achilles.earnings.compute_surprise(actual, estimate)`; keep
   `is_actionable_beat` (3–500% surprise, small/mid-cap).

6. **Confirm the reaction (the gate).** For each beat, fetch daily historicals
   (`get_equity_historicals`) and compute the post-report reaction:
   `achilles.earnings.reaction_return(pre_report_close, post_report_close)`.
   Keep only `is_rewarded_beat(surprise, reaction_pct)` — positive surprise AND
   positive reaction. Drop sold beats and beats whose reaction can't be verified.
   Attach `reaction_pct`, confirming signals (revenue beat, guidance raised,
   short float, insider pre-buy), and `market_cap` to a `BeatCandidate`.

7. **Rank into the basket.** `achilles.scanner.rank_beats(candidates, top_n=sleeve.open_slots())`
   — scores by surprise magnitude + confirming signals, drops unconfirmed
   reactions (`require_reaction=True`), returns the top rewarded beats to fill
   the open slots. **The 'already fired' guard (`max_reaction_pct`, default
   0.20):** a beat whose initial post-report reaction already ran past the cap
   is dropped — the drift is spent (PEAD is a moderate-surprise phenomenon;
   extreme initial reactions revert, they don't drift). Enter moderate
   reactions, never a name that already popped hard. The exact cap is a
   hypothesis the Achilles gauntlet will refine.

### Execute

8. **Exits first.** `sleeve.due_exits(quotes, today)` → for each (symbol, reason)
   place a market sell, `sleeve.exit(symbol=…, price=…, today=today, reason=reason)`,
   append to `cache/achilles_ledger.jsonl`. Hard stop takes precedence over the
   5-day time stop. A hard-stopped name gets a 4-week cooldown automatically.

9. **Pre-trade sanity check.** Fetch broker positions, `filter_broker_to_gods`,
   `shared.guards.pre_trade_check(...)`. If any symbol is out of sync, halt and
   run `/oracle-reconcile` before opening.

10. **Enter the basket.** `size = sleeve.target_dollars(marks)` (equal weight =
    equity / MAX_POSITIONS), clamped to available cash. For each ranked beat with
    an open slot: `shares = size / price`, check `shared.guards.already_placed_today`,
    place the market buy, `sleeve.enter(symbol=…, shares=…, price=…, today=today,
    score=…, surprise_pct=…, reaction_pct=…, revenue_beat=…, guidance_raised=…,
    short_float_pct=…)`, append to the ledger. Stop when slots are full.

11. **Update peak + persist.** `sleeve.update_peak(marks)`, save sleeve, append
    curve point, `pantheon.persist("achilles", …)`.

## Exit rules (per position)

| Condition | Trigger | Action |
|-----------|---------|--------|
| -8% from entry | `check_stop(sym, px)` | Market sell, 4-week cooldown |
| 5 trading days elapsed | `should_time_stop(sym, today)` | Market sell at close |
| 40% basket drawdown | `check_halt()` | Halt, no new opens |
| Kill switch | `KILL_SWITCH` | Liquidate the whole basket |

## What /achilles does NOT do

- Enter outside an earnings window, or off a sold/unconfirmed beat.
- Hold the same symbol in two slots, or exceed MAX_POSITIONS.
- Go all-in on one name — the basket IS the strategy.
- Add a position because the broker holds it (sleeve is authoritative).

## Calibration

The basket produces ~10–15 graded trades per season, so Achilles reaches a
statistically meaningful sample far faster than a one-bet-a-week god. Key reads:
`hit_rate`, `avg_return`, `hit_rate_by_surprise_bucket` (is the drift monotonic
in surprise size?), and `confirming_signal_stats` (do revenue/guidance/squeeze
confirmations actually lift the hit rate?). Capital stays at $1,000 until 30+
graded trades show a real edge net of costs — costs are the main threat on
small-caps, so watch slippage.
