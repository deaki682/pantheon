import json
import os
from datetime import datetime, timedelta

import pytest

from shared.fundamentals import (
    FundamentalSnapshot,
    annual,
    build_snapshot,
    load_cached_snapshot,
    load_stale,
    quarterly,
    latest_instant,
    save_cached_snapshot,
    score_data_quality,
    ttm,
    yoy,
)


def _q(start, end, val, fp=None, fy=None, filed=None, form="10-Q"):
    return {
        "start": start, "end": end, "val": val,
        "fp": fp, "fy": fy, "filed": filed or end, "form": form,
    }


def _instant(end, val, filed=None):
    return {"end": end, "val": val, "filed": filed or end}


def test_quarterly_filters_by_span():
    units = [
        _q("2023-01-01", "2023-03-31", 100),  # ~90 days
        _q("2023-01-01", "2023-12-31", 400, form="10-K"),  # ~365 days
        _q("2023-04-01", "2023-06-30", 110),
    ]
    qs = quarterly(units)
    assert len(qs) == 2
    assert qs[0]["val"] == 100


def test_quarterly_excludes_10k():
    units = [
        _q("2023-01-01", "2023-12-31", 400, form="10-K"),
    ]
    assert quarterly(units) == []


def test_annual_finds_yearly():
    units = [
        _q("2023-01-01", "2023-12-31", 400, form="10-K"),
        _q("2023-01-01", "2023-03-31", 100),
    ]
    ans = annual(units)
    assert len(ans) == 1
    assert ans[0]["val"] == 400


def test_latest_instant():
    units = [
        _instant("2023-06-30", 500),
        _instant("2023-09-30", 600),
        _instant("2023-03-31", 400),
    ]
    li = latest_instant(units)
    assert li["end"] == "2023-09-30"
    assert li["val"] == 600


def test_latest_instant_none():
    assert latest_instant([_q("2023-01-01", "2023-03-31", 100)]) is None


def test_ttm_sums_last_four_quarters():
    units = [
        _q("2022-10-01", "2022-12-31", 100),
        _q("2023-01-01", "2023-03-31", 110),
        _q("2023-04-01", "2023-06-30", 120),
        _q("2023-07-01", "2023-09-30", 130),
    ]
    assert ttm(units) == pytest.approx(460.0)


def test_ttm_returns_none_when_short():
    units = [_q("2023-01-01", "2023-03-31", 100)]
    assert ttm(units) is None


def test_ttm_dedupes_by_end_date_takes_latest_filed():
    units = [
        _q("2022-10-01", "2022-12-31", 100),
        _q("2023-01-01", "2023-03-31", 110),
        _q("2023-04-01", "2023-06-30", 120),
        _q("2023-07-01", "2023-09-30", 130, filed="2023-10-01"),
        _q("2023-07-01", "2023-09-30", 135, filed="2023-11-01"),  # restated, later filed
    ]
    # Should use the later-filed restated 135.
    assert ttm(units) == pytest.approx(100 + 110 + 120 + 135)


def test_yoy_growth():
    units = [
        _q("2021-10-01", "2021-12-31", 80),
        _q("2022-01-01", "2022-03-31", 90),
        _q("2022-04-01", "2022-06-30", 100),
        _q("2022-07-01", "2022-09-30", 110),  # prior TTM = 380
        _q("2022-10-01", "2022-12-31", 100),
        _q("2023-01-01", "2023-03-31", 110),
        _q("2023-04-01", "2023-06-30", 120),
        _q("2023-07-01", "2023-09-30", 130),  # cur TTM = 460
    ]
    # (460 - 380) / 380
    assert yoy(units) == pytest.approx((460 - 380) / 380)


def test_yoy_returns_none_when_short():
    assert yoy([]) is None


def test_yoy_returns_none_when_prior_negative():
    # Prior TTM = -40 (losses), cur TTM = +80 (profit). Growth from a negative
    # base is not meaningful; should return None rather than an inflated 300%.
    units = [
        _q("2021-10-01", "2021-12-31", -10),
        _q("2022-01-01", "2022-03-31", -10),
        _q("2022-04-01", "2022-06-30", -10),
        _q("2022-07-01", "2022-09-30", -10),  # prior TTM = -40
        _q("2022-10-01", "2022-12-31", 20),
        _q("2023-01-01", "2023-03-31", 20),
        _q("2023-04-01", "2023-06-30", 20),
        _q("2023-07-01", "2023-09-30", 20),  # cur TTM = +80
    ]
    assert yoy(units) is None


def test_data_quality_zero_for_empty():
    snap = FundamentalSnapshot(symbol="X")
    assert score_data_quality(snap) == 0.0


def test_data_quality_full():
    snap = FundamentalSnapshot(
        symbol="X",
        revenue_ttm=1.0, net_income_ttm=1.0, ocf_ttm=1.0, cash_and_equiv=1.0,
        equity=1.0, shares_diluted=1.0,
        revenue_yoy=0.1, free_cash_flow_ttm=1.0, sbc_ttm=1.0, debt_total=1.0,
        gross_margin_ttm=0.4, operating_margin_ttm=0.2, dilution_yoy=0.01,
    )
    assert score_data_quality(snap) == pytest.approx(1.0)


def test_data_quality_partial():
    snap = FundamentalSnapshot(symbol="X", revenue_ttm=1.0)
    # 1 of 6 critical, 0 of 7 secondary
    expected = 0.6 * (1 / 6) + 0.4 * 0
    assert score_data_quality(snap) == pytest.approx(expected)


def test_build_snapshot_minimal():
    facts = {
        "Revenues": {"units": {"USD": [
            _q("2022-10-01", "2022-12-31", 100),
            _q("2023-01-01", "2023-03-31", 110),
            _q("2023-04-01", "2023-06-30", 120),
            _q("2023-07-01", "2023-09-30", 130),
        ]}},
    }
    snap = build_snapshot("X", facts)
    assert snap.symbol == "X"
    assert snap.revenue_ttm == pytest.approx(460.0)


def test_build_snapshot_empty_facts():
    snap = build_snapshot("X", {})
    assert snap.symbol == "X"
    assert snap.revenue_ttm is None
    assert snap.data_quality == 0.0


def test_build_snapshot_runway_burn():
    # Negative OCF -> runway computed
    facts = {
        "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": [
            _q("2022-10-01", "2022-12-31", -25),
            _q("2023-01-01", "2023-03-31", -25),
            _q("2023-04-01", "2023-06-30", -25),
            _q("2023-07-01", "2023-09-30", -25),
        ]}},
        "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": [
            _instant("2023-09-30", 400),
        ]}},
    }
    snap = build_snapshot("X", facts)
    # ocf_ttm = -100, burn/q = 25, cash = 400, runway = 16 quarters
    assert snap.cash_runway_quarters == pytest.approx(16.0)


def test_cache_save_and_load(tmp_path):
    snap = FundamentalSnapshot(symbol="X", fetched_at=datetime.utcnow().isoformat(), revenue_ttm=100.0)
    save_cached_snapshot(str(tmp_path), snap)
    loaded = load_cached_snapshot(str(tmp_path), "X")
    assert loaded is not None
    assert loaded.revenue_ttm == 100.0


def test_cache_stale_returns_none(tmp_path):
    old = (datetime.utcnow() - timedelta(days=60)).isoformat()
    snap = FundamentalSnapshot(symbol="X", fetched_at=old, revenue_ttm=100.0)
    save_cached_snapshot(str(tmp_path), snap)
    assert load_cached_snapshot(str(tmp_path), "X", ttl_days=30) is None


def test_cache_load_stale_fallback(tmp_path):
    old = (datetime.utcnow() - timedelta(days=60)).isoformat()
    snap = FundamentalSnapshot(symbol="X", fetched_at=old, revenue_ttm=100.0)
    save_cached_snapshot(str(tmp_path), snap)
    # load_stale ignores TTL
    loaded = load_stale(str(tmp_path), "X")
    assert loaded is not None
    assert loaded.revenue_ttm == 100.0


def test_cache_missing(tmp_path):
    assert load_cached_snapshot(str(tmp_path), "MISSING") is None
    assert load_stale(str(tmp_path), "MISSING") is None
