import math
from datetime import datetime, timedelta

import pytest

from achilles.playbooks import build_playbooks
from achilles.scoring import (
    TIME_HALFLIFE_HOURS, has_disqualifier, liquidity_score, score_event, time_decay,
)


def test_liquidity_small_cap():
    assert liquidity_score(50_000_000) == pytest.approx(0.3)


def test_liquidity_mid_cap():
    assert liquidity_score(300_000_000) == pytest.approx(0.6)


def test_liquidity_large_cap():
    assert liquidity_score(1_000_000_000) == pytest.approx(0.8)


def test_liquidity_mega_cap():
    assert liquidity_score(10_000_000_000) == pytest.approx(1.0)


def test_liquidity_huge_cap_decays():
    assert liquidity_score(500_000_000_000) < 1.0
    assert liquidity_score(500_000_000_000) >= 0.2


def test_liquidity_megacap_below_decay_start():
    assert liquidity_score(40_000_000_000) == pytest.approx(1.0)


def test_liquidity_megacap_above_decay_end():
    assert liquidity_score(1_000_000_000_000) == pytest.approx(0.2)


def test_liquidity_tiny():
    assert liquidity_score(10_000_000) == 0.1


def test_liquidity_zero_or_negative():
    assert liquidity_score(None) == 0.0
    assert liquidity_score(0) == 0.0
    assert liquidity_score(-1) == 0.0


def test_time_decay_at_zero():
    now = datetime.utcnow()
    assert time_decay(now.isoformat(), now=now) == pytest.approx(1.0)


def test_time_decay_at_halflife():
    now = datetime.utcnow()
    seen = now - timedelta(hours=TIME_HALFLIFE_HOURS)
    assert time_decay(seen.isoformat(), now=now) == pytest.approx(0.5, abs=1e-3)


def test_time_decay_far_past():
    now = datetime.utcnow()
    seen = now - timedelta(hours=240)
    # 5 halflives -> 1/32
    assert time_decay(seen.isoformat(), now=now) < 0.05


def test_has_universal_disqualifier():
    assert has_disqualifier(["trading_halt"], "earnings_reaction")


def test_has_class_disqualifier():
    assert has_disqualifier(["guidance_withdrawn"], "earnings_reaction")


def test_no_disqualifier():
    assert not has_disqualifier(["unrelated_flag"], "earnings_reaction")


def test_score_event_disqualified_zero():
    pbs = build_playbooks()
    out = score_event(
        playbook=pbs["earnings_reaction"],
        event_strength=1.0, company_quality=1.0,
        market_cap=1_000_000_000,
        first_seen_iso=datetime.utcnow().isoformat(),
        disqualifier_flags=["trading_halt"],
    )
    assert out["score"] == 0.0


def test_score_event_disabled_playbook_zero():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    pb.disabled = True
    out = score_event(
        playbook=pb,
        event_strength=1.0, company_quality=1.0,
        market_cap=1_000_000_000,
        first_seen_iso=datetime.utcnow().isoformat(),
    )
    assert out["score"] == 0.0


def test_score_event_multiplicative():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    now = datetime.utcnow()
    out = score_event(
        playbook=pb,
        event_strength=0.8, company_quality=0.7,
        market_cap=1_000_000_000,
        first_seen_iso=now.isoformat(),
        now=now,
    )
    expected = pb.base_rate * 0.8 * 0.7 * 0.8 * 1.0  # liquidity 0.8, time_decay 1.0
    assert out["score"] == pytest.approx(expected, abs=1e-6)


def test_score_event_components_in_output():
    pbs = build_playbooks()
    now = datetime.utcnow()
    out = score_event(
        playbook=pbs["earnings_reaction"],
        event_strength=1.0, company_quality=1.0,
        market_cap=1_000_000_000,
        first_seen_iso=now.isoformat(),
        now=now,
    )
    assert "components" in out
    for k in ("base_rate", "event_strength", "company_quality", "liquidity", "time_decay"):
        assert k in out["components"]
