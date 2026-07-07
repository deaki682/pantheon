# Oracle floor-math bug — the screen over-states the floor (2026-07-06 fresh run)

Surfaced by the blind first-time verification fan-out (60 names). The four-trap
`debt_reconciled_full_stack` gate caught it on ~10 names across 4 batches — the
verification layer working exactly as designed, but the SCREEN should not emit these.

## The bug

`oracle.neglect_screen.floors()` and `oracle.asset_revaluation` compute the floor as
roughly **`assets − NET DEBT`** (financial debt only). That systematically OMITS:
- **preferred equity** ahead of common (PEB $677M, RLJ $328M, SRG $70M),
- **minority interest / redeemable NCI** (FBIO $40M, DEI $1.56B, JBGS $495M),
- **non-debt liabilities** (XLO's $48M deferred collaboration revenue; operating leases),
- and in at least one case **inverted the debt sign** (AIV net_debt carried as −$212M vs a
  true +$523M once the mortgage stack was included).

Result: manufactured phantom 30–65% "discounts" that collapse to ~0 or negative once the
TRUE common-equity claim is computed. Every levered REIT and consolidated-sub name in the
queue was a false positive for this reason.

## The fix (next engine session)

Floor = **`total assets − ALL liabilities − minority/NCI − preferred liquidation value`**,
not `assets − net debt`. Specifically:
- `net_cash` / `ncav`: subtract the FULL liability stack (incl. deferred revenue, leases),
  not just debt; net out minority interest for consolidated cash (the FBIO mirage).
- `tangible_book` / `transacting_asset` (REITs): subtract preferred liquidation preference
  and redeemable NCI before comparing to the common-equity cap; fix the AIV net-debt sign bug.
- Add a `full_stack_reconciled` flag the screen sets so the freshness/verification stage
  knows which floors are already stack-clean vs need the manual read.

Until fixed, the four-trap verification is the backstop — but the screen wastes queue slots
on phantom floors that a corrected floor computation would never emit. HIGH-value fix:
it would roughly halve the KILL rate and let `per_family` coverage reach genuinely new names.

## Also fixed this run
- `run_oracle_neglect_pull.py`: added `currency` + `location` columns (their omission made
  `is_common_tradable` reject EVERY name → 0 candidates). Committed 2026-07-06.
## Also surfaced (marketcap-source)
- SDHC: Sharadar marketcap used Class-A float only (5× understated); freshness caught it via
  the live-cap divergence. A share-count source that includes all classes would prevent it.
