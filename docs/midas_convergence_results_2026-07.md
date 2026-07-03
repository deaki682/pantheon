# Results: signal-convergence test at the Midas horizon

Graded 2026-07-04 per the frozen terms of
`docs/midas_prereg_convergence_test.md`. Data:
`docs/data_convergence_test_2026-07.json`.

## Result: REFUTED

892 cluster events with 5-day grades, joined against the complete
earnings-8-K catalog (23,688 events), the complete guidance-item
catalog (38,683 events), and the 13D annotations:

| Group | n | mean 5-day excess vs IWM | t | win |
|---|---|---|---|---|
| Cluster only | 306 | **+1.13%** | 1.75 | 52% |
| Cluster + 1 co-signal | 369 | +0.18% | 0.34 | 44% |
| Cluster + 2+ co-signals | 217 | **−0.14%** | −0.17 | 43% |

Spread (2+ minus none): **−1.27%** (t −1.2), monotonic in the WRONG
direction, with 586 events in the co-signal groups against the
80-event refutation floor. Under the frozen rule: REFUTED.

## Plain reading

More signals firing on the same name did not raise the one-week pop
probability — it lowered it, monotonically. The cleanest short-horizon
group in the entire weekend's data is the QUIET cluster: insiders
buying with no earnings event, no guidance-shaped 8-K, no activist
nearby (+1.13%, t 1.75 — still shy of significance, but the only
group that even points up). A plausible mechanism: clusters adjacent
to public events are reactions to news the market has already priced,
while quiet clusters are the ones carrying private conviction. Whatever
the mechanism, the non-linear convergence multiplier (2.5x/5x/8x) is
now measured folklore: on 18 months of complete data, stacking these
signals ADDS nothing and likely subtracts.

Caveats, stated once: conditional on a cluster firing (does not test
convergence among his other channels without a cluster); co-signals
are filing-proximity flags, not classified directions (an earnings 8-K
here is "reported," not "beat"); one 18-month window.

## Consequence (pre-committed)

- No mechanical change: the sieve and multipliers run as coded; a
  scoring change is a calibration-review decision with its own prereg
  once his graded live trades accumulate.
- Per the prereg: his weekly pick memo may no longer cite convergence
  count as conviction (runbook note added to midas.md). The
  pick-defining question stays expected value from the catalyst
  dossier — which his live rules already make primary.
- His live season doubles as the out-of-sample test: 50 graded trades
  per year, each with its convergence count recorded, will settle this
  on his own picks.
