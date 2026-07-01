import pytest

from buzz.acceleration import (
    MAX_ACCEL_RATIO,
    BuzzRow,
    accelerating,
    acceleration_ratio,
    parse_apewisdom,
    score_acceleration,
)
from buzz.confirm import Confirmation, confirm
from buzz.scanner import (
    BuzzCandidate,
    build_candidate,
    in_small_mid_band,
    rank_basket,
)


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


# ── scanner ───────────────────────────────────────────────────────────

class TestSmallMidBand:
    def test_keeps_small_mid(self):
        assert in_small_mid_band(500_000_000) is True

    def test_drops_megacap(self):
        assert in_small_mid_band(50_000_000_000) is False

    def test_drops_microcap(self):
        assert in_small_mid_band(10_000_000) is False

    def test_drops_unknown(self):
        assert in_small_mid_band(None) is False


def _cand(ticker, accel, cap, confirmed=True, vol_ratio=2.0):
    return BuzzCandidate(
        ticker=ticker, mentions=100, mentions_prev=20, accel_ratio=accel,
        rank_jump=10, new_entrant=False, upvotes=500, market_cap=cap,
        price_change_pct=0.05, volume_ratio=vol_ratio, confirmed=confirmed,
        confirm_reason="confirmed" if confirmed else "no_price_no_volume",
    )


class TestRankBasket:
    def test_ranks_confirmed_small_mid_by_accel(self):
        cands = [
            _cand("LOW", 2.5, 1e9),
            _cand("HIGH", 6.0, 1e9),
            _cand("MEGA", 9.0, 50e9),          # mega -> filtered
            _cand("FAKE", 8.0, 1e9, confirmed=False),  # unconfirmed -> filtered
        ]
        basket = rank_basket(cands, top_n=8)
        assert [c.ticker for c in basket] == ["HIGH", "LOW"]

    def test_top_n(self):
        cands = [_cand(f"S{i}", 2.0 + i, 1e9) for i in range(10)]
        assert len(rank_basket(cands, top_n=3)) == 3

    def test_require_confirmation_false_keeps_unconfirmed(self):
        cands = [_cand("FAKE", 8.0, 1e9, confirmed=False)]
        assert rank_basket(cands, require_confirmation=False)[0].ticker == "FAKE"

    def test_build_candidate_roundtrips_fields(self):
        from buzz.acceleration import AccelSignal
        sig = AccelSignal("XYZ", 120, 20, 6.0, 3, 15, 12, False, 400, "XYZ Corp")
        conf = Confirmation(True, 0.07, 2.3, "confirmed")
        c = build_candidate(sig, 800_000_000, conf, sector="Tech")
        assert c.ticker == "XYZ"
        assert c.accel_ratio == 6.0
        assert c.confirmed is True
        assert c.market_cap == 800_000_000
        assert c.sector == "Tech"
