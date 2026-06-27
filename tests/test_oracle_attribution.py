import pytest

from oracle.attribution import factor_regression, ols


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
