"""field_prep tested with tiny in-memory fixtures — no gz, no network. Proves the
panel->packet assembly (meta filtering, marketcap/trend, trajectories, floor
inputs, honest drop accounting) so the runner is just I/O around trusted funcs."""
from shared.field_prep import (
    FieldOptions,
    ORACLE_FIELD,
    WHOLE_MARKET,
    assemble_field,
    index_meta,
    marketcap_series,
    meta_ok,
    net_cash_ratio_pct,
    trajectories,
)

META = [
    {"ticker": "GOOD", "name": "Good Widgets", "sector": "Industrials",
     "industry": "Tools", "location": "United States", "currency": "USD", "isdelisted": "N"},
    {"ticker": "BANK", "name": "A Bank", "sector": "Financial Services",
     "industry": "Banks", "location": "United States", "currency": "USD", "isdelisted": "N"},
    {"ticker": "CHNA", "name": "China Co", "sector": "Technology",
     "industry": "Software", "location": "China", "currency": "USD", "isdelisted": "N"},
    {"ticker": "EURO", "name": "Euro Co", "sector": "Industrials",
     "industry": "Tools", "location": "Germany", "currency": "EUR", "isdelisted": "N"},
    {"ticker": "DEAD", "name": "Dead Co", "sector": "Industrials",
     "industry": "Tools", "location": "United States", "currency": "USD", "isdelisted": "Y"},
    {"ticker": "MEGA", "name": "Mega Cap", "sector": "Technology",
     "industry": "Software", "location": "United States", "currency": "USD", "isdelisted": "N"},
]
DAILY = (
    [{"ticker": "GOOD", "date": f"2026-06-{d:02d}", "marketcap": 400.0 + d} for d in range(1, 27)]
    + [{"ticker": "BANK", "date": f"2026-06-{d:02d}", "marketcap": 9000.0} for d in range(1, 27)]
    + [{"ticker": "MEGA", "date": f"2026-06-{d:02d}", "marketcap": 50_000.0} for d in range(1, 27)]
    # NOFIN has SF1 but no marketcap series -> counted as no_marketcap
)
M = 1_000_000.0  # SF1 rows are in actual dollars; toy values in $mm for readability
SF1 = {
    "GOOD": [{"ticker": "GOOD", "calendardate": f"2025-{q:02d}-01", "revenue": rev * M,
              "netinc": rev * 0.1 * M, "equity": 300.0 * M, "intangibles": 20.0 * M,
              "cashneq": 120.0 * M, "investmentsc": 30.0 * M, "debt": 40.0 * M}
             for q, rev in [(3, 100.0), (6, 110.0), (9, 130.0), (12, 160.0)]],
    "BANK": [{"ticker": "BANK", "calendardate": "2025-12-01", "revenue": 500.0 * M, "netinc": 90.0 * M,
              "equity": 2000.0 * M, "intangibles": 0.0, "cashneq": 100.0 * M, "debt": 8000.0 * M}],
    "MEGA": [{"ticker": "MEGA", "calendardate": "2025-12-01", "revenue": 9000.0 * M, "netinc": 3000.0 * M,
              "equity": 40000.0 * M, "intangibles": 0.0, "cashneq": 5000.0 * M, "debt": 1000.0 * M}],
    "NOFIN": [{"ticker": "NOFIN", "calendardate": "2025-12-01", "revenue": 5.0 * M, "netinc": 1.0 * M,
               "equity": 10.0 * M, "intangibles": 0.0, "cashneq": 1.0 * M, "debt": 0.0}],
}
SF1_ROWS = [r for rows in SF1.values() for r in rows]


def test_index_meta_prefers_live():
    rows = [{"ticker": "X", "isdelisted": "Y", "sector": "old"},
            {"ticker": "X", "isdelisted": "N", "sector": "new"}]
    assert index_meta(rows)["X"]["sector"] == "new"


def test_meta_ok_filters():
    meta = index_meta(META)
    assert meta_ok("GOOD", meta, ORACLE_FIELD) is True
    assert meta_ok("BANK", meta, ORACLE_FIELD) is False      # financials excluded
    assert meta_ok("CHNA", meta, ORACLE_FIELD) is False      # China excluded
    assert meta_ok("EURO", meta, ORACLE_FIELD) is False      # non-USD excluded
    assert meta_ok("DEAD", meta, ORACLE_FIELD) is False      # delisted excluded
    assert meta_ok("BANK", meta, WHOLE_MARKET) is True       # Proteus keeps financials
    assert meta_ok("UNKNOWN", meta, ORACLE_FIELD) is True    # unknown -> keep


def test_marketcap_series_current_and_trend():
    mcap, ret, median, as_of = marketcap_series(DAILY, recent_window=25)
    assert as_of == "2026-06-26"
    assert mcap["GOOD"] == 426.0                              # last bar, $mm
    # 25-bar window: from 2026-06-02 (402) to 2026-06-26 (426)
    assert round(ret["GOOD"], 4) == round(426.0 / 402.0 - 1.0, 4)
    assert ret["BANK"] == 0.0                                 # flat


def test_trajectories_trailing():
    t = trajectories(SF1["GOOD"], quarters=3)
    assert t["revenue_trajectory"] == [110.0, 130.0, 160.0]  # last 3, chronological, $mm
    assert t["margin_trajectory"] == [0.1, 0.1, 0.1]


def test_net_cash_ratio():
    latest = SF1["GOOD"][-1]                                  # cash 120mm + inv 30mm - debt 40mm = 110mm
    # net cash $110mm over a $426mm cap -> ~25.8% (dollars reconciled against $mm cap)
    assert net_cash_ratio_pct(latest, 426.0) == round(110.0 / 426.0 * 100, 2)
    assert net_cash_ratio_pct(latest, None) is None
    assert net_cash_ratio_pct(latest, 0) is None


def test_assemble_oracle_field_carves_ground():
    out = assemble_field(SF1_ROWS, DAILY, META, opt=ORACLE_FIELD)
    syms = {p["symbol"] for p in out["packets"]}
    assert syms == {"GOOD"}                                   # BANK excluded (financials), MEGA over cap
    d = out["coverage"]["drops"]
    assert d["meta_excluded"] == 1                            # BANK
    assert d["above_max_mcap"] == 1                           # MEGA (50_000 > 20_000)
    assert d["no_marketcap"] == 1                             # NOFIN has SF1 but no daily
    p = out["packets"][0]
    assert p["mcap_musd"] == 426.0 and p["revenue_trajectory"][-1] == 160.0  # $mm
    assert p["net_cash_ratio_pct"] == round(110.0 / 426.0 * 100, 2)
    assert p["as_of"] == "2026-06-26"


def test_assemble_whole_market_keeps_financials():
    out = assemble_field(SF1_ROWS, DAILY, META, opt=WHOLE_MARKET)
    syms = {p["symbol"] for p in out["packets"]}
    assert "BANK" in syms and "MEGA" in syms                  # Proteus keeps both
    assert "GOOD" in syms


def test_assemble_skip_symbols():
    opt = FieldOptions(skip_symbols=frozenset({"GOOD"}), max_mcap_musd=20_000.0,
                       exclude_sectors=frozenset({"Financial Services"}))
    out = assemble_field(SF1_ROWS, DAILY, META, opt=opt)
    assert "GOOD" not in {p["symbol"] for p in out["packets"]}
    assert out["coverage"]["drops"]["skip_symbols"] == 1


def test_assemble_attaches_theme_and_special():
    def tagger(industry, name):
        return {"theme": "ai", "theme_strength": 0.8} if industry == "Tools" else None
    out = assemble_field(SF1_ROWS, DAILY, META, opt=ORACLE_FIELD,
                         theme_tagger=tagger, special_symbols={"GOOD"})
    p = out["packets"][0]
    assert p["theme"] == "ai" and p["special_situation"] == "event"


def test_every_sf1_ticker_accounted():
    # conservation: packets + all drop reasons == number of SF1 tickers
    out = assemble_field(SF1_ROWS, DAILY, META, opt=ORACLE_FIELD)
    n_drop = sum(out["coverage"]["drops"].values())
    assert out["coverage"]["n_packets"] + n_drop == out["coverage"]["n_sf1_tickers"]
