# Oracle cold-start — full memory wipe + blind machine re-run (2026-07-06)

**Operator directive:** clear the slate. Wipe every FUND/WATCH/KILL name (including the
just-surfaced FPH), empty the dossier pool, and run the machine "as if it hasn't chosen a
single name yet" — no special treatment of the incumbent FUNDs, neither protective nor
hostile. Just the standard neutral machine on everything, on equal footing.

## What was wiped

- `cache/oracle_convex_dossiers.json` → `{dossiers: []}` (reset_at `2026-07-06-COLDSTART`)
- `cache/oracle_ab.json` → empty
- All prior verdict records backed up to `cache/*_PREWIPE.json.bak`

## The cold run

1. **Re-sourced with an empty pool** (nothing excluded): neglect screen → 280 candidates;
   asset-revaluation screen → 85 candidates.
2. **Ranked the whole queue by the machine's fundability prior** (sweet-spot discount ×
   floor-hardness × clean-flags × cap-weight) — the ranking that fixes raw-discount ordering
   putting deep-discount traps first.
3. **Blind primary-source verification of the top 14**, one verifier per name, floor-type-matched
   briefs, incumbents given no special treatment. Each read the actual 10-Q/10-K/20-F.

## Result — 2 FUND / 6 WATCH / 6 KILL (~14% fundable, matching the historical neglect rate)

### FUND (verified, convex — written to the pool)

| Ticker | Floor | Conv. | The bet |
|---|---|---|---|
| **XBIT** | hard net cash | **0.127** | $2.30 vs $3.63/sh net cash ($110.6M cash, $0 debt), ~37% FD discount, ~3yr runway, ~$495M tender history — dormant catalyst is the priced risk |
| **STRS** | transacting asset | 0.022 | Stockholder-approved liquidation trading *below* the conservative $29.73 floor; $5/sh pays 7/20; Austin land at cost — thin margin + dark-stub tail is the priced risk |

XBIT is the clean standout (hard countable-cash floor, deepest verified asymmetry). STRS is a
real but thinner catalyzed-liquidation play.

### WATCH (real floor, but a leg of the asymmetry test fails — no catalyst, leverage, or control)

- **ARL / TCI** — RAI/Pillar controlled-sub value traps (78–91% control, circular related-party
  receivables, no dividend, untradeable float). Real book discount, permanently inaccessible.
- **SAFE** — real ~55% discount to a primary-verified ~$43/sh fair-value NAV (the 10-Q fair-value
  note kills the "stale low-rate marks" bear case), but a 2x-levered ground-lease vehicle with a
  Sugarman/iStar governance overhang and no catalyst.
- **AIV** — audited liquidation-basis NAV (measured, not asserted) with a live distribution
  catalyst, but only ~12% margin to the conservative remaining figure on a slow dev residual.
- **IMPP** — debt-free with ~$213M cash ≈ market cap, but a Vafias trap: net-cash-to-common
  below price, fleet carried *above* market, related-party fee drag + serial dilution, no catalyst.
- **PHUN** — real ~$91M cash at 2x price, but a fresh $200M shelf + live $15.3M ATM + spend-the-pile
  pivot mean the floor isn't ring-fenced to common.
- **UFI** — genuine no-goodwill manufacturer at 0.39x tangible book, but net-debt, loss-making,
  book melting ~13%/yr; real-but-melting-and-levered floor.

### KILL (the four-trap gate — deep discount is an artifact or a mirage)

- **WKEY** — minority-interest consolidation artifact ($415M of $429M cash belongs to controlled
  sub SEALSQ); trades ~670% *above* real attributable floor.
- **XLO** — stale-share-count artifact (missed the 1-for-14 reverse split + pre-funded penny-warrant
  overhang); on the honest FD base it trades ~14% *above* net cash.
- **CTRM** — $100M insider Series D preferred + $84M debt erase the cash cushion; rest is illiquid
  related-party stakes.
- **INVE** — melting shell: selling its whole operating business into a $50M illiquid buyer-marked
  private preferred, no return-of-capital catalyst.
- **WWR** — sub-book value is entirely $144M of capitalized half-built graphite plant (project cost,
  impairment-triggered), against a ~$97M dilution stack + toxic converts.

## What this proves

The machine works cold. With zero name memory it independently reproduced the four-trap
discipline: it killed every deep-discount trap on primary-filing evidence (consolidation artifacts,
stale counts, insider preferreds, melting shells, project-cost books), demoted every
control/leverage/no-catalyst floor to WATCH, and funded only the hard countable-cash floor (XBIT)
and the below-floor approved liquidation (STRS) — on their own merits, no incumbency involved.
The book is now a fresh, concentrated 2-name FUND set on the `pending_funding` sleeve
(research/paper until funded), with a 6-name WATCH bench.
