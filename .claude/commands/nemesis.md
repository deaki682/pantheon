# /nemesis — spinoff pipeline scan + Form 10 reading + ghost entries + gated live sleeve

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
- **Live orders are GATED, not a default.** Broker orders happen ONLY when
  `shared.guards.is_live("nemesis")` is true — the env var `NEMESIS_LIVE`
  set to exactly `"true"`. Otherwise the live-sleeve step runs in paper
  mode. **CRITICAL: In paper mode, do NOT place orders, do NOT update the
  sleeve, do NOT append to the ledger, and do NOT persist live-god state.**
  Compute everything normally, print what *would* happen, then move on.
  Paper mode is read-only — it must never change live state. The ghost
  buy-all leg runs IDENTICALLY in both modes and remains sacred: it is the
  control group, and it does not care whether real dollars ride alongside
  it. **Promotion advisory:** the operator flips the switch, but the
  written gate is `signal_lift.llm_selected` positive over >= 20 graded
  reviewed names AND `verdict_groups` showing "own" beating "avoid".
  Flipping earlier is an explicit operator override, not a default.
  **Override exercised 2026-07-03:** the operator flipped `NEMESIS_LIVE`
  with zero graded names — on the record as the override, not the gate.
  The written gate remains the measuring stick, the ghost buy-all
  control runs unchanged, and the first graded cohort (~2026-11-29)
  judges the decision either way. The flag lives in the `env` block of
  `.claude/settings.json` so every session inherits it from main.
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

All in `cache/`. Ownership is split two ways and `pantheon/persist.py`
enforces the split: the ghost/pipeline files belong to god
**`ghost_nemesis`**, the live-sleeve files to god **`nemesis`** — two
separate persist calls, so a ghost run can never silently rewrite
real-money state and a live run can never contaminate the experiment's
control-group ledger.

| File | Owner | Purpose |
|------|-------|---------|
| `cache/nemesis_pipeline.json` | `ghost_nemesis` | Tracked registrations, keyed by CIK |
| `cache/nemesis_dossiers.json` | `ghost_nemesis` | SpinDossiers — the LLM's Form 10 reads |
| `cache/ghost_nemesis_ledger.json` | `ghost_nemesis` | Paper entries (buy-all + judgment tags) |
| `cache/ghost_nemesis_curve.json` | `ghost_nemesis` | Paper equity curve |
| `cache/ghost_nemesis_report.json` | `ghost_nemesis` | Judgment-vs-buy-all verdict |
| `cache/nemesis_cadence.json` | `ghost_nemesis` | Last-run stamp for the weekly scan |
| `cache/nemesis_sleeve.json` | `nemesis` | Live sleeve: cash, positions, peak equity |
| `cache/nemesis_ledger.jsonl` | `nemesis` | Every live order placed (for reconcile) |
| `cache/nemesis_curve.json` | `nemesis` | Live equity curve |

## Steps

0. **Hydrate.** `pantheon.hydrate()` — fetches `claude/live` and restores
   `cache/` so this session starts from real pipeline/ledger state, not
   empty defaults. Kill-switch and `is_live` are checked in step 5, where
   the live sleeve lives — steps 1–4 never trade, so paper vs live is
   irrelevant to them and they run identically in both modes.

   **Weekday short-circuit (live position management):** when Zeus
   dispatches this on a weekday because `cache/nemesis_sleeve.json` holds
   positions, skip steps 1–4 entirely — the scan/reading/ghost cadence is
   weekend work — and run step 5 as an **exits-only** pass: safety check
   (5a), restore (5b), exits (5c), then peak/halt/persist (5e). No new
   entries (5d), no cadence mark, no ghost-file persist. **Fill
   reconciliation first:** before evaluating exits, check
   `cache/nemesis_ledger.jsonl` for rows marked `"queued"` (orders placed
   on a closed market — holiday/weekend entries queue for the next open).
   `get_equity_orders` for each: if filled, true-up the sleeve position to
   the ACTUAL fill price and date (entry_price, stop_price = fill ×
   (1+HARD_STOP_PCT), exit_date = fill date + 150 days), update the ledger
   row to `"filled"`, persist. The bookkeeping price at placement is a
   reservation, not a record — grades run on real fills.

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
   Then backfill tickers from the OFFICIAL registry — display names lie
   (Qnity registered as "Novus SpinCo 1"; Cyprium renamed to Versigent;
   Atrium took a recycled symbol — all three hid from the display-name
   parser during the 2026-07-03 ocean sweep):
   ```python
   cik_to_sym = {}
   for sym, cik in edgar.fetch_company_tickers().items():
       cik_to_sym.setdefault(edgar.cik10(cik), sym)
   filled = spinoffs.backfill_tickers(pipeline, cik_to_sym)
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
     **first bar with real volume is the first trading day** — and "real"
     means `volume >= max(10_000, 0.02 * series_max_volume)`, not merely
     nonzero. When-issued sessions print token volume for days or weeks
     before the distribution (TRAX printed 200–31K shares for two weeks
     before its true 769K-share dump day, 2026-04-20; slicing at the
     first nonzero bar made the first-5-day baseline ~3K shares and the
     vol_ratio a meaningless 254x that could never normalize). Slice the
     series from the true dump day: day-one volume must be in the series
     or the window's volume-normalization ratio is meaningless.
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

   **Weekly freshness sweep (watch list):** for every distributed,
   not-yet-entered name with a dossier, `fetch_submissions(cik)` and
   compare the newest 10-Q/10-K/8-K/13D against the dossier's
   `researched_at`. A material new document — the first standalone
   quarterly or annual, a guidance 8-K, a fresh 13D — triggers the
   deep-read revision BEFORE the name's window opens, not after. A
   window opening on a stale verdict is either a missed trade (a watch
   that new numbers made an own) or a dodged bullet nobody aimed at (an
   own the new numbers broke) — either way the experiment learns nothing
   from luck. Routine no-news weeks trigger nothing.

   **A name that already HAS a dossier is not re-read** (the weekly Form 4
   re-sweep and thesis-break surveillance update specific fields; they are
   not re-reads). Re-reading requires either NEW primary documents (a
   fresh 10-Q/8-K that changes the picture — the freshness sweep above is
   what detects this) or an explicit operator instruction — and even then the new read is recorded as a revision
   with its `researched_at` bumped and the score changes justified
   against the prior read, NEVER a silent replacement. Two honest reads
   of the same documents can disagree; a disagreement is calibration
   data to surface, not noise to overwrite. Ghost judgment tags are
   stamped from the STANDING dossier at entry time — an entry's tags are
   the experiment's record and do not retroactively change when a
   dossier is later revised. (Bootstrap 2026-07-02 lesson: the run
   re-read OCTV over a standing refuter-verified dossier and silently
   flipped own→watch; the ghost entry then carried the replacement's
   tags. Both reads were honest — the overwrite was the defect.)

   **Fetch:** `shared.edgar.fetch_submissions(cik)` →
   `shared.edgar.parse_submissions_recent(payload)` → take the latest
   10-12B (amendments `10-12B/A` supersede the original — read the newest,
   it has the final capital structure) or, failing that, the latest Form 10
   document. **The primary document of a 10-12B is a thin cover page — the
   actual ~300-page information statement is Exhibit 99.1.** Fetch the
   accession's directory listing
   (`https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_nodash}/index.json`
   via `shared.edgar.http_get`), pick the LARGEST `.htm` exhibit (name
   usually matches `exhibit991*` / `*informationstat*`; it dwarfs the
   cover by 50x), and `shared.edgar.clean_html` that. Also worth pulling
   while you're in the filing history: the most recent 10-Q (post-spin
   economics), the closing 8-K (final debt actually drawn vs pro forma),
   and any 13D/G (anchor-holder intent). Record the information-statement
   exhibit URL as `form10_url` in the dossier.

   **Post-spin Form 4 sweep (distributed names only):**
   `nemesis.insiders.fetch_post_spin_txns(symbol, cik, distribution_date)`
   → `summarize_post_spin(txns, since=distribution_date)` →
   `render_summary(...)` into the dossier's `post_spin_insider_activity`
   field. This is the behavioral check on the Form 10's paper incentives —
   see the incentive_alignment instruction below. A name still
   pre-distribution has nothing to sweep; note that and re-sweep on later
   runs (insider buys can land any week of the hold, and for HELD names the
   weekly re-sweep doubles as thesis-break surveillance — a wave of
   code-"S" selling is how `insider_reversal`-style breaks announce
   themselves). **FPI caveat:** foreign private issuers (Irish/foreign
   plcs — OCTV is one) are Section 16-EXEMPT: their insiders never file
   Form 4s, so zero transactions means the channel is dark, not that
   insiders declined to buy. Record "FPI — Section 16 exempt, channel
   unavailable" and leave incentive_alignment resting on the Form 10 and
   13D evidence; never score the silence.

   **The deep-read standard (operator directive, 2026-07-03: cost is
   accepted — every RECORDED verdict gets the full treatment; a fast
   single-pass read is triage only and never becomes a dossier).** Four
   stages per name:

   1. *Prep:* download the complete document set (information-statement
      exhibit, latest 10-Q, closing 8-K, any 13D/G) to working files,
      split the information statement into section files, and run the
      post-spin Form 4 sweep.
   2. *Extract:* one subagent per section file — each reads its ENTIRE
      file and returns structured facts with citations (section name +
      quote fragment). "Not disclosed" beats a guess; no price talk.
   3. *Judge:* one pass, **with extended thinking**, over all extractions
      plus the insider sweep — produces every dossier field from the
      skeptical defaults (incentive up from 0.0 only on evidence; garbage
      down from 1.0 only on evidence). On a revision of an existing
      dossier, the judge must justify each score delta against the prior
      read.
   4. *Refute:* two MANDATORY adversarial passes before anything is
      recorded — an incentive-skeptic trying to push
      `incentive_alignment` below the own-gate, and a balance-sheet
      skeptic trying to push `garbage_barge_risk` above it. Fold in
      their non-flipping corrections; if either flips a gate score, the
      judgment is re-run with their evidence, not patched. The OCTV
      bootstrap disagreement (fast read: watch; deep read: own, refuters
      upheld) is the reference case for why the gates get attacked
      before a verdict stands.

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
     which company keeps the good business. **Then weigh what insiders
     DID (the Form 4 sweep above): the Form 10's grants are promises
     drafted by the parent's consultants; an officer's own cash buying in
     the open market post-distribution is the one alignment signal that
     can't be engineered, and it outranks any grant table. Conversely,
     insider code-"S" selling into the forced-seller dump is a hard
     negative. Score from both: paper incentives set the floor, observed
     behavior moves it — and cite the sweep's numbers, not vibes.**
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
   if available>, "verdict"/"conviction"/"incentive_alignment"/
   "garbage_barge_risk": <from its dossier, if one exists>}`. Then:
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

5. **Live sleeve (gated).** The live layer is additive: everything above
   already ran and nothing below touches the ghost ledger. Its exit rules
   are FROZEN NOW, before the first dollar — rules written in advance beat
   rules tuned after losses (the week of refutations in `docs/` is why).

   a. **Safety.** If `KILL_SWITCH` exists: restore the sleeve, place broker
      market sells for every live position, `sleeve.liquidate(marks,
      today)`, persist, and STOP. Then `shared.guards.is_live("nemesis")`:
      if `NEMESIS_LIVE` is not exactly `"true"`, run **paper mode**.
      **CRITICAL: In paper mode, do NOT place orders, do NOT update the
      sleeve, do NOT append to the ledger, and do NOT persist live-god
      state.** Compute the full exit/entry plan below, print what *would*
      happen, then continue to step 6 — the ghost is unaffected either way.

   b. **Restore.** Load `cache/nemesis_sleeve.json`, or initialize
      `NemesisSleeve(initial_cash=nemesis.sleeve.CAPITAL_BASE)` ($2,000) if absent. Then
      `sleeve.process_settlements(today)`.

   c. **EXITS FIRST.** `sleeve.due_exits(quotes, today)` returns the two
      mechanical exits: `hard_stop` (catastrophic −40% from entry — wide on
      purpose, because forced-seller bottoms are noisy) and `time_stop`
      (150 days — the horizon IS the thesis; past it, hold-and-hope is a
      different strategy). Thesis-break exits are MANUAL-JUDGMENT-ONLY:
      re-read the filings/news for each held name; a thesis-break sell
      requires a written reason from `nemesis.sleeve.THESIS_BREAK_REASONS`
      PLUS a one-paragraph case appended to the name's dossier — no reason,
      no case, no sell. `index_inclusion` is the one early *completion*
      exit: the orphan got discovered, so sell INTO the forced index
      buying — the exact mirror of the entry. Place market sells; every
      ledger row MUST record shares and price. After any live exit the
      pipeline entry KEEPS `status = "entered"` — a finished one-shot
      never returns to `"distributed"`; the re-buy protection lives in
      `sleeve.enter`'s trade-history refusal, which survives whatever
      the pipeline says.

   d. **ENTRIES — the VETO rule (v2, operator directive 2026-07-03).**
      Buy every pipeline name that clears ALL of:
      - `status` is `"distributed"` or `"entered"` (NOT `skipped`/`expired`;
        "entered" qualifies because step 4's ghost buy-all stamps it on the
        SAME run before this step ever sees the name),
      - `window_state` is `"in_window"` — NEVER `"late"` with real money,
      - a VALIDATED deep-read dossier EXISTS (an unread name is never
        bought — the veto cannot protect against a document nobody read),
      - and the dossier does NOT condemn it: condemned = verdict `"avoid"`
        OR `garbage_barge_risk > 0.6`. "Watch" is not a veto; only
        condemnation is.

      **Rule-change record:** v1 (frozen 2026-07-02, retired 2026-07-03
      with ZERO fills and ZERO grades under it) bought only verdict
      `"own"`. Changed by explicit operator directive after the ocean
      replay: the mechanical buy-all leg returned +41.2% vs SPY +30.2%
      over 2025-03→2026-07 with the entire excess carried by two names
      (SOLS, Q) whose big-parent/converted-award profiles the own-gate's
      incentive bar systematically fails, while the one catastrophic loss
      (TWNPQ, −58%) is precisely the profile the garbage gate condemns.
      The own-gate was selective in the wrong direction: strong against
      disasters, structurally blind to the vintage-carriers. The ghost
      experiment is UNAFFECTED — buy-all, own-selected (`signal_lift`),
      and veto-filtered legs are all still measured, and the ≥20-graded
      checkpoint re-decides the live rule among all three.

      The stale-window re-buy loop stays closed at the sleeve:
      `sleeve.enter` refuses any symbol in its trade history (one shot
      per spinco, ever) and any symbol currently held. The ghost buys late names to *measure* the decay;
      live dollars don't pay to confirm it, because the backtested anomaly
      decays past ~one quarter. One live shot per spinco, EVER —
      `sleeve.enter` also enforces this against its own trade history.
      Guards before every buy: `shared.guards.pre_trade_check` on
      `filter_broker_to_gods`-filtered broker positions (halt on any
      mismatch), and `shared.guards.already_placed_today` against
      `cache/nemesis_ledger.jsonl`. Size: `sleeve.target_dollars(marks)` —
      equal weight, respecting `open_slots`.

      **Order matters — sleeve first, broker second.** Call
      `sleeve.enter(…, verdict=…, conviction=…, incentive_alignment=…,
      entry_window=…)` (fields from the dossier) BEFORE placing any broker
      order. `enter()` returning False (halted, cooldown, basket full,
      duplicate, one-shot history, insufficient cash incl. fee) means NO
      broker order — a buy the sleeve refused would exist nowhere in god
      state, invisible to the one-sided pre-trade check. Only after
      `enter()` returns True: place the fractional-share market buy. If
      the broker rejects or errors, `sleeve.cancel_entry(sym, today)`
      reverses the bookkeeping and no ledger row is written. On a placed
      order: append the ledger row and set the pipeline entry's `status`
      to `"entered"`.

   e. **Peak / halt / persist.** `sleeve.update_peak(marks)`, then
      `sleeve.check_halt()` — a 40% drawdown from peak halts new entries
      (exits still run). Append an equity point to
      `cache/nemesis_curve.json`, then `pantheon.persist("nemesis",
      {sleeve, ledger, curve})` — a SEPARATE persist call from the
      `ghost_nemesis` one in step 7; `pantheon/persist.py` enforces the
      ownership split.

6. **Mark / grade / report.**
   - `ghost.mark_to_market(ledger, price_lookup)` →
     `ghost.append_equity_point(curve, today, snapshot)`; save the curve.
   - `ghost.grade_entries(ledger, price_lookup, today=today)` — grades
     entries whose 150-day horizon has elapsed. Unpriceable names grade as
     −100% (survivorship guard: a delisted spinco is an outcome, not
     missing data).
   - `ghost.spinoff_report(ledger)` → `cache/ghost_nemesis_report.json`.
     Read it in this order: the THREE-LEG race first — overall stats
     (buy-all control) vs `veto_filtered` (the live v2 rule: everything
     minus condemned) vs `signal_lift.llm_selected` (own-picks, the
     retired v1 rule) — the ≥20-graded checkpoint re-decides the live
     entry rule among these three. Then `verdict_groups` (if "avoid"
     re-rates as hard as "own", the garbage-barge detector detects
     nothing — and the veto rule loses its license), `condemned` (what
     the veto excluded — its mean return is the veto's report card),
     `conviction_terciles` / `incentive_terciles`, `window_groups`.
   - **Verdicts are slow by design.** HORIZON_DAYS = 150: the first graded
     cohort arrives ~5 months after the first entries, and a real sample
     takes a year-plus. Do not tune gates, thresholds, or the window
     constants on a handful of grades — patience is the strategy.

7. **Persist + mark cadence.** `ghost.save_ledger(...)`,
   `spinoffs.save_pipeline(...)`, `dossier.save_dossiers(...)` (all atomic
   tmp + `os.replace`), then
   `oracle.calendar.mark_run("cache/nemesis_cadence.json", "scan")` so
   Zeus's `should_run` guard fires this once per weekend, not every hour.
   Finally `pantheon.persist("ghost_nemesis", {…pipeline, dossiers, ledger,
   curve, report, cadence…}, branch="claude/live")`. The live-sleeve files
   were already persisted under god `"nemesis"` in step 5e — ownership
   enforcement means they cannot ride along here.

## Live exit rules (FROZEN before the first dollar)

Written now, while `NEMESIS_LIVE` is still unset, so no losing position can
lobby for a looser rule later.

| Condition | Trigger | Action |
|-----------|---------|--------|
| −40% from entry (catastrophic) | `hard_stop` via `sleeve.due_exits` | Market sell |
| 150 days held | `time_stop` via `sleeve.due_exits` | Market sell — the horizon IS the thesis |
| Thesis break (manual judgment) | reason from `THESIS_BREAK_REASONS` + one-paragraph dossier case | Market sell |
| Index inclusion | early completion — orphan discovered | Market sell INTO forced index buying |
| 40% drawdown from peak | `sleeve.check_halt()` | Halt new entries (exits still run) |
| Kill switch | `KILL_SWITCH` file | Liquidate immediately |

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

- Place any broker order unless `NEMESIS_LIVE` is exactly `"true"` — paper
  mode computes and prints, but never changes live-god state.
- Buy a `"late"` window with real money — the ghost measures the decay;
  live dollars never pay for it.
- Buy a name without a VALIDATED deep-read dossier — no read, no trade,
  however good the chart looks (the veto rule needs a document actually
  read; unread names are never live-bought).
- Buy a name the reading CONDEMNED — verdict "avoid" or garbage_barge_risk
  above 0.6 is an absolute veto on live money.
- Sell without a reason from `nemesis.sleeve.EXIT_REASONS` — and a
  thesis-break sell additionally requires its written dossier case.
- Touch any other god's sleeve/ledger/curve, or mix `nemesis` and
  `ghost_nemesis` state in one persist call.
- Predict prices, target prices, or expected returns — anywhere, ever.
- Skip the buy-all leg, or open only the LLM's picks — live trading never
  replaces the control group.
- Tune `nemesis/window.py` constants, the frozen exit rules, or the
  dossier honesty gates.
- Trade the parent, short anything, or touch options — long the spinco
  orphan, 150 days, that's the whole experiment.
