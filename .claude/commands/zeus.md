# /zeus — hourly dispatcher

Zeus is a coordinator, not a strategist. It wakes once per hour, checks
what's due, and dispatches the relevant gods and ghosts. It does not
think, trade, or override any god's logic.

## Dispatch table

| Skill | Condition | Notes |
|-------|-----------|-------|
| `/trinity` | Market hours (9:30–16:00 ET, weekdays) | Dashboard refresh with live quotes |
| `/midas-scan` | Weekend AND `should_run("cache/midas_cadence.json", "scan", 5)` | Heavy universe scan → top 10 → `cache/midas_scan.json`. Cadence guard = once per weekend, not every hour. **Research-only since 2026-07-04** — output feeds `/midas-ghost` (the A/B race), never a live entry |
| `/midas` | **WIND-DOWN ONLY** (live retired 2026-07-04, operator directive): weekday, and ONLY while `cache/midas_sleeve.json` still has a `position` or `cache/midas_cadence.json` has a `pending_exit_order_id` | Reconcile the queued DAKT sell (order `6a473615`) when it fills, then sweep ALL cash to Proteus's sleeve (see midas.md wind-down). NO new entries, ever. Once the sweep is done, never dispatch `/midas` again |
| `/oracle` | `should_run("cache/oracle_cadence.json", "research", 3)` | Every 3 days |
| `/delphi` | **WIND-DOWN ONLY** (live retired 2026-07-04, operator directive): weekday, and ONLY while `cache/delphi_sleeve.json` still has open `positions` OR unswept settled cash | Liquidate her positions to cash, sweep to Plutus's sleeve (see delphi.md wind-down). NO new entries, ever. Once flat and fully swept, never dispatch `/delphi` again |
| `/plutus` | Market hours AND `is_trading_day(today)` | **LIVE since 2026-07-06** (conscious override, docs/plutus_launch_override.md): net-issuance capital-return god, funded by Delphi's retired sleeve. The runbook self-gates — it only REBALANCES at a fresh quarter-end (once/quarter), every other pass is monitoring-only. Research-only until `plutus_sleeve.json` shows `pending_funding: null` and the swept cash has settled |
| `/hermes` | Market hours AND `is_trading_day(today)` | **LIVE since 2026-07-05** (armed, funded $4k; docs/hermes_launch_override.md): merger-arb LLM A/B. Tend open deals (break-stop / completion / past-close), detect new small-cap cash deals, LLM break-risk read (Arm A live / Arm B paper), grade LLM-lift. Owns only `cache/hermes_*`, parallelizes safely. Research-only until settled cash backs the sleeve |
| `/achilles` | **FOLDED into Proteus 2026-07-05** — NO standalone dispatch | PEAD now runs as a seasonal MODE inside `/proteus` during earnings windows; the `achilles/` package is a library. Do not dispatch `/achilles` (wind-down/library-only) |
| `/nemesis` | **FOLDED into Oracle 2026-07-05** — NO standalone dispatch | Spinoff forced-selling is now an `/oracle` sourcing channel (via the `nemesis.*` library). Sleeve retired, OCTV cancelled. Do not dispatch `/nemesis` (wind-down/library-only) |
| `/oracle-screen` | `should_run("cache/oracle_cadence.json", "screen", 90)` | Quarterly heavy scan (~60 min) |
| `/oracle-ghost` | After `/oracle` runs | Paper shadow |
| `/delphi-ghost` | After `/delphi` runs | Paper shadow |
| `/achilles-ghost` | After `/achilles` runs (earnings season only) | Paper shadow |
| `/midas-ghost` | Market-hours weekdays, once per day (`should_run("cache/ghost_midas_cadence.json", "session", 1)`) | Paper shadow — the live-vs-legacy A/B race. Survives Midas's live retirement; consumes the weekend `/midas-scan` finalists directly |
| `/proteus` | `should_run("cache/proteus_cadence.json", "session", 1)` — one full session per day, any day (operator mandate 2026-07-04: his purpose is a green book every day, so he hunts every day; weekends he researches with markets closed) | **LIVE since 2026-07-04** (operator directive): trades the real sleeve funded from Midas's retired capital. Until `proteus_sleeve.json` shows `pending_funding: null`, sessions are research-only |
| `/proteus-lab` | Weekend AND `should_run("cache/proteus_cadence.json", "lab", 7)` | Proteus's weekly lab session — files into the HOUSE registry (`shared.lab`, sponsor="proteus") since 2026-07-04. PAPER ONLY — never a broker order. Run BEFORE `/lab` (both write `cache/lab_registry.json`; sequencing avoids a lost-update race) |
| `/lab` | Weekend AND `should_run("cache/lab_cadence.json", "session", 7)` | The HOUSE research lab (operator directive 2026-07-04): works `docs/RESEARCH_BACKLOG.md` top-down through the shared.lab ratchet. PAPER ONLY. Run AFTER `/proteus-lab`, never concurrently with it |

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
   from shared.guards import is_paused
   import json, os

   # Oracle is on a soft HOLD (cache/oracle_paused.json) — do NOT dispatch the
   # Oracle family (/oracle, /oracle-screen, /oracle-ghost) while paused. This
   # spends no credits and writes no pre-Stage-1-rebuild output. (A pause is not a
   # kill — nothing is liquidated; the frozen legacy cohort is untouched.)
   oracle_paused = is_paused("oracle")
   oracle_due = (not oracle_paused) and should_run("cache/oracle_cadence.json", "research", 3)
   screen_due = (not oracle_paused) and should_run("cache/oracle_cadence.json", "screen", 90)
   # Proteus is on a soft HOLD (cache/proteus_paused.json) pending the
   # spare-no-expense rebuild — do NOT dispatch /proteus while paused (no runs, no
   # new entries, no credits). /proteus-lab (paper research) is unaffected.
   proteus_paused = is_paused("proteus")
   # Hermes freeze (cache/hermes_paused.json) — set when the book is mid-reconcile
   # (e.g. an auto-run over-deployed and trims are pending). While paused, do NOT
   # dispatch /hermes: no new detection, no new entries, no top-ups. Tending
   # (break-stops/completion on OPEN deals) may run manually; the freeze only stops
   # the auto-run from touching the book before an operator finalizes. Lift explicitly.
   hermes_paused = is_paused("hermes")
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

   # Delphi wind-down (live retired 2026-07-04): dispatch /delphi ONLY to
   # liquidate her remaining positions and sweep the cash to Plutus.
   # BUG-HUNT FIX 2026-07-05: gate on remaining positions OR unswept cash —
   # NEVER on the `retired` flag alone. delphi.md stamps `retired` on the first
   # FLAT pass, which lands Monday while proceeds are still unsettled (T+1);
   # keying off `retired` stopped dispatch before Tuesday's settled cash could
   # sweep, stranding ~$2k in a dead sleeve and underfunding Plutus's launch.
   # Also fail CLOSED on a missing sleeve file (no file = nothing to wind down).
   delphi_sleeve = {}
   if os.path.exists("cache/delphi_sleeve.json"):
       with open("cache/delphi_sleeve.json") as f:
           delphi_sleeve = json.load(f)
   delphi_wind_down = bool(delphi_sleeve) and (
       bool(delphi_sleeve.get("positions"))
       or float(delphi_sleeve.get("cash", 0) or 0) > 1.0)   # unswept cash keeps it alive

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
   - `/delphi` — ONLY if `delphi_wind_down` on a weekday (liquidate remaining positions + sweep to Plutus). Live retired 2026-07-04; no new entries. Once her sleeve is flat and marked `retired` with cash fully swept, never dispatch `/delphi` again
   - `/plutus` — if market hours AND `oracle.calendar.is_trading_day(today)`. LIVE since 2026-07-06 (conscious override): net-issuance god funded by Delphi's retired sleeve. The runbook self-gates to a once-per-quarter rebalance; every other pass is monitoring-only. Owns only `cache/plutus_*`, so parallelizes safely. EXCEPTION: on a day the Delphi wind-down sweep runs, dispatch `/delphi` BEFORE `/plutus` — the sweep writes Plutus's funding
   - `/hermes` — if `(not hermes_paused)` AND market hours AND `oracle.calendar.is_trading_day(today)`. LIVE since 2026-07-05 (armed, $4k): merger-arb LLM A/B. Tend open deals, detect new cash deals, LLM break-risk read (Arm A live / Arm B paper), grade LLM-lift. Owns only `cache/hermes_*`, parallelizes safely. Research-only until settled cash backs the sleeve. **FROZEN 2026-07-07 (`cache/hermes_paused.json`): an auto-run over-deployed (double-bought APGE/RAMP/GBTG + added FSEA); trims are queued for the 07-08 open and the sleeve is reconciled — do NOT dispatch until the operator lifts the freeze.**
   - `/midas-scan` — if weekend AND `midas_scan_due` (the cadence guard fires it once per weekend, not every hour). Research-only: feeds the ghost A/B
   - `/midas` — ONLY if `midas_wind_down` on a weekday (reconcile the final exit + sweep to Proteus). Live retired 2026-07-04; there are no new entries and no Monday dispatch once the sweep completes
   - `/oracle` — if `oracle_due` (its idea-sourcing now includes the folded spinoff channel via the `nemesis.*` library)
   - `/achilles`, `/nemesis` — FOLDED 2026-07-05, NEVER dispatched as standalone gods. PEAD runs inside `/proteus` seasonally; spinoffs are an `/oracle` channel. Their packages are libraries only.
   - `/oracle-screen` — if `screen_due` (runs before `/oracle` since oracle uses screen output)
   - `/proteus` — if `(not proteus_paused)` AND `should_run("cache/proteus_cadence.json", "session", 1)`. **PAUSED 2026-07-07 (soft hold) pending the spare-no-expense rebuild — not dispatched while `cache/proteus_paused.json` is active.** When live: one full session per day; trades his own real sleeve (and only his own); research-only until `pending_funding` clears.
   - `/proteus-lab` — if weekend AND `should_run("cache/proteus_cadence.json", "lab", 7)` (once per weekend; paper-only strategy research; run it after `/proteus` since both write `proteus_cadence.json`)
   - `/lab` — if weekend AND `should_run("cache/lab_cadence.json", "session", 7)` (the house research lab; run it AFTER `/proteus-lab` completes — both write `cache/lab_registry.json`, and sequencing prevents a lost update)
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

   **Group 0 — SWEEP BARRIER (sequential; must fully complete AND persist
   before group 1 dispatches).** A sweeping god WRITES the funded god's sleeve,
   so they can never run in parallel (bug-hunt 2026-07-05 — the old inline
   "run BEFORE" note inside a "run together" block was a self-contradiction):
   - `/delphi` (weekday, while `delphi_wind_down`) — its sweep writes PLUTUS's funding
   - `/midas` (weekday, while `midas_wind_down`) — its sweep writes PROTEUS's funding

   **Parallel group 1** (independent gods, run together — only after group 0):
   - `/oracle-screen` (if due — run first since `/oracle` uses its output)
   - `/plutus` (live; owns only `cache/plutus_*`, parallelizes safely within this group)
   - `/hermes` (live; owns only `cache/hermes_*`, parallelizes safely — tend deals + detect + LLM read + grade LLM-lift)
   - `/midas-scan` (weekend; `/midas` weekday wind-down runs in GROUP 0, never here)
   - `/proteus` (if due — live; owns only `cache/proteus_*`, so he parallelizes safely within this group. Runs the seasonal PEAD mode during earnings windows. His funding sweep, if pending, already landed in group 0)

   **Parallel group 2** (depends on group 1):
   - `/oracle` (needs screen output if screen just ran)

   **Parallel group 3** (ghosts — parentless cadences since the retirements/folds;
   bug-hunt 2026-07-05: "after their parent" orphaned the shadows of gods that
   no longer dispatch):
   - `/oracle-ghost` — after `/oracle` (its parent still runs)
   - `/achilles-ghost` — market-hours weekdays, once per day
     (`should_run("cache/ghost_achilles_cadence.json", "session", 1)`); parentless
     since the fold — it self-discovers beats and keeps grading the gate questions
   - `/delphi-ghost` — market-hours weekdays, once per day
     (`should_run("cache/ghost_delphi_cadence.json", "session", 1)`); parentless
     since the retirement — shadows for the record
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
- Weekend dispatches: only `/midas-scan` (heavy universe scan, research-only), `/proteus` (discretionary god — daily cadence includes weekends as research days; markets closed means no orders), `/proteus-lab` (weekly strategy lab, paper only), and `/lab` (house research lab, paper only, after `/proteus-lab`) run. No `/trinity`, `/plutus`, `/hermes`, or `/midas` on weekends (markets closed — nothing to trade). `/achilles` and `/nemesis` are folded and never dispatched.
- Midas is retired from live trading (2026-07-04, operator directive — capital reallocated to Proteus). `/midas` exists only to finish the DAKT wind-down; `/midas-scan` and `/midas-ghost` continue as the convergence A/B research program.
