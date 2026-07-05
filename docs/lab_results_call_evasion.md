# Lab results — `call_evasion` (VERDICT: inconclusive; the LLM-prose increment is negative)

**Sponsor:** operator. **Prereg:** docs/lab_prereg_call_evasion.md (committed before data).
**Run:** 2026-07-05. **Paper only.**

## The question

Does corporate **evasion** in disclosure predict negative forward drift, and — the
headline — does an **LLM evasion-read beat a mechanical word-count** (the "evasion
increment over mere tone")? Two backtestable arms plus one blocked arm:

1. **Lexicon (whole-filing):** Loughran-McDonald uncertainty-word density on 10-Q/10-K
   text; high-vs-low tercile, 63d excess vs same-bucket EW. (`run_call_evasion.py`)
2. **LLM candor read (blind):** a stratified 53-filing sample re-fetched, MD&A narrative
   extracted, numbers/dates stripped, scored 0–1 for management candor/evasion by **blind
   raters in fresh context** (no sight of the return or the word-count), then joined to
   the forward return. (`build_evasion_packets.py` + `join_evasion.py`)
3. **TRUE Q&A evasion (the real thesis):** LLM scores non-answers/deflection in the
   unscripted earnings-call Q&A. **Transcript-blocked** — not in Sharadar, no vendor. Untested.

## Results

**Lexicon, whole-filing (n=1427 events, 2022–24; EDGAR `recent` window only reaches ~2016
so NO in-sample ≤2015):**
- HIGH-minus-LOW uncertainty tercile: **−1.96%/63d, t=−0.75** — directionally right
  (high uncertainty underperforms) but not significant.

**LLM candor read vs lexicon, on the same 53 blind-scored filings:**

| Signal | Spearman vs 63d fwd | HIGH−LOW tercile (winsorized) |
|---|---|---|
| **LLM candor (evasion)** | +0.02 (t=0.16) | **+1.36%** (WRONG sign) |
| **Lexicon LM-density** | **−0.27 (t=−1.99)** | **−3.88%** (right sign) |
| OLS: LLM coef beyond lexicon | — | **+0.05, t=0.19 (adds nothing)** |

**The word-count beat the LLM.** On this sample the crude lexicon showed a
directionally-correct, borderline-significant tercile spread (~−3.9%), while the LLM
reading the *same* narratives for candor produced flat noise (+1.4%, wrong sign) and
added nothing in the joint regression. The prereg's core premise — "LLM evasion-read
beats mere tone" — is **negative** here.

## Verdict

**Inconclusive overall, with a negative LLM increment.**
- The backtestable proxies do **not** establish a tradeable edge (lexicon faint, LLM flat).
- The prereg's pre-committed "refuted" trigger requires *both* lexicon dead AND LLM
  evasion dead. Lexicon is not cleanly dead (faint −3.9% pulse); the **true Q&A-evasion
  arm is untested (transcript-blocked)**. So the slug is not refuted — it is
  **inconclusive / data-blocked on the arm that matters**, with the sharp sub-finding
  that the LLM-on-prepared-prose version is not worth a forward paper test.

## What it buys the house (instrument track)

This is a clean, blind measurement of **LLM text→signal skill on one construct**, and it
came back **null / worse-than-lexicon**. Consistent with the growth-hunt verdict (the
LLM's only measured-real skill is AVOIDANCE) and the house-view prior (the LLM edge is
thin). One more LLM text-read that did not beat a cheap mechanical baseline.

## Honest limitations (why this is a pre-screen, not a validation)

- **Wrong modality for the thesis:** prepared, lawyered MD&A prose — evasion lives in the
  unscripted Q&A. This tests a weaker proxy and finds the proxy dead; it does not kill the
  real (blocked) thesis.
- **n=53, 2023–24 only, one horizon (63d).** Underpowered.
- **Extraction noise:** the robust extractor grabbed varied sections (some risk/controls,
  not pure MD&A) across filers.
- **Numbers stripped** (protects blindness) may handicap a candor read that would lean on
  quantitative specificity.

## Consequence

- `call_evasion` → backtested, verdict **inconclusive**; stays open only for the
  transcript-gated Q&A arm (sourcing is the build; do not re-run the prose proxy).
- The blind-replay harness built here (fetch → blind → fan-out score → join) is the
  reusable prototype for the LLM instrument track's cheap triage layer — see
  RESEARCH_BACKLOG.
