from oracle.upside_sourcing import (
    arrival_penalty,
    bottom_up_signals,
    in_hunting_ground,
    is_arrived_52w,
    range_position,
    reconcile_queue,
    screen_panel,
    screen_row,
    spotlight_score,
    top_down_signal,
)


# ---- hunting ground (spec I1) ----------------------------------------------
def test_hunting_ground_small_thin_covered():
    assert in_hunting_ground({"mcap": 8e8, "coverage": 2}) is True


def test_hunting_ground_excludes_megacap():
    assert in_hunting_ground({"mcap": 50e9, "coverage": 2}) is False


def test_hunting_ground_excludes_well_covered():
    assert in_hunting_ground({"mcap": 8e8, "coverage": 20}) is False


def test_hunting_ground_special_situation_runs_larger():
    # a spinoff may be a bit bigger than the plain cap and unknown coverage
    assert in_hunting_ground({"mcap": 4.5e9, "special_situation": "spinoff"}) is True
    assert in_hunting_ground({"mcap": 6e9, "special_situation": "spinoff"}) is False


def test_hunting_ground_excludes_sub_microcap():
    assert in_hunting_ground({"mcap": 5e7, "coverage": 1}) is False


# ---- bottom-up signals -----------------------------------------------------
def test_accel_fires_on_accelerating_revenue():
    row = {"revenue": [100, 112, 158]}   # 12% then 41% growth -> +29pp accel
    sig = bottom_up_signals(row)
    assert "accel" in sig


def test_accel_silent_on_decelerating_revenue():
    row = {"revenue": [100, 141, 158]}   # 41% then 12% -> decelerating
    assert "accel" not in bottom_up_signals(row)


def test_beat_and_raise_stronger_than_bare_beat():
    raise_row = {"eps_surprise": 0.08, "guidance_raised": True}
    beat_row = {"eps_surprise": 0.08, "guidance_raised": False}
    assert "beat_and_raise" in bottom_up_signals(raise_row)
    assert "eps_beat" in bottom_up_signals(beat_row)


def test_rel_strength_fires_on_recent_trend():
    # recent (~5wk) trend beating the market fires; a faded name (recently negative)
    # does NOT, even if it was up over 6 months (the blowoff-fade fix).
    assert "rel_strength" in bottom_up_signals({"ret_recent": 0.15, "spy_ret_recent": 0.02})
    assert "rel_strength" not in bottom_up_signals({"ret_recent": -0.20, "spy_ret_recent": 0.02})
    assert "rel_strength" not in bottom_up_signals({"ret_recent": 0.03, "spy_ret_recent": 0.02})


def test_arrival_penalty_at_high():
    assert arrival_penalty({"pct_below_high": 0.02}) < 1.0     # near the high -> penalized
    assert arrival_penalty({"pct_below_high": 0.35}) == 1.0    # room to run -> no penalty
    assert arrival_penalty({}) == 1.0                          # unknown -> no penalty


def test_reconcile_drops_financials_shells_artifacts():
    cands = [{"symbol": "GOOD"}, {"symbol": "FIN"}, {"symbol": "SHELL"},
             {"symbol": "ARTIFACT"}, {"symbol": "UNKNOWN"}]
    live = {
        "GOOD": {"sector": "Technology Services", "num_employees": 3200, "pb_ratio": 2.9},
        "FIN": {"sector": "Finance", "num_employees": 17, "pb_ratio": 0.5},
        "SHELL": {"sector": "Commercial Services", "num_employees": 7, "pb_ratio": 40.0},
        "ARTIFACT": {"sector": "Industrials", "num_employees": 500, "pb_ratio": 45.0},
        # UNKNOWN has no live entry -> kept but flagged
    }
    kept, dropped = reconcile_queue(cands, live)
    ksym = {c["symbol"] for c in kept}
    dsym = {c["symbol"] for c in dropped}
    assert "GOOD" in ksym
    assert dsym == {"FIN", "SHELL", "ARTIFACT"}
    assert all(c.get("drop_reason") for c in dropped)
    assert any(c["symbol"] == "UNKNOWN" and c.get("unreconciled") for c in kept)


def test_range_position_and_arrived():
    # RRGB-like: $2.46-$8.26, now $7.15 -> ~82% up range -> arrived
    assert range_position(7.15, 2.46, 8.26) > 0.6
    assert is_arrived_52w({"last_price": 7.15, "low_52_weeks": 2.46, "high_52_weeks": 8.26}) is True
    # ACVA-like: $4.07-$16.76, now $7.40 -> ~26% up range -> NOT arrived
    assert range_position(7.40, 4.07, 16.76) < 0.6
    assert is_arrived_52w({"last_price": 7.40, "low_52_weeks": 4.07, "high_52_weeks": 16.76}) is False
    assert is_arrived_52w({"last_price": 7.40}) is None   # missing range -> unknown


def test_screen_row_penalizes_arrived_name():
    # two names, identical signals; the one at its high scores lower
    base = {"mcap": 8e8, "coverage": 2, "revenue": [100, 112, 158],
            "ret_recent": 0.15, "spy_ret_recent": 0.02}
    early = screen_row({**base, "symbol": "EARLY", "pct_below_high": 0.35})
    arrived = screen_row({**base, "symbol": "ARRIVED", "pct_below_high": 0.02})
    assert arrived["at_high"] is True and early["at_high"] is False
    assert early["spotlight_score"] > arrived["spotlight_score"]


def test_margin_turn_fires():
    assert "margin_turn" in bottom_up_signals({"op_margin": [0.08, 0.11]})
    assert "margin_turn" not in bottom_up_signals({"op_margin": [0.11, 0.08]})


# ---- top-down thematic -----------------------------------------------------
def test_thematic_fires_for_forming_theme_undercovered():
    row = {"theme": "grid_power", "coverage": 1, "theme_strength": 0.7}
    assert "thematic" in top_down_signal(row, {"grid_power"})


def test_thematic_silent_when_theme_not_forming():
    row = {"theme": "grid_power", "coverage": 1}
    assert top_down_signal(row, {"nuclear"}) == {}


def test_thematic_silent_when_well_covered():
    # if the Street already covers it, the theme is priced through it
    row = {"theme": "grid_power", "coverage": 15}
    assert top_down_signal(row, {"grid_power"}) == {}


# ---- scoring + row + panel -------------------------------------------------
def test_spotlight_score_rewards_more_and_stronger_signals():
    weak = spotlight_score({"eps_beat": 0.3}, {})
    strong = spotlight_score({"accel": 0.9, "rel_strength": 0.8}, {"thematic": 0.7})
    assert strong > weak


def test_screen_row_keeps_signal_in_ground():
    row = {"symbol": "wdgt", "mcap": 8e8, "coverage": 2, "revenue": [100, 112, 158]}
    c = screen_row(row)
    assert c and c["symbol"] == "WDGT" and "accel" in c["nets"]


def test_screen_row_drops_out_of_ground_even_with_signal():
    row = {"symbol": "MEGA", "mcap": 80e9, "coverage": 2, "revenue": [100, 112, 158]}
    assert screen_row(row) is None


def test_screen_row_drops_no_signal():
    row = {"symbol": "FLAT", "mcap": 8e8, "coverage": 2, "revenue": [100, 100, 100]}
    assert screen_row(row) is None


def test_screen_panel_sorts_and_flags_queue():
    panel = [
        {"symbol": "A", "mcap": 8e8, "coverage": 2, "revenue": [100, 112, 158],
         "ret_6m": 0.4, "spy_ret_6m": 0.1},                       # two signals
        {"symbol": "B", "mcap": 8e8, "coverage": 2, "eps_surprise": 0.03},  # one weak
        {"symbol": "MEGA", "mcap": 90e9, "revenue": [100, 112, 158]},       # out of ground
    ]
    out = screen_panel(panel, limit=1)
    syms = [c["symbol"] for c in out]
    assert "MEGA" not in syms
    assert syms[0] == "A"                    # strongest first
    assert out[0]["queued"] is True
    # B is kept in the record but flagged not-queued (no silent truncation)
    assert any(c["symbol"] == "B" and c["queued"] is False for c in out)
