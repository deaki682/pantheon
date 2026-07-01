import math

import pytest

from catalyst.expectations import (
    edge_vs_priced,
    implied_move_from_chain,
    implied_move_from_iv,
    one_sigma_move,
    pick_atm_straddle,
    straddle_move,
)


class TestImpliedMoveMath:
    def test_iv_scales_with_sqrt_time(self):
        # 32% annualized IV over ~7 days
        m = implied_move_from_iv(0.32, 7)
        assert m == pytest.approx(0.32 * math.sqrt(7 / 365.0))

    def test_iv_guards(self):
        assert implied_move_from_iv(None, 7) is None
        assert implied_move_from_iv(0.3, 0) is None

    def test_straddle_move(self):
        # $6 straddle on a $100 stock = 6% priced move
        assert straddle_move(3.0, 3.0, 100.0) == pytest.approx(0.06)

    def test_one_sigma_scaling(self):
        m = one_sigma_move(3.0, 3.0, 100.0)
        assert m == pytest.approx(0.06 * math.sqrt(2 / math.pi))

    def test_straddle_guards(self):
        assert straddle_move(3.0, 3.0, 0) is None
        assert straddle_move(None, 3.0, 100) is None
        assert straddle_move(-1.0, 3.0, 100) is None


class TestEdge:
    def test_positive_when_expecting_more(self):
        # expect 12%, market priced 8% -> +4 points of surprise
        assert edge_vs_priced(0.12, 0.08) == pytest.approx(0.04)

    def test_direction_flips_sign(self):
        assert edge_vs_priced(0.12, 0.08, direction=-1) == pytest.approx(-0.04)

    def test_none_when_priced_absent(self):
        assert edge_vs_priced(0.12, None) is None


def _chain(spot):
    # two expiries; nearest-after-event should win; ATM strike closest to spot
    return [
        {"strike": 95, "type": "call", "expiration": "2026-07-03", "mark": 6.0},
        {"strike": 95, "type": "put", "expiration": "2026-07-03", "mark": 1.0},
        {"strike": 100, "type": "call", "expiration": "2026-07-03", "mark": 3.0},
        {"strike": 100, "type": "put", "expiration": "2026-07-03", "mark": 3.2},
        {"strike": 105, "type": "call", "expiration": "2026-07-03", "mark": 1.1},
        {"strike": 105, "type": "put", "expiration": "2026-07-03", "mark": 6.4},
        # a farther expiry that should be ignored when event is before 07-03
        {"strike": 100, "type": "call", "expiration": "2026-08-21", "mark": 8.0},
        {"strike": 100, "type": "put", "expiration": "2026-08-21", "mark": 8.0},
    ]


class TestAtmStraddle:
    def test_picks_atm_and_nearest_expiry(self):
        atm = pick_atm_straddle(101.0, _chain(101.0), event_date="2026-07-02")
        assert atm["expiry"] == "2026-07-03"
        assert atm["strike"] == 100  # closest to 101 spot
        assert atm["call"] == 3.0 and atm["put"] == 3.2

    def test_bid_ask_midpoint(self):
        contracts = [
            {"strike": 50, "type": "call", "expiration": "2026-07-03", "bid": 1.0, "ask": 3.0},
            {"strike": 50, "type": "put", "expiration": "2026-07-03", "bid": 1.0, "ask": 1.0},
        ]
        atm = pick_atm_straddle(50, contracts, event_date="2026-07-02")
        assert atm["call"] == 2.0  # (1+3)/2

    def test_no_paired_strike_returns_none(self):
        contracts = [{"strike": 50, "type": "call", "expiration": "2026-07-03", "mark": 2.0}]
        assert pick_atm_straddle(50, contracts, event_date="2026-07-02") is None

    def test_illiquid_empty(self):
        assert pick_atm_straddle(50, [], event_date="2026-07-02") is None


class TestImpliedMoveFromChain:
    def test_end_to_end(self):
        res = implied_move_from_chain(100.0, _chain(100.0), event_date="2026-07-02")
        assert res["priced_move_pct"] == pytest.approx(0.062)  # (3.0+3.2)/100
        assert res["expiry"] == "2026-07-03"
        # output is rounded to 4dp for a clean review table
        assert res["one_sigma_pct"] == pytest.approx(0.062 * math.sqrt(2 / math.pi), abs=1e-4)

    def test_illiquid_returns_none(self):
        assert implied_move_from_chain(100.0, [], event_date="2026-07-02") is None
