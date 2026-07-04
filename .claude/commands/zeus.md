# /zeus — hourly dispatcher

Zeus is a coordinator, not a strategist. It wakes once per hour, checks
what's due, and dispatches the relevant gods and ghosts. It does not
think, trade, or override any god's logic.

## Dispatch table

| Skill | Condition | Notes |
|-------|-----------|-------|
| `/trinity` | Market hours (9:30–16:00 ET, weekdays) | Dashboard refresh with live quotes |
| `/midas-scan` | Weekend AND `should_run("cache/midas_cadence.json", "scan", 5)` | Heavy universe scan → top 10 → `cache/midas_scan.json`. Cadence guard = once per weekend, not every hour. **Research-only since 2026-07-04** — output feeds `/midas-ghost` (the A/B race), never a live entry |
| `/nemesis` | Weekend AND `should_run("cache/nemesis_cadence.json", "scan", 5)`, OR weekday if live position open | Weekend: full pass (pipeline scan + Form 10 reading + ghost entries + gated live sleeve; cadence guard = once per weekend). Weekday with live positions: exits-only pass — the runbook short-circuits, same pattern as `/midas` stop checks |
| `/midas` | **WIND-DOWN ONLY** (live retired 2026-07-04, operator directive): weekday, and ONLY while `cache/midas_sleeve.json` still has a `position` or `cache/midas_cadence.json` has a `pending_exit_order_id` | Reconcile the queued DAKT sell (order `6a473615`) when it fills, then sweep ALL cash to Proteus's sleeve (see midas.md wind-down). NO new entries, ever. Once the sweep is done, never dispatch `/midas` again |
| `/oracle` | `should_run("cache/oracle_cadence.json", "research", 3)` | Every 3 days |
| `/delphi` | Market hours AND `is_trading_day(today)` AND NOT `ran_today("cache/delphi_cadence.json", "trade")` | ONE trade pass per trading day (guard added 2026-07-04 after hourly churn); holidays excluded. Skip entirely if already traded today — Delphi's signals are daily-bar, hourly re-runs only trade noise |
| `/achilles` | `is_earnings_season(today)` | Only during 4 earnings windows/year |
| `/oracle-screen` | `should_run("cache/oracle_cadence.json", "screen", 90)` | Quarterly heavy scan (~60 min) |
| `/oracle-ghost` | After `/oracle` runs | Paper shadow |
| `/delphi-ghost` | After `/delphi` runs | Paper shadow |
| `/achilles-ghost` | After `/achilles` runs (earnings season only) | Paper shadow |
| `/midas-ghost` | Market-hours weekdays, once per day (`should_run("cache/ghost_midas_cadence.json", "session", 1)`) | Paper shadow — the live-vs-legacy A/B race. Survives Midas's live retirement; consumes the weekend `/midas-scan` finalists directly |
| `/proteus` | `should_run("cache/proteus_cadence.json", "session", 1)` — one full session per day, any day (operator mandate 2026-07-04: his purpose is a green book every day, so he hunts every day; weekends he researches with markets closed) | **LIVE since 2026-07-04** (operator directive): trades the real sleeve funded from Midas's retired capital. Until `proteus_sleeve.json` shows `pending_funding: null`, sessions are research-only |
| `/proteus-lab` | Weekend AND `should_run("cache/proteus_cadence.json", "lab", 7)` | Strategy lab (operator mandate 2026-07-04): invent/pre-register/backtest/forward-test new strategies. PAPER ONLY — never a broker order |

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores `cache/`.

1. **Read the clock.** Get today's date (UTC), day of week, and current
   time in US/Eastern. Determine:
   - `is_weekday` — Monday through Friday
   - `is_market_hours` — 9:30–16:00 ET on weekdays
   - `is_weekend` — Saturday or Sunday
   - `is_monday` — for Midas entry
   - `today` — ISO date string

2. **Check cadence files.** Read the cadence/state files to decide what's due:
   ```python
   from oracle.calendar import should_run
   from achilles.season import is_earnings_season
   import json, os

   oracle_due = should_run("cache/oracle_cadence.json", "research", 3)
   screen_due = should_run("cache/oracle_cadence.json", "screen", 90)
   midas_scan_due = should_run("cache/midas_cadence.json", "scan", 5)
   earnings_season = is_earnings_season(today)

   # Midas wind-down (live retired 2026-07-04): dispatch /midas ONLY to
   # reconcile the final queued exit and sweep cash to Proteus.
   midas_sleeve, midas_cadence = {}, {}
   if os.path.exists("cache/midas_sleeve.json"):
       with open("cache/midas_sleeve.json") as f:
           midas_sleeve = json.load(f)
   if os.path.exists("cache/midas_cadence.json"):
       with open("cache/midas_cadence.json") as f:
           midas_cadence = json.load(f)
   midas_wind_down = bool(midas_sleeve.get("position")) or bool(
       midas_cadence.get("pending_exit_order_id"))

   # Check if Nemesis holds live positions (for weekday exit checks)
   nemesis_sleeve = {}
   if os.path.exists("cache/nemesis_sleeve.json"):
       with open("cache/nemesis_sleeve.json") as f:
           nemesis_sleeve = json.load(f)
   nemesis_has_position = bool(nemesis_sleeve.get("positions"))
   ```

3. **Build the dispatch list.** Apply the conditions from the table above:

   **Always (market hours, weekdays):**
   - `/trinity` — dashboard refresh

   **Conditional:**
   - `/delphi` — if market hours AND `oracle.calendar.is_trading_day(today)` (weekday + not an NYSE holiday) AND NOT `oracle.calendar.ran_today("cache/delphi_cadence.json", "trade")`. One trade pass per trading day — if she already traded today, don't dispatch her at all (2026-07-04 churn fix)
   - `/midas-scan` — if weekend AND `midas_scan_due` (the cadence guard fires it once per weekend, not every hour). Research-only: feeds the ghost A/B
   - `/nemesis` — if weekend AND `should_run("cache/nemesis_cadence.json", "scan", 5)` (same once-per-weekend cadence-guard pattern as `/midas-scan`), OR weekday when `nemesis_has_position` (live position management: exits-only pass — the runbook handles the short-circuit, mirroring the `/midas` weekday stop checks)
   - `/midas` — ONLY if `midas_wind_down` on a weekday (reconcile the final exit + sweep to Proteus). Live retired 2026-07-04; there are no new entries and no Monday dispatch once the sweep completes
   - `/oracle` — if `oracle_due`
   - `/achilles` — if `earnings_season` and market hours
   - `/oracle-screen` — if `screen_due` (runs before `/oracle` since oracle uses screen output)
   - `/proteus` — if `should_run("cache/proteus_cadence.json", "session", 1)` (one full session per day, every day — the daily-green mandate). LIVE since 2026-07-04: he trades his own real sleeve (and only his own). Research-only until his sleeve's `pending_funding` clears.
   - `/proteus-lab` — if weekend AND `should_run("cache/proteus_cadence.json", "lab", 7)` (once per weekend; paper-only strategy research; run it after `/proteus` since both write `proteus_cadence.json`)
   - `/midas-ghost` — market-hours weekdays, once per day (`should_run("cache/ghost_midas_cadence.json", "session", 1)`): opens paper entries when fresh finalists exist, marks/grades daily

   **Ghosts (run after their parent):**
   - `/oracle-ghost` — after `/oracle`
   - `/delphi-ghost` — after `/delphi`
   - `/achilles-ghost` — after `/achilles`
   - `/midas-ghost` — after `/midas`

4. **Dispatch.** Run the due skills. Independent gods can run in parallel
   since they never touch each other's sleeves. Ghosts run after their
   parent god completes (they may depend on freshly-written cache files
   like `midas_dossiers.json`).

   **Parallel group 1** (independent gods, run together):
   - `/oracle-screen` (if due — run first since `/oracle` uses its output)
   - `/delphi`
   - `/achilles`
   - `/midas-scan` (weekend) or `/midas` (weekday wind-down only, while `midas_wind_down`)
   - `/nemesis` (weekend if due — full pass; or weekday with `nemesis_has_position` — exits-only. Shares no state with the other gods)
   - `/proteus` (if due — live; owns only `cache/proteus_*`, so he parallelizes safely with everyone. EXCEPTION: on the day the Midas wind-down sweep runs, run `/midas` BEFORE `/proteus` — the sweep writes Proteus's funding)

   **Parallel group 2** (depends on group 1):
   - `/oracle` (needs screen output if screen just ran)

   **Parallel group 3** (ghosts, after their parents):
   - `/oracle-ghost`, `/delphi-ghost`, `/achilles-ghost`
   - `/midas-ghost` (parentless since the live retirement — runs on its own daily cadence)

   **Last:**
   - `/trinity` (reads all sleeves, so runs after everything else)

   Skip any skill whose condition wasn't met. If nothing is due, log
   "Zeus: nothing due this hour" and exit.

5. **Log.** Print a summary of what ran and what was skipped. No persist
   needed — Zeus has no state of its own. Each god persists its own files.

## Scheduling

Zeus runs as a **hourly routine**. Set up via Claude Code's routine/cron
system to fire once per hour during waking hours (or 24/7 if you want
weekend `/midas-scan` runs to fire automatically).

Suggested cron: every hour, 7 days a week. Zeus itself decides what's
due — the cron just wakes it up.

## Hard rules

- Zeus does NOT trade. It only invokes skills.
- Zeus does NOT override any god's logic or skip conditions.
- Zeus does NOT persist any state. Each dispatched skill handles its own persistence.
- If a skill fails, log the error and continue with the next skill. One god's failure does not block the others.
- Weekend dispatches: only `/midas-scan` (heavy universe scan, research-only), `/nemesis` (spinoff pipeline, gated live sleeve), `/proteus` (discretionary god — daily cadence includes weekends as research days; markets closed means no orders), and `/proteus-lab` (weekly strategy lab, paper only) run. No `/trinity`, `/delphi`, `/achilles`, or `/midas` on weekends.
- Midas is retired from live trading (2026-07-04, operator directive — capital reallocated to Proteus). `/midas` exists only to finish the DAKT wind-down; `/midas-scan` and `/midas-ghost` continue as the convergence A/B research program.
