import pytest

from midas.calibration import (
    CAPITAL_BASE,
    MIN_GRADED_FOR_SCALING,
    calibration_summary,
    compute_alpha,
    convergence_validates,
    target_capital,
)
from midas.sleeve import MidasSleeve, WeeklyResult


def _make_result(ret, convergence=2):
    return WeeklyResult(
        symbol="X", week_id="W01", entry_date="", entry_price=100,
        exit_date="", exit_price=100 * (1 + ret), exit_reason="time_stop",
        return_pct=ret, pnl=ret * 1000, score=0.5,
        convergence_count=convergence, signals={},
    )


class TestComputeAlpha:
    def test_insufficient_data(self):
        results = [_make_result(0.05)] * 3
        benchmarks = [0.01] * 3
        assert compute_alpha(results, benchmarks) is None

    def test_positive_alpha(self):
        results = [_make_result(0.05)] * 20
        benchmarks = [0.01] * 20
        stats = compute_alpha(results, benchmarks)
        assert stats is not None
        assert stats["alpha"] == pytest.approx(0.04)
        assert stats["alpha_t"] > 0
        assert stats["n"] == 20

    def test_negative_alpha(self):
        results = [_make_result(-0.05)] * 20
        benchmarks = [0.01] * 20
        stats = compute_alpha(results, benchmarks)
        assert stats["alpha"] < 0

    def test_mismatched_lengths(self):
        results = [_make_result(0.05)] * 10
        benchmarks = [0.01] * 5
        assert compute_alpha(results, benchmarks) is None


class TestConvergenceValidates:
    def test_multi_beats_single(self):
        results = (
            [_make_result(0.02, convergence=1) for _ in range(5)]
            + [_make_result(0.08, convergence=2) for _ in range(5)]
        )
        assert convergence_validates(results) is True

    def test_single_beats_multi(self):
        results = (
            [_make_result(0.08, convergence=1) for _ in range(5)]
            + [_make_result(0.02, convergence=2) for _ in range(5)]
        )
        assert convergence_validates(results) is False

    def test_insufficient_data_passes(self):
        results = [_make_result(0.05, convergence=1)] * 3
        assert convergence_validates(results) is True


class TestTargetCapital:
    def test_below_threshold(self):
        s = MidasSleeve()
        s.weekly_results = [_make_result(0.05)] * 10
        assert target_capital(s, [0.01] * 10) == CAPITAL_BASE

    def test_at_threshold_positive_alpha(self):
        s = MidasSleeve()
        s.weekly_results = [_make_result(0.05)] * MIN_GRADED_FOR_SCALING
        benchmarks = [0.01] * MIN_GRADED_FOR_SCALING
        cap = target_capital(s, benchmarks)
        assert cap > CAPITAL_BASE

    def test_negative_alpha_stays_base(self):
        s = MidasSleeve()
        s.weekly_results = [_make_result(-0.02)] * MIN_GRADED_FOR_SCALING
        benchmarks = [0.01] * MIN_GRADED_FOR_SCALING
        assert target_capital(s, benchmarks) == CAPITAL_BASE


class TestCalibrationSummary:
    def test_empty_sleeve(self):
        s = MidasSleeve()
        summary = calibration_summary(s)
        assert summary["graded_trades"] == 0
        assert summary["trades_needed"] == MIN_GRADED_FOR_SCALING

    def test_with_results(self):
        s = MidasSleeve()
        s.weekly_results = [_make_result(0.05), _make_result(-0.03)]
        summary = calibration_summary(s)
        assert summary["graded_trades"] == 2
        assert summary["hit_rate"] == pytest.approx(0.5)
