# Lab prereg — `residual_momentum_llm` (COMMITTED BEFORE DATA)

**Sponsor:** operator (cram-for-one-more-god, 2026-07-05, candidate #3).
**Committed before data.**

## ⚠️ G1 operator override (required, recorded here)

This strategy's base signal is computable from past returns alone → it **FAILS
G1** (the tape test), and the entire raw price-signal family measured dead in
gauntlet_v1 (80/90 cells). Per lab.md §3b, proceeding requires an **explicit
operator override, recorded in the prereg.** Granted 2026-07-05: the operator
wants to know whether the ONE un-tested momentum variant — *factor-neutral
(residual) momentum, with an LLM reversal-prune* — rescues momentum where the
raw version died. The two things that distinguish it from the refuted family:
(1) residualizing removes the crash-prone factor tilt (Blitz-Huij-Martens: much
higher Sharpe than raw momentum, no momentum-crash), and (2) the LLM
reversal-prune is a **non-price overlay** — the part that isn't just tape. This
is a bounded, one-shot test of a specific, distinct construction, NOT a
re-litigation of raw momentum (which stays refuted).

## Hypothesis

**Residual momentum** — the 12-1 momentum of a stock's returns *after* removing
its factor exposure — earns positive excess vs a size-matched benchmark where
raw momentum does not, because it strips the factor/beta tilt that causes
momentum crashes and leaves the idiosyncratic continuation. An **LLM
reversal-prune** on the top names (drop the extended/blow-off/bad-news names
likely to mean-revert) adds the tradable edge — the moonshot-de-risked-by-
avoidance shape.

## Construction (frozen)

- **Signal:** for each name at each month-end, regress its trailing 12-month
  returns (weekly) on the market return (and size) over the formation window;
  take the **residual** return series; the momentum score = cumulative residual
  return over months t-12..t-2 (skip the most recent month, standard). Rank
  cross-sectionally.
- **Book:** long-only, **top N=25 and N=50**, equal-weight, **monthly rebalance**.
- **Universe:** liquid US common — the gauntlet_v1 PIT universes (LARGE ranks
  1-500, SMALL 501-2000), point-in-time, survivorship-free, price/liquidity
  floors already applied. × {LARGE, SMALL}.
- **Benchmark:** same-bucket equal-weight over the identical window (the house
  standard — momentum's raw return is partly size/beta; the bar is bucket-relative).
- **Costs:** momentum is high-turnover — realistic per-bucket costs + a **2×
  stress**. Turnover + cost drag reported (`turnover_stats`) — this is the most
  likely killer.
- **Regime split:** in-sample ≤2015-12-31; holdout 2016-2025 (touched once).

## The LLM reversal-prune (FORWARD overlay, not backtested)

The LLM read cannot be run cheaply on every historical month, so — like Plutus's
buyback overlay — it is a **paper forward A/B**, not a backtest: Arm B = the
mechanical residual-momentum top-N; Arm A = the same list with the LLM pruning
names it reads as reversal-prone. The base signal must earn its forward test
FIRST; the overlay is graded only if the base clears.

## Success thresholds (base signal — pass ALL or refuted)

1. In-sample 252d/annualized excess vs same-bucket EW > 0, **t ≥ 2**, non-isolated
   across {N25,N50}×{LARGE,SMALL} (a lone cell is not support).
2. Holdout same-sign positive excess.
3. **Positive at 2× cost in the holdout** — the turnover gate; this is where
   momentum usually dies.
4. Beats a raw-12-1-momentum control on the same universe (else residualizing
   added nothing and it's just the refuted family in disguise).

Miss any → **refuted** (terminal). Supported → forward test with the LLM-prune
A/B (Arm A vs Arm B), god-scaffold candidacy as a small momentum diversifier.

## Honest prior

Likely **refuted** — the house killed the momentum family hard, and long-only
after-cost vs a bucket benchmark is a brutal bar. But residual momentum is the
one variant with a real academic case for surviving where raw momentum didn't,
and the LLM-prune is a genuine non-price overlay. Worth one clean, pre-committed
shot. Population-quality lesson from post_bk stands: this one has NO population
risk (systematic on the survivorship-free panel), so a refutation here IS clean.
