# Results — `tender_target_14d9` (third-party tender targets)

- **Prereg:** [docs/lab_prereg_tender_target_14d9.md](lab_prereg_tender_target_14d9.md)
- **Run:** 2026-07-04, `run_tender_target_14d9.py`; artifacts
  `docs/data/tender_target_14d9/results.json`
- **Registry:** **inconclusive** (backtested); `hypotheses_ever` 104→105

## Verdict: INCONCLUSIVE — economically, a precise null

All 669 SC 14D-9 filings 2016–2025; 384 matched-deduped listed targets
(delisted names included via secfilings-CIK matching — acquired
targets delist, so this is the study's anti-survivorship spine):

| measurement | n | mean CAR(25) | t | win | median |
|---|---|---|---|---|---|
| **carry-at-cash-out (primary)** | 384 | **+0.15%** | 0.21 | 34.6% | −1.45% |
| survivors-only (biased, disclosed) | 129 | +2.60% | 1.28 | 41.1% | −0.97% |

Not refuted (the mean is a hair above zero), nowhere near the
supported bars. The post-14D-9 merger-arb residual at a daily-bar
horizon is **institutionally priced to zero gross** — and any real
spread cost turns it reliably slightly negative for a harvester at
our scale. The prereg's G3 answer ("partial — this is institutional
territory") was the operative truth.

## The measurement lesson (third defect caught today, before recording)

The first pass silently dropped 255 of 384 events from the day-25
sample: their price series ENDED mid-window because the acquisition
COMPLETED — the successes cashing out at the deal price. The
surviving 129 were disproportionately busted and lagging deals, and
their +2.60% was attrition bias, not edge. `event_car` now has a
tested `carry_last` mode (stock leg frozen at the final print, the
benchmark keeps running) and its docstring carries the rule: for
M&A-family populations, series-ends-drop deletes exactly the winners.

## Family close-out

Four tender-family cells tonight tell one consistent story: the
announcement may carry regime-bound value (TO-C window 1, killed in
replication), and every post-filing residual — CEF launch, operating
launch, target response — is priced. The tender family is closed;
a fifth anchor would be curve-fitting the event timeline.
