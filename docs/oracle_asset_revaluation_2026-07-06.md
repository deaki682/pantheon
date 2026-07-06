# Oracle asset-revaluation lens (2026-07-06) — the ALCO gap, built

The fourth floor type, and the first that attacks the mandate's UPSIDE deficit.
The neglect screen finds `price < book`; this finds the opposite mispricing —
names whose BOOK UNDERSTATES their assets: land / farmland / timberland /
vineyards / real estate carried at historical (or depreciated) cost and worth
multiples at market. A below-book screen is structurally blind to it (these names
trade ABOVE book), yet they can trade far below the market value of the land.

`oracle/asset_revaluation.py`: for asset-heavy names in APPRECIATION industries
(farmland, real estate ex-mortgage-REIT, timber/paper, vineyards, plus
commodity-reserve names flagged `commodity_dependent`), compute long-term tangible
assets at cost (`ltta = assets − current assets − intangibles`) and net-asset-
value-at-cost after debt (`nav_at_cost = ltta − net_debt`); flag names where
nav_at_cost is ≥0.80× the market cap with debt not swamping the assets. Since
market value ≥ cost in these sectors, a name whose COST-basis net assets already
rival its cap is likely cheap to true NAV. Reuses the neglect leg's
`is_common_tradable` hygiene gate. floor_basis = `transacting_asset`.

**First run: 85 candidates (70 land/RE/timber, 15 resource).** The lens
immediately surfaced the exact archetypes the other three legs are blind to —
several with LIVE realization catalysts (the floor+catalyst convex combo):

| Ticker | Industry | Coverage | Note |
|---|---|---|---|
| **SRG** | REIT - Retail | 2.4× | Seritage — the Sears real-estate liquidation (active winddown = catalyst) |
| **STHO** | Real Estate Services | 2.9× | Star Holdings — iStar residual, winding down |
| **NLOP** | REIT - Office | 1.6× | Net Lease Office Properties — a liquidating W.P. Carey spinoff |
| **HHH** | RE - Diversified | 1.8× | Howard Hughes — master-planned-community land (activist-held) |
| **FOR / FPH / STRS** | RE - Development | 1.7–3.9× | land developers, big land banks at cost |
| **WVVI** | Wineries | 2.9× | Willamette Valley Vineyards — appreciating vineyard land |
| **LAND** | REIT - Specialty | 1.9× | Gladstone Land — farmland |

**Honest caveat — coverage, not conviction.** The screen CANNOT appraise market
value (that is the precision read's job: acreage × $/acre, property × cap rate,
reserves at strip). And a below-NAV REIT can be cheap for a REAL reason (office
apocalypse, tenant distress — MPT, SLG) rather than hidden value. So the lens
SURFACES candidates; the four-trap gate must (a) confirm the assets are worth more
than book, not impaired, and (b) find the realization catalyst — a hidden-asset
floor with no path to realization is a value trap (the land/holdco discount can
persist for decades). But unlike the melting cash-boxes, these floors GROW and
several already carry a live liquidation/activist catalyst — exactly the convex
"floor + catalyst" the mandate's option side wants. This is the highest-EV lens to
drive to verification next.
