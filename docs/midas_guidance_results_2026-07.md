# Results: guidance-channel replay (Midas) — INCONCLUSIVE + a live-code flag

Graded 2026-07-04 per `docs/midas_prereg_guidance_channel.md`.

## Catalog

Complete sweep: **38,683** 8-Ks with Item 7.01/8.01, 2025-01-02..
2026-05-31, across 8,006 issuers, 2 fetch errors. Seeded 900-event
sample drawn (seed 20260704, fixed pre-catalog).

## Result: the classifier fired on almost nothing

Production `guidance_direction` on each event's PRIMARY document
(per the frozen prereg):

| Direction | count in 900 |
|---|---|
| unknown | 892 |
| reaffirmed | 6 |
| lowered | 2 |
| **raised** | **0** |

Zero raised events. The refutation floor was ≥100 raised. **Verdict:
INCONCLUSIVE — the channel could not be tested because it essentially
never classified as raised.**

## Verified mechanism (not speculation)

Inspected a sampled 'unknown' filing directly: the 8-K primary document
is a 3,834-character COVER SHELL with no guidance text; the press
release with the actual numbers is a separate exhibit
(`ex_762255.htm`). `guidance_direction` ran on the cover and correctly
found nothing. This is the SAME primary-doc-only coverage gap that
wrongly excluded 42 spinoffs in the ocean-extension triage — a
recurring defect class: **a classifier pointed at 7.01/8.01 primary
docs reads cover pages, not content.**

## Operational flag (NOT a rule change — needs a code audit)

Open question this surfaces: does LIVE Midas (`/midas` step 6d) pass
EXHIBIT text to `guidance_direction`, or only the primary doc? The
runbook says "run guidance_direction() on each" without specifying the
text source. If live Midas also feeds primary docs only, then **the
guidance channel is nearly inert in production** — it almost never
contributes a signal, and its 1.0 weight in the sieve is mostly
theoretical. That is worth knowing whether or not the channel has edge.

- No frozen rule changed by this study.
- Follow-up (its own task, not this prereg): audit the live guidance
  text source; if primary-doc-only, decide — with a prereg — whether
  reading exhibits is worth it, or whether the channel should be
  retired. Retiring a near-inert channel is low-risk; activating it
  (reading exhibits) would need the guidance-EDGE question answered
  first, which THIS study could not do.

## Note on the convergence test

The 2026-07-04 convergence test used guidance as a FILING-PROXIMITY
flag (any 7.01/8.01 near the cluster), explicitly NOT the classified
direction, so its REFUTED verdict is unaffected by this coverage gap —
that coarsening was disclosed in its prereg for exactly this reason.

## Addendum-2 results: exhibit-text rerun (2026-07-04)

Same seeded 900, re-classified from press-release EXHIBITS per the
pre-committed addendum. Classification: **10 raised / 8 reaffirmed /
2 lowered / 878 none-or-unknown / 2 no-exhibit** — the exhibit fix
raised the hit rate from 0% to 1.1%.

Graded (entry next open, 5td, excess vs IWM; none-group = seeded
200-subsample):

| Group | n graded | mean excess | t | win |
|---|---|---|---|---|
| Raised | 9 | +2.46% | 0.38 | 56% |
| Reaffirmed | 7 | +1.04% | 0.44 | 71% |
| None sample | 176 | +0.85% | 0.76 | 54% |

Raised-vs-none spread +1.61%, t = 0.25. **Verdict: INCONCLUSIVE**
(refutation floor was 100 raised events; we found 10 in 900).

**The structural finding matters more than the returns:** even with
perfect document access, the production classifier fires on ~1% of
guidance-shaped 8-Ks — partly because `guidance_direction` requires
the literal word "guidance" while issuers routinely write "raises
outlook" (a NEW observed coverage gap, noted for any future rebuild
prereg; not acted on here). A channel with this hit rate cannot reach
statistical significance in any practical sample and contributes
almost nothing to the sieve either way.

**Consequence (per the pre-stated map):** inconclusive → the channel
stays as-is (near-inert on cover shells) and the question waits for
live grades. Practically: the channel is decorative. Anyone proposing
to spend effort here should rebuild the classifier (exhibits +
outlook-language) under its own prereg — or retire the channel at the
next legitimate rule-change window. Nothing changed today.
