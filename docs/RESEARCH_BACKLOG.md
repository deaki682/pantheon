# Research Backlog — the house lab's queue

Created 2026-07-04 with the house lab (operator directive). Rules:

- Every item states **the decision it buys** — a study whose result
  changes nothing is not research, it's decoration.
- Priority is operator-set; the lab works top-down unless an item is
  blocked on data.
- An item enters the lab pipeline via `shared.lab.new_strategy` (if a
  tradable hypothesis) or a plain prereg doc (if a measurement study).
  Either way: prereg committed BEFORE data, ledger row after, win or
  lose.
- Done items move to docs/RESEARCH_LEDGER.md and are struck here with a
  pointer.
- **Candidate gates (2026-07-04):** every new item answers the five
  binary gates in lab.md §3b (tape / constraint / capacity-inversion /
  arithmetic / power) BEFORE earning a slug. The gates order the queue.

## Queue order under the gates (2026-07-04 re-rank)

Applying G1–G5 to the open items, using the day's ~100-cell graveyard
as the prior:

1. ~~#7 CEF tenders~~ — ran same evening it topped the queue:
   **REFUTED, wrong sign** (−1.81% CAR, t −3.91 at the filing-date
   entry). The gates' structural read was right; the residual was
   already priced/prorated away. See ledger row 2026-07-04.
2. **#1 quiet-cluster ghost** — already forward-accruing; G2 is its
   weak point (insiders are informed, not constrained) but the cost
   is sunk and the prereg is committed. Tend it, don't expand it.
3. **#2 quality-lens validation** — G4/G2 weak (forecast-shaped), but
   it buys a decision cohort-2 NEEDS and the deadline is real.
4. **#5 guidance rebuild-or-retire** and **#3 sold-ban replication** —
   gated on the fall earnings window; #3 is an avoidance rule (the
   kind that has actually validated here).
5. **#8 PEAD horizon** — G1-adjacent (reaction is tape) but anchored
   to a non-tape event (the report); rides the fall season.
6. **#10 retail-acceleration (ex-Buzz)** — fails G1 and G2; stays
   last unless its mentions archive plus an operator override say
   otherwise.
- Operator's sector-rotation idea (2026-07-04 discussion): fails G1
  as stated; needs a written override plus a frozen regime rule
  before it can take a slug.

| # | Question | Decision it buys | Data needed | Blockers | Priority |
|---|----------|------------------|-------------|----------|----------|
| 1 | **Quiet-cluster ghost**: do insider clusters in names with NO news and NO price move (the "nobody noticed" subset) outperform the full cluster population that measured -6.4%/yr? | Whether a filtered cluster strategy earns a ghost, after the raw signal was refuted | Fresh Form 4 population (fresh-data prereg — the replay dataset is spent), news/price screens at filing date | **Prereg committed 2026-07-04**: [docs/lab_prereg_quiet_cluster_ghost.md](lab_prereg_quiet_cluster_ghost.md); `quiet_cluster_ghost` registered + preregistered in the lab (`hypotheses_ever` 91→92). Fresh window is 2026-06-01 onward (zero overlap with the spent replay). Flags a real gap: `shared.lab`'s registry has no path from `preregistered` straight to forward-tracking when no backtest is possible (this hypothesis has none by design) — prereg recommends running it as a measurement study outside the registry (paper entries via `shared.ghost` under this slug) until the operator decides whether the registry needs a no-backtest-possible transition added. Next: build the rolling fresh population (EDGAR Form-4 scan + 8-K/price/volume quiet-filter) and open first ghost entries. | High |
| 2 | **Quality-lens validation**: does Oracle's quality score predict anything out-of-sample? | Whether quality stays in the cohort-2 selection stack or gets dropped | Fresh XBRL fundamentals + forward returns; prereg BEFORE cohort-2 selection (~11 months away, but prereg soon locks honesty) | None — schedule pressure only | High |
| 3 | **Sold-report ban replication**: does the reaction-direction gate's -1.6%/wk penalty on sold beats replicate in the fall earnings season? | Confidence in Achilles' one validated avoidance rule before real capital rides it again | Fall season earnings + reactions as they occur (pure forward test, zero look-back risk) | Waits for the fall window (~Oct) | Medium |
| 4 | **Delphi point-in-time universe**: rebuild the 118-name momentum backtest with index membership as-of each date; does the +85% survive? | Whether Delphi's backtest evidence is real or survivorship artifact — bears directly on her capital ceiling | Historical index membership lists (point-in-time), delisting-inclusive bars | **COMPLETE 2026-07-04.** Total return replicates (+85.6% vs claimed +85.2%); **alpha and Sharpe do not — the original SPY leg was broken** (honest SPY +86.7% same window: the curated-list system MATCHED the index, −1.1pp). Twist: blind PIT top-119 universe outperformed (+143.5%, +56.8pp) — curation muted the backtest, survivorship story ran backwards. Runbook corrected; capital case rests on live grades as gates already require. [prereg](lab_prereg_delphi_pit_universe.md) · [results](lab_results_delphi_pit_universe.md) · ledger row 2026-07-04 | **DONE** — citation corrected; any curation-rule change is a separate operator decision |
| 5 | **Guidance channel rebuild-or-retire**: does an ex-99-exhibit-based guidance classifier find enough raised-guidance events at a live earnings window to be a usable signal? | Whether the guidance channel stays in Midas/scanner code or is deleted | A legitimate earnings window (next: ~mid-July season start) with exhibit fetching | Waits for earnings season | Medium |
| ~~6~~ | ~~Insider-cluster replay, survivorship-corrected~~ | **DONE 2026-07-04** — refutation stands; only 1/42 gap events resolved in Sharadar (deep-OTC coverage gap persists, disclosed as irreducible-for-now). See [ledger](RESEARCH_LEDGER.md) · [results](oracle_results_cluster_replay_sharadar_2026-07.md). | — | — | — |
| ~~7~~ | ~~CEF tender/discount mechanics~~ | **DONE 2026-07-04 — REFUTED, wrong sign.** Listed-CEF SC TO-I events (n=132, complete 2020–2026 catalog) show mean CAR(25) −1.81%, t −3.91 vs SPY from the filing-date entry. See [ledger](RESEARCH_LEDGER.md) · [results](lab_results_cef_tender_convergence.md). A press-release-anchor variant is a new hypothesis and must re-pass the gates | — | — | — |
| ~~8~~ | ~~Achilles PEAD horizon sensitivity~~ | **CLOSED 2026-07-05 — REFUTED at the source.** `achilles_pead_gauntlet` tested holds {5,10,20} × SMALL/MICRO directly: ALL negative excess (no hold rescues it; 20-day is *more* negative, not less). The tradable long PEAD drift is absent/reversed in the exchange-listed universe. No horizon is "right" because there is no drift to catch. [ledger](RESEARCH_LEDGER.md) · [results](lab_results_achilles_pead_gauntlet.md) |
| 9 | **The Gauntlet — strategy-factory simulation**: build a decade+ daily-bar simulation on the full Sharadar panel (~22k names incl. delisted, point-in-time market-cap universes, cost model) and run a PRE-COMMITTED grid of hundreds of simple strategy variants through it | A quantitative graveyard (which idea families are dead across 12 years x 22k names) + at most a few holdout survivors that earn forward tests — the empirical floor under every god's priors | Sharadar SEP bulk export; EDGAR event caches for event-driven families | **(a) DONE 2026-07-04** — engine (`shared/gauntlet.py`) + bulk fetch (`fetch_sep_bulk_range`, `fetch_daily_bulk_range`) built and tested; see [status doc](lab_gauntlet_engine_status_2026-07-04.md). The market-cap blocker found that morning (SEP-only subscription; DAILY/SF1 served free samples) was **RESOLVED same day** — operator bought the fundamentals entitlement; DAILY verified full (cross-sections ~5.5k names/day, late-1998+, delisted names through final day, marketcap in USD millions) and SF1 serves full quarterly history (AAPL ARQ back to 1993). **COMPLETE 2026-07-04 — REFUTED at the holdout.** (a) engine, (b) prereg ([docs/lab_prereg_gauntlet_v1.md](lab_prereg_gauntlet_v1.md), committed before data), (c) 90-cell in-sample screen, (d) holdout — all run same day. In-sample: 80/90 cells dead (ALL momentum/reversal/size/neglect vs same-bucket EW benchmarks after costs); low-vol sole surviving family (10/12). Holdout: all top-5 low-vol cells positive absolute but NONE beat benchmark 2016-2025 → factory verdict refuted, no forward tests. Full row in [RESEARCH_LEDGER](RESEARCH_LEDGER.md); results [lab_results_gauntlet_v1.md](lab_results_gauntlet_v1.md); per-cell data docs/data/gauntlet_v1/. Reusable: PIT universe catalog (`gauntlet_v1_universes`, unblocks #4), `shared/gauntlet_fast.py` vectorized runner, bulk export pipeline. Any v2 (event-driven families, other implementations) is a NEW prereg + fresh counter increment | **DONE — refuted.** The graveyard is the deliverable and it is now on the ledger. #4 (Delphi PIT) inherits the engine, panel pipeline, and universe catalog |

| ~~11~~ | ~~Delphi ruleset, full window~~ | **DONE 2026-07-04 — REFUTED.** Primary cell 1.08% CAGR vs EW-119 benchmark 7.94% (excess −6.86%/yr, −7.60% vs SPY; negative at 2× costs). The MA exit COST ~5.8pp/yr (no-exit ablation: 6.92%) — 4,552 whipsaws at 32% win, zero drawdown protection. Every pre-2013 regime negative; the #4 window was the outlier. Retire-or-demote decision now with the operator per the pre-committed consequence. See [ledger](RESEARCH_LEDGER.md) · [results](lab_results_delphi_ruleset_fullwindow.md) | — | — | — |
| 10 | **Retail-acceleration basket** (ex-Buzz): do names with *accelerating* (not merely loud) retail mentions, confirmed by real price/volume so it's organic money, outperform over ~5-day horizons as a diversified basket? | Whether the retired Buzz scaffolding earns its way back — validation via the standard lab ratchet (prereg → backtest → ≥20-grade paper forward test) would restore god status; anything less stays dead | ApeWisdom mentions time series (NO history vendor exists — start archiving weekly snapshots NOW so a backtest is possible later), bars for the confirmation gates | Mentions archive must accrue forward before any backtest is honest; mechanical layer already built and tested (`buzz/` package: `parse_apewisdom`, `accelerating`) | Low |

## Retired god scaffolding (2026-07-04, operator directive)

Two gods were cut the same day the house reviewed all its creations:

- **Buzz** — commands `/buzz` and `/buzz-ghost` removed. He entered the
  pantheon through the side door: full god scaffolding for a hypothesis
  with no prereg, no backtest, and no ledger row. The principle this cut
  enforces: **the lab is the only door for new strategies.** The
  hypothesis lives on as backlog #10; the mechanical layer
  (`buzz/acceleration.py`, `buzz/confirm.py`) and his existing cache
  files on `claude/live` remain for the lab study to reuse. The god
  scaffolding (`buzz/scanner.py`, `buzz/ghost.py`) was deleted with the
  commands — if #10 validates, it gets rebuilt from the lab's spec, not
  resurrected from the pre-prereg draft (git history keeps it).
- **Catalyst** — command `/catalyst` removed. A weekly research report
  with no trader, no falsifiable claim, and no downstream consumer. Its
  one reusable output — the coming week's event map — belongs in
  `shared/event_calendar.py` deposits, which any session can make. The
  `catalyst/` package remains as a library (the options-implied-move
  math is citable by any god that wants a priced-in baseline).

## The Alpha Bounty (2026-07-04) — 9-front sweep additions

Full menu + gate scores in **[docs/alpha_bounty_2026-07-04.md](alpha_bounty_2026-07-04.md)**.
Prioritized new items (the long-factor space is spanned; live edge is structure + text):

| Priority | Item | Score | Path |
|---|---|---|---|
| **1** | `gauntlet_v6` — tail-preserving combinations + growth (quality-at-a-price, cap-return-at-a-price, net-iss∩gross-prof, ΔGPOA, ΔATO; min-rank) | 4/5 | RUNNABLE-NOW, one prereg |
| **2** | Spinoff-PARENT drift (add parent leg to Nemesis catalog) | 4/5 | near-free event study |
| **3** | Small-cap cash merger-arb (contractual G4, forced-seller G2) | 4/5 | EDGAR feed build; gauntlet-able |
| **4** | Post-bankruptcy-emergence equity (untested LONG leg of killed distress) | 5/5 prior | hard EDGAR population build; god-able |
| **5** | Lens-B avoidance slate: Beneish M-score + distress-disclosure bundle + Lazy-Prices — exclusion overlays on Plutus | 4/5 each | EDGAR/SF1 builds |
| 6 | Activist 13D (small-mid + escalation); buyback-authorization timing residual | 3/5 | feed builds |

Kills logged (do not slug): sin-premium (owned-factor relabel), earnings-persistence (published null), NOA/ΔNWC/capex (accruals+asset-growth relabels), seasonality (G1-fail), ROIC-WACC (imports dead factors), ESG forced-flows (dead by Greenwood-Sammon).

## Standing sources of new items

- Any god's post-mortem ("why did this trade lose?") that generalizes.
- RESEARCH_LEDGER open questions and "what changed" follow-ups.
- Operator curiosity — filed here first so it gets a prereg, not a vibe.
- Proteus lab hypotheses that need house-scale data he can't build in
  one weekend session.

## House-view steer (2026-07-05) — map every new item by its barrier

Read docs/house_view_llm_edge_2026-07-05.md before proposing. The LLM edge is
real but narrow (reading text→signal, strongest small/negative/neglected),
**decays with adoption**, and is eaten by costs + overtrading. So the queue is
re-steered by the barrier an edge sits behind:

- **STOP proposing crowded-text edges** (news/headline sentiment, naive 10-K
  sentiment) — they fail the barrier test (LLMs already dissolved "text is hard").
  Do not slug them.
- **FAVOR structural forced-seller hypotheses** (durable barrier; also passes G2).
  This is where core research weight goes — items #3 (merger-arb), #4
  (post-BK-emergence), spinoff-orphans, index-deletion, sub-NAV wind-downs.
- **PILOT one capability-frontier hypothesis at a time** (a *window* edge,
  measured for decay from day one):
  - **#11 (new) Full-document synthesis vs headline read** — does an LLM reading
    the ENTIRE merger docket + exhibits + litigation history beat a headline/
    summary read on the same deals? Decision it buys: whether Hermes/Oracle should
    invest in deep-document reads or stay shallow. Barrier: long-context frontier
    the fleet isn't exploiting. G-gates: G2 (structural deals) + power (needs a
    deal population).
  - **#12 (new) Agentic cross-referencing edge** — does an agent that CONNECTS
    sources (index-deletion filing + distressed holder + price dislocation, à la
    the 2026-07-05 forced-seller scan) surface convex names a single-doc screen
    misses? Decision it buys: whether Oracle's sourcing should be agentic-multi-source
    vs single-lens. Barrier: agentic-reasoning frontier.
- **Read A/B decay as the rotate signal.** When any LLM-lift (Hermes, Oracle,
  Proteus) trends toward zero, the edge is crowding — the lab should already be
  testing the next barrier, not defending the old one.

The moat is the rotation, not the position: durable barriers for the core,
frontier windows for the extra, ruthless decay-measurement to know when to move.

## Exhaustive-hunt output (2026-07-05, 14-domain full sweep — 147 mapped, 8 verified)

Survivors (enter the ratchet top-down; neither auto-slugs):

| Item | Verdict | Gate reads | Next step |
|---|---|---|---|
| **#13 Odd-lot tender/Dutch/exchange proration-exemption arb** | LAB_HYPOTHESIS | G2✓ G4✓ (Rule 13e-4 odd-lot carve-out = issuer contractually bound, un-proratable by rule) G5✗ (~3-8 strong events/yr) | Forward event log from EDGAR (SC TO-I/13E-4/S-4) tagging odd-lot carve-outs; ONE live 99-share operational test on RH; kill if supply <12/yr or RH can't un-prorate or median $/event <$150. Opportunistic-only ceiling (~1%/yr of book) — never a god |
| **#4 Post-BK-emergence equity** (re-confirmed) | LAB_HYPOTHESIS | G2✓ verified real (CLO indentures force divestiture of reorg equity) G4✗ G5 thin (~10-20/yr) | Already queued — execute the existing #4 prereg; population from confirmed Plans of Reorganization 2015-2025 |

Kills logged (do not slug; do not re-surface): term/target-term CEF pull-to-NAV
(42/44 are bond funds, priced to par, board escape-hatch breaks G4); Hatch-Waxman
P-IV exclusivity (statutory windfall ≠ forced counterparty; AG cannibalization);
IPO lockup-expiry reversal (ALREADY terminal-refuted: ipo_lockup_reversion,
-10.4% mean excess — the hunt's verify caught the synthesis missing our own
graveyard); event-contagion cross-referencing (Cohen-Frazzini relabel, no forced
seller); tradable CVR arb (compound forecast w/ adversarial payer — Celgene $9→$0;
NOT a contract). Short-vol VRP flagged anti-convex — never propose for this book.

Hunt meta-finding: the contractual-payoff × tiny-capacity quadrant is real but
supply-starved (~1%/yr ceiling). The evening scan's coverage was validated as
~complete for a long-only no-options $19k book — growth comes from proving the
edges we hold, not finding more.

> **post_bk_emergence — CRAM #1 update 2026-07-05: population inadequate, NOT recorded.** The fast
> research fan-out produced 84 emergences but ~70% energy, time-clustered 2016-2021, survivorship-
> floored (OTC re-failers under-captured) — failing the prereg's own exhaustiveness bar. A first-pass
> sim on 52 priceable names shows raw 252d +32.5% but that is ENTIRELY the 2020-21 recovery cohort
> (holdout +113% vs in-sample 2015-19 ~ -18%) = regime/recovery beta, not a forced-seller drift; the
> pre-committed in-sample criterion fails. NOT recorded as refuted (would burn the slug on sub-standard
> data). Slug stays `preregistered`; a fair test needs a survivorship-complete, sector-diversified
> EDGAR plan-of-reorg build (a real project). Moved to cram #2 (spinoff_orphans).

---

## Operator stance (2026-07-05, for the record)

**The operator is comfortable with refutation.** Refuted is a *valued* outcome,
not a failure — it buys a real decision (don't risk capital there) and sharpens
the map of what's dead. The lab is directed to keep churning, researching, and
thinking out-of-the-box indefinitely; a session must NEVER soften a verdict,
avoid a hard test, or keep a refuted idea alive to spare feelings or optics. The
moat is the search-and-retire machine, not any single god. Kill freely; the
capital rides beta while the search runs.

## Cram out-of-box wave (2026-07-05) — queued behind the forced-seller batch

Directions that differ in KIND from the event-population / factor-backtest work,
seeded so the hunt has fresh non-obvious hypotheses ready. Honest gate reads
(incl. the weak points) up front.

| # | Candidate | Thesis / decision it buys | Gate read (honest) |
|---|-----------|---------------------------|--------------------|
| **14** | **`avoidance_overlay` — the "beta-minus-landmines" god** | Every buy-signal died, but the LLM's ONE measured-real skill is AVOIDANCE (Achilles sold-ban −1.6%/wk was the only thing that half-validated; Nemesis veto condemned TWNPQ −58%; Plutus Lens-B is a keep/drop). So make avoidance the THESIS, not a garnish: hold beta/Plutus, LLM VETOES the names it reads as fraud / going-concern / covenant-breach / terminal-decline. **Decision it buys:** whether avoidance is a standalone god or an overlay folded into Plutus/Proteus. **Backtest path:** mechanical distress flags (EDGAR going-concern, auditor resignation, restatement, covenant breach) as the avoidance signal first; LLM version as the forward A/B (Arm A LLM-veto vs Arm B mechanical vs Arm C no-veto). | G1 PASS (filing/text read, not price). **G2 WEAK — the honest flag:** it's an information-PROCESSING edge (read deterioration before slow institutions), not a structural-constraint edge; "the market underreacts" is not a constraint. It's a CAPABILITY-FRONTIER bet that DECAYS with adoption (house-view doc). G3 **SCALABLE (rare plus)** — avoidance applies to the whole book at any size, unlike the capacity-capped forced-seller scraps → fits the growth mandate as an overlay. G4 fail (avoids drift, no contractual terminal). G5 strong (whole-universe). |
| **15** | **`event_diversifier_sleeve` — the portfolio IS the god** | The small forced-seller/event edges (post-BK, spinoff-orphans, merger-arb, sub-NAV, CEF-discount) are each modest and capacity-capped, but UNCORRELATED. Combined into one convex event sleeve, the *diversification* compounds with far lower drawdown than any piece — the free lunch is construction, not discovery. **Decision it buys:** whether Oracle becomes a multi-edge event-driven diversifier fund rather than the house hunting one big edge. | SECOND-ORDER — activates once ≥2 component edges clear their own backtests (can't combine unproven scraps). G1/G2/G4 INHERITED per-component. G3 capacity-capped (sum of capped edges) but that's fine for a diversifier. G5 **HELPED** — the combined event rate across channels beats any single edge's thin cadence. **Test:** `combine_curves` / correlated-drawdown gap — does the combined sleeve's Sharpe/maxDD beat the best single component? |

### Trodden-ground wave (2026-07-05) — edge in the MOST-efficient corners

The principle: efficiency kills INFORMATION edges but not STRUCTURAL/MECHANICAL
ones — the flows the crowd creates BY crowding. Look for the mechanical residue,
not the informational one. Two angles hiding in the most-arbitraged ground.

| # | Candidate | Thesis / decision it buys | Gate read (honest) |
|---|-----------|---------------------------|--------------------|
| **16** | **`passive_crowding_reflexivity`** — trade the distortion indexing creates in the S&P 500 itself | Every S&P dollar buys mega-caps in proportion to size, price-insensitively → mechanically inflates the top regardless of fundamentals; passive % keeps RISING (deepening barrier). Edge = the flow, not stock-picking: cap-weight vs equal-weight at concentration extremes, index add/delete flow, top-heaviness mean-reversion. **Decision it buys:** whether an EW-vs-CW tilt (or an index-flow overlay) earns a real, GROWING structural premium in the most-efficient universe. | G1 borderline (uses index weights, but the signal is a FLOW state, not a price forecast). **G2 STRONG + growing** — passive funds are the named price-insensitive counterparty and the pool expands yearly. G3 **SCALABLE** (it IS the S&P — a rare growth-compatible structural edge). G4 fail (drift/mean-reversion). G5 strong. The standout: durable, scalable, strengthening. |
| **17** | **`overnight_intraday_split`** — the equity premium accrues overnight, not intraday | In SPY/large-caps, ~the entire historical equity premium is earned close→open; the intraday session is ~flat-to-negative. Persists in the most-studied instrument because it's structural (overnight = macro news + futures flows + ETF-creation hit a market that can't trade), not an info edge anyone arbitrages by "knowing" it. **Decision it buys:** whether a close-buy/open-sell overlay (or just tilting exposure to the overnight window) is real net of costs — likely NOT for a small book (daily turnover), but a clean, famous, mechanical oddity worth one measurement. | G1 FAIL (pure price/time signal) → needs operator override; the mechanism is structural (flow-timing), not predictive. G2 medium (overnight-flow structure). G3 scalable but G5-killed-by-COST (daily round-trips) — the turnover gate is the likely killer, same as momentum. Measure, expect refutation-by-cost. |

> **spinoff_orphans — CRAM #2: REFUTED 2026-07-05.** Fair population (227, sector-diverse), clean kill: small tail underperforms size-matched EW -9.3% (holdout -22.6%). Opposite of thesis; criterion 5 fails. Terminal. Not a diversifier-sleeve component. See [ledger](RESEARCH_LEDGER.md) / [results](lab_results_spinoff_orphans.md). Cram continues: residual_momentum_llm (ready) -> avoidance_direct / call_evasion -> sub-NAV / odd-lot.

> **CRAM update 2026-07-05:** `residual_momentum_llm` REFUTED (momentum closed in all forms). `avoidance_direct` mechanical arm **SUPPORTED (weak/decaying)** -- first non-refutation; the 'LLM=avoidance' foundation holds. Next: forward LLM-vs-mechanical A/B for avoidance (measure #1 of the LLM instrument track); cram continues to sub-NAV / odd-lot / call_evasion lexicon arm.

> **call_evasion — VERDICT filed 2026-07-05: INCONCLUSIVE, LLM lost to the word-count.** The blind LLM candor-read on 53 MD&A packets was FLAT (Spearman +0.02) while the crude Loughran-McDonald lexicon showed the only pulse (−0.27, t=−1.99) and the LLM added nothing in the joint OLS (t=0.19). Prereg premise ("LLM evasion beats mere tone") negative. Slug → backtested; stays open only for the transcript-gated Q&A arm. See [ledger](RESEARCH_LEDGER.md) / [results](lab_results_call_evasion.md).

---

## Exhaustive-hunt output (2026-07-05 re-run, 14-domain full sweep — 86 mapped, 12 promising, 2 verified)

**The seam this sweep found: forced-flow's UNDERLYING side.** The house has killed the
EVENT side of forced flow (index add/delete, CEF tenders — all refuted). It has NEVER
tested the reversal of forced SELLING in the concentrated *underlying holdings* a
distressed fund is forced to dump. Freshly evidenced 2024-26: **Ponzi Funds** (arXiv
2405.12768, ~−6%/yr constituent alpha at ~20× ADV); **Residual Supply** (arXiv
2605.30672, +160–342bps decile spreads, doubling when absorption is tight). **0
GOD_CANDIDATE** (no scalable engine — consistent with the house prior); **2
LAB_HYPOTHESIS** survivors. Both FAIL G4 (reversion forecast, not contract) and carry the
small-cap-reversal refutation headwind — real hypotheses to test honestly, NOT god tracks.

Survivors (enter the ratchet top-down; neither auto-slugs; recon does NOT tick `hypotheses_ever`):

| # | Item | Verdict | Gate reads | Next step |
|---|---|---|---|---|
| **18** | **`thematic_etf_firesale_reversal`** ✅ PREREGISTERED 2026-07-05 ([prereg](lab_prereg_thematic_etf_firesale_reversal.md), hypotheses_ever 197) — buy orphaned constituents of SHRINKING thematic ETFs | LAB_HYPOTHESIS | G1✓ (daily flow state, not price forecast) · G2✓-caveat (redeeming AP is the named seller; in-kind redemption is one step removed but non-offsetting in the illiquid tail Greenwood-Sammon can't reach) · G3✓✓ STRONG (effect lives only where ETF position ≫ constituent ADV; $19k ideal) · **G4✗ (reversion forecast, not contract)** · G5~ (~20/yr, unverified) | **Cleanest advantage: daily-public ETF holdings + shares-out sidestep BOTH the N-PORT lag AND the Wardlaw-2020 return-contamination.** Prereg BEFORE data. Survivorship-free constituent panel (issuer daily basket + shares-out + Sharadar SEP bars). Signal = LONG when per-constituent forced-sell pressure (net redemption × weight / ADV) EXHAUSTS. DECISIVE guard (from spinoff_orphans/ipo_lockup): excess vs SIZE-and-SECTOR-matched EW, NOT raw return. Pre-commit kills: (a) reversal excess ≤0 net of realistic microcap cost, (b) small/illiquid subset is the WORST subset again, (c) <20 events/12mo. Mid-priority — two-refutation headwind (spinoff_orphans −9.3%, ipo_lockup −10.4%, identical shape). |
| **19** | **`absorption_pressure_reversal`** — mutual-fund redemption fire-sale reversal (residual-supply construction ONLY) | LAB_HYPOTHESIS | G1✓ (return-orthogonal residual-supply signal, survives pre-event-return controls — NOT the Wardlaw-contaminated FIT) · G2✓✓ STRONG/durable ('40-Act daily-redemption fund = named non-discretionary seller; no Greenwood-Sammon offset) · G3✓ PATHOLOGICAL (edge only in lowest-$-volume names: 375bps/3mo low-vol vs 4–24bps high-vol) · G4✗ · G5~ | Viable ONLY with the return-orthogonal residual-supply construction (the classic Coval-Stafford FIT measure is Wardlaw-2020 contaminated — the reversal vanishes once cleaned). Same size-matched-benchmark + realistic-cost discipline as #18. LOWER priority than #18 (which observes the forcing event directly rather than inferring it). |

Kills logged (do not slug; do not re-surface): **SPAC redemption-floor arb** (contractual
floor real but G4 upside too thin for this book + most-crowded riskless arb); **fund
liquidation overhang** (wind-down carries a best-execution duty = NOT forced-price-insensitive,
G2 weak); **distressed deep-discount preferreds** (G1 discount-lean + RH baby-bond
tradability); **foreign-filing/ADR translation latency** (crowded text underreaction, NO
forced counterparty — the exact edge the house-view says LLMs dissolved); **credit-agreement
exhibit read** (covenant binds issuer→lenders, equity is residual — no forced seller pays
you); **intangible-adjusted profitability factor** (pure factor, G2/G4 fail; fights the
'fundamentals spanned' prior). **Russell small-cap DELETION reversal** (from the delta
pre-run): LAB but low-priority — Greenwood-Sammon shows the deletion effect decayed to
~−0.6%, and it's the same dumped-microcap shape as the two terminal refutations; log
behind the underlying-holdings family, which is more fertile. Avoidance-overlay text ideas
(non-GAAP-gap, comment-letters, exec-departure) fold onto the existing Lens-B slate (#14) —
justify at most ONE more A/B arm (credit-agreement had the best G2 of that cluster), not four new flags.

Hunt meta-finding (re-run): the fertile corner is the **UNDERLYING-HOLDINGS side of forced
flow** — not the event side (mined dry) and not the text-avoidance side (decaying, already
queued as #14). Growth still comes from proving the edges we hold; these two are the first
genuinely-new structural hypotheses since the evening sweep, and they enter the ratchet
behind the already-queued forced-seller batch (#4 post-BK, #13 odd-lot).

> **#18 `thematic_etf_firesale_reversal` — PREREGISTERED then DATA-BLOCKED 2026-07-05.**
> Feasibility probe on commit: the daily-flow backtest as frozen is NOT buildable with house
> data. Sharadar SEP is equities-only (no ETFs — SPY/ARKK/XLK all empty), and there is no
> daily ETF shares-outstanding / holdings source for CLOSED funds in the repo or free feeds.
> Only EDGAR N-PORT exists, and it is inadequate for the frozen design: quarterly (not daily),
> clean only post-2019 (collapses the ≤2019 in-sample), month-end net-assets only (a
> Δ-net-assets flow proxy confounds flow with return — the Wardlaw-2020 contamination, and ARKK
> is the cautionary case: AUM fell on PERFORMANCE while net flows were positive). Per the prereg's
> own pre-commitment, the slug **STAYS `preregistered`, not refuted** — the ratchet caught the wall
> before a contaminated build burned the slug (the `post_bk_emergence` precedent). Clean unblock =
> a paid ETF-holdings-history source (operator decision).
>
> **EXPLORATORY PEEK OUTCOME (2026-07-05, LOOK-DON'T-TOUCH — may NOT be cited for any rule change):**
> Ran the liquidated-thematic-ETF smell-test on 3 cannabis funds (POTX/THCX/PSDN). DATA-DEFEATED,
> with one substantive lesson: (1) N-PORT series resolution failed for 2/3 (POTX/THCX file under large
> multi-series trusts — the fund's series didn't resolve even in a 60-filing wide search); (2) **PSDN was
> already down to 4 tiny holdings MONTHS before its close** — the insight: a dying thematic fund BLEEDS OUT
> GRADUALLY over its decline, it does NOT hold a full basket to the end and dump it in one forced event,
> so the clean "100% forced liquidation" premise is weaker than assumed; (3) the OTC MSOs that carry the
> effect aren't in SEP; (4) the n=2 names that DID resolve showed the graveyard's wrong-sign pattern —
> dumped −4.5% into the close, then KEPT FALLING −6.1%/63d (no reversion). Net: NO positive signal to
> justify buying data, mild DISCOURAGEMENT (clean-dump events rarer/messier than assumed + the resolvable
> slice echoed spinoff_orphans/ipo_lockup). Recommendation: **do NOT buy ETF-holdings data for #18 on
> current evidence**; leave it preregistered/data-blocked as a standing option that re-opens only if a
> survivorship-free daily-holdings source arrives cheaply for another reason.

---

## Weird-hunt output (2026-07-05, 12 unconventional domains — 75 mapped, 6 promising, 1 verified)

Deliberately off-beat sweep (attention/salience, settlement plumbing, number psychology, network
topology, reflexive flows, bio-rhythms, behavioral tells, calendar micro-structure, lottery/skew,
long-tail info-geometry, weird forced-flow corners, wrapper mechanics). Same 5 gates, extra-strict G1.
Most weird ideas died on G1 (no forced seller = "crowd misprices" = noise); 2 auto-dropped in
synthesis (a stray test injection; a net-issuance/Lens-B relabel). **0 GOD_CANDIDATE; 1 LAB_HYPOTHESIS.**

| # | Item | Verdict | Gate reads | Next step |
|---|---|---|---|---|
| **20** | **`drip_paydate_pressure`** — DRIP reinvestment creates a price-insensitive forced BUYER on calendar-certain pay dates | LAB_HYPOTHESIS | G1✓ (real mechanical flow) · **G2✓✓ HARD (the prize: named, contract-bound, price-insensitive forced buyer = DRIP plan administrator, on a calendar-certain date — a genuine weird spine, not a G1 sentiment fail)** · G3✓ but double-edged (edge only in illiquid high-limits-to-arb names — where cost also lives) · **G4✗ (pressure hump COMPLETELY reverses → required round-trip, a reversion forecast, no contract pays you)** · G5✓ (thousands of pay dates/yr; monthly-pay CEFs give dozens) | Prereg a cheap survivorship-free backtest BEFORE data (Sharadar bars + calendar-certain CEF/high-DRIP pay-date calendar). DECISIVE pre-committed kill = net-of-realistic-retail-round-trip-cost excess ≤0 vs a size/liquidity/yield-matched EW benchmark (NOT raw return). Test the round-trip explicitly at 1× AND 2× cost + the tightest-cost expression (monthly-pay CEF basket). Pre-commit kills: (a) net excess ≤0 at realistic spread, (b) the illiquid/high-spread subset is the WORST subset (the three-refutation pattern), (c) effect decayed post-2017-publication. **Honest prior: expected death at the cost gate** — published effect (Berkman-Koch JFQA 2017, Hartzmark-Solomon AER 2024) whose gross edge scales with the exact spread you pay. Low priority; file behind the forced-seller batch. Not a god — a whisker from REJECT.

Kills logged (do not slug; do not re-surface): **coverage_termination_shock** (broker research-coverage
termination as an attention shock — breaks on structural gates + external evidence; the exogenous-event
framing is cleaner than static-neglect but doesn't clear G2/G4/power); **holdco_stub_discount_collapse**
(graveyard-adjacent relabel of the already-killed term/target-term CEF pull-to-NAV — same discount-lean
G1, same board/controller escape-hatch G4; listed-stake NAV arithmetic doesn't rescue it); most
bio-rhythm / ticker-psychology / calendar theories (pure G1, no forced counterparty).

> **STRATEGICALLY-FLAGGED REJECT — `vol_control_releveraging`.** Named a REAL and GROWING forced
> counterparty (~$132B systematic vol-control funds, prospectus-bound to mechanically RE-LEVER after
> realized vol falls, −0.95 vol-to-exposure). Excellent, strengthening G2. But our long-only /
> no-leverage / no-derivatives book can only express it as "buy the VIX dip" — a forbidden G1 timing
> signal. **A perfect named counterparty attached to an instrument we are not allowed to trade.** REJECT
> for THIS book — but log it: **re-open only if the mandate ever gains derivatives/futures**, because the
> counterparty is real and growing.

Weird-hunt meta-finding: even in deliberately unconventional territory the pattern held — the single
real-spine survivor (DRIP) still fails G4 and rides a cost-gated round-trip, expected to die at cost.
No engine hides in the weird corners either; consistent with LEAN_ON_BETA (growth = prove the edges
already held, not find a new one). Recon only — did NOT tick `hypotheses_ever`.
