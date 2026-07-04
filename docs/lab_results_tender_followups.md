# Results — tender-family follow-ups (`cef_tender_toc_anchor` + `issuer_tender_operating`)

- **Prereg:** [docs/lab_prereg_tender_followups.md](lab_prereg_tender_followups.md)
  (committed before the TO-C sweep and before any operating outcome)
- **Run:** 2026-07-04, `run_tender_followups.py`; engine
  `shared.gauntlet.event_car`; artifacts
  `docs/data/tender_followups/results.json`
- **Registry:** `cef_tender_toc_anchor` → **inconclusive**
  (backtested); `issuer_tender_operating` → **refuted** (terminal);
  `hypotheses_ever` 102→103 (incl. B's preregistered secondary)

## A — `cef_tender_toc_anchor`: INCONCLUSIVE, and the first non-negative reading in the house

82 of #7's 153 frozen CEF events had an SC TO-C communication filed
1–90 days before the TO-I. Entered at the first close after the
EARLIEST TO-C:

| statistic | value | frozen bar |
|---|---|---|
| n | 82 | ≥ 30 ✓ |
| mean CAR(25) | **+1.00%** | — |
| shrunk mean | **+0.81%** | > +1.0% ✗ (narrow miss) |
| t | **1.92** | ≥ 2.0 ✗ (narrow miss) |
| win rate | 61.0% | — |
| median | +1.52% | — |

Outlier audit: median above the mean, mean excluding the top-1 event
+0.85% and top-3 +0.63%, p10/p90 roughly symmetric — the positive
lean is broad-based, not one winner. **The sign flip vs #7's TO-I
anchor (−1.81%, t −3.91, same funds, same tenders) confirms #7's
mechanism reading: the convergence is captured between announcement
and launch.** Verdict is INCONCLUSIVE because the frozen bars were
missed — narrowly, on both — and frozen is frozen; the number was not
talked up to a pass. Coverage caveat: TO-C usage is self-selected by
funds (82/153); this subset cannot speak for non-TO-C tenders.

**Honest continuation:** fresh TO-C events accrue forward from
2026-06. A forward continuation under the SAME frozen rule on NEW
data would be a legitimate new prereg (not a re-cut) — the operator's
call to commission. This is the single most promising thread the lab
has produced.

## B — `issuer_tender_operating`: REFUTED

227 operating-company self-tenders matched (206 after the listing
screen) from the 2,797 non-CEF filers in the frozen catalog:

| population | n | mean CAR(25) | shrunk | t | win |
|---|---|---|---|---|---|
| screened (primary) | 206 | −1.82% | −1.66% | −1.20 | 43.7% |
| < $2B (capacity cut) | 138 | −2.33% | −2.03% | −1.08 | 42.8% |
| ≥ $2B | 68 | −0.78% | −0.60% | −0.56 | 45.6% |

REFUTED on the sign bar at 6.9× the n floor — and the preregistered
capacity-inversion hope failed with it (the small half is *worse*).
Post-filing operating tenders behave like post-filing CEF tenders:
whatever the announcement was worth is spent by the time the SC TO-I
lands.

Coverage: unmatched filers are overwhelmingly non-traded vehicles
(BDC/interval/LLC funds ~2,100, non-traded REITs), by-design foreign
exclusions (Diana Shipping class), and rename misses (Assertio
class); liquid listed filers (MCK, MGM, DISH, SLM) matched. The
under-sampling of later-renamed/acquired filers is the residual
survivorship caveat, disclosed.

## The day's tender-family picture

Three anchors, one coherent story: value at the ANNOUNCEMENT (+1.0%,
inconclusive-positive), nothing at the LAUNCH (−1.8%, refuted, CEF),
nothing at the launch for operating companies either (−1.8%,
refuted). The edge, if it survives a forward test, lives in the
announcement-to-launch gap — exactly where a small, fast, filing-
watching reader can stand and a fund complex cannot bother to.
