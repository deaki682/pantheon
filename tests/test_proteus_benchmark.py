"""The benchmark stack (charter v2.1, art. 23) — defined once, honest both ways."""
import pytest

from proteus.benchmark import (BenchmarkError, deployment_adjusted, headline)


def test_headline():
    marks = [{"date": "2026-07-13", "equity": 2500.0, "spy": 750.0},
             {"date": "2026-08-13", "equity": 2600.0, "spy": 765.0}]
    h = headline(marks)
    assert h["sleeve_return"] == pytest.approx(0.04)
    assert h["spy_return"] == pytest.approx(0.02)
    assert h["excess"] == pytest.approx(0.02)


def test_headline_too_few_marks():
    assert headline([{"date": "d", "equity": 1, "spy": 1}])["excess"] is None


def test_flat_book_defaults_to_cash_park_vs_tbill():
    # 365 days flat at $2,500, SPY rallies 10%: the deployment-adjusted
    # line docks the cash park only the T-bill rate, not the rally.
    marks = [{"date": "2026-07-13", "equity": 2500.0, "spy": 750.0},
             {"date": "2027-07-13", "equity": 2500.0, "spy": 825.0}]
    d = deployment_adjusted(marks, tbill_annual=0.04)
    assert d["excess_dollars"] == pytest.approx(-100.0)   # -2500*4%
    assert d["risk_dollar_days"] == 0.0


def test_index_park_is_the_benchmark():
    # Fully parked in SPY through a 10% rally: zero excess BY DEFINITION.
    marks = [{"date": "2026-07-13", "equity": 2500.0, "spy": 750.0,
              "risk_capital": 0.0, "cash_park": 0.0, "tbill_park": 0.0,
              "index_park": 2500.0},
             {"date": "2027-07-13", "equity": 2750.0, "spy": 825.0}]
    d = deployment_adjusted(marks)
    assert d["excess_dollars"] == pytest.approx(0.0)


def test_risk_capital_benchmarked_against_spy():
    # $1,000 at risk returns $150 while SPY does 10%: excess = 150 - 100
    # minus the T-bill dock on the $1,500 cash park (half-year: 2%= $30).
    marks = [{"date": "2026-01-01", "equity": 2500.0, "spy": 700.0,
              "risk_capital": 1000.0, "cash_park": 1500.0,
              "tbill_park": 0.0, "index_park": 0.0},
             {"date": "2026-07-02", "equity": 2650.0, "spy": 770.0}]
    d = deployment_adjusted(marks, tbill_annual=0.04)
    days = 182
    expected = 150.0 - 1000.0 * 0.10 - 1500.0 * 0.04 * days / 365.0
    assert d["excess_dollars"] == pytest.approx(round(expected, 2))
    assert d["risk_dollar_days"] == pytest.approx(1000.0 * days)


def test_crash_cannot_flatter_a_cash_book():
    # SPY -20% while the sleeve sits in cash: excess is only the missed
    # T-bill yield, NOT +20% — the deployment-adjusted line doesn't pay
    # the sleeve for a crash it merely sat out. (The headline line does
    # show the +20% — that's its job.)
    marks = [{"date": "2026-07-13", "equity": 2500.0, "spy": 750.0},
             {"date": "2027-07-13", "equity": 2500.0, "spy": 600.0}]
    d = deployment_adjusted(marks, tbill_annual=0.04)
    assert d["excess_dollars"] == pytest.approx(-100.0)
    assert headline(marks)["excess"] == pytest.approx(0.20)


def test_bad_decomposition_refused():
    marks = [{"date": "2026-07-13", "equity": 2500.0, "spy": 750.0,
              "risk_capital": 100.0, "cash_park": 100.0,
              "tbill_park": 0.0, "index_park": 0.0},   # sums to 200 != 2500
             {"date": "2026-08-13", "equity": 2500.0, "spy": 760.0}]
    with pytest.raises(BenchmarkError):
        deployment_adjusted(marks)
