import math
import pytest

from achilles.pead_gauntlet import (
    seasonal_sue, build_entity_map, is_tradable_common, in_listing_window,
    simulate_trade, run_cell, summarize,
)


def test_seasonal_sue_math():
    # realistic EPS with natural quarter-to-quarter variation (nonzero seasonal
    # surprise variance), then a big final-quarter jump -> a large positive SUE.
    dates = [f"{y}-{m:02d}-01" for y in range(2018, 2022) for m in (3, 6, 9, 12)]
    vals = [1.0, 1.1, 0.9, 1.0,
            1.5, 1.4, 1.5, 1.4,
            2.0, 2.1, 1.9, 2.0,
            2.5, 2.4, 2.5, 7.0]   # last quarter jumps
    eps = list(zip(dates, vals))
    sue = seasonal_sue(eps, min_history=8)
    last_date = dates[-1]
    assert last_date in sue
    assert sue[last_date] > 5.0          # a huge surprise vs the recent-delta std


def test_seasonal_sue_needs_history():
    eps = [(f"2020-{m:02d}-01", 1.0 + i) for i, m in enumerate((3, 6, 9, 12))]
    assert seasonal_sue(eps) == {}          # <12 quarters -> nothing computable


def test_entity_window_guard_catches_recycled_ticker():
    rows = [{"ticker": "XYZ", "permaticker": 222, "firstpricedate": "2010-01-01",
             "lastpricedate": "2026-01-01", "category": "Domestic Common Stock",
             "exchange": "NASDAQ", "isdelisted": "N"}]
    emap = build_entity_map(rows)
    assert is_tradable_common("XYZ", emap)
    # a 2003 bar under "XYZ" is a DIFFERENT (old/recycled) entity -> rejected
    assert in_listing_window("XYZ", "2015-06-01", emap) is True
    assert in_listing_window("XYZ", "2003-06-01", emap) is False
    # OTC / non-common excluded from the tradable universe
    otc = build_entity_map([{"ticker": "PINK", "permaticker": 1, "firstpricedate": "2010-01-01",
                             "lastpricedate": "2026-01-01", "category": "Domestic Common Stock",
                             "exchange": "OTC"}])
    assert not is_tradable_common("PINK", otc)


def _flat_then(px_list):
    return [{"date": f"2020-01-{i+1:02d}", "px": p, "low": p} for i, p in enumerate(px_list)]


def test_simulate_trade_time_exit():
    path = _flat_then([10.0, 10.5, 11.0, 11.5, 12.0])
    t = simulate_trade(path, hold_days=3, stop_pct=0.08)
    assert t["reason"] == "time" and t["hold_used"] == 3
    assert t["gross_ret"] == pytest.approx(11.5 / 10.0 - 1)


def test_simulate_trade_stop_hit_intraday():
    # day 2 lows through the -8% stop (9.2)
    path = [{"date": "d0", "px": 10.0, "low": 10.0},
            {"date": "d1", "px": 9.7, "low": 9.5},
            {"date": "d2", "px": 9.4, "low": 9.0},   # low 9.0 <= 9.2 -> stop
            {"date": "d3", "px": 9.6, "low": 9.5}]
    t = simulate_trade(path, hold_days=3, stop_pct=0.08)
    assert t["reason"] == "stop" and t["hold_used"] == 2
    assert t["gross_ret"] == pytest.approx(9.2 / 10.0 - 1)   # exits at the stop level


def test_run_cell_gates_and_excess():
    events = [
        {"symbol": "A", "entry_date": "2020-01-01", "sue": 2.0, "reaction": 0.05, "bucket": "MICRO"},
        {"symbol": "B", "entry_date": "2020-01-01", "sue": 0.1, "reaction": 0.05, "bucket": "MICRO"},  # sue too low
        {"symbol": "C", "entry_date": "2020-01-01", "sue": 2.0, "reaction": 0.40, "bucket": "MICRO"},  # already fired
        {"symbol": "D", "entry_date": "2020-01-01", "sue": 2.0, "reaction": -0.02, "bucket": "MICRO"}, # sold beat
    ]
    paths = {"A": _flat_then([10.0, 10.5, 11.0])}

    def price_path(sym, entry, n):
        return paths.get(sym, [])

    def bucket_bench(bucket, entry, exit_):
        return 0.02   # bucket EW +2% over the window

    trades = run_cell(events, price_path=price_path, bucket_bench=bucket_bench,
                      hold_days=2, reaction_cap=0.20, sue_threshold=1.0, cost_oneway=0.0)
    assert [t["symbol"] for t in trades] == ["A"]       # only A clears all gates
    a = trades[0]
    assert a["net_ret"] == pytest.approx(11.0 / 10.0 - 1)
    assert a["excess"] == pytest.approx((11.0 / 10.0 - 1) - 0.02)


def test_run_cell_cost_reduces_return():
    events = [{"symbol": "A", "entry_date": "2020-01-01", "sue": 2.0, "reaction": 0.05, "bucket": "SMALL"}]
    paths = {"A": _flat_then([10.0, 10.5, 11.0])}
    trades = run_cell(events, price_path=lambda s, e, n: paths["A"],
                      bucket_bench=lambda b, e, x: 0.0,
                      hold_days=2, reaction_cap=0.20, sue_threshold=1.0, cost_oneway=0.005)
    # round-trip cost = 2 * 0.005 = 1% off the gross
    assert trades[0]["net_ret"] == pytest.approx((11.0 / 10.0 - 1) - 0.01)


def test_summarize():
    trades = [{"excess": 0.05, "reason": "time"}, {"excess": -0.03, "reason": "stop"},
              {"excess": 0.02, "reason": "time"}, {"excess": 0.04, "reason": "time"}]
    s = summarize(trades)
    assert s["n"] == 4
    assert s["win"] == 0.75
    assert s["stop_rate"] == 0.25
    assert s["mean_excess"] == pytest.approx(0.02)
