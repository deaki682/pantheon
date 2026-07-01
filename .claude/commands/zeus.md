# /zeus — hourly dispatcher

Zeus is a coordinator, not a strategist. It wakes once per hour, checks
what's due, and dispatches the relevant gods and ghosts. It does not
think, trade, or override any god's logic.

## Dispatch table

| Skill | Condition | Notes |
|-------|-----------|-------|
| `/trinity` | Market hours (9:30–16:00 ET, weekdays) | Dashboard refresh with live quotes |
| `/midas` | Weekend (Sat/Sun): pre-scan + pick. Monday: enter. Weekdays if position open: stop checks | Full cycle or stop-check depending on day |
| `/oracle` | `should_run("cache/oracle_cadence.json", "research", 3)` | Every 3 days |
| `/delphi` | Market hours, weekdays | Rebalance check on each run |
| `/achilles` | `is_earnings_season(today)` | Only during 4 earnings windows/year |
| `/oracle-screen` | `should_run("cache/oracle_cadence.json", "screen", 90)` | Quarterly heavy scan (~60 min) |
| `/oracle-ghost` | After `/oracle` runs | Paper shadow |
| `/delphi-ghost` | After `/delphi` runs | Paper shadow |
| `/achilles-ghost` | After `/achilles` runs (earnings season only) | Paper shadow |
| `/midas-ghost` | After `/midas` runs | Paper shadow |

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
   earnings_season = is_earnings_season(today)

   # Check if Midas has an open position (for weekday stop checks)
   midas_sleeve = {}
   if os.path.exists("cache/midas_sleeve.json"):
       with open("cache/midas_sleeve.json") as f:
           midas_sleeve = json.load(f)
   midas_has_position = bool(midas_sleeve.get("position"))
   ```

3. **Build the dispatch list.** Apply the conditions from the table above:

   **Always (market hours, weekdays):**
   - `/trinity` — dashboard refresh

   **Conditional:**
   - `/delphi` — if market hours + weekday
   - `/midas` — if weekend (full scan), or Monday (entry), or weekday with open position (stop check)
   - `/oracle` — if `oracle_due`
   - `/achilles` — if `earnings_season` and market hours
   - `/oracle-screen` — if `screen_due` (runs before `/oracle` since oracle uses screen output)

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
   - `/midas`

   **Parallel group 2** (depends on group 1):
   - `/oracle` (needs screen output if screen just ran)

   **Parallel group 3** (ghosts, after their parents):
   - `/oracle-ghost`, `/delphi-ghost`, `/achilles-ghost`, `/midas-ghost`

   **Last:**
   - `/trinity` (reads all sleeves, so runs after everything else)

   Skip any skill whose condition wasn't met. If nothing is due, log
   "Zeus: nothing due this hour" and exit.

5. **Log.** Print a summary of what ran and what was skipped. No persist
   needed — Zeus has no state of its own. Each god persists its own files.

## Scheduling

Zeus runs as a **hourly routine**. Set up via Claude Code's routine/cron
system to fire once per hour during waking hours (or 24/7 if you want
weekend Midas pre-scans to fire automatically).

Suggested cron: every hour, 7 days a week. Zeus itself decides what's
due — the cron just wakes it up.

## Hard rules

- Zeus does NOT trade. It only invokes skills.
- Zeus does NOT override any god's logic or skip conditions.
- Zeus does NOT persist any state. Each dispatched skill handles its own persistence.
- If a skill fails, log the error and continue with the next skill. One god's failure does not block the others.
- Weekend dispatches: only `/midas` (pre-scan) runs. No `/trinity`, `/delphi`, or `/achilles` on weekends.
