# Lab prereg — `call_evasion` (COMMITTED BEFORE DATA)

**Sponsor:** operator (2026-07-05). The purest "only an LLM could do this at
scale" text→signal edge: reading corporate **evasion** — not content. Committed
before data. No strong prior in either direction, which is exactly why it's worth
the number.

## Hypothesis

Companies whose management **evades** on the earnings call — non-answers to
analyst questions, hedging, defensiveness, deflection, uncertainty markers,
refusing to reaffirm guidance — **underperform** over the following 1–3 months,
because the market underreacts to soft linguistic signals that a human desk can't
read across thousands of calls but an LLM can. (Academic support: Mayew-
Venkatachalam on vocal/linguistic cues; Loughran-McDonald on financial-text
uncertainty predicting returns.)

## What makes it LLM-native (vs the lexicon baseline)

A word-count lexicon (Loughran-McDonald uncertainty/weak-modal/negative counts)
captures *tone* but NOT *evasion*: a CEO can be verbally confident while never
actually answering the question. **Evasion is a structural Q&A property** —
question asked → non-responsive answer — that only a reader who understands the
exchange can score. That gap (LLM evasion-read minus mechanical lexicon) is the
whole experiment.

## The honest data + cost reality

Transcripts are NOT in Sharadar and historical LLM-scoring of thousands of calls
is expensive. So, layered:
- **BACKTESTABLE NOW (the lexicon baseline):** compute Loughran-McDonald
  uncertainty/weak-modal density on available EDGAR text (10-Q/10-K MD&A + 8-K
  earnings exhibits) at each report; does high-uncertainty language predict
  negative forward drift? This is the mechanical floor.
- **FORWARD A/B (paper, the real test):** as calls happen, the LLM scores the
  Q&A **evasion** (non-answer rate, deflection, hedged reaffirmations) on a fixed
  rubric; grade the 1–3-month drift of high-evasion vs low-evasion, and — the
  headline — LLM evasion vs the lexicon baseline. Transcript sourcing (vendor or
  scrape) is the gating build for the forward arm.

## Test design (frozen)

- **Signal date:** the earnings call/report date; entry T+1.
- **Horizons:** {21, 63} trading days (~1 and 3 months); primary 63d.
- **Benchmark:** same-bucket EW (size-matched), the house standard.
- **Book:** the signal is an AVOIDANCE/short-lean read — long-only expression =
  *exclude/underweight* high-evasion names from a basket (we can't short); the
  measurable claim is high-evasion underperforms low-evasion within the bucket.
- **Costs:** 30bps + 2× stress; quarterly cadence keeps turnover sane.
- **Regime split:** in-sample ≤2015-12-31 / holdout 2016-2025 (lexicon arm).

## Gates

- **G1:** text read, not price. PASS.
- **G2 — honest weak point:** market-underreaction-to-language = an
  information-processing edge, not a structural constraint. Capability-frontier,
  DECAYS as LLM transcript-reading spreads (already being commoditized — a real
  risk). Justified: it's the most LLM-native signal in the house and directly
  tests "reading text→signal," the house's claimed core edge.
- **G3:** scalable (whole universe). **G4:** fail (drift). **G5:** very strong —
  thousands of calls/quarter → fast power once transcripts are sourced.

## Success thresholds

**Backtest (lexicon):** high-uncertainty-language names underperform same-bucket
EW at 63d, t ≥ 2, holdout + 2× cost, non-isolated. Establishes the floor.
**Forward (LLM evasion A/B):** LLM evasion-read beats the lexicon over ≥20 graded
quarters — the evasion increment over mere tone.

## Pre-committed consequence

Lexicon predicts → build transcript sourcing, open the LLM evasion A/B. Lexicon
dead AND (later) LLM evasion dead → refuted; corporate weaseling is priced or
un-tradable long-only, and the "LLM reads tone→signal" hope loses its cleanest
test. Ledger row either way. (This is the honest one: I have no prior — the
number decides.)
