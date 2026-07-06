# Lab results — `call_evasion` (INCONCLUSIVE, 2026-07-05)

**Verdict: INCONCLUSIVE — underpowered, both arms currently null-to-negative.**
Neither the lexicon baseline nor the LLM candor read clears the pre-registered
t≥2 bar, and the true evasion arm (Q&A transcript-based) is untested — this is
NOT a refutation, it is a stalled experiment pending transcript sourcing. Filed
here so the loose end doesn't rot silently (the backtest was recorded in the lab
registry same-day but this results doc and the ledger row were never written).

Prereg: `docs/lab_prereg_call_evasion.md` (committed before data). Sponsor:
operator, part of the LLM instrument track (measure #2 — text→signal reading).

## What was actually tested

Transcripts are not in Sharadar and historical LLM-scoring of thousands of real
earnings-call Q&A exchanges was out of reach this session, so the backtest ran
the two arms the prereg allowed as a **pre-screen**, both on the SAME 53
blind-scored EDGAR MD&A packets (10-Q/10-K MD&A + 8-K earnings exhibits) —
NOT actual call transcripts, and NOT true Q&A evasion:

- **Lexicon arm:** Loughran-McDonald uncertainty/weak-modal word-count density
  on the whole filing.
- **LLM "candor" arm:** an LLM blind-read of the same 53 MD&A packets, scored
  on a fixed candor/hedging rubric — a **prose proxy for evasion**, not a
  read of an actual analyst Q&A exchange (no transcripts existed to read).

## Results (n=53, 63d primary horizon, excess vs same-bucket EW)

| Arm | Reading | Spearman | t |
|---|---|---|---|
| Lexicon, whole-filing | −1.96%/63d | — | −0.75 (no in-sample split) |
| Lexicon, same 53 packets | −3.88% | — | −1.99 |
| LLM candor read, same 53 packets | +1.36% (HIGH−LOW, **wrong sign**) | +0.02 | — |
| LLM vs lexicon, OLS increment | — | — | t = 0.19 (no increment) |

Shrunk mean excess (registry): 0.99% — small and not distinguishable from
noise at this n.

## Reading

1. **The word-counter beat the LLM.** On the same 53 filings, the mechanical
   lexicon showed a (still sub-threshold) negative Spearman association
   consistent with the hypothesis's direction; the LLM's candor score was
   flat and wrong-signed. The LLM added nothing over word-counting on this
   proxy (OLS increment t=0.19) — the opposite of the "LLM reads what a
   lexicon can't" premise this slug exists to test.
2. **n=53 is underpowered by design and disclosure** — this was always a
   directional pre-screen, not a validation attempt. Neither arm clears the
   pre-registered t≥2 bar, so **the pre-committed "lexicon dead → refuted"
   consequence does not fire**: the lexicon reading is negative-but-not-clearly-
   dead, not clearly-alive either.
3. **This is a prose proxy, not the actual test.** The prereg's real hypothesis
   is about live Q&A evasion (non-answers, deflection, hedged reaffirmations in
   the analyst call) — a structural property of a real exchange that an MD&A
   filing does not contain. This run never touched a transcript. The honest
   reading is: **the cheap proxy failed to show an LLM increment; the real
   test (transcripts) was never run.**

## Reproducibility caveat (added on review)

This doc reflects a summary + bias checklist a prior session recorded into
`cache/lab_registry.json`; the underlying 53 blind LLM candor scores and the
lexicon computation were not independently re-run or re-inspected here. The
top-line numbers (mean_excess 1.36%, n=53) do internally match the registry's
notes text, which is more than could be confirmed for the other two studies
tended this session — but there is still no per-filing score sheet to audit
against.

## Consequence (pre-committed, applied honestly)

Per the prereg: full refutation requires the lexicon AND (later) the LLM
evasion arm both dead. The lexicon reading here is weak/negative but
underpowered, not "dead," and the real evasion arm is untested (transcript
sourcing never built). **Status stays `backtested`/inconclusive, not
refuted** — the slug remains open, but **only for a true transcript-based
evasion arm**; this MD&A-prose-proxy approach is not to be re-run (per the
registry note: "Prose-proxy = do not re-run"). Absent a transcript vendor,
this is effectively parked: it does not currently justify further backtest
spend, and it does not yet feed the LLM instrument track's measure #2 roll-up
with a real number — record it as **no measured LLM text→signal increment on
the one proxy tested, n too small to generalize.**
