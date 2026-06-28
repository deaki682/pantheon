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

## Liquidity / size floor on the universe

**Why it could matter:** The screen has no liquidity or size filter, so an
un-investable name can float into the candidate set. Concretely, **RHLD**
(Resolute Holdings — a ~7-employee, ~8.3M-share micro-float quoted bid/ask
$100–$213) reached the top-12 and consumed a dossier slot a real name could have
had. A $1k book can't trade names like that.

**Why it's deferred:**
1. A *proper* liquidity floor (dollar volume / float) needs **market data** —
   price × shares for market cap, plus volume — which the SEC-only screen does
   not have. Building it means adding a market-data feed dependency (same problem
   as the Ghost cron). Not worth it for a $1k sleeve.
2. A *crude* proxy (e.g. a shares-outstanding floor from XBRL) is a half-measure
   with false positives — it would drop legitimate low-share, high-price names.
3. **The dossier already backstops it.** The balanced research pass flagged RHLD
   as illiquid/misidentified on its own; the only cost of leaving it is a few
   wasted dossier slots on junk that gets rejected downstream anyway.

**Trigger to revisit:** a market-data feed gets wired in (e.g. for the Ghost
cron) — at which point a real dollar-volume floor is nearly free — OR the sleeve
scales past $1k where execution/liquidity actually bind.

## Activist lens excludes insider/founder 13Ds

**Why it could matter:** The 13D lens treats *any* fresh Schedule 13D as an
activist signal. But **EQPT**'s "activist 13D" was the **founder-CEO's own 16.2%
stake disclosure**, not an outside activist. The documented activism edge
(Brav, Jiang, Partnoy & Thomas) comes specifically from *outside* hedge-fund
activists; a founder/insider topping up their control stake is a different,
weaker signal. The lens should exclude 13Ds where the filer is an insider,
affiliate, or the issuer itself.

**Why it's deferred:**
1. Distinguishing an outside activist from a founder/affiliate filer requires
   parsing the filer-vs-subject relationship out of the 13D / FTS metadata —
   bounded but fiddly, and easy to get wrong.
2. Low frequency / low impact — one name in the top 12, and it still carried a
   real insider signal, so it wasn't pure noise.
3. **Backstopped by the balanced dossier**, which caught the founder-not-activist
   distinction directly.

**Trigger to revisit:** the activist lens starts driving real position decisions,
OR a clean filer-relationship signal becomes available in the FTS data.
