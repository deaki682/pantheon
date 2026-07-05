# Lab results — `achilles_pead_gauntlet` (REFUTED, 2026-07-05)

**Verdict: REFUTED.** Zero non-isolated survivors across the full 18-cell grid.
The tradable long side of seasonal-SUE PEAD, in the exchange-listed
SMALL/MICRO universe the house can actually trade, is not merely absent — it
is **significantly negative** vs the same-bucket equal-weight benchmark, in
both the in-sample and the once-touched holdout, and worse at 2× cost.

Prereg: `docs/lab_prereg_achilles_pead_gauntlet.md` (committed before data).
Engine: `achilles/pead_gauntlet.py` + `run_achilles_cells.py`. Data:
survivorship-free Sharadar SEP, 30,637,571 bars / 11,824 tickers (the
exchange-listed SMALL 501–2000 and MICRO 2001–3500 mktcap bands, 312 monthly
PIT snapshots). Signal: seasonal-random-walk SUE (Bernard-Thomas, from SF1 EPS,
no analyst estimates), reaction-gated (direction + magnitude cap), −8% stop.
**221,510 events priced** (5,103 skipped for short series). SUE threshold =
80th pct of **in-sample only** (1.074).

## The grid (mean excess vs bucket-EW; t in parens)

| Cell | In-sample | Holdout | Holdout @2× cost |
|------|-----------|---------|------------------|
| SMALL h5 | −0.64% (t −14.0) | −0.40% (t −6.5) | −1.00% |
| SMALL h10 | −0.65% (t −11.1) | **−0.34% (t −4.3)** | −0.94% |
| SMALL h20 | −0.59% (t −7.6) | −0.46% (t −3.5) | −1.06% |
| MICRO h5 | −1.18% (t −15.9) | −0.85% (t −9.2) | −2.05% |
| MICRO h10 | −1.24% (t −13.1) | −0.78% (t −6.8) | −1.98% |
| MICRO h20 | −1.04% (t −7.6) | −0.83% (t −5.2) | −2.03% |

(reaction-cap variants `cap20`/`cap10` shown in `cells_verdict.json`; all
tracked the `none` column within a few bps — the magnitude guard did not
rescue any cell.) **The least-negative cell in the entire grid** (SMALL h10,
holdout) is still −0.34% with t = −4.3 and a 44.8% win rate. Every cell is
negative; none has an adjacent passer; `supported_non_isolated = []`.

## Reading

1. **The tradable long PEAD drift is not there — it is reversed.** This
   confirms and extends the earlier reaction-gate replay (which found the
   5-day drift on rewarded beats *absent*): at population scale, across 27
   years and both size bands, high-SUE beats *underperform* their bucket over
   5/10/20 days. What historical PEAD studies caught lived in the pre-decimal,
   pre-Reg-FD, higher-friction era and/or in names too small/illiquid to trade;
   in the exchange-listed universe with realistic costs it is gone.
2. **MICRO is worse than SMALL, not better.** The smallest tradable names —
   where a residual might have hidden — carry the *most* negative excess
   (−0.8 to −1.2% holdout), consistent with cost/liquidity drag swamping any
   reaction signal rather than a harvestable underreaction.
3. **Cost sensitivity is fatal, not marginal.** Doubling costs roughly doubles
   the loss — there is no thin-margin positive case that only costs erase.

## Consequence (pre-committed)

Per the prereg's pre-committed consequence and CLAUDE.md (the PEAD seasonal
mode carried the honest caveat "the long drift is unproven until
`achilles_pead_gauntlet` says otherwise; never an autopilot"): **the gauntlet
says refuted.** Proteus's seasonal PEAD mode is NOT a supported edge and may
not be cited as one; the long beat-basket is shelved. The `achilles/` library
(scanner/scoring/season/earnings, the reaction-direction gate + magnitude
guard) is retained as mechanical plumbing only. No forward test is opened
(refuted is terminal per slug). The only PEAD reading the house ever measured
as real was the *short* side of a sold beat — which is un-tradable long-only
and out of scope.

Full per-cell data: `data/achilles_gauntlet/cells_verdict.json`.
