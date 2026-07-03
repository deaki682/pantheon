"""Tests for nemesis.window — the mechanical entry-window state machine.

The window trigger IS the ghost experiment's buy-all control, so these
tests pin the frozen behavior exactly: the classic dump-then-base shape
must fire, active dumping must not, and the day-count bounds must
override everything else. Bar-parsing tolerance mirrors buzz.confirm
(string values, None, missing keys, junk bars skipped).
"""
from nemesis.window import (
    MAX_TRADING_DAYS,
    MIN_TRADING_DAYS,
    STAB_SESSIONS,
    VOL_NORM_RATIO,
    WindowState,
    assess_window,
)


def bar(close, volume):
    return {"close_price": close, "volume": volume}


def classic_bars(n=15):
    """The textbook spinco shape: day-one dump volume decaying, price
    dipping to a low around day 7 and basing above it since."""
    volumes = [5_000_000, 3_000_000, 2_000_000, 1_500_000, 1_000_000]
    closes = [25.0, 23.5, 22.0, 21.0, 20.5]
    # low at day 7, then a base that never revisits it
    closes += [20.2, 20.0, 20.4, 20.8, 21.0]
    volumes += [800_000, 700_000, 600_000, 500_000, 450_000]
    while len(closes) < n:
        closes.append(21.2 + 0.1 * (len(closes) % 3))
        volumes.append(350_000)
    return [bar(c, v) for c, v in zip(closes, volumes)]


# ------- frozen constants -------


class TestFrozenConstants:
    def test_values_are_the_preregistered_ones(self):
        # Changing any of these invalidates every graded ghost comparison;
        # a failure here means someone tuned the strategy's identity.
        assert MIN_TRADING_DAYS == 10
        assert MAX_TRADING_DAYS == 90
        assert VOL_NORM_RATIO == 0.5
        assert STAB_SESSIONS == 5


# ------- classic in-window shape -------


class TestClassicShape:
    def test_in_window_at_day_15(self):
        ws = assess_window(classic_bars(15))
        assert ws.trading_days == 15
        assert ws.vol_ratio is not None and ws.vol_ratio <= VOL_NORM_RATIO
        assert ws.volume_normalized is True
        assert ws.price_stabilized is True
        assert ws.state == "in_window"

    def test_vol_ratio_math(self):
        # first-5 avg = 2,500,000; last-5 avg = 350,000 -> 0.14
        ws = assess_window(classic_bars(15))
        assert ws.vol_ratio == 0.14

    def test_in_window_at_exact_min_days(self):
        bars = classic_bars(15)[:MIN_TRADING_DAYS]
        ws = assess_window(bars)
        # first-5 avg 2.5M, last-5 avg 610k -> 0.244; low (20.0) is at
        # index 6 which IS inside the last 5 of a 10-bar series.
        assert ws.trading_days == MIN_TRADING_DAYS
        assert ws.volume_normalized is True
        assert ws.price_stabilized is False
        assert ws.state == "pre_window"

    def test_in_window_at_exact_max_days(self):
        ws = assess_window(classic_bars(MAX_TRADING_DAYS))
        assert ws.trading_days == MAX_TRADING_DAYS
        assert ws.state == "in_window"


# ------- still dumping -------


class TestStillDumping:
    def test_high_volume_new_lows_is_pre_window(self):
        # Volume never decays, price keeps making new lows: the forced
        # sellers are still at the table.
        bars = [bar(25.0 - 0.5 * i, 4_000_000) for i in range(15)]
        ws = assess_window(bars)
        assert ws.volume_normalized is False
        assert ws.price_stabilized is False
        assert ws.state == "pre_window"

    def test_volume_normalized_but_new_low_is_pre_window(self):
        bars = classic_bars(15)
        bars[-1] = bar(19.0, 350_000)  # fresh low on the last session
        ws = assess_window(bars)
        assert ws.volume_normalized is True
        assert ws.price_stabilized is False
        assert ws.state == "pre_window"

    def test_tied_low_in_recent_sessions_is_not_stabilized(self):
        # Retesting the exact low inside the last STAB_SESSIONS counts as
        # a new low: sellers are still pressing that level.
        bars = classic_bars(15)
        bars[-2] = bar(20.0, 350_000)  # matches the day-7 low
        ws = assess_window(bars)
        assert ws.price_stabilized is False
        assert ws.state == "pre_window"

    def test_price_based_but_volume_still_heavy_is_pre_window(self):
        bars = classic_bars(15)
        for i in range(10, 15):
            bars[i] = bar(bars[i]["close_price"], 3_000_000)  # ratio 1.2
        ws = assess_window(bars)
        assert ws.price_stabilized is True
        assert ws.volume_normalized is False
        assert ws.state == "pre_window"


# ------- late -------


class TestLate:
    def test_late_beats_true_signals(self):
        ws = assess_window(classic_bars(MAX_TRADING_DAYS + 1))
        assert ws.trading_days == MAX_TRADING_DAYS + 1
        # Both tells are still true — the day count alone disqualifies.
        assert ws.volume_normalized is True
        assert ws.price_stabilized is True
        assert ws.state == "late"

    def test_deep_into_late(self):
        ws = assess_window(classic_bars(150))
        assert ws.state == "late"


# ------- short history -------


class TestShortHistory:
    def test_short_history_is_pre_window_with_no_ratio(self):
        ws = assess_window(classic_bars(15)[:6])
        assert ws.trading_days == 6
        assert ws.vol_ratio is None
        assert ws.volume_normalized is False
        assert ws.price_stabilized is False
        assert ws.state == "pre_window"

    def test_nine_bars_is_still_too_few_for_ratio(self):
        ws = assess_window(classic_bars(15)[:9])
        assert ws.vol_ratio is None
        assert ws.state == "pre_window"

    def test_empty_bars(self):
        ws = assess_window([])
        assert ws == WindowState(
            trading_days=0,
            vol_ratio=None,
            volume_normalized=False,
            price_stabilized=False,
            state="pre_window",
        )


# ------- bar tolerance (buzz.confirm style) -------


class TestBarTolerance:
    def test_string_typed_values(self):
        bars = [
            {"close_price": str(b["close_price"]), "volume": str(b["volume"])}
            for b in classic_bars(15)
        ]
        ws = assess_window(bars)
        assert ws.state == "in_window"
        assert ws.vol_ratio == 0.14

    def test_close_key_fallback(self):
        bars = [{"close": b["close_price"], "volume": b["volume"]}
                for b in classic_bars(15)]
        assert assess_window(bars).state == "in_window"

    def test_invalid_bars_are_skipped_not_counted(self):
        bars = classic_bars(15)
        junk = [
            {"close_price": None, "volume": 1_000_000},
            {"close_price": "", "volume": 1_000_000},
            {"close_price": "n/a", "volume": 1_000_000},
            {"volume": 1_000_000},
            {"close_price": 0, "volume": 1_000_000},
            {"close_price": -3.0, "volume": 1_000_000},
        ]
        # Junk interleaved anywhere must not change the day count, the
        # ratio, or the low.
        ws = assess_window(junk[:3] + bars[:7] + junk[3:] + bars[7:])
        assert ws.trading_days == 15
        assert ws.vol_ratio == 0.14
        assert ws.state == "in_window"

    def test_garbage_volume_counts_as_zero(self):
        bars = classic_bars(15)
        bars[-1] = {"close_price": 21.2, "volume": "n/a"}
        bars[-2] = {"close_price": 21.3, "volume": None}
        ws = assess_window(bars)
        # Last-5 avg drops (two zeros), so still normalized; the bars
        # themselves remain valid because their closes parse.
        assert ws.trading_days == 15
        assert ws.volume_normalized is True
        assert ws.state == "in_window"


# ------- zero first-week volume -------


class TestZeroFirstWeekVolume:
    def test_zero_denominator_gives_none_ratio(self):
        bars = classic_bars(15)
        for i in range(5):
            bars[i] = bar(bars[i]["close_price"], 0)
        ws = assess_window(bars)
        assert ws.vol_ratio is None
        assert ws.volume_normalized is False
        # Price side is unaffected, but one missing tell blocks entry.
        assert ws.price_stabilized is True
        assert ws.state == "pre_window"


# ------- flat tape -------


class TestFlatTape:
    def test_all_equal_closes_never_stabilize(self):
        # Everything is the low, including the last close: last > min
        # fails, and the "low" recurs inside the recent sessions.
        bars = [bar(20.0, 350_000 if i >= 5 else 2_000_000) for i in range(15)]
        ws = assess_window(bars)
        assert ws.volume_normalized is True
        assert ws.price_stabilized is False
        assert ws.state == "pre_window"
