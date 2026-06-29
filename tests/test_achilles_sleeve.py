import pytest

from achilles.sleeve import (
    AchillesPosition, AchillesSleeve, DRAWDOWN_HALT, HARD_FLOOR,
    MAX_CONCURRENT_POSITIONS, MAX_TRADES_PER_DAY, MIN_SCORE_TO_OPEN,
    PER_POSITION_CAP_FRAC, PER_POSITION_MAX, PER_POSITION_MIN,
    STOP_COOLDOWN_DAYS,
)


def test_standalone_no_base_sleeve_inheritance():
    """Critical: AchillesSleeve must NOT inherit from BaseSleeve."""
    from shared.base_sleeve import BaseSleeve
    assert not issubclass(AchillesSleeve, BaseSleeve)


def test_init_defaults():
    s = AchillesSleeve(initial_cash=1000.0)
    assert s.cash == 1000.0
    assert s.positions == {}
    assert s.halted is False
    assert s.conservative_mode is True  # ON by default
    assert s.peak_equity == 1000.0


def test_constants():
    assert HARD_FLOOR == 600.0
    assert DRAWDOWN_HALT == 0.40
    assert MAX_CONCURRENT_POSITIONS == 20
    assert MAX_TRADES_PER_DAY == 5
    assert MIN_SCORE_TO_OPEN == 0.05
    assert PER_POSITION_CAP_FRAC == 0.10
    assert PER_POSITION_MIN == 100.0
    assert PER_POSITION_MAX == 400.0


def test_position_dollars_clamped():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    # 10% of $10k = $1000, clamped to $400 max
    assert s.position_dollars(score=0.5) == 400.0


def test_position_dollars_min_floor():
    s = AchillesSleeve(initial_cash=500, conservative_mode=False)
    # 10% of $500 = $50, clamped UP to $100 min
    assert s.position_dollars(score=0.5) == 100.0


def test_position_dollars_conservative_halves():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=True)
    # Otherwise $400, halved to $200
    assert s.position_dollars(score=0.5) == 200.0


def test_position_dollars_conviction_scales():
    s = AchillesSleeve(initial_cash=1000, conservative_mode=False)
    # 10% of $1k = $100, conviction 2.0 → $200, within [$100, $200]
    assert s.position_dollars(score=0.5, conviction=2.0) == 200.0
    # conviction 1.0 → base $100
    assert s.position_dollars(score=0.5, conviction=1.0) == 100.0


def _open_args():
    return dict(
        event_id="e1",
        symbol="ACME",
        event_class="earnings_reaction",
        entry_price=10.0,
        score=0.3,
        hard_stop_price=9.0,
        profit_target_price=12.0,
        time_stop_date="2024-06-15",
        today="2024-05-29",
    )


def test_open_succeeds():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    pos = s.open(**_open_args())
    assert pos is not None
    assert pos.event_id == "e1"
    assert pos.symbol == "ACME"
    assert pos.dollars_at_entry == 400.0
    assert pos.shares == pytest.approx(40.0)


def test_open_event_keyed_same_symbol_two_events():
    """Same stock, two events -> two distinct positions."""
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    s.open(**_open_args())
    args2 = _open_args()
    args2["event_id"] = "e2"
    args2["event_class"] = "insider_cluster"
    pos2 = s.open(**args2)
    assert pos2 is not None
    assert len(s.positions) == 2
    assert s.positions["e1"].symbol == s.positions["e2"].symbol == "ACME"


def test_open_low_score_allowed():
    """Score threshold is advisory — LLM decides, sleeve doesn't block."""
    s = AchillesSleeve(initial_cash=10000)
    args = _open_args()
    args["score"] = 0.01
    assert s.open(**args) is not None


def test_open_blocked_when_halted():
    s = AchillesSleeve(initial_cash=10000)
    s.halted = True
    assert s.open(**_open_args()) is None


def test_open_blocked_by_max_concurrent():
    s = AchillesSleeve(initial_cash=10000)
    for i in range(MAX_CONCURRENT_POSITIONS):
        args = _open_args()
        args["event_id"] = f"e{i}"
        s.open(**args)
    args = _open_args()
    args["event_id"] = "extra"
    assert s.open(**args) is None


def test_open_past_daily_limit_allowed():
    """Daily limit is advisory — LLM decides, sleeve doesn't block."""
    s = AchillesSleeve(initial_cash=10000)
    for i in range(MAX_TRADES_PER_DAY):
        args = _open_args()
        args["event_id"] = f"e{i}"
        s.open(**args)
    args = _open_args()
    args["event_id"] = "extra"
    assert s.open(**args) is not None


def test_trades_today_resets_on_new_day():
    s = AchillesSleeve(initial_cash=10000)
    for i in range(MAX_TRADES_PER_DAY):
        args = _open_args()
        args["event_id"] = f"e{i}"
        s.open(**args)
    # New day
    args = _open_args()
    args["event_id"] = "next_day"
    args["today"] = "2024-05-30"
    pos = s.open(**args)
    assert pos is not None


def test_close_realizes_pnl():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    s.open(**_open_args())
    realized = s.close("e1", exit_price=12.0, today="2024-06-01")
    assert realized is not None
    # Bought 20 shares at 10 for ~$200 (+fee). Sold 20 at 12 = $240 - fee.
    # PnL ~ +$40 minus fees.
    assert realized > 35


def test_close_unknown_position():
    s = AchillesSleeve(initial_cash=10000)
    assert s.close("ghost", exit_price=10, today="2024-06-01") is None


def test_hard_floor_halts():
    s = AchillesSleeve(initial_cash=1000)
    s.cash = 500
    halted = s.check_hard_floor()
    assert halted is True
    assert s.halted is True


def test_drawdown_halts_at_40pct():
    s = AchillesSleeve(initial_cash=1000)
    s.peak_equity = 2000
    s.cash = 1200  # 40% drawdown
    halted = s.check_hard_floor()
    assert halted is True


def test_manual_reset_clears_halted():
    s = AchillesSleeve(initial_cash=1000)
    s.halted = True
    s.manual_reset()
    assert s.halted is False


def test_persistence_roundtrip(tmp_path):
    s = AchillesSleeve(initial_cash=1000, conservative_mode=False)
    s.open(**_open_args())
    p = tmp_path / "achilles.json"
    s.save(str(p))
    s2 = AchillesSleeve.load(str(p))
    assert s2.cash == s.cash
    assert "e1" in s2.positions
    assert s2.positions["e1"].symbol == "ACME"


def test_cooldown_advisory_not_enforced():
    """Cooldown is advisory — LLM decides, sleeve doesn't block."""
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    s.add_cooldown("ACME", "2024-05-29")
    args = _open_args()
    args["today"] = "2024-06-15"
    assert s.open(**args) is not None


def test_cooldown_expires():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    s.add_cooldown("ACME", "2024-05-29")
    args = _open_args()
    args["today"] = "2024-08-28"  # 91 days later, past 90-day cooldown
    assert s.open(**args) is not None


def test_cooldown_persists(tmp_path):
    s = AchillesSleeve(initial_cash=1000)
    s.add_cooldown("ACME", "2024-05-29")
    p = tmp_path / "achilles.json"
    s.save(str(p))
    s2 = AchillesSleeve.load(str(p))
    assert s2.in_cooldown("ACME", "2024-06-15") is True


def test_liquidate_all_kills_positions():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    s.open(**_open_args())
    out = s.liquidate_all({"ACME": 11.0}, today="2024-06-01")
    assert len(out) == 1
    assert s.positions == {}
