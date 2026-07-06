from oracle.upside_ranker import (
    ALL_NETS,
    composite_score,
    net_acceleration,
    net_earnings_surprise,
    net_range_reversal,
    net_scores,
    net_value_floor,
    rank_all,
    reconcile_top,
)


# ---- individual nets -------------------------------------------------------
def test_net_acceleration_none_without_data():
    assert net_acceleration({"symbol": "X"}) is None
    assert net_acceleration({"revenue": [100, 112, 158]}) > 0     # accelerating


def test_net_earnings_surprise_beat_and_raise():
    assert net_earnings_surprise({"symbol": "X"}) is None
    bare = net_earnings_surprise({"eps_surprise": 0.05})
    raised = net_earnings_surprise({"eps_surprise": 0.05, "guidance_raised": True})
    assert raised > bare


def test_net_range_reversal_prefers_low_in_range():
    low = net_range_reversal({"range_pos": 0.15, "ret_recent": 0.1, "spy_ret_recent": 0.0})
    high = net_range_reversal({"range_pos": 0.85, "ret_recent": 0.1, "spy_ret_recent": 0.0})
    assert low > high
    assert net_range_reversal({"symbol": "X"}) is None   # no range -> inactive


def test_net_value_floor():
    assert net_value_floor({"symbol": "X"}) is None
    assert net_value_floor({"price_to_tangible_book": 0.6}) > net_value_floor({"price_to_tangible_book": 1.8})
    assert net_value_floor({"net_cash_ratio": 1.0}) == 1.0


# ---- composite -------------------------------------------------------------
def test_composite_rewards_more_nets():
    one = composite_score({"acceleration": 0.8})
    many = composite_score({"acceleration": 0.8, "recent_strength": 0.8, "earnings_surprise": 0.8})
    assert many > one


def test_net_scores_only_active():
    row = {"revenue": [100, 112, 158], "eps_surprise": 0.05}
    s = net_scores(row)
    assert "acceleration" in s and "earnings_surprise" in s
    assert "thematic" not in s and "special_situation" not in s   # no inputs -> absent


# ---- rank_all over a whole panel ------------------------------------------
def test_rank_all_orders_and_reports_coverage():
    panel = [
        # strong: accelerating + beat-raise, in ground
        {"symbol": "STRONG", "mcap": 8e8, "coverage": 2, "revenue": [100, 112, 158],
         "eps_surprise": 0.08, "guidance_raised": True, "ret_recent": 0.1, "spy_ret_recent": 0.02},
        # weak: only a mild single signal
        {"symbol": "WEAK", "mcap": 8e8, "coverage": 2, "eps_surprise": 0.03},
        # out of ground (megacap)
        {"symbol": "MEGA", "mcap": 90e9, "revenue": [100, 112, 158]},
        # no signal
        {"symbol": "FLAT", "mcap": 8e8, "coverage": 2, "revenue": [100, 100, 100]},
    ]
    out = rank_all(panel)
    ranked, cov = out["ranked"], out["coverage"]
    syms = [c["symbol"] for c in ranked]
    assert syms[0] == "STRONG"
    assert "MEGA" not in syms and "FLAT" not in syms
    assert cov["dropped"]["out_of_ground"] == 1
    assert cov["dropped"]["no_signal"] == 1
    assert ranked[0]["rank"] == 1
    # earnings/acceleration fired somewhere -> active; thematic never -> inactive
    assert "acceleration" in cov["active_nets"]
    assert "thematic" in cov["inactive_nets"]


def test_reconcile_top_drops_and_activates_range_reversal():
    ranked = [
        {"symbol": "EARLY", "nets": {"acceleration": 0.8}, "composite": 0.8, "ret_recent": 0.1, "mcap": 8e8},
        {"symbol": "ARRIVED", "nets": {"acceleration": 0.8}, "composite": 0.8, "ret_recent": 0.1, "mcap": 8e8},
        {"symbol": "FIN", "nets": {"acceleration": 0.8}, "composite": 0.8, "mcap": 8e8},
    ]
    live = {
        "EARLY": {"sector": "Technology Services", "num_employees": 3000, "pb_ratio": 1.2,
                  "last_price": 7.4, "low_52_weeks": 4.07, "high_52_weeks": 16.76},   # 26% up range
        "ARRIVED": {"sector": "Consumer Services", "num_employees": 5000, "pb_ratio": 2.0,
                    "last_price": 7.15, "low_52_weeks": 2.46, "high_52_weeks": 8.26},  # 82% up range
        "FIN": {"sector": "Finance", "num_employees": 100, "pb_ratio": 1.0},
    }
    out = reconcile_top(ranked, live)
    qsym = {c["symbol"] for c in out["queue"]}
    assert "EARLY" in qsym                                  # low in range -> kept + range_reversal added
    assert "ARRIVED" not in qsym                            # high in range -> dropped
    assert "FIN" not in qsym                                # financial -> dropped
    early = next(c for c in out["queue"] if c["symbol"] == "EARLY")
    assert "range_reversal" in early["nets"]                # net activated from live range
    assert any(c["symbol"] == "ARRIVED" for c in out["dropped_arrived"])
    assert any(c["symbol"] == "FIN" for c in out["dropped_reconcile"])


def test_all_nets_constant():
    assert set(ALL_NETS) == {"acceleration", "recent_strength", "range_reversal",
                             "earnings_surprise", "thematic", "special_situation", "value_floor"}
