# Results: survivorship-correction of the insider-cluster replay via Sharadar SEP

Graded 2026-07-04 per the frozen terms of
`docs/oracle_prereg_cluster_replay_sharadar.md`. Backlog item #6
(docs/RESEARCH_BACKLOG.md) — the first study through the Sharadar SEP
feed. One shot, no re-cuts. Per-event data:
`docs/data_oracle_replay_sharadar_correction_2026-07.json`.

## Headline: the vendor does NOT close this gap

Of the 42 events the original replay (docs/oracle_replay_results_2026-07.md)
could not price:

| Outcome | n | Detail |
|---|---|---|
| No ticker match in SEP at all | 34 | Deep OTC/pink-sheet microcaps outside Sharadar's ~21,893-company, exchange-history-rooted universe |
| Symbol matches, wrong era (recycled ticker) | 4 | NORD (x2, real window 2014–2017), UTGN (x2, 1990–2001), CHUC (ends 2023-11, event 2025-12), PALX (ends 2000-03, event 2026-04) — same ticker, decades-earlier unrelated company |
| Symbol matches, wrong instrument | 1 | OABIW: insider bought the WARRANT; only the common (OABI) prices in SEP. Substituting common-stock return for a warrant purchase would misrepresent the position — excluded on principle, not just availability |
| Genuine match, correctly windowed, correct instrument | **1** | PHXE-P (Phoenix Energy One LLC, NYSE) |

**1 of 42 (2.4%)** — well under the pre-registered ≥50% bar for
"Sharadar validated for this use case." Per the prereg, this decides
the vendor-scope question before any statistical test: **Sharadar SEP
does not reach the deep-OTC tail that the insider-cluster replay's
unpriceable bucket disproportionately samples.** It remains validated
for its QA'd strengths — bankrupt/acquired/renamed NYSE-NASDAQ-AMEX
history (backlog #4, #8) — but this specific gap needs a different
vendor (OTC Markets historical data, or hand-collection) if it is ever
to close.

## The one priced event

PHXE-P: 7-buyer, $400K cluster, knowable 2025-10-01, entry 2025-10-06
at $20.30. At +126 trading days (2026-04-08, $24.225): stock return
+19.33% vs IWM +5.53% → **excess +13.80%**. The 252-trading-day horizon
has not elapsed (series runs only to 2026-07-02); reported as
not-elapsed, not forced.

## Combined verdict — unchanged

| Horizon | n | mean excess | t | Δ from frozen |
|---|---|---|---|---|
| ~6mo (126td) | 613 (was 612) | −4.09% (was −4.12%) | −1.65 (was −1.66) | +1 event, +0.03pp |
| ~12mo (252td) | 291 (unchanged) | −6.38% (unchanged) | −1.06 (unchanged) | none — PHXE-P not yet elapsed |

One additional positive event nudges the 6-month mean by three
hundredths of a point. **The 2026-07-03 refutation stands exactly as
frozen** — this was decided by the prereg's own math before the bar
was fetched (n=1 cannot move n=291-612), but it is worth having the
actual number rather than assuming it.

## Consequences

1. **The insider-cluster replay verdict is now final for this data
   generation.** No further correction is expected to be possible with
   currently-purchased vendors; the 41 remaining gap events are a
   disclosed, irreducible-for-now hole (they lean toward distress
   outcomes per the same spot-check logic as the IPO-lockup study —
   deep-OTC names in trouble are exactly the names that never got
   picked up by an exchange-history vendor).
2. **Sharadar SEP's first live trial confirms its QA scope, not more.**
   Backlog #4 (Delphi PIT universe) and #8 (Achilles PEAD horizon) both
   target Sharadar's actual strength — large/mid-cap, exchange-listed,
   possibly-delisted-since names — and should proceed unblocked. Any
   future OTC-microcap survivorship work needs a different data source;
   flagged as a new backlog item rather than re-litigated here.
3. No live-rule change. This corrects a data gap in an already-refuted
   signal; Oracle's cohort trades unaffected either way.
