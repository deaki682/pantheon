# Pre-registration: insider-cluster replay, survivorship correction

Committed 2026-07-04, BEFORE any Sharadar bar is fetched for this study.
House lab measurement study (backlog item #6) — no tradable claim, so
it does not enter the `shared.lab` strategy registry, but the same
discipline applies: prereg before data, results doc + ledger row
regardless of outcome.

## Question

The 2026-07-03 full-population insider-cluster replay
(`docs/oracle_prereg_cluster_replay.md` /
`docs/oracle_replay_results_2026-07.md`) found 12-month excess vs IWM
of **−6.38%** (n=291) and REFUTED the cluster signal as an auto-buy.
42 of the 934 events (4.5%) were tagged `unpriceable_no_bars` and
excluded from every horizon — the broker (Robinhood) carries no bars
for OTC/delisted/thinly-traded names. Sharadar SEP (purchased
2026-07-04, survivorship-bias-free, 15,593 delisted companies) may
resolve some of these.

**Does including the previously-unpriceable events change the −6.4%
verdict, and in which direction?** The backlog's own framing: dead
names were buys too, so if they can now be priced, excess return
should get WORSE on average (delistings skew down) unless the
Sharadar-recoverable subset happens to be dominated by buyouts
(delisted at a premium) rather than failures.

## Population (FROZEN — reused, not re-derived)

- **No new Form 4 fetching.** The 934-event population, cluster
  definition, entry-price rule (first close ≥ knowability + 5 calendar
  days), and horizons (126td / 252td) are exactly as frozen in
  `docs/oracle_prereg_cluster_replay.md`. This study only attempts to
  PRICE the 42 events tagged `status: unpriceable_no_bars` in
  `docs/data_oracle_replay_graded_2026-07.json`, using Sharadar SEP
  where the broker had no bars.
- The 42 tickers (frozen list, taken verbatim from the existing data
  file, not re-selected): ETST, LBSR, MYCB, NORD (×2 events), NWPP
  (×3), QNBC, LCTC, LARAX, GTHP, OABIW, EMYB (×3), VREOF, SCND, BMNM
  (×2), CSBB (×2), UTGN (×2), RYES (×2), VWFB, NNUP, LAWIL, PHXE-P,
  GGROU, CWGL, CCFN (×2), CHUC, BUKS, PGIM, IVFH, PALX, WBHC.

## Method (FROZEN)

1. For each of the 42 events, `shared.sharadar.resolve_ticker(sym,
   as_of=event_date)` — if this raises (no TICKERS match: name
   predates coverage, or is an OTC/pink-sheet ticker Sharadar's
   NYSE/NASDAQ/AMEX-centric universe never carried), the event stays
   **unresolved** and is reported as such, same disclosure standard as
   the original "unpriceable" bucket. This is not expected to resolve
   all 42 — Sharadar's own QA (`docs/sharadar_qa_2026-07-04.md`) notes
   no OTC/pink-sheet coverage claim, and several of these tickers
   (e.g. PHXE-P, GGROU) look like non-major-exchange names.
2. For resolved tickers: `fetch_sep_bars(final_ticker)`, apply the
   SAME entry rule (first close ≥ knowability + 5 calendar days) and
   the SAME horizon windows (126 / 252 trading days from entry) as the
   frozen study. If the bar series ends before the horizon (delisted
   mid-window), the event is `unresolved_delisted_before_horizon` for
   that horizon specifically — reported, not scored as a loss (same
   "manual disposition" rule as the original prereg — a delisting is
   often a premium buyout, not death, and auto-scoring either way
   biases).
3. Benchmark: IWM total return over the identical window, from the
   broker (Robinhood `get_equity_historicals`) — Sharadar does not
   carry ETFs (confirmed in `docs/sharadar_qa_2026-07-04.md`), so the
   benchmark leg is unchanged from the original study.
4. **Combine, don't replace.** The corrected h126/h252 stats =
   original graded events (892/612/291 respectively, unchanged) PLUS
   whichever of the 42 newly resolve at each horizon. Report both the
   original and corrected n/mean/t/win-rate side by side.

## What would count as a meaningfully changed verdict

- **Materially worse**: corrected 12-month mean excess drops below
  −8% (roughly 25% relative move) AND the newly-added events'
  individual mean excess is below the original −6.38%.
- **Materially better**: corrected 12-month mean excess rises above
  −4% AND newly-added events average better than −6.38%.
- **No material change**: corrected mean stays within ~±2pp of −6.38%,
  OR fewer than 5 of the 42 events resolve with a completed 12-month
  horizon (too few new data points to move a 291-event mean
  meaningfully — reported as "resolved but immaterial," not silently
  dropped).
- The frozen REFUTED verdict from the original study is not
  reversible by this correction alone regardless of direction — that
  requires the corrected mean to cross the original refutation
  threshold (excess > 0, t ≥ 2, n ≥ 150), which 5-40 additional
  microcap events cannot achieve on their own. This study answers
  "does the magnitude move, and which way," not "is the signal now
  validated."

## Bias checklist (all 8 items addressed before data)

1. **Look-ahead**: entry/exit rules are byte-identical to the frozen
   original study; no rule is loosened or tightened based on knowing
   any outcome.
2. **Survivorship**: this study EXISTS to reduce survivorship bias
   (the 42 excluded events were disproportionately likely to be
   delistings, i.e. survivorship's classic failure mode); any ticker
   that still can't be resolved is named and reported, not dropped
   silently.
3. **Multiple testing**: this is re-analysis of an existing frozen
   population's residual, not a new hypothesis draw — it does not
   increment `hypotheses_ever` in `cache/lab_registry.json` (no
   tradable claim registered) but IS logged in
   `docs/RESEARCH_LEDGER.md` with the house's current
   `hypotheses_ever` count cited for context.
4. **Selection on outcome**: the 42-ticker list was frozen on
   2026-07-03 (before Sharadar existed as an option), so there is no
   opportunity to have cherry-picked which unpriceable names to
   attempt.
5. **Benchmark consistency**: IWM windows are computed with the exact
   same date-alignment code path as the original study; no new
   benchmark logic.
6. **Regime caveat**: unchanged from the original — this is the same
   Jan 2025 – Jul 2026 window riding the same small-cap rally; a
   worse or better correction from 42 microcap names does not change
   that caveat.
7. **Data-vendor honesty**: Sharadar SEP's own documented gap (no
   OTC/pink-sheet universe guarantee) is disclosed up front in this
   prereg, not discovered after seeing how many resolve.
8. **One shot**: results are reported exactly as computed on the first
   pass — no re-cutting the 42 into sub-groups after seeing which
   ones look good.

## What this is NOT

- Not a new `shared.lab` strategy hypothesis — no registry entry.
- Not a reversal of the REFUTED verdict on the original study (that
  stands, frozen, regardless of this correction's direction).
- Not a change to Oracle's live cohort or dossier selection.
