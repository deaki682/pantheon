"""Tests for the smaller Oracle modules: calendar, prescreener, screener,
smart_money, backtest, capital."""
import datetime
import pytest

from oracle.backtest import run as backtest_run
from oracle.calendar import days_since, mark_run, should_run
from oracle.capital import (
    CAPITAL_BASE, CAPITAL_CEILING, ACHILLES_RESERVE,
    compute_allocation,
)
from oracle.prescreener import prescreen, batch_prescreen
from oracle.screener import multi_lens_score, quality_score, rank_survivors
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


def test_multi_lens_all():
    out = multi_lens_score("X", insider_cluster=True, smart_money=True,
                            activist_13d=True, quality=1.0, sector_breadth=1.0)
    assert out["score"] == pytest.approx(1.0)


def test_multi_lens_none():
    out = multi_lens_score("X")
    assert out["score"] == 0.0


def test_rank_survivors_top_n():
    rows = [
        {"symbol": f"S{i}", "score": i * 0.1} for i in range(20)
    ]
    top = rank_survivors(rows, top_n=5)
    assert len(top) == 5
    assert top[0]["symbol"] == "S19"


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
    assert out[0].symbol == "APPLE INC"
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
