# /nemesis — spinoff pipeline scan + Form 10 reading + ghost entries

Nemesis v2 reads what the market discards. Every spinoff announces itself
months in advance on SEC Form 10-12B (the "Form 10") — a 300-page document
almost nobody reads: no analyst coverage, no earnings history, and index
funds that held the parent receive spinco shares they are not allowed to
keep (wrong index, wrong size bucket) and must sell regardless of price.
Nemesis never buys the distribution — it buys AFTER the forced-seller dump,
on a mechanical window trigger, and holds ~5 months (150 days) while the
orphan gets discovered. The LLM's job is the document: it judges the three
things that decide a spinoff (management incentives, dumped liabilities,
forced-seller flows). It never predicts prices.

**Hard rules (non-negotiable):**
- **NO broker orders. Ever.** Nemesis has no sleeve and no live ledger, and
  gets none until the ghost's `llm_selected` lift proves that document
  judgment adds alpha over buying every spinoff. Until then this command
  produces paper entries and reports only.
- **The buy-all leg is sacred.** Every priceable in-window spinco is
  ghost-bought — read or unread, "own" or "avoid". It is the control group:
  academic spinoff outperformance needs no reader at all, so filtering the
  ghost to the LLM's picks would destroy the only measurement that matters.
- **Dossiers must validate.** `nemesis.dossier.make_dossier` raises on a
  lazy read — missing bear case, no forced-seller map, an "own" without
  incentive alignment. The honesty gates are not advisory; a dossier that
  fails them gets rewritten, not waved through.
- **The LLM reads and judges documents; it NEVER predicts prices or invents
  numbers.** Every material claim in a dossier must say where in the filing
  it came from.
- The window constants in `nemesis/window.py` are FROZEN — the trigger
  definition IS the experiment; changing it mid-sample invalidates every
  graded comparison.
- The name's history: v1 was a crash-fade contrarian, tested seven ways and
  refuted, retired 2026-07-02 — `docs/nemesis_v1_crashfade_verdicts.md`.
  Read it before proposing anything that resembles it.

## State files

All in `cache/`, persisted under god name **`ghost_nemesis`** — its
`OWNERSHIP_PREFIXES` entry covers both `cache/ghost_nemesis_*` and
`cache/nemesis_*`, so one persist call carries everything below.

| File | Purpose |
|------|---------|
| `cache/nemesis_pipeline.json` | Tracked registrations, keyed by CIK |
| `cache/nemesis_dossiers.json` | SpinDossiers — the LLM's Form 10 reads |
| `cache/ghost_nemesis_ledger.json` | Paper entries (buy-all + judgment tags) |
| `cache/ghost_nemesis_curve.json` | Paper equity curve |
| `cache/ghost_nemesis_report.json` | Judgment-vs-buy-all verdict |
| `cache/nemesis_cadence.json` | Last-run stamp for the weekly scan |

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores
   `cache/` so this session starts from real pipeline/ledger state, not
   empty defaults. No kill-switch or `is_live` check: this command never
   trades, so paper vs live is irrelevant here.

1. **Weekly EDGAR scan.**
   `nemesis.spinoffs.search_spinoff_registrations(date_from=<today − ~8 months>, date_to=today)`
   — one EDGAR full-text search for "spin-off" on form 10-12B. The trailing
   8-month lookback is deliberate: a Form 10 is filed months before
   distribution and amended several times, and the *tradeable* moment
   (post-dump window) arrives weeks after that — a narrow scan window would
   forget a spinco between its registration and its entry. Then:
   ```python
   from nemesis import spinoffs
   pipeline = spinoffs.load_pipeline("cache/nemesis_pipeline.json")
   events = spinoffs.search_spinoff_registrations(date_from, date_to)
   spinoffs.update_pipeline(pipeline, events, today=today)
   ```
   `update_pipeline` owns discovery state (company, ticker, filing dates,
   statuses "registered"/"ticker_assigned") and by contract never touches
   the runbook-owned lifecycle: statuses `distributed`/`entered`/`skipped`/
   `expired` and the fields `distribution_date`, `first_trade_date`,
   `window_state`, `dossier_verdict`. A re-scan can never un-distribute a
   spinoff. This runbook is the only writer of those fields — keep it that
   way.

2. **Distribution detection + window assessment.** For each pipeline entry
   that has a ticker and is not yet `entered`/`expired`:
   - `get_equity_quotes` — does the symbol trade at the broker yet? No
     quote → still pre-distribution; leave it and move on.
   - `get_equity_historicals` (daily bars, span long enough to reach back
     to the listing — 3 months minimum, a year for bootstrap names). The
     **first bar with real volume is the first trading day** — earlier bars
     are when-issued placeholders. Slice the series from that bar: day-one
     volume must be in the series or the window's volume-normalization
     ratio is meaningless.
   - `nemesis.window.assess_window(sliced_bars)` → `WindowState`. The state
     machine answers "are the forced sellers done?" mechanically: volume
     normalized (last-5-day avg ≤ 50% of the first-5-day dump) AND price
     stabilized (the series low is behind us), inside 10–90 trading days.
     `pre_window` = too early / sellers still pressing; `in_window` = buy;
     `late` = past ~one quarter, the anomaly has decayed.
   - Update the runbook fields on the pipeline entry: `status` →
     `"distributed"` (unless already `entered`), `distribution_date` /
     `first_trade_date` from the first real-volume bar's date,
     `window_state` from the assessment.
   - A registration that never goes anywhere — no ticker and no new filings
     for ~12 months, or a withdrawn/abandoned deal — gets `status` =
     `"expired"` so the pipeline doesn't accumulate zombies.

3. **THE READING.** For each pipeline name (tickered, not `expired`) without
   a dossier in `cache/nemesis_dossiers.json`: fetch its Form 10 and have
   the LLM judge it.

   **Fetch:** `shared.edgar.fetch_submissions(cik)` →
   `shared.edgar.parse_submissions_recent(payload)` → take the latest
   10-12B (amendments `10-12B/A` supersede the original — read the newest,
   it has the final capital structure) or, failing that, the latest Form 10
   document → `shared.edgar.fetch_body(filing)`. Record `filing.primary_url`
   as `form10_url` in the dossier.

   **Model routing:** a Form 10 body is enormous (300+ pages, easily 100k+
   tokens). As in `/oracle-research`, dispatch the extraction reads via the
   Agent tool with `model: "sonnet"` — one subagent per section bundle
   (compensation & equity-award treatment; pro-forma financials &
   separation agreements; risk factors & business), each returning exact
   quotes with section references. Reserve the main session model, **with
   extended thinking**, for the judgment and the dossier itself.

   **Analyst instructions — judge these five things, in this order:**

   - **Map management equity incentives** (`incentive_alignment`, 0–1;
     default 0.0 — assume management gets nothing until the filing shows
     otherwise). WHERE do executives get their stock — parent or spinco?
     Read Executive Compensation and the treatment-of-equity-awards
     section: are parent RSUs/options converted into SPINCO equity, or do
     spinco officers keep riding parent stock? What triggers vesting —
     time, spinco share-price hurdles, or merely the distribution closing?
     Are there founder/CEO purchases or a meaningful stake? Greenblatt's
     tell: management that takes its pay in spinco equity expects the
     spinco to work; management compensated in parent stock is telling you
     which company keeps the good business.
   - **Hunt the dumped liabilities** (`garbage_barge_risk`, 0–1; default
     1.0 — assume the parent dumped its problems until the pro-formas prove
     clean). Spinoffs are where parents park what they want off their
     balance sheet: pension/OPEB obligations, environmental and litigation
     exposure, above-market leases, stranded corporate costs, and debt
     raised specifically to pay the parent a pre-spin dividend. Read the
     pro-forma balance sheet, the separation and tax-matters agreements,
     and Risk Factors: who indemnifies whom, and what does the spinco owe
     the parent on day one?
   - **Map the forced sellers** (`forced_seller_map`, prose — this map is
     the reason the trade exists). WHICH indexes and mandates must exit,
     and WHEN? Parent in the S&P 500 but spinco too small to qualify →
     every S&P index fund is a seller. Style mismatch (a value/dividend
     mandate receiving a no-yield growth orphan) → active mandates sell
     too. Estimate what fraction of the float is mandate-driven supply and
     when it clears (typically the first weeks post-distribution). A
     spinoff whose holders may all keep it has no dump to buy — say so.
   - **Judge pro-forma honesty** (`pro_forma_notes`). Pro-formas are
     drafted by the parent's bankers. What do the adjustments hide —
     optimistic "standalone cost" estimates, one-time separation costs
     that will recur, allocated overhead that will really be higher as an
     independent company?
   - **Score neglect** (`neglect`, 0–1): how orphaned is it — analyst
     coverage, earnings history, index membership? Neglect is fuel: the
     re-rating happens when someone finally looks.

   Then the verdict: `own` / `avoid` / `watch`, `conviction` 0–1, plus an
   articulated `bull_case`, `bear_case`, and `key_risk`, and
   `expected_rerating_months` (1–12 — a patience budget, not a forecast).
   "own" must clear `incentive_alignment >= 0.5` AND
   `garbage_barge_risk <= 0.6`: an "own" that fails the two Greenblatt
   tells may be a fine stock, but it is not this strategy's trade.

   **HARD RULE: the LLM reads and judges documents; it NEVER predicts
   prices and NEVER invents numbers. Every material claim in the dossier —
   a debt figure, a pension liability, a vesting trigger, an indemnity —
   must say where in the filing it came from (section or exhibit). If the
   filing does not state it, the dossier says "not disclosed"; it does not
   guess.**

   Build via `nemesis.dossier.make_dossier(symbol=…, parent=…, cik=…,
   form10_url=…, distribution_date=…, …, researched_at=today)` — it raises
   with EVERY problem listed, so one revision fixes everything. Save via
   `nemesis.dossier.save_dossiers("cache/nemesis_dossiers.json", dossiers)`
   and write the verdict into the pipeline entry's `dossier_verdict`.

4. **Ghost entries at the window trigger.** Build `price_lookup` from
   `get_equity_quotes`. Collect every pipeline entry with `status` =
   `"distributed"` and `window_state` in (`in_window`, `late`) — NOT names
   already `entered` — as spin dicts:
   `{"symbol", "entry_window": window_state, "market_cap": <fundamentals,
   if available>, "verdict"/"conviction"/"incentive_alignment": <from its
   dossier, if one exists>}`. Then:
   ```python
   from nemesis import ghost
   cands = ghost.spins_to_ghost(
       spins, price_lookup,
       reviewed=[d.symbol for d in dossiers],          # Form 10 actually read
       selected=[d.symbol for d in dossiers if d.verdict == "own"],
   )
   ledger.extend(ghost.open_entries(cands, ledger, today=today, skip_open=True))
   ```
   - **Every `in_window` spinco opens** — the buy-all control. No vetoes,
     no exceptions: an "avoid" verdict rides along as a tag, because the
     ghost is measuring whether "avoid" means anything.
   - **`late` entries are allowed**, tagged `entry_window="late"` — the
     report's `window_groups` row is what tells us whether the post-dump
     window is real or washes out over a 5-month hold.
   - The fair-comparison rule is structural: `spins_to_ghost` attaches
     judgment tags (`llm_selected`, `verdict`, `conviction`,
     `incentive_alignment`) ONLY to reviewed symbols. An unread spinoff is
     not a rejected one — don't try to tag it.
   - After opening, set the pipeline entry's `status` = `"entered"`. A name
     with no broker price (untradeable, OTC-only) gets `"skipped"` — revisit
     it on a later run if it becomes priceable.

5. **Mark / grade / report.**
   - `ghost.mark_to_market(ledger, price_lookup)` →
     `ghost.append_equity_point(curve, today, snapshot)`; save the curve.
   - `ghost.grade_entries(ledger, price_lookup, today=today)` — grades
     entries whose 150-day horizon has elapsed. Unpriceable names grade as
     −100% (survivorship guard: a delisted spinco is an outcome, not
     missing data).
   - `ghost.spinoff_report(ledger)` → `cache/ghost_nemesis_report.json`.
     Read it in this order: `signal_lift.llm_selected` (the whole ballgame
     — do the LLM's picks beat the reviewed names it passed over?),
     `verdict_groups` (if "avoid" re-rates as hard as "own", the
     garbage-barge detector detects nothing), `conviction_terciles` /
     `incentive_terciles` (do the two committed scores predict returns?),
     `window_groups` (in_window vs late).
   - **Verdicts are slow by design.** HORIZON_DAYS = 150: the first graded
     cohort arrives ~5 months after the first entries, and a real sample
     takes a year-plus. Do not tune gates, thresholds, or the window
     constants on a handful of grades — patience is the strategy.

6. **Persist + mark cadence.** `ghost.save_ledger(...)`,
   `spinoffs.save_pipeline(...)`, `dossier.save_dossiers(...)` (all atomic
   tmp + `os.replace`), then
   `oracle.calendar.mark_run("cache/nemesis_cadence.json", "scan")` so
   Zeus's `should_run` guard fires this once per weekend, not every hour.
   Finally `pantheon.persist("ghost_nemesis", {…pipeline, dossiers, ledger,
   curve, report, cadence…}, branch="claude/live")`.

## Bootstrap (first run)

The first run is the same steps with a retroactive twist: the trailing
8-month scan surfaces spincos that registered months ago and have already
distributed and traded for weeks.

- **Reading late is legitimate.** Form 10s are public documents; a dossier
  written today on a March spinco is exactly as informative as one written
  in March, and it is dated `researched_at=today` so nothing pretends
  otherwise.
- **Entering stale windows is not.** Honor `window_state`: a bootstrap name
  past its window enters (if at all) tagged `late`, at TODAY's price on
  TODAY's date. Never backdate an entry, never reconstruct "what we would
  have paid" — a ghost ledger with imagined fills proves nothing.
- **Currently-known pipeline** (from the 2026-06/07 sweeps): tickered —
  VSNT, OCTV, TRAX, FDXF, HONA, MFP, MBGL, ADIG — plus several
  registrations with no ticker assigned yet. The retro scan should
  rediscover all of these; if it doesn't, debug the scan before trusting
  anything else it returns.
- The bootstrap's deliverable is a populated pipeline, a first tranche of
  dossiers, and the first ghost entries — the 5-month clock cannot start
  until they exist, so run it promptly and then let the weekly cadence
  take over.

## What /nemesis does NOT do

- Place any broker order, or touch any god's sleeve/ledger/curve.
- Predict prices, target prices, or expected returns — anywhere, ever.
- Skip the buy-all leg, or open only the LLM's picks.
- Tune `nemesis/window.py` constants or the dossier honesty gates.
- Trade the parent, short anything, or touch options — long the spinco
  orphan in paper, 150 days, that's the whole experiment.
