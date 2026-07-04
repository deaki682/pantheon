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
| 1 | **Quiet-cluster ghost**: do insider clusters in names with NO news and NO price move (the "nobody noticed" subset) outperform the full cluster population that measured -6.4%/yr? | Whether a filtered cluster strategy earns a ghost, after the raw signal was refuted | Fresh Form 4 population (fresh-data prereg — the replay dataset is spent), news/price screens at filing date | Needs a fresh quarter of filings; population buildable now, outcomes accrue forward | High |
| 2 | **Quality-lens validation**: does Oracle's quality score predict anything out-of-sample? | Whether quality stays in the cohort-2 selection stack or gets dropped | Fresh XBRL fundamentals + forward returns; prereg BEFORE cohort-2 selection (~11 months away, but prereg soon locks honesty) | None — schedule pressure only | High |
| 3 | **Sold-report ban replication**: does the reaction-direction gate's -1.6%/wk penalty on sold beats replicate in the fall earnings season? | Confidence in Achilles' one validated avoidance rule before real capital rides it again | Fall season earnings + reactions as they occur (pure forward test, zero look-back risk) | Waits for the fall window (~Oct) | Medium |
| 4 | **Delphi point-in-time universe**: rebuild the 118-name momentum backtest with index membership as-of each date; does the +85% survive? | Whether Delphi's backtest evidence is real or survivorship artifact — bears directly on her capital ceiling | Historical index membership lists (point-in-time), delisting-inclusive bars | Sharadar SEP landed 2026-07-04 (no PIT index membership — reconstruct small/mid-cap-as-of from SEP market-cap fields; method goes in the prereg) | High — UNBLOCKED |
| 5 | **Guidance channel rebuild-or-retire**: does an ex-99-exhibit-based guidance classifier find enough raised-guidance events at a live earnings window to be a usable signal? | Whether the guidance channel stays in Midas/scanner code or is deleted | A legitimate earnings window (next: ~mid-July season start) with exhibit fetching | Waits for earnings season | Medium |
| 6 | **Insider-cluster replay, survivorship-corrected**: re-run the full-population cluster replay including the delisted names the broker couldn't serve — does -6.4%/yr get worse (dead names were buys too) or better? | Final word on the cluster signal; also the acceptance test for the vendor data | Delisting-inclusive daily bars 2020-2026 | Sharadar SEP landed 2026-07-04 (docs/sharadar_qa_2026-07-04.md) | High — UNBLOCKED, first in queue (doubles as the feed's trial by fire) |
| 7 | **CEF tender/discount mechanics** (Proteus's shelved thread): do announced tenders at >12% discounts close mechanically? | A potential validated strategy for the live book | Complete SC TO-I / N-23C-3 catalog from EDGAR full-index; CEF NAV series | Population buildable now at EDGAR rate limits; NAV data source TBD | Medium |
| 8 | **Achilles PEAD horizon sensitivity**: is 5 trading days the right hold, or does the drift run 10-20 days in the neglected-name subset? | Achilles' hold parameter for the fall season (one decision, once) | Fresh season's trades (forward), or vendor bars for a clean replay on names outside the spent replay dataset | Sharadar SEP landed 2026-07-04 | Low — unblocked |

## Standing sources of new items

- Any god's post-mortem ("why did this trade lose?") that generalizes.
- RESEARCH_LEDGER open questions and "what changed" follow-ups.
- Operator curiosity — filed here first so it gets a prereg, not a vibe.
- Proteus lab hypotheses that need house-scale data he can't build in
  one weekend session.
