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

| # | Question | Decision it buys | Data needed | Blockers | Priority |
|---|----------|------------------|-------------|----------|----------|
| 1 | **Quiet-cluster ghost**: do insider clusters in names with NO news and NO price move (the "nobody noticed" subset) outperform the full cluster population that measured -6.4%/yr? | Whether a filtered cluster strategy earns a ghost, after the raw signal was refuted | Fresh Form 4 population (fresh-data prereg — the replay dataset is spent), news/price screens at filing date | **Prereg committed 2026-07-04**: [docs/lab_prereg_quiet_cluster_ghost.md](lab_prereg_quiet_cluster_ghost.md); `quiet_cluster_ghost` registered + preregistered in the lab (`hypotheses_ever` 91→92). Fresh window is 2026-06-01 onward (zero overlap with the spent replay). Flags a real gap: `shared.lab`'s registry has no path from `preregistered` straight to forward-tracking when no backtest is possible (this hypothesis has none by design) — prereg recommends running it as a measurement study outside the registry (paper entries via `shared.ghost` under this slug) until the operator decides whether the registry needs a no-backtest-possible transition added. Next: build the rolling fresh population (EDGAR Form-4 scan + 8-K/price/volume quiet-filter) and open first ghost entries. | High |
| 2 | **Quality-lens validation**: does Oracle's quality score predict anything out-of-sample? | Whether quality stays in the cohort-2 selection stack or gets dropped | Fresh XBRL fundamentals + forward returns; prereg BEFORE cohort-2 selection (~11 months away, but prereg soon locks honesty) | None — schedule pressure only | High |
| 3 | **Sold-report ban replication**: does the reaction-direction gate's -1.6%/wk penalty on sold beats replicate in the fall earnings season? | Confidence in Achilles' one validated avoidance rule before real capital rides it again | Fall season earnings + reactions as they occur (pure forward test, zero look-back risk) | Waits for the fall window (~Oct) | Medium |
| 4 | **Delphi point-in-time universe**: rebuild the 118-name momentum backtest with index membership as-of each date; does the +85% survive? | Whether Delphi's backtest evidence is real or survivorship artifact — bears directly on her capital ceiling | Historical index membership lists (point-in-time), delisting-inclusive bars | Was re-blocked 2026-07-04 (morning) when `SHARADAR/DAILY` turned out to be unentitled sample data; **UNBLOCKED same day** — operator bought the fundamentals entitlement, DAILY verified full (cross-sections ~5.5k names/day from late 1998, delisted names through final trading day). `shared/gauntlet.py` (with `signal_lag`) is now built and battle-tested by #9; reuse it rather than duplicating. **Process gap found 2026-07-04 (this session)**: a `delphi_pit_top119` population (21 quarterly top-119 lists, `cache/shared_pop_delphi_pit_top119.json`) already exists, built 2026-07-04, and its own `definition` field cites `docs/lab_prereg_delphi_pit_universe.md` as its prereg — that file was never committed to the code branch (checked: absent from `docs/` and from all git history). Before this backlog item's actual backtest (the momentum-return computation) runs, a real prereg for #4's success criteria/splits must be committed FIRST — the existing population (pure index-membership, no return/outcome data) is reusable as infrastructure, but the metric/thresholds are not yet frozen anywhere in the repo. | High — UNBLOCKED, needs its prereg written before any return is computed |
| 5 | **Guidance channel rebuild-or-retire**: does an ex-99-exhibit-based guidance classifier find enough raised-guidance events at a live earnings window to be a usable signal? | Whether the guidance channel stays in Midas/scanner code or is deleted | A legitimate earnings window (next: ~mid-July season start) with exhibit fetching | Waits for earnings season | Medium |
| ~~6~~ | ~~Insider-cluster replay, survivorship-corrected~~ | **DONE 2026-07-04** — refutation stands; only 1/42 gap events resolved in Sharadar (deep-OTC coverage gap persists, disclosed as irreducible-for-now). See [ledger](RESEARCH_LEDGER.md) · [results](oracle_results_cluster_replay_sharadar_2026-07.md). | — | — | — |
| 7 | **CEF tender/discount mechanics** (Proteus's shelved thread): do announced tenders at >12% discounts close mechanically? | A potential validated strategy for the live book | Complete SC TO-I / N-23C-3 catalog from EDGAR full-index; CEF NAV series | Population buildable now at EDGAR rate limits; NAV data source TBD | Medium |
| 8 | **Achilles PEAD horizon sensitivity**: is 5 trading days the right hold, or does the drift run 10-20 days in the neglected-name subset? | Achilles' hold parameter for the fall season (one decision, once) | Fresh season's trades (forward), or vendor bars for a clean replay on names outside the spent replay dataset | Sharadar SEP landed 2026-07-04 | Low — unblocked |
| ~~9~~ | ~~The Gauntlet — strategy-factory simulation~~ | **DONE 2026-07-04** — **REFUTED, factory-wide**: 0/90 cells passed stage 2; the 10 stage-1 survivors (all low-vol) all failed the holdout benchmark. See [ledger](RESEARCH_LEDGER.md) · [results](lab_results_gauntlet_v1.md). Reusable house assets from the build: `shared/gauntlet.py` engine (`signal_lag` execution-lag feature), `gauntlet_v1_universes` population (612 rows, `cache/shared_pop_gauntlet_v1_universes.json`) — both available for #4 below without rebuilding. | — | — | — |

## Standing sources of new items

- Any god's post-mortem ("why did this trade lose?") that generalizes.
- RESEARCH_LEDGER open questions and "what changed" follow-ups.
- Operator curiosity — filed here first so it gets a prereg, not a vibe.
- Proteus lab hypotheses that need house-scale data he can't build in
  one weekend session.
