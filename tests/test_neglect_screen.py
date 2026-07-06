"""Neglect-leg below-floor screen — pure-logic tests (2026-07-06, no network).

The three floors, the hardest-first pick, the full-debt-stack netting (XRN),
the melting-floor runway flag (ARVN), the common-stock/financials gates, and
the panel dedupe/rank.
"""
from oracle import neglect_screen as ns


def _bs(**kw):
    base = dict(ticker="TST", datekey="2026-03-31", cashneq=0, investmentsc=0,
                debt=0, assetsc=0, assets=0, liabilities=0, liabilitiesc=0,
                equity=0, intangibles=0, sharesbas=1, netinc=0, ncfo=0, revenue=0)
    base.update(kw)
    return base


def _meta(**kw):
    base = dict(name="Test Co", exchange="NASDAQ", category="Domestic Common Stock",
                isdelisted="N", sector="Technology", currency="USD")
    base.update(kw)
    return base


# --- floors -----------------------------------------------------------------

def test_net_cash_is_net_of_full_debt_stack():
    # the XRN trap: cash-rich on one line, but debt nets it to below zero
    fl = ns.floors(_bs(cashneq=100e6, investmentsc=20e6, debt=652.7e6))
    assert round(fl.net_cash) == round(120e6 - 652.7e6)
    assert fl.net_cash < 0  # a levered "cash-rich" name is NOT net-cash


def test_ncav_and_tangible_book():
    fl = ns.floors(_bs(assetsc=500e6, liabilities=200e6, equity=400e6, intangibles=150e6))
    assert fl.ncav == 300e6           # current assets − total liabilities
    assert fl.tangible_book == 250e6  # equity − intangibles(incl goodwill)


# --- best_floor: hardest applicable floor wins ------------------------------

def test_best_floor_reports_hardest_below():
    fl = ns.Floors(net_cash=200e6, ncav=300e6, tangible_book=400e6)
    hit = ns.best_floor(150e6, fl)                 # below all three
    assert hit["floor_type"] == "net_cash"          # hardest reported
    assert hit["floor_basis"] == "net_net"
    assert hit["discount"] == round(1 - 150 / 200, 4)


def test_best_floor_falls_to_book_when_above_cash():
    fl = ns.Floors(net_cash=100e6, ncav=120e6, tangible_book=500e6)
    hit = ns.best_floor(300e6, fl)                  # above cash & ncav, below book
    assert hit["floor_type"] == "tangible_book"
    assert hit["floor_basis"] == "book"


def test_best_floor_none_when_priced_above_all():
    fl = ns.Floors(net_cash=100e6, ncav=120e6, tangible_book=200e6)
    assert ns.best_floor(500e6, fl) is None


def test_best_floor_ignores_negative_floors():
    fl = ns.Floors(net_cash=-50e6, ncav=-10e6, tangible_book=300e6)
    hit = ns.best_floor(200e6, fl)
    assert hit["floor_type"] == "tangible_book"     # negatives skipped


# --- runway: the melting-floor flag -----------------------------------------

def test_runway_none_when_cash_generative():
    assert ns.cash_runway_quarters(_bs(ncfo=5e6), net_cash=100e6) is None


def test_runway_flags_short_burn():
    # burns 25M/quarter, 100M net cash -> 4 quarters -> eroding (<8)
    q = ns.cash_runway_quarters(_bs(ncfo=-25e6), net_cash=100e6)
    assert q == 4.0


# --- gates ------------------------------------------------------------------

def test_common_tradable_gate():
    assert ns.is_common_tradable(_meta())
    assert not ns.is_common_tradable(_meta(isdelisted="Y"))
    assert not ns.is_common_tradable(_meta(category="Domestic Common Stock Warrant"))
    assert not ns.is_common_tradable(_meta(category="ETF"))
    assert not ns.is_common_tradable(_meta(category="CEF"))
    assert not ns.is_common_tradable(_meta(sector="Financial Services"))
    assert not ns.is_common_tradable(_meta(currency="KRW"))  # FX-artifact guard
    assert not ns.is_common_tradable(  # mortgage REIT = financial float, no floor
        _meta(sector="Real Estate", industry="REIT - Mortgage"))
    assert ns.is_common_tradable(  # equity REIT = real property floor, kept
        _meta(sector="Real Estate", industry="REIT - Office"))
    assert ns.is_common_tradable(_meta(category="ADR Common Stock"))  # USD ADR ok


def test_screen_name_emits_neglect_candidate():
    # 500M net cash, burns 30M/q -> 16.7q runway (>8) -> NOT eroding
    row = _bs(ticker="ARVN", cashneq=500e6, investmentsc=0, debt=0, ncfo=-30e6,
              assetsc=520e6, liabilities=60e6, equity=480e6, intangibles=0)
    cand = ns.screen_name(row, 400e6, _meta(name="Arvinas"))
    assert cand["why_mispriced_type"] == "neglect"
    assert cand["floor_type"] == "net_cash"
    assert cand["floor_basis"] == "net_net"
    assert cand["runway_quarters"] == round(500 / 30, 1)
    assert cand["eroding_floor"] is False


def test_screen_name_flags_melting_floor():
    # 120M net cash, burns 40M/q -> 3q runway (<8) -> ERODING flag (the ARVN caveat)
    row = _bs(ticker="MELT", cashneq=120e6, debt=0, ncfo=-40e6)
    cand = ns.screen_name(row, 90e6, _meta(name="Melting Co"))
    assert cand["floor_type"] == "net_cash"
    assert cand["runway_quarters"] == 3.0
    assert cand["eroding_floor"] is True


def test_screen_name_cap_bounds():
    row = _bs(cashneq=10_000e6, debt=0)             # $10B net cash
    # a $5B mcap below a $10B floor but ABOVE the neglect cap -> not neglect
    assert ns.screen_name(row, 5_000e6, _meta()) is None
    # a $5M mcap below MIN_CAP -> untradable noise
    tiny = _bs(cashneq=8e6, debt=0)
    assert ns.screen_name(tiny, 5e6, _meta()) is None


def test_screen_name_rejects_priced_above_floor():
    row = _bs(cashneq=100e6, debt=0, assetsc=100e6, liabilities=90e6,
              equity=100e6, intangibles=0)
    assert ns.screen_name(row, 500e6, _meta()) is None  # above every floor


# --- panel: rank + exclude --------------------------------------------------

def test_screen_panel_ranks_by_discount_and_excludes():
    sf1 = {
        "AAA": _bs(ticker="AAA", cashneq=400e6, debt=0),   # deep discount
        "BBB": _bs(ticker="BBB", cashneq=110e6, debt=0),   # shallow discount
        "CCC": _bs(ticker="CCC", cashneq=400e6, debt=0),   # excluded
    }
    mcap = {"AAA": 100e6, "BBB": 100e6, "CCC": 100e6}
    meta = {t: _meta(name=t) for t in sf1}
    out = ns.screen_panel(sf1, mcap, meta, exclude_tickers={"CCC"})
    assert [c["ticker"] for c in out] == ["AAA", "BBB"]  # deepest first
    assert out[0]["discount"] > out[1]["discount"]
