"""Tests for the smaller Oracle modules: calendar, prescreener, screener,
smart_money, backtest, capital."""
import datetime
import pytest

from oracle.backtest import run as backtest_run
from oracle.calendar import (
    days_since, is_trading_day, mark_run, ran_today, should_run,
)
from oracle.capital import (
    CAPITAL_BASE, CAPITAL_CEILING, ACHILLES_RESERVE,
    compute_allocation,
)
from oracle.prescreener import prescreen, batch_prescreen
from oracle.screener import multi_lens_score, pick_candidates, quality_score, rank_survivors
from oracle.smart_money import (
    SMART_MONEY_FUNDS, Holding, activist_signal, is_fresh_13d,
    parse_13f_information_table, smart_money_holders,
)
from shared.fundamentals import FundamentalSnapshot


# ---- calendar ----

def test_should_run_when_no_record(tmp_path):
    p = tmp_path / "cal.json"
    assert should_run(str(p), "screen", interval_days=7)


def test_should_run_after_interval(tmp_path):
    p = tmp_path / "cal.json"
    long_ago = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    mark_run(str(p), "screen", now=long_ago)
    assert should_run(str(p), "screen", interval_days=7)


def test_should_not_run_before_interval(tmp_path):
    p = tmp_path / "cal.json"
    mark_run(str(p), "screen")
    assert not should_run(str(p), "screen", interval_days=7)


def test_days_since(tmp_path):
    p = tmp_path / "cal.json"
    long_ago = datetime.datetime.utcnow() - datetime.timedelta(days=10)
    mark_run(str(p), "screen", now=long_ago)
    assert days_since(str(p), "screen") >= 9.9


def test_should_run_mixed_naive_and_aware_timestamps(tmp_path):
    # Different callers have stamped mark_run() with naive and tz-aware
    # datetimes (e.g. "...T04:14:30+00:00" vs "...T04:14:30"). should_run
    # must not crash comparing across that mix — both are UTC in practice.
    p = tmp_path / "cal.json"
    aware_ts = (
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)
    ).isoformat()
    p.write_text('{"research": "%s"}' % aware_ts)
    assert should_run(str(p), "research", interval_days=3)
    assert days_since(str(p), "research") >= 9.9


def test_is_trading_day_weekday():
    assert is_trading_day("2026-07-02")   # Thursday


def test_is_trading_day_weekend():
    assert not is_trading_day("2026-07-04")  # Saturday
    assert not is_trading_day("2026-07-05")  # Sunday


def test_is_trading_day_holiday():
    # July-4 observed Friday — the day Delphi queued the churn orders.
    assert not is_trading_day("2026-07-03")
    assert not is_trading_day("2026-11-26")  # Thanksgiving
    assert not is_trading_day("2027-07-05")  # July-4 observed Monday


def test_is_trading_day_outside_table_raises():
    with pytest.raises(ValueError):
        is_trading_day("2028-01-03")


def test_ran_today_no_record(tmp_path):
    p = tmp_path / "cal.json"
    assert not ran_today(str(p), "trade")


def test_ran_today_same_calendar_date(tmp_path):
    p = tmp_path / "cal.json"
    mark_run(str(p), "trade")
    assert ran_today(str(p), "trade")


def test_ran_today_compares_dates_not_24h(tmp_path):
    # A run late yesterday must not block an early run today (the flaw
    # of should_run's rolling 24h window for a daily trade guard).
    p = tmp_path / "cal.json"
    yesterday_2300 = datetime.datetime.utcnow().replace(
        hour=23, minute=0
    ) - datetime.timedelta(days=1)
    mark_run(str(p), "trade", now=yesterday_2300)
    assert not ran_today(str(p), "trade")


# ---- prescreener ----

def test_prescreen_passes_clean():
    snap = FundamentalSnapshot(
        symbol="X", revenue_ttm=100, net_income_ttm=10, ocf_ttm=15,
        cash_and_equiv=50, equity=100, shares_diluted=10,
        revenue_yoy=0.1, free_cash_flow_ttm=10, sbc_ttm=2, debt_total=20,
        gross_margin_ttm=0.5, operating_margin_ttm=0.15, dilution_yoy=0.02,
        data_quality=0.9,
    )
    out = prescreen(snap)
    assert out["pass"] is True


def test_prescreen_fails_low_data():
    snap = FundamentalSnapshot(symbol="X")
    out = prescreen(snap)
    assert out["pass"] is False
    assert "data_quality_low" in out["reasons"]


def test_prescreen_fails_no_revenue():
    snap = FundamentalSnapshot(
        symbol="X", revenue_ttm=0, net_income_ttm=10, ocf_ttm=15,
        cash_and_equiv=50, equity=100, shares_diluted=10,
        data_quality=0.9,
    )
    out = prescreen(snap)
    assert "no_revenue" in out["reasons"]


def test_prescreen_fails_dilutive():
    snap = FundamentalSnapshot(
        symbol="X", revenue_ttm=100, net_income_ttm=10, ocf_ttm=15,
        cash_and_equiv=50, equity=100, shares_diluted=10,
        dilution_yoy=1.0, data_quality=0.9,
    )
    out = prescreen(snap)
    assert "dilutive" in out["reasons"]


def test_batch_prescreen():
    snaps = [FundamentalSnapshot(symbol="A"), FundamentalSnapshot(symbol="B")]
    out = batch_prescreen(snaps)
    assert len(out) == 2
    assert out[0]["symbol"] == "A"


# ---- screener ----

def test_quality_score_zero_for_empty():
    assert quality_score(FundamentalSnapshot(symbol="X")) == 0.0


def test_quality_score_full():
    snap = FundamentalSnapshot(
        symbol="X",
        gross_margin_ttm=0.6, operating_margin_ttm=0.25,
        free_cash_flow_ttm=30, revenue_ttm=100,
        revenue_yoy=0.3, dilution_yoy=0.0,
    )
    assert quality_score(snap) > 0.7


def test_quality_score_penalizes_sparse_coverage():
    # Only one component present (dilution clamps to 1.0). It must NOT read as
    # perfect quality — divide by the 3-component floor, not by 1.
    snap = FundamentalSnapshot(symbol="X", dilution_yoy=0.0)
    assert quality_score(snap) <= 1.0 / 3 + 1e-9


def test_quality_score_bounded_by_one_for_buybacks():
    # A heavy buyback (negative dilution_yoy) — possibly a noisy data artifact —
    # must not push the score above 1.0; the dilution term is clamped.
    snap = FundamentalSnapshot(
        symbol="X",
        gross_margin_ttm=0.6, operating_margin_ttm=0.25,
        free_cash_flow_ttm=30, revenue_ttm=100,
        revenue_yoy=0.3, dilution_yoy=-5.0,
    )
    assert 0.0 <= quality_score(snap) <= 1.0


def test_multi_lens_all():
    out = multi_lens_score("X", insider_cluster=True, smart_money=True,
                            activist_13d=True, quality=1.0, valuation=1.0,
                            sector_breadth=1.0)
    assert out["score"] == pytest.approx(1.0)
    assert out["insider_backed"] is True
    assert out["insider_tier"] == "full"


def test_multi_lens_none():
    out = multi_lens_score("X")
    assert out["score"] == 0.0
    assert out["insider_backed"] is False
    assert out["insider_tier"] == "none"


def test_rank_survivors_top_n():
    rows = [
        {"symbol": f"S{i}", "score": i * 0.1} for i in range(20)
    ]
    top = rank_survivors(rows, top_n=5)
    assert len(top) == 5
    assert top[0]["symbol"] == "S19"


def test_multi_lens_valuation_without_insider():
    """Without insider backing, valuation and quality still score but tier is 'none'."""
    out = multi_lens_score("X", valuation=0.8, quality=0.5)
    assert out["score"] == pytest.approx(0.25 * 0.8 + 0.15 * 0.5)
    assert out["lenses"]["valuation"] == 0.8
    assert out["insider_backed"] is False
    assert out["insider_tier"] == "none"


def test_multi_lens_insider_with_valuation():
    """Insider-backed + cheap + quality -> full tier."""
    out = multi_lens_score("X", insider_cluster=True, valuation=0.8, quality=0.5)
    assert out["insider_backed"] is True
    assert out["insider_tier"] == "full"
    assert out["score"] == pytest.approx(0.25 * 0.8 + 0.15 * 0.5 + 0.20)


def test_multi_lens_insider_without_quality():
    """Insider-backed but low quality -> half tier."""
    out = multi_lens_score("X", smart_money=True, valuation=0.5, quality=0.1)
    assert out["insider_backed"] is True
    assert out["insider_tier"] == "half"


# ---- valuation scoring ----

def test_valuation_score_cheap_stock():
    from shared.quality import valuation_score
    snap = FundamentalSnapshot(
        symbol="X", net_income_ttm=100e6, free_cash_flow_ttm=80e6,
        equity=500e6, revenue_ttm=1e9,
    )
    mcap = 1e9  # P/E=10, FCF yield=8%, P/B=2, ROE=20%
    v = valuation_score(snap, mcap)
    assert v > 0.5  # should score well — it's cheap

def test_valuation_score_expensive_stock():
    from shared.quality import valuation_score
    snap = FundamentalSnapshot(
        symbol="X", net_income_ttm=100e6, free_cash_flow_ttm=50e6,
        equity=500e6, revenue_ttm=1e9,
    )
    mcap = 50e9  # P/E=500, FCF yield=0.1%, P/B=100, ROE=20%
    v = valuation_score(snap, mcap)
    assert v < 0.3  # expensive — low score

def test_valuation_score_no_mcap():
    from shared.quality import valuation_score
    snap = FundamentalSnapshot(symbol="X", net_income_ttm=100e6)
    assert valuation_score(snap, 0.0) == 0.0

def test_fcf_yield_score_negative():
    from shared.quality import fcf_yield_score
    snap = FundamentalSnapshot(symbol="X", free_cash_flow_ttm=-50e6)
    assert fcf_yield_score(snap, 1e9) == 0.0

def test_pb_score_sweet_spot():
    from shared.quality import pb_score
    snap = FundamentalSnapshot(symbol="X", equity=1e9)
    assert pb_score(snap, 1e9) == pytest.approx(1.0)  # P/B = 1
    assert pb_score(snap, 3e9) == pytest.approx(0.5)  # P/B = 3
    assert pb_score(snap, 5e9) == pytest.approx(0.0)  # P/B = 5


# ---- smart_money ----

def test_smart_money_funds_present():
    assert "BERKSHIRE HATHAWAY" in SMART_MONEY_FUNDS


def test_is_fresh_13d():
    assert is_fresh_13d("SC 13D")
    assert is_fresh_13d("13D")
    assert not is_fresh_13d("SC 13D/A")
    assert not is_fresh_13d("SC 13G")


def test_activist_signal():
    class F: pass
    a = F(); a.form = "SC 13D"; a.symbol = "ACME"
    b = F(); b.form = "SC 13D/A"; b.symbol = "BACME"
    c = F(); c.form = "SC 13D"; c.symbol = "CACME"
    out = activist_signal([a, b, c])
    assert out == ["ACME", "CACME"]


def test_parse_13f_minimal():
    xml = """<informationTable xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable">
    <infoTable>
        <nameOfIssuer>APPLE INC</nameOfIssuer>
        <cusip>037833100</cusip>
        <value>1000000</value>
        <shrsOrPrnAmt><sshPrnamt>10000</sshPrnamt></shrsOrPrnAmt>
    </infoTable>
</informationTable>"""
    out = parse_13f_information_table(xml, manager="Berkshire Hathaway")
    assert len(out) == 1
    # nameOfIssuer goes to `name`; `symbol` stays empty until CUSIP resolution.
    assert out[0].name == "APPLE INC"
    assert out[0].symbol == ""
    assert out[0].cusip == "037833100"
    assert out[0].shares == 10000


def test_smart_money_holders_filters_by_fund():
    by_manager = {
        "Berkshire Hathaway Inc": [Holding("ACME", "x", 1000, 100000, "Berkshire Hathaway Inc")],
        "Some Random Fund": [Holding("MSFT", "y", 100, 1000, "Some Random Fund")],
    }
    out = smart_money_holders(by_manager)
    assert "ACME" in out
    assert "MSFT" not in out


# ---- backtest ----

def test_backtest_minimal():
    dossiers = [
        {"symbol": "A", "created_at": "2023-01-01T00:00:00", "horizon_years": 1.0, "conviction": 0.8},
    ]
    prices = {"A": [("2023-01-02", 100.0), ("2024-01-02", 120.0)]}
    res = backtest_run(dossiers, prices)
    assert res["n"] == 1
    assert res["mean_return"] == pytest.approx(0.20)
    assert res["hit_rate"] == 1.0


def test_backtest_empty_prices():
    dossiers = [{"symbol": "X", "created_at": "2023-01-01T00:00:00", "horizon_years": 1.0}]
    res = backtest_run(dossiers, {})
    assert res["n"] == 0


# ---- capital ----

def test_capital_base_when_unproven():
    out = compute_allocation(graded_calls=10, alpha=0.05, alpha_t=1.5, monotonic_conviction=True)
    assert out == CAPITAL_BASE


def test_capital_base_when_negative_alpha():
    out = compute_allocation(graded_calls=50, alpha=-0.05, alpha_t=3, monotonic_conviction=True)
    assert out == CAPITAL_BASE


def test_capital_base_when_not_monotonic():
    out = compute_allocation(graded_calls=50, alpha=0.10, alpha_t=3, monotonic_conviction=False)
    assert out == CAPITAL_BASE


def test_capital_scales_up_when_proven():
    out = compute_allocation(graded_calls=100, alpha=0.20, alpha_t=3, monotonic_conviction=True)
    assert out > CAPITAL_BASE
    # Cannot exceed ceiling - reserve
    assert out <= CAPITAL_CEILING - ACHILLES_RESERVE


def test_fcf_margin_implausible_ratio_distrusted():
    # FCF reported as 9x revenue (mis-tagged data) must not score as quality.
    from shared.quality import fcf_margin_score
    from shared.fundamentals import FundamentalSnapshot
    bad = FundamentalSnapshot(symbol="X", free_cash_flow_ttm=26_434_000.0, revenue_ttm=2_835_000.0)
    assert fcf_margin_score(bad) is None
    good = FundamentalSnapshot(symbol="Y", free_cash_flow_ttm=20.0, revenue_ttm=100.0)
    assert fcf_margin_score(good) == 1.0  # 20% FCF margin -> full marks


def test_margin_scores_distrust_impossible_values():
    # Operating/gross margin above 100% of revenue is impossible -> mis-tagged data.
    from shared.quality import gross_margin_score, operating_margin_score
    from shared.fundamentals import FundamentalSnapshot
    assert operating_margin_score(FundamentalSnapshot(symbol="X", operating_margin_ttm=1.003)) is None
    assert gross_margin_score(FundamentalSnapshot(symbol="X", gross_margin_ttm=1.5)) is None
    # plausible margins still score
    assert operating_margin_score(FundamentalSnapshot(symbol="Y", operating_margin_ttm=0.2)) == 1.0
    assert gross_margin_score(FundamentalSnapshot(symbol="Y", gross_margin_ttm=0.45)) > 0


# ---- pick_candidates ----

def _write_screen(path, rows):
    import json
    with open(str(path), "w") as f:
        json.dump({"survivors": rows}, f)


def _write_dossiers(path, symbols):
    import json
    with open(str(path), "w") as f:
        json.dump({"dossiers": [{"symbol": s} for s in symbols]}, f)


def test_pick_candidates_returns_undossiered_sorted(tmp_path):
    screen = tmp_path / "screen.json"
    doss = tmp_path / "dossiers.json"
    _write_screen(screen, [
        {"symbol": "A", "score": 0.9, "insider_tier": "full"},
        {"symbol": "B", "score": 0.8, "insider_tier": "full"},
        {"symbol": "C", "score": 0.7, "insider_tier": "full"},
        {"symbol": "D", "score": 0.6, "insider_tier": "half"},
    ])
    _write_dossiers(doss, ["B"])
    result = pick_candidates(str(screen), str(doss), n=10)
    syms = [r["symbol"] for r in result]
    assert syms == ["A", "C", "D"]


def test_pick_candidates_respects_n(tmp_path):
    screen = tmp_path / "screen.json"
    doss = tmp_path / "dossiers.json"
    _write_screen(screen, [
        {"symbol": s, "score": 1.0 - i * 0.1, "insider_tier": "full"}
        for i, s in enumerate(["A", "B", "C", "D", "E"])
    ])
    _write_dossiers(doss, [])
    result = pick_candidates(str(screen), str(doss), n=3)
    assert len(result) == 3
    assert [r["symbol"] for r in result] == ["A", "B", "C"]


def test_pick_candidates_full_tier_only(tmp_path):
    screen = tmp_path / "screen.json"
    doss = tmp_path / "dossiers.json"
    _write_screen(screen, [
        {"symbol": "A", "score": 0.9, "insider_tier": "half"},
        {"symbol": "B", "score": 0.8, "insider_tier": "full"},
        {"symbol": "C", "score": 0.7, "insider_tier": "full"},
    ])
    _write_dossiers(doss, [])
    result = pick_candidates(str(screen), str(doss), n=10, full_tier_only=True)
    syms = [r["symbol"] for r in result]
    assert syms == ["B", "C"]


def test_pick_candidates_no_dossier_file(tmp_path):
    screen = tmp_path / "screen.json"
    doss = tmp_path / "dossiers.json"  # does not exist
    _write_screen(screen, [
        {"symbol": "A", "score": 0.5, "insider_tier": "full"},
    ])
    result = pick_candidates(str(screen), str(doss), n=10)
    assert len(result) == 1


def test_pick_candidates_missing_screen_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        pick_candidates(str(tmp_path / "nope.json"), str(tmp_path / "d.json"))
