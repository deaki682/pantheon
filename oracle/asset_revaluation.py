"""Asset-revaluation lens — the ALCO gap (2026-07-06).

The neglect screen finds `price < book`. This finds the OPPOSITE mispricing: a
name whose BOOK UNDERSTATES its assets — land / farmland / timberland / vineyards /
real estate carried at HISTORICAL COST (or depreciated cost) and worth multiples
at market. Alico's Florida acreage sits on the books at 1960s cost; a below-book
screen is structurally blind to it because ALCO trades ABOVE book — yet possibly
far below the market value of the land. The convex floor here is the
TRANSACTING-ASSET value (acreage x $/acre, buildings x cap rate), which the
precision read appraises; the catalyst is a realization path (parcel sales, land-
use conversion, a REIT liquidation, an activist forcing a sale).

This is a COVERAGE screen, deliberately generous: it cannot appraise market value
(that is the whole point — book is cost, not market), so it surfaces the
CANDIDATES most likely to hold hidden asset value — asset-heavy names in
APPRECIATION sectors where cost systematically understates market — for the
four-trap precision gate to appraise. A generic capital-heavy money-loser (a
steel mill, an old factory) is NOT here: its plant/equipment is worth LESS than
cost (obsolescence), not more. Only LAND-and-real-estate-type assets appreciate
above carrying value, so the industry filter is load-bearing.

Every candidate still faces `make_convex_dossier -> verify_dossier ->
rank_fundable`; here the verification is an ASSET APPRAISAL (is the market value
really above book?) plus a REALIZATION-catalyst read (is anything unlocking it?).
A hidden-asset floor with no path to realization is a value trap (the holdco/land
discount can persist for decades) — the catalyst is what makes it convex.

Reuses the neglect leg's `is_common_tradable` gate (USD reporter, not a financial/
mortgage-REIT/China-shell/crypto-name/warrant/delisted) so the two lenses share
one hygiene layer.
"""
from __future__ import annotations

from typing import Optional

from oracle.neglect_screen import is_common_tradable, _num

# --- coverage dials ---------------------------------------------------------
AR_CAP_USD = 5_000e6         # real-estate / ag / timber can run larger than the
                             # net-cash neglect names; allow up to $5B
AR_MIN_CAP_USD = 10e6
# net appreciating-assets (at cost, after debt) must be at least this fraction of
# the market cap — since market value >= cost in these sectors, a name whose
# COST-basis net hard assets already rival its cap is likely cheap to true NAV.
AR_COVERAGE_MIN = 0.80
# debt must not swamp the assets — the equity needs a real claim on the land.
AR_LEVERAGE_MAX = 0.70       # net_debt / long-term tangible assets

# Industries where CARRYING VALUE (historical / depreciated cost) systematically
# UNDERSTATES market value — land-and-real-estate-type assets that appreciate.
# Mortgage REITs are NOT here (they hold financial paper, and are already excluded
# by the neglect gate). Plant/equipment-heavy industries (Steel, Chemicals) are
# deliberately excluded — their PP&E depreciates below cost, it does not appreciate.
LAND_REAL_ASSET_INDUSTRIES = frozenset({
    # farmland / agriculture
    "Farm Products", "Agricultural Inputs",
    # vineyards / distilleries — own land + appreciating aging inventory
    "Beverages - Wineries & Distilleries",
    # timberland / forest products
    "Lumber & Wood Production", "Paper & Paper Products",
    # equity real estate — GAAP depreciated-cost book understates appreciating property
    "Real Estate - Development", "Real Estate Services", "Real Estate - Diversified",
    "REIT - Office", "REIT - Retail", "REIT - Residential", "REIT - Industrial",
    "REIT - Diversified", "REIT - Specialty", "REIT - Hotel & Motel",
    "REIT - Healthcare Facilities",
})
# Resource RESERVES (metals/coal/uranium) — reserves carried at cost can be worth
# far more (or less) at strip prices; commodity-dependent, so surfaced but FLAGGED
# `commodity_dependent` for the precision read to appraise at current prices.
RESOURCE_RESERVE_INDUSTRIES = frozenset({
    "Gold", "Silver", "Copper", "Uranium", "Thermal Coal", "Coking Coal",
    "Other Precious Metals & Mining", "Other Industrial Metals & Mining",
})


def asset_metrics(row: dict) -> dict:
    """Long-term tangible assets (at cost), net debt, and net-asset-value-at-cost
    from a Sharadar SF1 row (dollars).

    ltta = total assets − current assets − intangibles ≈ the long-term TANGIBLE
    asset base (PP&E / land / property; also folds in long-term investments — a
    coverage-stage imprecision the precision read resolves). net_debt = debt −
    cash − current investments. nav_at_cost = ltta − max(net_debt, 0): the equity's
    claim on the appreciating assets, valued at COST (so a floor on the true NAV)."""
    assets = _num(row, "assets")
    assetsc = _num(row, "assetsc")
    intang = _num(row, "intangibles")
    ltta = assets - assetsc - intang
    net_debt = _num(row, "debt") - _num(row, "cashneq") - _num(row, "investmentsc")
    nav_at_cost = ltta - max(net_debt, 0.0)
    return {"ltta": ltta, "net_debt": net_debt, "nav_at_cost": nav_at_cost}


def is_appreciation_asset(meta: dict) -> Optional[str]:
    """Return 'land' if the name is in a land/real-estate/timber appreciation
    industry, 'resource' for a commodity-reserve industry, else None."""
    ind = meta.get("industry") or ""
    if ind in LAND_REAL_ASSET_INDUSTRIES:
        return "land"
    if ind in RESOURCE_RESERVE_INDUSTRIES:
        return "resource"
    return None


def screen_name(
    row: dict, mcap_usd: float, meta: dict, *,
    ar_cap_usd: float = AR_CAP_USD,
    ar_min_cap_usd: float = AR_MIN_CAP_USD,
    coverage_min: float = AR_COVERAGE_MIN,
    leverage_max: float = AR_LEVERAGE_MAX,
) -> Optional[dict]:
    """Screen ONE name → an asset-revaluation candidate, or None. Surfaces
    asset-heavy names in appreciation sectors whose COST-basis net hard assets
    already rival the market cap (so true NAV likely exceeds it). Emits
    why_mispriced_type='neglect', floor_basis='transacting_asset' — the precision
    read appraises the true market value and looks for a realization catalyst."""
    if not is_common_tradable(meta):
        return None
    kind = is_appreciation_asset(meta)
    if kind is None:
        return None
    if not (ar_min_cap_usd <= mcap_usd <= ar_cap_usd):
        return None
    m = asset_metrics(row)
    if m["ltta"] <= 0:
        return None
    # debt must not swamp the appreciating assets
    if m["net_debt"] > 0 and (m["net_debt"] / m["ltta"]) > leverage_max:
        return None
    coverage = m["nav_at_cost"] / mcap_usd if mcap_usd > 0 else 0.0
    if coverage < coverage_min:
        return None
    return {
        "ticker": row.get("ticker"),
        "company": meta.get("name"),
        "sector": meta.get("sector"),
        "industry": meta.get("industry"),
        "asset_kind": kind,                       # land | resource
        "commodity_dependent": kind == "resource",
        "why_mispriced_type": "neglect",
        "floor_basis": "transacting_asset",
        "ltta_usd": round(m["ltta"], 0),          # long-term tangible assets at cost
        "net_debt_usd": round(m["net_debt"], 0),
        "nav_at_cost_usd": round(m["nav_at_cost"], 0),
        "marketcap_usd": round(mcap_usd, 0),
        "asset_coverage": round(coverage, 2),     # cost-basis net hard assets / mkt cap
        "as_of": row.get("datekey"),
        "source": "asset_revaluation",
        "mechanism": ("Hidden-asset floor: land / real estate / timber carried at "
                      "historical cost that understates market value; the market "
                      "prices the operating result, not the appreciating asset."),
        "precision_note": ("APPRAISE the true market value (acreage x $/acre, "
                           "property x cap rate, reserves at strip) AND find the "
                           "realization catalyst (parcel sales / conversion / "
                           "liquidation / activist) — a hidden floor with no "
                           "realization path is a value trap, not convex."),
    }


def screen_panel(
    sf1_by_ticker: dict[str, dict],
    mcap_by_ticker: dict[str, float],
    meta_by_ticker: dict[str, dict],
    *,
    ar_cap_usd: float = AR_CAP_USD,
    ar_min_cap_usd: float = AR_MIN_CAP_USD,
    exclude_tickers: Optional[set[str]] = None,
) -> list[dict]:
    """Run the asset-revaluation screen across the panel → candidates, most
    asset-backed (highest coverage) first."""
    exclude = exclude_tickers or set()
    out: list[dict] = []
    for ticker, row in sf1_by_ticker.items():
        if ticker in exclude:
            continue
        mcap = mcap_by_ticker.get(ticker)
        meta = meta_by_ticker.get(ticker)
        if mcap is None or meta is None:
            continue
        cand = screen_name(row, mcap, meta,
                           ar_cap_usd=ar_cap_usd, ar_min_cap_usd=ar_min_cap_usd)
        if cand:
            out.append(cand)
    return sorted(out, key=lambda c: -c["asset_coverage"])
