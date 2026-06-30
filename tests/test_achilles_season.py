import pytest

from achilles.season import (
    SEASON_WINDOWS,
    current_season,
    is_earnings_season,
    next_season,
)


# --- is_earnings_season ---


class TestIsEarningsSeason:
    """is_earnings_season(date_str) returns True inside the four windows."""

    @pytest.mark.parametrize(
        "date_str",
        [
            "2026-01-15",  # Q4 window
            "2026-04-20",  # Q1 window
            "2026-07-25",  # Q2 window
            "2026-10-30",  # Q3 window
        ],
    )
    def test_mid_season_true(self, date_str):
        assert is_earnings_season(date_str) is True

    @pytest.mark.parametrize(
        "date_str",
        [
            "2026-01-13",  # first day Q4 window
            "2026-02-21",  # last day Q4 window
            "2026-04-13",  # first day Q1 window
            "2026-05-21",  # last day Q1 window
            "2026-07-13",  # first day Q2 window
            "2026-08-21",  # last day Q2 window
            "2026-10-13",  # first day Q3 window
            "2026-11-21",  # last day Q3 window
        ],
    )
    def test_boundary_days_included(self, date_str):
        assert is_earnings_season(date_str) is True

    @pytest.mark.parametrize(
        "date_str",
        [
            "2026-03-15",  # between Q4 and Q1 windows
            "2026-06-15",  # between Q1 and Q2 windows
            "2026-09-15",  # between Q2 and Q3 windows
            "2026-12-15",  # after Q3 window, before next Q4
        ],
    )
    def test_off_season_false(self, date_str):
        assert is_earnings_season(date_str) is False

    def test_day_before_season_start(self):
        assert is_earnings_season("2026-01-12") is False

    def test_day_after_season_end(self):
        assert is_earnings_season("2026-02-22") is False

    def test_accepts_different_years(self):
        assert is_earnings_season("2025-01-15") is True
        assert is_earnings_season("2027-07-20") is True


# --- current_season ---


class TestCurrentSeason:
    def test_returns_tuple_during_season(self):
        result = current_season("2026-01-20")
        assert result is not None
        start, end = result
        assert start == "2026-01-13"
        assert end == "2026-02-21"

    def test_returns_none_off_season(self):
        assert current_season("2026-03-15") is None

    def test_first_day_of_season(self):
        result = current_season("2026-04-13")
        assert result == ("2026-04-13", "2026-05-21")

    def test_last_day_of_season(self):
        result = current_season("2026-08-21")
        assert result == ("2026-07-13", "2026-08-21")

    def test_each_window(self):
        expected = [
            ("2026-01-15", "2026-01-13", "2026-02-21"),
            ("2026-04-25", "2026-04-13", "2026-05-21"),
            ("2026-07-31", "2026-07-13", "2026-08-21"),
            ("2026-10-14", "2026-10-13", "2026-11-21"),
        ]
        for test_date, exp_start, exp_end in expected:
            result = current_season(test_date)
            assert result == (exp_start, exp_end), f"Failed for {test_date}"


# --- next_season ---


class TestNextSeason:
    def test_off_season_returns_next_window(self):
        # March is between Q4 and Q1 windows
        result = next_season("2026-03-15")
        assert result == ("2026-04-13", "2026-05-21")

    def test_before_first_window(self):
        result = next_season("2026-01-01")
        assert result == ("2026-01-13", "2026-02-21")

    def test_after_last_window(self):
        # After Nov 21 -> wraps to next year's Jan 13
        result = next_season("2026-12-01")
        assert result == ("2027-01-13", "2027-02-21")

    def test_between_q1_and_q2(self):
        result = next_season("2026-06-01")
        assert result == ("2026-07-13", "2026-08-21")

    def test_between_q2_and_q3(self):
        result = next_season("2026-09-01")
        assert result == ("2026-10-13", "2026-11-21")

    def test_year_boundary_wrap(self):
        result = next_season("2025-12-31")
        assert result == ("2026-01-13", "2026-02-21")

    def test_during_season_returns_next(self):
        # During Q4 window (Jan 20) -- next_season looks for start > today
        # Jan 20 < Apr 13, so next is Q1 window
        result = next_season("2026-01-20")
        assert result == ("2026-04-13", "2026-05-21")
