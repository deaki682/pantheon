import pytest

from delphi.screener import build_candidate, quality_for_delphi, screen_universe
from shared.fundamentals import FundamentalSnapshot


def test_quality_zero_for_empty():
    assert quality_for_delphi(FundamentalSnapshot(symbol="X")) == 0.0


def test_quality_full():
    snap = FundamentalSnapshot(
        symbol="X", operating_margin_ttm=0.25, free_cash_flow_ttm=30, revenue_ttm=100,
        revenue_yoy=0.3, dilution_yoy=0.0,
    )
    assert quality_for_delphi(snap) > 0.7


def test_build_candidate_blocked():
    out = build_candidate("XLK", sector="tech", prices=[100] * 64, snap=None)
    assert out.get("blocked") is True


def test_build_candidate_normal():
    prices = [100.0] * 64
    prices[-1] = 110.0
    out = build_candidate("AAPL", sector="technology", prices=prices, snap=None)
    assert out["symbol"] == "AAPL"
    assert out["sector"] == "technology"
    assert out["momentum"] == pytest.approx(0.10)


def test_screen_universe():
    inp = {
        "technology": [
            ("AAPL", [100.0] * 64, None),
            ("MSFT", [100.0] * 64, None),
        ],
    }
    out = screen_universe(inp)
    assert "technology" in out
    assert len(out["technology"]) == 2
