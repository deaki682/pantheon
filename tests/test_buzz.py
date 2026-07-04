import pytest

from buzz.acceleration import (
    MAX_ACCEL_RATIO,
    BuzzRow,
    accelerating,
    acceleration_ratio,
    parse_apewisdom,
    score_acceleration,
)
from buzz.confirm import confirm


# ── acceleration ──────────────────────────────────────────────────────

class TestParseApewisdom:
    def test_parses_real_shape(self):
        payload = {"results": [
            {"rank": 6, "ticker": "NKE", "name": "Nike", "mentions": 158,
             "upvotes": 1079, "rank_24h_ago": 68, "mentions_24h_ago": 11},
            {"rank": 1, "ticker": "MU", "mentions": 580, "mentions_24h_ago": 679},
        ]}
        rows = parse_apewisdom(payload)
        assert len(rows) == 2
        assert rows[0].ticker == "NKE"
        assert rows[0].mentions == 158 and rows[0].mentions_prev == 11

    def test_empty(self):
        assert parse_apewisdom({}) == []


class TestAccelerationRatio:
    def test_basic(self):
        assert acceleration_ratio(100, 50) == pytest.approx(2.0)

    def test_baseline_floor_caps_new_entrant(self):
        # 1 -> 40 shouldn't be 40x; baseline floored, then capped
        assert acceleration_ratio(40, 1) == pytest.approx(min(40 / 5, MAX_ACCEL_RATIO))

    def test_cap(self):
        assert acceleration_ratio(10_000, 5) == MAX_ACCEL_RATIO


class TestScoreAcceleration:
    def test_igniting_passes(self):
        # NKE: 11 -> 158, rank 68 -> 6
        sig = score_acceleration(BuzzRow("NKE", 158, 11, rank=6, rank_prev=68))
        assert sig is not None
        assert sig.accel_ratio > 2.0
        assert sig.rank_jump == 62  # climbed 62 spots toward #1
        assert sig.new_entrant is False  # prev 11 >= MIN_BASELINE (5)

    def test_new_entrant_flagged(self):
        sig = score_acceleration(BuzzRow("NEW", 40, 2))  # prev below baseline
        assert sig is not None
        assert sig.new_entrant is True

    def test_loud_but_fading_rejected(self):
        # MU: 679 -> 580 is deceleration, not acceleration
        assert score_acceleration(BuzzRow("MU", 580, 679)) is None

    def test_too_quiet_rejected(self):
        # only 8 current mentions -> below MIN_MENTIONS_NOW
        assert score_acceleration(BuzzRow("TINY", 8, 1)) is None

    def test_accelerating_sorts_hottest_first(self):
        rows = [
            BuzzRow("A", 30, 15),   # 2.0x
            BuzzRow("B", 160, 10),  # capped/high
            BuzzRow("MU", 580, 679),  # fading -> excluded
        ]
        sigs = accelerating(rows)
        assert [s.ticker for s in sigs] == ["B", "A"]


# ── confirmation ──────────────────────────────────────────────────────

def _bars(closes, volumes):
    return [{"close_price": str(c), "volume": v} for c, v in zip(closes, volumes)]


class TestConfirm:
    def test_confirmed_price_up_volume_elevated(self):
        closes = [10.0] * 20 + [10.2, 10.5, 11.0]
        vols = [100] * 20 + [300, 320, 340]
        c = confirm(_bars(closes, vols))
        assert c.confirmed is True
        assert c.price_change_pct > 0
        assert c.volume_ratio >= 1.5

    def test_chatter_without_money_rejected(self):
        # flat price, normal volume -> manufactured chatter
        closes = [10.0] * 25
        vols = [100] * 25
        c = confirm(_bars(closes, vols))
        assert c.confirmed is False
        assert c.reason == "no_price_no_volume"

    def test_volume_without_price_rejected(self):
        # huge volume but price DOWN -> no long direction
        closes = [10.0] * 20 + [9.5, 9.0, 8.5]
        vols = [100] * 20 + [400, 400, 400]
        c = confirm(_bars(closes, vols))
        assert c.confirmed is False
        assert c.reason == "volume_without_price"

    def test_price_without_volume_rejected(self):
        closes = [10.0] * 20 + [10.2, 10.5, 11.0]
        vols = [100] * 25
        c = confirm(_bars(closes, vols))
        assert c.confirmed is False
        assert c.reason == "price_without_volume"

    def test_insufficient_history(self):
        c = confirm(_bars([10.0, 10.1], [100, 100]))
        assert c.confirmed is False
        assert c.reason == "insufficient_history"
