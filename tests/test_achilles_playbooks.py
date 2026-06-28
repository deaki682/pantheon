import pytest

from achilles.playbooks import (
    AUTO_DISABLE_DELTA, CLASS_DISQUALIFIERS, UNIVERSAL_DISQUALIFIERS,
    build_playbooks, maybe_autodisable, recalibrate, record_outcome,
)


def test_six_classes():
    pbs = build_playbooks()
    assert set(pbs.keys()) == {
        "earnings_reaction", "insider_cluster", "activist_13d",
        "ma_target", "spinoff_window", "guidance_revision",
    }


def test_default_uncalibrated():
    pbs = build_playbooks()
    # earnings_reaction is calibrated from backtest; others remain uncalibrated
    # Non-earnings classes are disabled pending Ghost Achilles calibration
    for name, pb in pbs.items():
        if name == "earnings_reaction":
            assert pb.uncalibrated is False
            assert pb.disabled is False
        else:
            assert pb.uncalibrated is True
            assert pb.disabled is True


def test_earnings_params():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    assert pb.hold_days == 30
    assert pb.hard_stop_pct == -0.15
    assert pb.profit_target_pct == 0.20
    assert pb.time_stop_days == 45
    assert "Bernard" in pb.citation


def test_insider_cluster_params():
    pbs = build_playbooks()
    pb = pbs["insider_cluster"]
    assert pb.hold_days == 20
    assert pb.hard_stop_pct == -0.10
    assert pb.profit_target_pct == 0.15
    assert pb.time_stop_days == 30


def test_activist_params():
    pbs = build_playbooks()
    pb = pbs["activist_13d"]
    assert pb.hold_days == 5
    assert pb.hard_stop_pct == -0.07
    assert pb.profit_target_pct == 0.10
    assert pb.time_stop_days == 10


def test_ma_params():
    pbs = build_playbooks()
    pb = pbs["ma_target"]
    assert pb.hard_stop_pct == -0.05
    assert pb.profit_target_pct == 0.06


def test_spinoff_params():
    pbs = build_playbooks()
    pb = pbs["spinoff_window"]
    assert pb.hold_days == 15
    assert pb.time_stop_days == 25


def test_guidance_params():
    pbs = build_playbooks()
    pb = pbs["guidance_revision"]
    assert pb.hold_days == 5
    assert pb.profit_target_pct == 0.10


def test_universal_disqualifiers_present():
    for d in ("trading_halt", "delisting_notice", "bankruptcy_filing", "going_concern"):
        assert d in UNIVERSAL_DISQUALIFIERS


def test_class_disqualifiers_per_class():
    assert "guidance_withdrawn" in CLASS_DISQUALIFIERS["earnings_reaction"]
    assert "concurrent_dilution" in CLASS_DISQUALIFIERS["insider_cluster"]
    assert "13d_amendment_reduces_below_5pct" in CLASS_DISQUALIFIERS["activist_13d"]


def test_record_and_autodisable():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    pb.expected_hit_rate = 0.55
    # 20 outcomes, only 8 hits -> 0.40 live rate, 15pp below expected
    for i in range(20):
        record_outcome(pb, hit=(i < 8))
    assert maybe_autodisable(pb, min_n=20) is True
    assert pb.disabled is True


def test_no_autodisable_when_close_to_expected():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    pb.expected_hit_rate = 0.55
    for i in range(20):
        record_outcome(pb, hit=(i < 10))  # 50% — only 5pp below
    assert maybe_autodisable(pb, min_n=20) is False
    assert pb.disabled is False


def test_no_autodisable_when_small_n():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    for i in range(5):
        record_outcome(pb, hit=False)
    assert maybe_autodisable(pb, min_n=20) is False


def test_recalibrate_flips_flag():
    pbs = build_playbooks()
    pb = pbs["insider_cluster"]
    assert pb.uncalibrated is True
    recalibrate(pb, new_base_rate=0.60, new_hold_days=18)
    assert pb.uncalibrated is False
    assert pb.base_rate == 0.60
    assert pb.hold_days == 18


def test_earnings_calibrated_from_backtest():
    pbs = build_playbooks()
    pb = pbs["earnings_reaction"]
    assert pb.base_rate == 0.70
    assert pb.expected_hit_rate == 0.70
    assert pb.uncalibrated is False


def test_auto_disable_delta():
    assert AUTO_DISABLE_DELTA == 0.10
