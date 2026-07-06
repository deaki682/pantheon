"""Asset-revaluation lens — pure-logic tests (2026-07-06, no network)."""
from oracle import asset_revaluation as ar


def _bs(**kw):
    base = dict(ticker="TST", datekey="2026-03-31", cashneq=0, investmentsc=0,
                debt=0, assetsc=0, assets=0, liabilities=0, equity=0,
                intangibles=0, sharesbas=1)
    base.update(kw)
    return base


def _meta(**kw):
    base = dict(name="Land Co", exchange="NYSE", category="Domestic Common Stock",
                isdelisted="N", sector="Consumer Defensive", industry="Farm Products",
                currency="USD", location="Florida; U.S.A")
    base.update(kw)
    return base


def test_metrics_ltta_and_nav():
    # $500M total assets, $50M current, $10M intangibles -> $440M long-term tangible
    # $40M debt, $20M cash -> net_debt $20M -> nav_at_cost $420M
    m = ar.asset_metrics(_bs(assets=500e6, assetsc=50e6, intangibles=10e6,
                             debt=40e6, cashneq=20e6))
    assert m["ltta"] == 440e6
    assert m["net_debt"] == 20e6
    assert m["nav_at_cost"] == 420e6


def test_appreciation_industry_classifier():
    assert ar.is_appreciation_asset(_meta(industry="Farm Products")) == "land"
    assert ar.is_appreciation_asset(_meta(industry="REIT - Office")) == "land"
    assert ar.is_appreciation_asset(_meta(industry="Gold")) == "resource"
    assert ar.is_appreciation_asset(_meta(industry="Steel")) is None  # depreciates, not appreciates
    assert ar.is_appreciation_asset(_meta(industry="Software - Application")) is None


def test_screen_flags_land_rich_below_nav():
    # farmland co: $400M LT tangible assets at cost, no debt, $250M mkt cap
    row = _bs(assets=440e6, assetsc=40e6, intangibles=0, debt=0, cashneq=0)
    cand = ar.screen_name(row, 250e6, _meta(name="Alico-like"))
    assert cand is not None
    assert cand["asset_kind"] == "land"
    assert cand["floor_basis"] == "transacting_asset"
    assert cand["why_mispriced_type"] == "neglect"
    assert cand["asset_coverage"] == round(400e6 / 250e6, 2)   # 1.6x asset backing


def test_screen_rejects_non_appreciation_industry():
    row = _bs(assets=440e6, assetsc=40e6, debt=0)
    assert ar.screen_name(row, 250e6, _meta(industry="Steel")) is None


def test_screen_rejects_leverage_swamped():
    # assets $400M but net debt $350M (0.875x) -> debt swamps the land
    row = _bs(assets=440e6, assetsc=40e6, debt=350e6, cashneq=0)
    assert ar.screen_name(row, 250e6, _meta()) is None


def test_screen_rejects_thin_coverage():
    # net assets at cost only $100M vs $250M cap -> 0.4x, below 0.80 -> skip
    row = _bs(assets=140e6, assetsc=40e6, debt=0)
    assert ar.screen_name(row, 250e6, _meta()) is None


def test_resource_flagged_commodity_dependent():
    row = _bs(assets=440e6, assetsc=40e6, debt=0)
    cand = ar.screen_name(row, 250e6, _meta(sector="Basic Materials", industry="Gold"))
    assert cand["asset_kind"] == "resource"
    assert cand["commodity_dependent"] is True


def test_reuses_neglect_hygiene_gate():
    # China domicile / crypto name / financials still excluded via is_common_tradable
    row = _bs(assets=440e6, assetsc=40e6, debt=0)
    assert ar.screen_name(row, 250e6, _meta(location="Beijing; China")) is None
    assert ar.screen_name(row, 250e6, _meta(sector="Financial Services", industry="Banks")) is None
