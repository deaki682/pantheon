import pytest

from delphi.selector import pick_stocks, score_stock, select_for_sectors


def test_score_stock_pure_momentum():
    # +20% momentum over 63 days, quality ignored
    prices = [100.0] * 64
    prices[-1] = 120.0
    out = score_stock(prices, quality=0.8)
    # pure momentum: (120 - 100) / 100 = 0.2
    assert out == pytest.approx(0.2, abs=1e-6)


def test_pick_stocks_top_n():
    candidates = [
        {"symbol": f"S{i}", "score": 0.1 * i} for i in range(10)
    ]
    out = pick_stocks(candidates, top_n=4)
    assert len(out) == 4
    assert out[0]["symbol"] == "S9"


def test_pick_stocks_excludes_blocked():
    candidates = [
        {"symbol": "XLK", "score": 1.0},
        {"symbol": "AAPL", "score": 0.5},
    ]
    out = pick_stocks(candidates, top_n=2)
    assert all(c["symbol"] != "XLK" for c in out)


def test_select_for_sectors_basic():
    inp = {
        "tech": [
            {"symbol": "AAPL", "score": 0.5},
            {"symbol": "MSFT", "score": 0.4},
        ],
        "finance": [
            {"symbol": "JPM", "score": 0.3},
        ],
    }
    out = select_for_sectors(inp, top_n=3)
    assert len(out["tech"]) == 2
    assert len(out["finance"]) == 1
