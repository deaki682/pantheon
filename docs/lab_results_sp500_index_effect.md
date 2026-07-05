# Results — `sp500_index_effect` — REFUTED / DECAYED

- **Prereg:** [docs/lab_prereg_sp500_index_effect.md](lab_prereg_sp500_index_effect.md)
- **Data:** 222 S&P 500 additions (announce<effective, 1998+) from the
  Wikipedia changes table; Sharadar SEP bars; 203 priced.

## Verdict: DEAD in the deployable window

| subset | n | CAR peak (offset 5) | shrunk | t | win |
|---|---|---|---|---|---|
| ALL 1998–2026 | 203 | −0.28% | −0.25% | −0.67 | 49% |
| pre-2010 | 14 | −0.67% | −0.28% | −0.19 | 29% |
| **2010-onward (deployability)** | **189** | **−0.25%** | **−0.22%** | **−0.68** | **50%** |

The CAR curve is monotonically negative from announcement through +25
trading days — added names slightly *underperform* SPY after the
announcement. No run-up, no edge; if anything a small reversal.

## Reading

Textbook arbitrage decay. The index-addition premium was real in the
1990s but front-runners now predict and buy additions BEFORE S&P
announces, so by the announcement the pop is priced and an
announcement-entry trade catches only the give-back. The Wikipedia data
was adequate (announcement dates recoverable from the S&P citation
refs) — the effect, not the data, is what's dead.

## Decision for the god

The alpha map's highest-prior UNTESTED family is now tested and closed.
No deployable forced-flow edge here. **net-issuance-low LARGE remains
the house's only supported, deployable candidate** — which sharpens
rather than complicates the launch decision.
