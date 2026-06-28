# Deferred improvements

Ideas with real merit that we deliberately did **not** build yet, with the
reason — so the decision is recoverable later.

## Opportunistic vs. routine filtering for the insider lens

**Why it could matter:** The insider-cluster lens is the most-fired signal in the
screen (~94% of the top-100 are insider-driven). Academic evidence (Cohen,
Malloy & Pomorski, *Decoding Inside Information*) finds the predictive power is
concentrated in *opportunistic* insider trades — *routine* trades (e.g. scheduled
10b5-1 / same-month-every-year patterns) carry ~zero signal, and filtering for
opportunistic-only delivers roughly **4× the alpha**. Our lens currently treats
all cluster buys equally, so it includes routine noise.

**Why it's deferred:**
1. Not cheap — classifying "routine" properly needs each insider's *multi-year*
   Form 4 history, a real expansion of the insider lens's data fetching (today it
   only pulls a 60-day window). A lighter proxy is to drop 10b5-1-flagged trades,
   but that's only a partial approximation.
2. Premature at $1k — the documented alpha was measured on diversified, long-short,
   value-weighted portfolios; it may not survive a concentrated, long-only,
   retail-executed $1k book.
3. **Build-it-on-faith risk.** Hard-coding the filter because a paper says 4×
   would repeat the mistake we avoided with backtesting. The disciplined path is
   to **measure it first**: tag each insider ghost entry opportunistic-vs-routine
   as a feature, let `shared.ghost.boolean_lift` report whether opportunistic
   clusters actually outperform routine ones *in our universe*, and only then wire
   the filter into the live screen.

**Trigger to revisit:** the sleeve scales past the $1k proving stage, OR Ghost
data accumulates enough to test the opportunistic-vs-routine lift directly.
