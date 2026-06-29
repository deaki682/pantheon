import pytest

from achilles.brief import Brief, Play, brief_from_dict, brief_to_dict, build_play, make_brief
from achilles.brief_check import BriefError, validate_brief
from achilles.playbooks import build_playbooks


def test_build_play_basic():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    p = build_play(playbook=pb, entry_price=100.0, entry_date="2024-05-29", entry_dollars=200.0)
    assert p.hard_stop_price == pytest.approx(80.0)  # -20%
    assert p.profit_target_price == pytest.approx(120.0)  # +20%
    assert p.time_stop_date == "2024-07-13"  # +45 days


def test_build_play_llm_overrides():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    p = build_play(
        playbook=pb, entry_price=100.0, entry_date="2024-05-29", entry_dollars=200.0,
        hard_stop_pct=-0.10, profit_target_pct=0.15, time_stop_days=25,
        trail_armed_at=0.06, trail_pct=0.04,
    )
    assert p.hard_stop_price == pytest.approx(90.0)
    assert p.profit_target_price == pytest.approx(115.0)
    assert p.time_stop_date == "2024-06-23"
    assert p.trail_armed_at == pytest.approx(0.06)
    assert p.trail_pct == pytest.approx(0.04)


def test_build_play_rejects_zero_price():
    pbs = build_playbooks()
    with pytest.raises(ValueError):
        build_play(playbook=pbs["earnings_reaction"], entry_price=0, entry_date="2024-01-01", entry_dollars=100)


def test_build_play_bad_date():
    pbs = build_playbooks()
    with pytest.raises(ValueError):
        build_play(playbook=pbs["earnings_reaction"], entry_price=10, entry_date="not-a-date", entry_dollars=100)


def test_make_brief_basic():
    pbs = build_playbooks()
    play = build_play(playbook=pbs["earnings_reaction"], entry_price=10, entry_date="2024-05-29", entry_dollars=200)
    b = make_brief(
        event_id="e1", event_class="earnings_reaction", symbol="acme",
        score=0.3, filing={"items": "2.02"}, setup={"prior_return": 0.05},
        disqualifiers=[], play=play,
    )
    assert b.symbol == "ACME"  # uppercased
    assert b.event_class == "earnings_reaction"
    assert b.play.profit_target_price == pytest.approx(12.0)


def test_brief_roundtrip():
    pbs = build_playbooks()
    play = build_play(playbook=pbs["earnings_reaction"], entry_price=10, entry_date="2024-05-29", entry_dollars=200)
    b = make_brief(
        event_id="e1", event_class="earnings_reaction", symbol="ACME",
        score=0.3, filing={}, setup={}, disqualifiers=[], play=play,
    )
    d = brief_to_dict(b)
    b2 = brief_from_dict(d)
    assert b2.event_id == "e1"
    assert b2.play.entry_dollars == 200.0


def test_validate_brief_ok():
    pbs = build_playbooks()
    play = build_play(playbook=pbs["earnings_reaction"], entry_price=10, entry_date="2024-05-29", entry_dollars=200)
    b = make_brief(
        event_id="e1", event_class="earnings_reaction", symbol="ACME",
        score=0.3, filing={}, setup={}, disqualifiers=[], play=play,
    )
    validate_brief(b)  # no exception


def test_validate_brief_missing_event_id():
    b = Brief(event_id="", event_class="x", symbol="X", score=0.1)
    with pytest.raises(BriefError):
        validate_brief(b)


def test_validate_brief_no_play_no_disqualifier():
    b = Brief(event_id="e", event_class="earnings_reaction", symbol="X", score=0.1)
    with pytest.raises(BriefError):
        validate_brief(b)


def test_validate_brief_disqualified_no_play_ok():
    b = Brief(
        event_id="e", event_class="earnings_reaction", symbol="X",
        score=0.0, disqualifiers=["trading_halt"], play=None,
    )
    validate_brief(b)  # disqualified briefs don't need a play


def test_validate_brief_bad_target_below_stop():
    play = Play(
        entry_dollars=100, hard_stop_price=10, profit_target_price=5,
        time_stop_date="2024-06-15",
    )
    b = Brief(event_id="e", event_class="earnings_reaction", symbol="X", score=0.1, play=play)
    with pytest.raises(BriefError):
        validate_brief(b)
