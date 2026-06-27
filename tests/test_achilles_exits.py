import pytest

from achilles.exits import evaluate
from achilles.sleeve import AchillesPosition


def _pos(entry=100, stop=92, target=112, time_stop="2024-06-15"):
    return AchillesPosition(
        event_id="e1", symbol="X", event_class="earnings_reaction",
        shares=10, entry_price=entry, entry_date="2024-05-29",
        dollars_at_entry=1000, hard_stop_price=stop,
        profit_target_price=target, time_stop_date=time_stop,
        high_water_price=entry,
    )


def test_hold_in_window():
    pos = _pos()
    out = evaluate(pos, current_price=100, today="2024-05-30")
    assert out["action"] == "hold"


def test_hard_stop_priority():
    """Hard stop fires even if other conditions could also trigger."""
    pos = _pos(stop=95)
    out = evaluate(pos, current_price=94, today="2024-05-30")
    assert out["action"] == "exit"
    assert out["reason"] == "hard_stop"


def test_profit_target():
    pos = _pos()
    out = evaluate(pos, current_price=113, today="2024-05-30")
    assert out["action"] == "exit"
    assert out["reason"] == "profit_target"


def test_time_stop():
    pos = _pos()
    out = evaluate(pos, current_price=100, today="2024-06-15")
    assert out["action"] == "exit"
    assert out["reason"] == "time_stop"


def test_trailing_stop_not_armed():
    pos = _pos()
    pos.trail_armed_at = 0.10
    pos.trail_pct = 0.05
    # Price went to 105, less than 110 trigger -> not armed
    out = evaluate(pos, current_price=105, today="2024-05-30")
    assert out["action"] == "hold"


def test_trailing_stop_armed_and_triggers():
    pos = _pos()
    pos.trail_armed_at = 0.10
    pos.trail_pct = 0.05
    # First take price up to 111 (arms), then back down to 105 (trips)
    evaluate(pos, current_price=111, today="2024-05-30")
    out = evaluate(pos, current_price=105, today="2024-05-31")
    assert out["action"] == "exit"
    assert out["reason"] == "trailing_stop"


def test_no_price_holds():
    pos = _pos()
    out = evaluate(pos, current_price=0, today="2024-05-30")
    assert out["action"] == "hold"
    assert out["reason"] == "no_price"


def test_hard_stop_before_time_stop():
    pos = _pos(stop=99)
    # Both conditions met: today >= time_stop AND price < stop -> hard_stop wins
    out = evaluate(pos, current_price=98, today="2024-07-01")
    assert out["reason"] == "hard_stop"


def test_profit_target_before_time_stop():
    pos = _pos(target=110)
    out = evaluate(pos, current_price=120, today="2024-07-01")
    assert out["reason"] == "profit_target"
