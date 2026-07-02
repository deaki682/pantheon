# Pre-registration: "quality names that crash ON news overshoot" (one shot)

Registered 2026-07-02, BEFORE fetching any test data. This hypothesis arose
post-hoc from the 2018-2024 backtest (news-crash buckets: large +0.51pp,
small +1.99pp excess) and therefore carries zero evidential weight until it
survives this test on unseen data. One shot; no parameter changes after
results; the verdict stands either way.

## Hypothesis (directional)
In quality universes, violent single-day crashes accompanied by company news
(SEC filing within ±1 day) are OVERREACTIONS: buying the next open and holding
5 trading days earns positive excess return vs the same name's unconditional
baseline, net of costs.

## Test data (never touched by any prior test this week)
- Period: 2012-01-01 → 2017-12-31 (fully disjoint from 2018-2024; if the data
  source's history starts later for some names, use what exists and disclose).
- Large tier (40, offset stride [1::3] of sorted Delphi universe):
  ABBV ACN AMAT AMZN BA BMY CI CME CRM CVX DIS ELV ETN GD GM HAL IBM INTU JNJ
  KLAC LMT MA MDT MO MRVL MU NKE NVDA PEP PGR PYPL SBUX SNPS SRE TJX TXN UNP
  VZ WM XOM
- Small tier (40, offset stride [1::17] of the quality-gated prescreener pool):
  AAT AIR ARCB AVO BEIGF BWMN CDRE COLL CSR CXM DSGR ELMD EVCM FIVE GDYN GTEC
  HHH HQY IDXX IRMD KALU LAND LMAT MAMA MOV NBIX NPK NYT ORA PDEX PR RDN RLI
  SBCWW SPSC TBLAW TNC ULBI VCTR VSECU
- Zero overlap with the prior 80-name sample (verified).

## Frozen rules (identical to prior tests)
- Crash: day return <= -4% AND <= -2 sigma vs own trailing 60d vol.
- News: any 8-K/8-K/A/10-Q/10-Q/A/10-K/10-K/A/6-K filed within [t-1, t+1]
  (point-in-time EDGAR; crashes before a name's filing coverage = unknown,
  excluded from buckets).
- Trade: entry next open, exit close t+5; costs 10bps RT large / 80bps small.
- Validity: >=1200 in-window sessions, median close >=$3, median $vol >=$1M.
- Stats: excess vs per-name unconditional baseline (same fill rule);
  episodes = calendar clusters (>7-day gaps); episode-clustered t.

## Success criteria (pre-specified)
PASS requires ALL of:
1. Pooled news-driven excess: episode-clustered t >= +2.0 and mean > 0.
2. Positive news-bucket point estimate in EACH tier that has >=30 news events.
3. A tier with <10 usable names or <30 news events is underpowered:
   informational only, cannot pass or fail alone.
FAIL otherwise. No partial credit, no re-cuts, no "almost."

## RESULT (recorded 2026-07-02, same day, one shot as pledged)

FAIL — decisively.

53 usable names (36 large / 17 small after validity; small tier heavily
attrited by late IPOs, but both tiers cleared 30+ news events so both were
powered). 689 crash events, 267 with confirmed news, EDGAR coverage to 2012
for 44/51 names via archived submission files.

- News-crash bounce (the hypothesis): large −0.11pp excess, small −0.05pp,
  pooled −0.08pp, episode-clustered t = −1.25. The 2018-24 pattern
  (+0.5/+2.0pp) evaporated completely on unseen data. It was noise.
- The mirror lesson: in THIS period the no-news buckets were positive
  (+1.05pp/+0.69pp) — the exact OPPOSITE of 2018-24, where no-news lost
  1.3-1.5pp. Each conditioning flips sign across regimes. There is no stable
  5-day crash-fade edge under either flag.

Nemesis is retired as a capital strategy. The contrarian idea survives where
it always lived: Oracle (insider-confirmed, 12-month clock) and dry powder.
