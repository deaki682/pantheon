# Results — `cef_toc_anchor_2014_19` (out-of-sample replication: FAILED)

- **Prereg:** [docs/lab_prereg_cef_toc_anchor_2014_19.md](lab_prereg_cef_toc_anchor_2014_19.md)
  (committed before the 2014–2019 window was touched)
- **Run:** 2026-07-04, `run_cef_toc_2014_19.py`; artifacts
  `docs/data/cef_toc_2014_19/results.json`
- **Registry:** **refuted** (terminal); `hypotheses_ever` 103→104

## Verdict: REFUTED — the announcement-anchor edge does not replicate

Same frozen rule as `cef_tender_toc_anchor`, untouched window:

| statistic | 2014–2019 (this study) | 2020–2026 (window 1) |
|---|---|---|
| n | 65 | 82 |
| mean CAR(25) | **−1.96%** | +1.00% |
| shrunk | −1.50% | +0.81% |
| t | **−5.34** | 1.92 |
| win rate | **21.5%** | 61.0% |
| median | −2.16% | +1.52% |

The curve is monotonically negative from day 0 (−0.5% at 5, −1.7% at
20, −2.0% at 25/40): **no hump, no rise, no reversal** — the shape
prediction stated in the prereg failed alongside the level. Five of
six years negative; the one positive year (2017, n=9) is small and
calm. Coverage clean: zero events without bars, two screened.

## Reading

Window 1's +1.00% was the era, not the mechanism — most plausibly the
2024 activist/discount-management tender wave (Saba-pressure
programs), where announcements coincided with sustained activist
buying. In an ordinary regime, a CEF announcing a tender is a fund
whose discount reflects real distress in its holder base, and the
announcement window UNDERPERFORMS.

**Consequences:** no forward test (the 2.3-year forward accrual this
replication was run to pre-empt is cancelled — one hour of compute
bought the same answer). `cef_tender_toc_anchor` remains recorded
inconclusive on its own window; the tender-anchor family (TO-I entry
× 2 populations, TO-C entry × 2 windows) is CLOSED absent genuinely
new structure — a third anchor shuffle would be curve-fitting the
event timeline. The gates and the ratchet both did their jobs: the
family looked perfect ex ante, produced the house's only positive
reading, and died honestly in out-of-sample within the same day.
