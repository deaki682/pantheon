import pytest

from oracle.attribution import compute_factor_attribution, factor_regression, ols


def test_ols_perfect_fit():
    # y = 2*x + 1
    y = [3, 5, 7, 9, 11]
    X = [[1, 1], [1, 2], [1, 3], [1, 4], [1, 5]]
    res = ols(y, X)
    assert res["coefs"][0] == pytest.approx(1.0, abs=1e-6)
    assert res["coefs"][1] == pytest.approx(2.0, abs=1e-6)
    assert res["r2"] == pytest.approx(1.0, abs=1e-6)


def test_ols_intercept_only():
    y = [1.0, 2.0, 3.0, 4.0]
    X = [[1], [1], [1], [1]]
    res = ols(y, X)
    assert res["coefs"][0] == pytest.approx(2.5)


def test_ols_rejects_short():
    with pytest.raises(ValueError):
        ols([1, 2], [[1, 2], [1, 3]])  # n == k


def test_factor_regression_alpha():
    # Use truly non-collinear factor returns so the design matrix is invertible.
    factor_returns = {
        "MTUM": [0.02, -0.01, 0.03, 0.00, -0.02, 0.04, 0.01, -0.03, 0.05, -0.01],
        "QUAL": [0.01, 0.00, -0.01, 0.02, 0.03, -0.02, 0.01, 0.00, 0.02, -0.01],
        "IWM":  [-0.01, 0.02, 0.01, -0.02, 0.03, 0.00, -0.01, 0.02, 0.00, 0.01],
        "VTV":  [0.00, 0.01, -0.02, 0.01, -0.01, 0.02, 0.00, 0.01, -0.02, 0.03],
    }
    n = len(factor_returns["MTUM"])
    oracle = [0.01 + 0.5 * factor_returns["MTUM"][i] for i in range(n)]
    out = factor_regression(oracle, factor_returns)
    assert out["alpha"] == pytest.approx(0.01, abs=1e-6)
    assert out["betas"]["MTUM"] == pytest.approx(0.5, abs=1e-6)


def test_factor_regression_missing_factor():
    with pytest.raises(ValueError):
        factor_regression(
            [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.01, 0.02, 0.03, 0.04],
            {"MTUM": [0] * 10},
        )


def test_factor_regression_length_mismatch():
    with pytest.raises(ValueError):
        factor_regression(
            [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.01, 0.02, 0.03, 0.04],
            {"MTUM": [0] * 9, "QUAL": [0] * 10, "IWM": [0] * 10, "VTV": [0] * 10},
        )


# ---------- compute_factor_attribution ----------

def _make_curve(dates, equities):
    return [{"ts": f"{d}T12:00:00", "equity": e} for d, e in zip(dates, equities)]


def _make_bars(dates, prices):
    return [{"begins_at": f"{d}T00:00:00Z", "close_price": str(p)} for d, p in zip(dates, prices)]


def test_compute_attribution_end_to_end():
    dates = [f"2026-01-{d:02d}" for d in range(1, 12)]  # 11 dates -> 10 returns
    equities = [1000, 1012, 1005, 1030, 1025, 1040, 1038, 1055, 1048, 1070, 1065]
    curve = _make_curve(dates, equities)

    factor_hist = {
        "MTUM": _make_bars(dates, [100, 101, 99, 103, 102, 105, 104, 107, 106, 109, 108]),
        "QUAL": _make_bars(dates, [200, 202, 204, 201, 205, 203, 207, 206, 210, 208, 212]),
        "IWM":  _make_bars(dates, [150, 149, 152, 151, 154, 153, 156, 155, 158, 157, 160]),
        "VTV":  _make_bars(dates, [80, 81, 79, 82, 80, 83, 81, 84, 82, 85, 83]),
    }

    result = compute_factor_attribution(curve, factor_hist)
    assert result is not None
    assert result["skipped"] is False
    assert "alpha" in result
    assert "betas" in result
    assert result["n"] == 10


def test_compute_attribution_skips_too_few_dates():
    dates = ["2026-01-01", "2026-01-02", "2026-01-03"]
    curve = _make_curve(dates, [1000, 1010, 1020])
    factor_hist = {
        etf: _make_bars(dates, [100 + i for i in range(3)])
        for etf in ("MTUM", "QUAL", "IWM", "VTV")
    }
    result = compute_factor_attribution(curve, factor_hist)
    assert result["skipped"] is True
    assert "common dates" in result["reason"] or "need" in result["reason"]


def test_compute_attribution_skips_all_zero_returns():
    dates = [f"2026-01-{d:02d}" for d in range(1, 12)]
    curve = _make_curve(dates, [1000] * 11)  # flat equity
    factor_hist = {
        etf: _make_bars(dates, [100 + i for i in range(11)])
        for etf in ("MTUM", "QUAL", "IWM", "VTV")
    }
    result = compute_factor_attribution(curve, factor_hist)
    assert result["skipped"] is True
    assert "zero" in result["reason"]


def test_compute_attribution_skips_missing_etf():
    dates = [f"2026-01-{d:02d}" for d in range(1, 12)]
    curve = _make_curve(dates, [1000 + i * 10 for i in range(11)])
    factor_hist = {
        "MTUM": _make_bars(dates, [100 + i for i in range(11)]),
        "QUAL": _make_bars(dates, [200 + i for i in range(11)]),
        "IWM": _make_bars(dates, [150 + i for i in range(11)]),
        # VTV missing
    }
    result = compute_factor_attribution(curve, factor_hist)
    assert result["skipped"] is True
    assert "VTV" in result["reason"]


def test_compute_attribution_handles_mismatched_dates():
    oracle_dates = [f"2026-01-{d:02d}" for d in range(1, 12)]  # 01-01 to 01-11
    factor_dates = [f"2026-01-{d:02d}" for d in range(3, 14)]  # 01-03 to 01-13, 9 overlap
    equities = [1000, 1012, 1005, 1030, 1025, 1040, 1038, 1055, 1048, 1070, 1065]
    curve = _make_curve(oracle_dates, equities)
    factor_hist = {
        "MTUM": _make_bars(factor_dates, [99, 103, 102, 105, 104, 107, 106, 109, 108, 110, 112]),
        "QUAL": _make_bars(factor_dates, [204, 201, 205, 203, 207, 206, 210, 208, 212, 211, 214]),
        "IWM":  _make_bars(factor_dates, [152, 151, 154, 153, 156, 155, 158, 157, 160, 159, 162]),
        "VTV":  _make_bars(factor_dates, [79, 82, 80, 83, 81, 84, 82, 85, 83, 86, 84]),
    }
    result = compute_factor_attribution(curve, factor_hist)
    assert result is not None
    assert result["skipped"] is False
    assert result["n"] == 8  # 9 common dates -> 8 returns


def test_compute_attribution_deduplicates_curve():
    dates = [f"2026-01-{d:02d}" for d in range(1, 12)]
    real_equities = [1000, 1012, 1005, 1030, 1025, 1040, 1038, 1055, 1048, 1070, 1065]
    # Prepend stale dupes for first 3 dates — later entries (real) should win
    curve = (
        _make_curve(dates[:3], [999, 999, 999])
        + _make_curve(dates, real_equities)
    )
    factor_hist = {
        "MTUM": _make_bars(dates, [100, 101, 99, 103, 102, 105, 104, 107, 106, 109, 108]),
        "QUAL": _make_bars(dates, [200, 202, 204, 201, 205, 203, 207, 206, 210, 208, 212]),
        "IWM":  _make_bars(dates, [150, 149, 152, 151, 154, 153, 156, 155, 158, 157, 160]),
        "VTV":  _make_bars(dates, [80, 81, 79, 82, 80, 83, 81, 84, 82, 85, 83]),
    }
    result = compute_factor_attribution(curve, factor_hist)
    assert result is not None
    assert result["skipped"] is False
