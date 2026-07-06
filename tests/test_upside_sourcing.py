from oracle.upside_sourcing import (
    bottom_up_signals,
    in_hunting_ground,
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


def test_rel_strength_fires():
    assert "rel_strength" in bottom_up_signals({"ret_6m": 0.35, "spy_ret_6m": 0.10})
    assert "rel_strength" not in bottom_up_signals({"ret_6m": 0.12, "spy_ret_6m": 0.10})


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
