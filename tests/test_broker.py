"""Tests for shared.broker — Robinhood client wrapper."""
import os
from unittest.mock import MagicMock, patch

import pytest

from shared import broker


@pytest.fixture(autouse=True)
def _reset_broker():
    """Reset broker state between tests."""
    broker._logged_in = False
    broker._account_number = None
    yield
    broker._logged_in = False


def test_login_no_env_returns_false():
    with patch.dict(os.environ, {}, clear=True):
        assert broker.login() is False


def test_login_caches_result():
    broker._logged_in = True
    assert broker.login() is True


def test_get_quotes_without_login_returns_empty():
    assert broker.get_quotes(["AAPL"]) == {}


def test_get_latest_prices_without_login_returns_empty():
    assert broker.get_latest_prices(["AAPL"]) == {}


def test_get_fundamentals_without_login_returns_empty():
    assert broker.get_fundamentals(["AAPL"]) == {}


def test_get_market_caps_without_login_returns_empty():
    assert broker.get_market_caps(["AAPL"]) == {}


def test_buy_fractional_without_login_returns_none():
    assert broker.buy_fractional("AAPL", 100.0) is None


def test_sell_fractional_without_login_returns_none():
    assert broker.sell_fractional("AAPL", 1.5) is None


def test_get_quotes_empty_symbols():
    assert broker.get_quotes([]) == {}


def test_get_holdings_without_login_returns_empty():
    assert broker.get_holdings() == {}


def test_get_account_cash_without_login_returns_none():
    assert broker.get_account_cash() is None


def test_get_earnings_without_login_returns_none():
    assert broker.get_earnings("AAPL") is None


def test_logout_when_not_logged_in():
    broker.logout()
    assert broker._logged_in is False
