import pytest

from achilles.brief import Brief, Play
from achilles.execution import plan_exits, plan_open
from achilles.sleeve import AchillesPosition, AchillesSleeve


def _brief(event_id="e1", score=0.2, disq=()):
    return Brief(
        event_id=event_id, event_class="earnings_reaction",
        symbol="ACME", score=score,
        play=Play(
            entry_dollars=200, hard_stop_price=92, profit_target_price=112,
            time_stop_date="2024-06-15",
        ),
        disqualifiers=list(disq),
    )


def test_plan_open_emits_buy():
    s = AchillesSleeve(initial_cash=10000)
    out = plan_open(s, _brief(), today="2024-05-29", current_price=100.0)
    assert out is not None
    assert out["side"] == "buy"
    assert out["symbol"] == "ACME"
    assert out["dollars"] == 200.0


def test_plan_open_blocked_low_score():
    s = AchillesSleeve(initial_cash=10000)
    out = plan_open(s, _brief(score=0.01), today="2024-05-29", current_price=100.0)
    assert out is None


def test_plan_open_blocked_when_halted():
    s = AchillesSleeve(initial_cash=10000)
    s.halted = True
    out = plan_open(s, _brief(), today="2024-05-29", current_price=100.0)
    assert out is None


def test_plan_open_blocked_with_disqualifiers():
    s = AchillesSleeve(initial_cash=10000)
    out = plan_open(s, _brief(disq=["trading_halt"]), today="2024-05-29", current_price=100.0)
    assert out is None


def test_plan_open_blocked_duplicate_event():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    s.open(
        event_id="e1", symbol="ACME", event_class="earnings_reaction",
        entry_price=10, score=0.2, hard_stop_price=9, profit_target_price=11,
        time_stop_date="2024-06-15", today="2024-05-29",
    )
    out = plan_open(s, _brief(event_id="e1"), today="2024-05-29", current_price=100.0)
    assert out is None


def test_plan_exits_triggers_hard_stop():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    s.open(
        event_id="e1", symbol="ACME", event_class="earnings_reaction",
        entry_price=100, score=0.2, hard_stop_price=92, profit_target_price=112,
        time_stop_date="2024-06-15", today="2024-05-29",
    )
    out = plan_exits(s, quotes={"ACME": 90}, today="2024-05-30")
    assert len(out) == 1
    assert out[0]["side"] == "sell"
    assert out[0]["reason"] == "hard_stop"


def test_plan_exits_holds_in_window():
    s = AchillesSleeve(initial_cash=10000, conservative_mode=False)
    s.open(
        event_id="e1", symbol="ACME", event_class="earnings_reaction",
        entry_price=100, score=0.2, hard_stop_price=92, profit_target_price=112,
        time_stop_date="2024-06-15", today="2024-05-29",
    )
    out = plan_exits(s, quotes={"ACME": 100}, today="2024-05-30")
    assert out == []
